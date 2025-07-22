"""
SQL 검증 및 최적화 서비스

이 모듈은 생성된 SQL의 문법 검증, SQL 인젝션 방지 및 보안 검사, 쿼리 최적화 제안 기능을 구현합니다.
"""
from typing import Dict, Any, List, Optional, Tuple
import re
import logging
from enum import Enum
import sqlparse
import json

from .base import LLMService
from .response_utils import validate_sql_query, extract_sql_from_response
from .prompt_utils import SQL_VALIDATION_TEMPLATE, create_schema_context
from backend.db.connectors.dialect_handler import SQLDialectHandler

logger = logging.getLogger(__name__)


class SQLValidationLevel(str, Enum):
    """SQL 검증 수준"""
    BASIC = "basic"  # 기본 문법 및 보안 검사
    STANDARD = "standard"  # 기본 + 스키마 검증
    STRICT = "strict"  # 기본 + 스키마 검증 + 성능 검사


class SQLValidator:
    """SQL 검증 및 최적화 서비스 클래스"""
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        SQL 검증 및 최적화 서비스 초기화
        
        Args:
            llm_service (Optional[LLMService]): LLM 서비스 인스턴스 (고급 검증 및 최적화에 사용)
        """
        self.llm_service = llm_service
    
    def validate_sql(
        self,
        sql_query: str,
        db_type: str,
        schema: Optional[Dict[str, Any]] = None,
        validation_level: SQLValidationLevel = SQLValidationLevel.STANDARD
    ) -> Tuple[bool, List[str], List[str]]:
        """
        SQL 쿼리 검증
        
        Args:
            sql_query (str): 검증할 SQL 쿼리
            db_type (str): 데이터베이스 유형 ('mssql' 또는 'hana')
            schema (Optional[Dict[str, Any]]): DB 스키마 정보 (스키마 검증에 사용)
            validation_level (SQLValidationLevel): 검증 수준
            
        Returns:
            Tuple[bool, List[str], List[str]]: (유효성 여부, 오류 메시지 목록, 경고 메시지 목록)
        """
        errors = []
        warnings = []
        
        # 1. 기본 문법 및 보안 검사
        is_valid, error_msg = self._validate_basic_syntax(sql_query)
        if not is_valid:
            errors.append(error_msg)
            return False, errors, warnings
        
        # 2. SQL 인젝션 패턴 검사
        injection_issues = self._check_sql_injection(sql_query)
        if injection_issues:
            errors.extend(injection_issues)
            return False, errors, warnings
        
        # 3. 데이터베이스 방언 호환성 검사
        is_compatible, incompatibility_reason = SQLDialectHandler.is_compatible(sql_query, db_type)
        if not is_compatible:
            warnings.append(f"데이터베이스 방언 호환성 문제: {incompatibility_reason}")
        
        # 4. 스키마 검증 (STANDARD 이상)
        if validation_level in [SQLValidationLevel.STANDARD, SQLValidationLevel.STRICT] and schema:
            schema_issues = self._validate_schema(sql_query, schema)
            if schema_issues:
                warnings.extend(schema_issues)
        
        # 5. 성능 최적화 검사 (STRICT)
        if validation_level == SQLValidationLevel.STRICT:
            performance_warnings = self._check_performance_issues(sql_query, db_type)
            if performance_warnings:
                warnings.extend(performance_warnings)
        
        return len(errors) == 0, errors, warnings
    
    async def optimize_sql(
        self,
        sql_query: str,
        db_type: str,
        schema: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[str]]:
        """
        SQL 쿼리 최적화
        
        Args:
            sql_query (str): 최적화할 SQL 쿼리
            db_type (str): 데이터베이스 유형 ('mssql' 또는 'hana')
            schema (Optional[Dict[str, Any]]): DB 스키마 정보
            
        Returns:
            Tuple[str, List[str]]: (최적화된 SQL 쿼리, 최적화 설명 목록)
        """
        optimizations = []
        optimized_query = sql_query
        
        # 1. 기본 최적화 적용
        optimized_query, basic_optimizations = self._apply_basic_optimizations(sql_query, db_type)
        optimizations.extend(basic_optimizations)
        
        # 2. 데이터베이스별 최적화 제안
        db_optimizations = SQLDialectHandler.suggest_optimizations(optimized_query, db_type)
        optimizations.extend(db_optimizations)
        
        # 3. LLM 기반 고급 최적화 (LLM 서비스가 있는 경우)
        if self.llm_service and schema:
            try:
                # 스키마 정보를 포함한 최적화 요청
                schema_json = create_schema_context(schema)
                
                # 성능 최적화를 위한 힌트 추가
                performance_warnings = self._check_performance_issues(optimized_query, db_type)
                performance_context = ""
                if performance_warnings:
                    performance_context = "### 성능 개선 필요 사항:\n" + "\n".join([f"- {warning}" for warning in performance_warnings])
                
                # LLM에 최적화 요청
                llm_optimized_query, is_modified = await self.llm_service.validate_and_fix_sql(
                    optimized_query, 
                    schema, 
                    db_type,
                    f"SQL 쿼리를 최적화해주세요. {performance_context}"
                )
                
                if is_modified:
                    # 최적화된 쿼리가 유효한지 확인
                    is_valid, errors, _ = self.validate_sql(llm_optimized_query, db_type, schema)
                    
                    if is_valid:
                        optimized_query = llm_optimized_query
                        optimizations.append("LLM 기반 최적화가 적용되었습니다.")
                        
                        # 최적화 전후 비교 분석
                        if optimized_query != sql_query:
                            # 쿼리 길이 변화
                            original_length = len(sql_query)
                            optimized_length = len(optimized_query)
                            length_diff = original_length - optimized_length
                            
                            if length_diff > 0:
                                optimizations.append(f"쿼리 길이가 {length_diff}자 ({(length_diff/original_length)*100:.1f}%) 감소했습니다.")
                            
                            # 주요 최적화 패턴 감지
                            if "SELECT *" in sql_query and "SELECT *" not in optimized_query:
                                optimizations.append("필요한 컬럼만 선택하도록 최적화되었습니다.")
                            
                            if "WITH (NOLOCK)" in optimized_query and "WITH (NOLOCK)" not in sql_query:
                                optimizations.append("읽기 성능 향상을 위해 NOLOCK 힌트가 추가되었습니다.")
                            
                            if "TOP" in optimized_query and "TOP" not in sql_query:
                                optimizations.append("결과 제한을 위해 TOP 절이 추가되었습니다.")
                    else:
                        # 최적화된 쿼리가 유효하지 않으면 원본 쿼리 유지
                        optimizations.append(f"LLM 최적화 결과가 유효하지 않아 적용되지 않았습니다: {', '.join(errors)}")
            except Exception as e:
                logger.error(f"LLM 기반 최적화 중 오류 발생: {str(e)}")
                optimizations.append(f"LLM 기반 최적화 실패: {str(e)}")
        
        return optimized_query, optimizations
    
    def _validate_basic_syntax(self, sql_query: str) -> Tuple[bool, Optional[str]]:
        """
        기본 SQL 문법 검증
        
        Args:
            sql_query (str): 검증할 SQL 쿼리
            
        Returns:
            Tuple[bool, Optional[str]]: (유효성 여부, 오류 메시지)
        """
        # 빈 쿼리 확인
        if not sql_query or not sql_query.strip():
            return False, "SQL 쿼리가 비어 있습니다."
        
        # 기본 SQL 구문 확인
        try:
            # 주석 제거
            query_without_comments = re.sub(r"--.*?(\n|$)", "", sql_query)
            query_without_comments = re.sub(r"/\*.*?\*/", "", query_without_comments, flags=re.DOTALL)
            
            # 첫 번째 단어 추출 (SQL 작업)
            first_word_match = re.search(r"^\s*(\w+)", query_without_comments)
            if not first_word_match:
                return False, "SQL 쿼리에서 작업을 식별할 수 없습니다."
            
            operation = first_word_match.group(1).upper()
            
            # SELECT 작업만 허용
            if operation != "SELECT":
                return False, f"SQL 작업 '{operation}'은(는) 허용되지 않습니다. 오직 SELECT 작업만 허용됩니다."
            
            # 기본 구문 요소 확인
            if "FROM" not in query_without_comments.upper():
                return False, "SQL 쿼리에 FROM 절이 없습니다."
            
            # 괄호 짝 확인
            if query_without_comments.count('(') != query_without_comments.count(')'):
                return False, "SQL 쿼리에 괄호 짝이 맞지 않습니다."
            
            # SQL 파싱을 통한 추가 검증
            try:
                parsed = sqlparse.parse(query_without_comments)
                if not parsed:
                    return False, "SQL 쿼리를 파싱할 수 없습니다."
            except Exception as e:
                return False, f"SQL 파싱 중 오류 발생: {str(e)}"
            
            return True, None
            
        except Exception as e:
            return False, f"SQL 구문 검증 중 오류 발생: {str(e)}"
    
    def _check_sql_injection(self, sql_query: str) -> List[str]:
        """
        SQL 인젝션 패턴 검사
        
        Args:
            sql_query (str): 검사할 SQL 쿼리
            
        Returns:
            List[str]: 발견된 SQL 인젝션 패턴 목록
        """
        injection_issues = []
        
        # 주석 제거
        query_without_comments = re.sub(r"--.*?(\n|$)", "", sql_query)
        query_without_comments = re.sub(r"/\*.*?\*/", "", query_without_comments, flags=re.DOTALL)
        
        # SQL 인젝션 패턴 확인 (확장된 패턴 목록)
        injection_patterns = [
            # 기본 SQL 인젝션 패턴
            (r";\s*\w+", "세미콜론 뒤에 다른 명령이 있습니다."),
            (r"UNION\s+ALL\s+SELECT", "UNION ALL SELECT 패턴이 감지되었습니다."),
            (r"UNION\s+SELECT", "UNION SELECT 패턴이 감지되었습니다."),
            
            # 데이터 조작/정의 명령
            (r"DROP\s+TABLE", "DROP TABLE 명령이 감지되었습니다."),
            (r"DROP\s+DATABASE", "DROP DATABASE 명령이 감지되었습니다."),
            (r"ALTER\s+TABLE", "ALTER TABLE 명령이 감지되었습니다."),
            (r"DELETE\s+FROM", "DELETE FROM 명령이 감지되었습니다."),
            (r"INSERT\s+INTO", "INSERT INTO 명령이 감지되었습니다."),
            (r"UPDATE\s+\w+\s+SET", "UPDATE SET 명령이 감지되었습니다."),
            (r"TRUNCATE\s+TABLE", "TRUNCATE TABLE 명령이 감지되었습니다."),
            (r"CREATE\s+TABLE", "CREATE TABLE 명령이 감지되었습니다."),
            (r"CREATE\s+DATABASE", "CREATE DATABASE 명령이 감지되었습니다."),
            (r"CREATE\s+INDEX", "CREATE INDEX 명령이 감지되었습니다."),
            (r"CREATE\s+PROCEDURE", "CREATE PROCEDURE 명령이 감지되었습니다."),
            (r"CREATE\s+FUNCTION", "CREATE FUNCTION 명령이 감지되었습니다."),
            (r"CREATE\s+TRIGGER", "CREATE TRIGGER 명령이 감지되었습니다."),
            (r"CREATE\s+VIEW", "CREATE VIEW 명령이 감지되었습니다."),
            (r"GRANT\s+", "GRANT 권한 명령이 감지되었습니다."),
            (r"REVOKE\s+", "REVOKE 권한 명령이 감지되었습니다."),
            
            # 저장 프로시저 및 명령 실행
            (r"EXEC\s*\(", "EXEC() 함수 호출이 감지되었습니다."),
            (r"EXECUTE\s*\(", "EXECUTE() 함수 호출이 감지되었습니다."),
            (r"xp_cmdshell", "xp_cmdshell 저장 프로시저 호출이 감지되었습니다."),
            (r"sp_executesql", "sp_executesql 저장 프로시저 호출이 감지되었습니다."),
            (r"sp_OACreate", "sp_OACreate 저장 프로시저 호출이 감지되었습니다."),
            (r"sp_OAMethod", "sp_OAMethod 저장 프로시저 호출이 감지되었습니다."),
            (r"sp_configure", "sp_configure 저장 프로시저 호출이 감지되었습니다."),
            (r"xp_regread", "xp_regread 저장 프로시저 호출이 감지되었습니다."),
            (r"xp_regwrite", "xp_regwrite 저장 프로시저 호출이 감지되었습니다."),
            
            # 시간 지연 및 블라인드 인젝션 패턴
            (r"WAITFOR\s+DELAY", "WAITFOR DELAY 명령이 감지되었습니다."),
            (r"SLEEP\s*\(", "SLEEP() 함수 호출이 감지되었습니다."),
            (r"BENCHMARK\s*\(", "BENCHMARK() 함수 호출이 감지되었습니다."),
            (r"PG_SLEEP\s*\(", "PG_SLEEP() 함수 호출이 감지되었습니다."),
            
            # 파일 시스템 접근
            (r"LOAD_FILE\s*\(", "LOAD_FILE() 함수 호출이 감지되었습니다."),
            (r"LOAD\s+DATA\s+INFILE", "LOAD DATA INFILE 명령이 감지되었습니다."),
            (r"SELECT\s+.*\s+INTO\s+OUTFILE", "SELECT INTO OUTFILE 명령이 감지되었습니다."),
            (r"SELECT\s+.*\s+INTO\s+DUMPFILE", "SELECT INTO DUMPFILE 명령이 감지되었습니다."),
            
            # 시스템 명령
            (r"SHUTDOWN", "SHUTDOWN 명령이 감지되었습니다."),
            (r"KILL\s+\d+", "KILL 명령이 감지되었습니다."),
            
            # 의심스러운 변환 및 조작
            (r"CONVERT\s*\(\s*INT\s*,", "의심스러운 형변환이 감지되었습니다."),
            (r"CAST\s*\(\s*.*\s+AS\s+INT\s*\)", "의심스러운 형변환이 감지되었습니다."),
            
            # 주석 및 코드 숨김
            (r"--", "인라인 주석이 감지되었습니다."),
            (r"/\*", "블록 주석이 감지되었습니다."),
            (r"#", "해시 주석이 감지되었습니다."),
            
            # 조건 우회 패턴
            (r"OR\s+1\s*=\s*1", "OR 1=1 패턴이 감지되었습니다."),
            (r"OR\s+'1'\s*=\s*'1'", "OR '1'='1' 패턴이 감지되었습니다."),
            (r"OR\s+\w+\s*=\s*\w+", "OR 조건에 의심스러운 패턴이 감지되었습니다."),
            (r"OR\s+\d+\s*>\s*\d+", "OR 조건에 의심스러운 패턴이 감지되었습니다."),
            (r"OR\s+\d+\s*<\s*\d+", "OR 조건에 의심스러운 패턴이 감지되었습니다."),
            (r"OR\s+\w+\s+LIKE\s+", "OR LIKE 조건에 의심스러운 패턴이 감지되었습니다."),
            (r"AND\s+1\s*=\s*1", "AND 1=1 패턴이 감지되었습니다."),
            (r"AND\s+0\s*=\s*0", "AND 0=0 패턴이 감지되었습니다."),
            (r"AND\s+'1'\s*=\s*'1'", "AND '1'='1' 패턴이 감지되었습니다."),
            
            # 기타 위험한 함수
            (r"SUSER_NAME\s*\(", "SUSER_NAME() 함수 호출이 감지되었습니다."),
            (r"USER_NAME\s*\(", "USER_NAME() 함수 호출이 감지되었습니다."),
            (r"SYSTEM_USER", "SYSTEM_USER 함수 호출이 감지되었습니다."),
            (r"IS_SRVROLEMEMBER\s*\(", "IS_SRVROLEMEMBER() 함수 호출이 감지되었습니다."),
            (r"IS_MEMBER\s*\(", "IS_MEMBER() 함수 호출이 감지되었습니다.")
        ]
        
        for pattern, message in injection_patterns:
            if re.search(pattern, query_without_comments, re.IGNORECASE):
                injection_issues.append(f"SQL 인젝션 위험: {message}")
        
        # 추가 보안 검사: 여러 명령문 실행 시도 확인
        if ";" in query_without_comments:
            statements = [stmt.strip() for stmt in query_without_comments.split(";") if stmt.strip()]
            if len(statements) > 1:
                injection_issues.append("SQL 인젝션 위험: 여러 SQL 명령문이 감지되었습니다.")
        
        # 추가 보안 검사: 중첩 쿼리 깊이 확인
        nested_query_count = query_without_comments.count("SELECT") - 1
        if nested_query_count > 3:
            injection_issues.append(f"SQL 인젝션 위험: 과도하게 중첩된 쿼리({nested_query_count}개)가 감지되었습니다.")
        
        # 추가 보안 검사: 문자열 리터럴 내 의심스러운 패턴
        string_literals = re.findall(r"'(.*?)'", query_without_comments)
        for literal in string_literals:
            # 문자열 내 SQL 키워드 확인
            sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "EXEC", "UNION"]
            for keyword in sql_keywords:
                if keyword in literal.upper():
                    injection_issues.append(f"SQL 인젝션 위험: 문자열 리터럴 내에 SQL 키워드 '{keyword}'가 포함되어 있습니다.")
            
            # 문자열 내 이스케이프 시퀀스 확인
            if "\\'" in literal or "''" in literal:
                injection_issues.append("SQL 인젝션 위험: 문자열 리터럴 내에 따옴표 이스케이프 시퀀스가 포함되어 있습니다.")
        
        # 추가 보안 검사: 동적 쿼리 생성 패턴
        if "+" in query_without_comments and "'" in query_without_comments:
            injection_issues.append("SQL 인젝션 위험: 문자열 연결(+)과 따옴표가 함께 사용되어 동적 쿼리 생성이 의심됩니다.")
        
        # 추가 보안 검사: 16진수 인코딩 사용
        if re.search(r"0x[0-9a-fA-F]{10,}", query_without_comments):
            injection_issues.append("SQL 인젝션 위험: 긴 16진수 인코딩 문자열이 감지되었습니다.")
        
        return injection_issues
    
    def _validate_schema(self, sql_query: str, schema: Dict[str, Any]) -> List[str]:
        """
        SQL 쿼리와 DB 스키마 일치 여부 검증
        
        Args:
            sql_query (str): 검증할 SQL 쿼리
            schema (Dict[str, Any]): DB 스키마 정보
            
        Returns:
            List[str]: 스키마 관련 문제 목록
        """
        schema_issues = []
        
        # 테이블 및 컬럼 추출
        tables_in_query = self._extract_tables_from_query(sql_query)
        columns_in_query = self._extract_columns_from_query(sql_query)
        
        # 스키마에서 테이블 및 컬럼 정보 가져오기
        schema_tables = {}  # 테이블 이름 -> 테이블 정보 매핑
        schema_columns = set()  # 모든 컬럼 (테이블명.컬럼명 형식)
        table_columns = {}  # 테이블 이름 -> 컬럼 목록 매핑
        
        for schema_item in schema.get("schemas", []):
            schema_name = schema_item.get("name", "").lower()
            
            for table in schema_item.get("tables", []):
                table_name = table.get("name", "").lower()
                schema_tables[table_name] = table
                table_columns[table_name] = []
                
                for column in table.get("columns", []):
                    column_name = column.get("name", "").lower()
                    schema_columns.add(f"{table_name}.{column_name}")
                    table_columns[table_name].append({
                        "name": column_name,
                        "type": column.get("type", ""),
                        "nullable": column.get("nullable", True)
                    })
        
        # 테이블 존재 여부 확인
        for table in tables_in_query:
            if table.lower() not in schema_tables:
                schema_issues.append(f"테이블 '{table}'이(가) 스키마에 존재하지 않습니다.")
                # 유사한 테이블 이름 제안
                similar_tables = [t for t in schema_tables.keys() if self._is_similar(table.lower(), t)]
                if similar_tables:
                    schema_issues.append(f"혹시 다음 테이블을 찾으시나요? {', '.join(similar_tables)}")
        
        # 컬럼 존재 여부 확인
        for column in columns_in_query:
            if "." in column:
                # 테이블이 명시된 컬럼 (예: table.column)
                if column.lower() not in schema_columns:
                    table_part, column_part = column.lower().split(".", 1)
                    
                    # 테이블은 존재하지만 컬럼이 없는 경우
                    if table_part in schema_tables:
                        schema_issues.append(f"컬럼 '{column}'이(가) 테이블 '{table_part}'에 존재하지 않습니다.")
                        
                        # 유사한 컬럼 이름 제안
                        if table_part in table_columns:
                            similar_columns = [col["name"] for col in table_columns[table_part] 
                                              if self._is_similar(column_part, col["name"])]
                            if similar_columns:
                                schema_issues.append(f"혹시 다음 컬럼을 찾으시나요? {', '.join(similar_columns)}")
                    else:
                        schema_issues.append(f"테이블 '{table_part}'이(가) 스키마에 존재하지 않습니다.")
            else:
                # 테이블이 명시되지 않은 컬럼
                matching_columns = []
                for schema_column in schema_columns:
                    if schema_column.endswith(f".{column.lower()}"):
                        matching_columns.append(schema_column)
                
                if not matching_columns:
                    schema_issues.append(f"컬럼 '{column}'이(가) 스키마에 존재하지 않습니다.")
                elif len(matching_columns) > 1:
                    # 여러 테이블에 동일한 이름의 컬럼이 있는 경우
                    tables_with_column = [col.split(".")[0] for col in matching_columns]
                    schema_issues.append(f"컬럼 '{column}'이(가) 여러 테이블({', '.join(tables_with_column)})에 존재하여 모호합니다. 테이블 이름을 명시하세요.")
        
        # JOIN 조건 검증
        if "JOIN" in sql_query.upper():
            join_conditions = self._extract_join_conditions(sql_query)
            
            for condition in join_conditions:
                left_col, right_col = condition
                
                # 양쪽 컬럼이 모두 스키마에 존재하는지 확인
                if left_col.lower() not in schema_columns:
                    schema_issues.append(f"JOIN 조건의 컬럼 '{left_col}'이(가) 스키마에 존재하지 않습니다.")
                
                if right_col.lower() not in schema_columns:
                    schema_issues.append(f"JOIN 조건의 컬럼 '{right_col}'이(가) 스키마에 존재하지 않습니다.")
                
                # 데이터 타입 호환성 확인
                if left_col.lower() in schema_columns and right_col.lower() in schema_columns:
                    left_table, left_column = left_col.lower().split(".", 1)
                    right_table, right_column = right_col.lower().split(".", 1)
                    
                    left_type = next((col["type"] for col in table_columns.get(left_table, []) 
                                     if col["name"] == left_column), None)
                    right_type = next((col["type"] for col in table_columns.get(right_table, []) 
                                      if col["name"] == right_column), None)
                    
                    if left_type and right_type and not self._are_types_compatible(left_type, right_type):
                        schema_issues.append(f"JOIN 조건의 컬럼 '{left_col}'({left_type})과 '{right_col}'({right_type})의 데이터 타입이 호환되지 않을 수 있습니다.")
        
        # WHERE 조건에서 NULL 비교 검증
        if "WHERE" in sql_query.upper():
            null_comparisons = self._extract_null_comparisons(sql_query)
            
            for column, operator in null_comparisons:
                if "." in column:
                    table_part, column_part = column.lower().split(".", 1)
                    
                    # NULL 비교 시 올바른 연산자 사용 확인
                    if operator not in ["IS", "IS NOT"]:
                        schema_issues.append(f"NULL 비교 시 '{operator}' 대신 'IS NULL' 또는 'IS NOT NULL'을 사용해야 합니다.")
        
        return schema_issues
    
    def _is_similar(self, str1: str, str2: str, threshold: float = 0.7) -> bool:
        """
        두 문자열의 유사도 확인 (간단한 구현)
        
        Args:
            str1 (str): 첫 번째 문자열
            str2 (str): 두 번째 문자열
            threshold (float): 유사도 임계값 (0.0 ~ 1.0)
            
        Returns:
            bool: 유사도가 임계값 이상이면 True
        """
        # 완전히 동일한 경우
        if str1 == str2:
            return True
        
        # 한 문자열이 다른 문자열에 포함된 경우
        if str1 in str2 or str2 in str1:
            return True
        
        # 문자열 길이가 너무 다른 경우
        if len(str1) < 3 or len(str2) < 3:
            return False
        
        # 간단한 편집 거리 기반 유사도 계산
        common_chars = set(str1) & set(str2)
        similarity = len(common_chars) / max(len(set(str1)), len(set(str2)))
        
        return similarity >= threshold
    
    def _are_types_compatible(self, type1: str, type2: str) -> bool:
        """
        두 데이터 타입의 호환성 확인
        
        Args:
            type1 (str): 첫 번째 데이터 타입
            type2 (str): 두 번째 데이터 타입
            
        Returns:
            bool: 호환 가능하면 True
        """
        # 대소문자 무시하고 비교
        type1 = type1.upper()
        type2 = type2.upper()
        
        # 완전히 동일한 타입
        if type1 == type2:
            return True
        
        # 숫자 타입 호환성
        numeric_types = ["INT", "INTEGER", "SMALLINT", "BIGINT", "TINYINT", "DECIMAL", "NUMERIC", "FLOAT", "REAL", "DOUBLE"]
        if any(t in type1 for t in numeric_types) and any(t in type2 for t in numeric_types):
            return True
        
        # 문자열 타입 호환성
        string_types = ["CHAR", "VARCHAR", "TEXT", "NCHAR", "NVARCHAR", "NTEXT", "STRING"]
        if any(t in type1 for t in string_types) and any(t in type2 for t in string_types):
            return True
        
        # 날짜/시간 타입 호환성
        date_types = ["DATE", "TIME", "DATETIME", "TIMESTAMP", "SMALLDATETIME"]
        if any(t in type1 for t in date_types) and any(t in type2 for t in date_types):
            return True
        
        # 기본적으로 호환되지 않음
        return False
    
    def _extract_join_conditions(self, sql_query: str) -> List[Tuple[str, str]]:
        """
        SQL 쿼리에서 JOIN 조건 추출
        
        Args:
            sql_query (str): SQL 쿼리
            
        Returns:
            List[Tuple[str, str]]: JOIN 조건 목록 (왼쪽 컬럼, 오른쪽 컬럼)
        """
        join_conditions = []
        
        # JOIN ... ON 패턴 찾기
        join_pattern = r"JOIN\s+(\w+)(?:\s+AS\s+|\s+)?(\w+)?\s+ON\s+([\w.]+)\s*=\s*([\w.]+)"
        join_matches = re.finditer(join_pattern, sql_query, re.IGNORECASE)
        
        for match in join_matches:
            table = match.group(1)
            alias = match.group(2) or table
            left_col = match.group(3)
            right_col = match.group(4)
            
            # 테이블 별칭이 없는 경우 테이블 이름 추가
            if "." not in left_col:
                # 어떤 테이블의 컬럼인지 추측할 수 없음
                continue
            
            if "." not in right_col:
                # 어떤 테이블의 컬럼인지 추측할 수 없음
                continue
            
            join_conditions.append((left_col, right_col))
        
        return join_conditions
    
    def _extract_null_comparisons(self, sql_query: str) -> List[Tuple[str, str]]:
        """
        SQL 쿼리에서 NULL 비교 추출
        
        Args:
            sql_query (str): SQL 쿼리
            
        Returns:
            List[Tuple[str, str]]: NULL 비교 목록 (컬럼, 연산자)
        """
        null_comparisons = []
        
        # NULL 비교 패턴 찾기
        null_pattern = r"([\w.]+)\s+(=|!=|<>|IS|IS NOT)\s+NULL"
        null_matches = re.finditer(null_pattern, sql_query, re.IGNORECASE)
        
        for match in null_matches:
            column = match.group(1)
            operator = match.group(2).upper()
            null_comparisons.append((column, operator))
        
        return null_comparisons
    
    def _extract_tables_from_query(self, sql_query: str) -> List[str]:
        """
        SQL 쿼리에서 테이블 이름 추출
        
        Args:
            sql_query (str): SQL 쿼리
            
        Returns:
            List[str]: 추출된 테이블 이름 목록
        """
        tables = []
        
        # FROM 절과 JOIN 절에서 테이블 추출
        from_pattern = r"FROM\s+([^\s,;()]+)"
        join_pattern = r"JOIN\s+([^\s,;()]+)"
        
        from_matches = re.finditer(from_pattern, sql_query, re.IGNORECASE)
        join_matches = re.finditer(join_pattern, sql_query, re.IGNORECASE)
        
        for match in from_matches:
            tables.append(match.group(1))
        
        for match in join_matches:
            tables.append(match.group(1))
        
        # 별칭 제거
        clean_tables = []
        for table in tables:
            # 별칭이 있는 경우 (예: "table AS alias" 또는 "table alias")
            alias_match = re.match(r"([^\s]+)\s+(?:AS\s+)?([^\s]+)", table, re.IGNORECASE)
            if alias_match:
                clean_tables.append(alias_match.group(1))
            else:
                clean_tables.append(table)
        
        return clean_tables
    
    def _extract_columns_from_query(self, sql_query: str) -> List[str]:
        """
        SQL 쿼리에서 컬럼 이름 추출
        
        Args:
            sql_query (str): SQL 쿼리
            
        Returns:
            List[str]: 추출된 컬럼 이름 목록
        """
        columns = []
        
        # SELECT 절에서 컬럼 추출
        select_pattern = r"SELECT\s+(.*?)\s+FROM"
        select_match = re.search(select_pattern, sql_query, re.IGNORECASE | re.DOTALL)
        
        if select_match:
            select_columns = select_match.group(1).split(",")
            for column in select_columns:
                column = column.strip()
                
                # 별칭 제거
                alias_match = re.match(r"(.*?)\s+(?:AS\s+)?([^\s]+)$", column, re.IGNORECASE)
                if alias_match:
                    column = alias_match.group(1).strip()
                
                # 함수 호출 제외
                if not re.match(r".*\(.*\).*", column):
                    # 테이블 명시된 컬럼 (예: "table.column")
                    if "." in column:
                        columns.append(column)
                    # 일반 컬럼
                    elif column != "*":
                        columns.append(column)
        
        # WHERE 절에서 컬럼 추출
        where_pattern = r"WHERE\s+(.*?)(?:ORDER BY|GROUP BY|HAVING|$)"
        where_match = re.search(where_pattern, sql_query, re.IGNORECASE | re.DOTALL)
        
        if where_match:
            where_clause = where_match.group(1)
            # 컬럼 = 값 패턴
            column_pattern = r"([^\s=<>!]+)\s*[=<>!]"
            column_matches = re.finditer(column_pattern, where_clause)
            
            for match in column_matches:
                column = match.group(1).strip()
                if not re.match(r".*\(.*\).*", column):
                    columns.append(column)
        
        return columns
    
    def _check_performance_issues(self, sql_query: str, db_type: str) -> List[str]:
        """
        SQL 쿼리 성능 이슈 검사
        
        Args:
            sql_query (str): 검사할 SQL 쿼리
            db_type (str): 데이터베이스 유형
            
        Returns:
            List[str]: 성능 관련 경고 목록
        """
        performance_warnings = []
        
        # 1. SELECT * 사용 확인
        if re.search(r"SELECT\s+\*", sql_query, re.IGNORECASE):
            performance_warnings.append("'SELECT *' 사용은 필요한 컬럼만 선택하는 것보다 성능이 떨어질 수 있습니다.")
        
        # 2. WHERE 절 없는 대규모 테이블 쿼리 확인
        if re.search(r"FROM\s+\w+(?:\s+\w+)?(?!\s+WHERE)", sql_query, re.IGNORECASE):
            performance_warnings.append("WHERE 절 없이 테이블을 쿼리하면 전체 테이블을 스캔하여 성능이 저하될 수 있습니다.")
        
        # 3. DISTINCT 사용 확인
        if re.search(r"SELECT\s+DISTINCT", sql_query, re.IGNORECASE):
            performance_warnings.append("DISTINCT 사용은 정렬 작업이 필요하여 성능에 영향을 줄 수 있습니다.")
        
        # 4. 서브쿼리 사용 확인
        subquery_count = len(re.findall(r"\(\s*SELECT", sql_query, re.IGNORECASE))
        if subquery_count > 0:
            performance_warnings.append(f"서브쿼리({subquery_count}개)는 JOIN으로 대체하면 성능이 향상될 수 있습니다.")
            
            # 상관 서브쿼리(correlated subquery) 확인
            if re.search(r"\(\s*SELECT.*?FROM.*?WHERE.*?=\s*\w+\.\w+", sql_query, re.IGNORECASE | re.DOTALL):
                performance_warnings.append("상관 서브쿼리는 성능에 큰 영향을 줄 수 있습니다. JOIN으로 대체를 고려하세요.")
        
        # 5. 함수 사용으로 인한 인덱스 미사용 확인
        if re.search(r"WHERE\s+\w+\s*\(\s*[\w.]+\s*\)", sql_query, re.IGNORECASE):
            performance_warnings.append("WHERE 절에서 컬럼에 함수를 적용하면 인덱스를 사용할 수 없어 성능이 저하될 수 있습니다.")
        
        # 6. 여러 OR 조건 사용 확인
        or_count = len(re.findall(r"\bOR\b", sql_query, re.IGNORECASE))
        if or_count > 2:
            performance_warnings.append(f"다수의 OR 조건({or_count}개)은 쿼리 최적화를 방해할 수 있습니다. IN 절 사용을 고려하세요.")
        
        # 7. 복잡한 JOIN 확인
        join_count = len(re.findall(r"\bJOIN\b", sql_query, re.IGNORECASE))
        if join_count > 3:
            performance_warnings.append(f"다수의 JOIN({join_count}개)은 성능에 영향을 줄 수 있습니다. 쿼리 분할을 고려하세요.")
        
        # 8. GROUP BY와 ORDER BY 함께 사용 확인
        if re.search(r"GROUP\s+BY", sql_query, re.IGNORECASE) and re.search(r"ORDER\s+BY", sql_query, re.IGNORECASE):
            performance_warnings.append("GROUP BY와 ORDER BY를 함께 사용하면 정렬 작업이 두 번 발생할 수 있습니다.")
        
        # 9. LIKE 패턴 확인
        if re.search(r"LIKE\s+['\"]%", sql_query, re.IGNORECASE):
            performance_warnings.append("LIKE '%...'와 같은 패턴은 인덱스를 사용할 수 없어 성능이 저하될 수 있습니다.")
        
        # 10. 문자열 함수 사용 확인
        string_functions = ["UPPER", "LOWER", "SUBSTRING", "CONCAT", "REPLACE", "TRIM", "LTRIM", "RTRIM"]
        for func in string_functions:
            if re.search(rf"\b{func}\s*\(", sql_query, re.IGNORECASE):
                performance_warnings.append(f"{func} 함수 사용은 인덱스 활용을 방해할 수 있습니다.")
                break
        
        # 데이터베이스별 특화 검사
        if db_type == "mssql":
            # MS-SQL 특화 검사
            
            # NOLOCK 힌트 확인
            if "SELECT" in sql_query.upper() and "WITH (NOLOCK)" not in sql_query.upper():
                performance_warnings.append("MS-SQL에서는 읽기 전용 쿼리에 WITH (NOLOCK) 힌트를 추가하여 동시성을 향상시킬 수 있습니다.")
            
            # 임시 테이블 사용 확인
            if "#" in sql_query:
                performance_warnings.append("임시 테이블(#)은 성능에 영향을 줄 수 있습니다. 테이블 변수(@) 사용을 고려하세요.")
            
            # 커서 사용 확인
            if re.search(r"\bDECLARE\s+\w+\s+CURSOR\b", sql_query, re.IGNORECASE):
                performance_warnings.append("커서 사용은 성능에 큰 영향을 줍니다. 집합 기반 작업으로 대체를 고려하세요.")
            
        elif db_type == "hana":
            # SAP HANA 특화 검사
            
            # LIKE '%...' 패턴 확인
            if re.search(r"LIKE\s+['\"]%", sql_query, re.IGNORECASE):
                performance_warnings.append("SAP HANA에서는 LIKE '%...' 대신 CONTAINS 함수 사용을 고려하세요.")
            
            # 계산 컬럼 확인
            if re.search(r"SELECT\s+.*?[\w.]+\s*[\+\-\*\/]\s*[\w.]+", sql_query, re.IGNORECASE):
                performance_warnings.append("계산 컬럼은 성능에 영향을 줄 수 있습니다. 필요한 경우 계산된 컬럼을 뷰로 만들어 사용하세요.")
            
            # LIMIT 절 확인
            if "SELECT" in sql_query.upper() and "LIMIT" not in sql_query.upper():
                performance_warnings.append("SAP HANA에서는 대용량 결과셋을 제한하기 위해 LIMIT 절 사용을 고려하세요.")
            
            # 병렬 처리 힌트 확인
            if "GROUP BY" in sql_query.upper() and "/*+ PARALLEL" not in sql_query.upper():
                performance_warnings.append("SAP HANA에서는 복잡한 집계 쿼리에 /*+ PARALLEL */ 힌트를 추가하여 성능을 향상시킬 수 있습니다.")
        
        return performance_warnings상관 서브쿼리(correlated subquery)는 성능에 큰 영향을 줄 수 있습니다. 가능하면 JOIN으로 대체하세요.")
        
        # 5. 함수를 사용한 WHERE 조건 확인
        function_in_where = re.findall(r"WHERE\s+.*?\w+\s*\(\s*[\w.]+\s*\)", sql_query, re.IGNORECASE | re.DOTALL)
        if function_in_where:
            performance_warnings.append("WHERE 절에서 컬럼에 함수를 적용하면 인덱스를 사용할 수 없어 성능이 저하될 수 있습니다.")
            
            # 구체적인 함수 이름 추출
            functions = re.findall(r"(\w+)\s*\(\s*[\w.]+\s*\)", "".join(function_in_where), re.IGNORECASE)
            if functions:
                performance_warnings.append(f"WHERE 절에서 사용된 함수 {', '.join(functions)}는 인덱스 사용을 방해할 수 있습니다.")
        
        # 6. 대용량 결과 제한 확인
        if not re.search(r"TOP\s+\d+|LIMIT\s+\d+", sql_query, re.IGNORECASE):
            performance_warnings.append("대용량 결과를 제한하기 위해 TOP 또는 LIMIT 절 사용을 고려하세요.")
        
        # 7. 복잡한 ORDER BY 확인
        order_by_columns = re.findall(r"ORDER\s+BY\s+(.*?)(?:LIMIT|$)", sql_query, re.IGNORECASE | re.DOTALL)
        if order_by_columns:
            columns_count = len(re.split(r",\s*", order_by_columns[0]))
            if columns_count > 3:
                performance_warnings.append(f"ORDER BY 절에 {columns_count}개의 컬럼이 사용되어 정렬 성능이 저하될 수 있습니다.")
        
        # 8. 복잡한 GROUP BY 확인
        group_by_columns = re.findall(r"GROUP\s+BY\s+(.*?)(?:HAVING|ORDER|LIMIT|$)", sql_query, re.IGNORECASE | re.DOTALL)
        if group_by_columns:
            columns_count = len(re.split(r",\s*", group_by_columns[0]))
            if columns_count > 3:
                performance_warnings.append(f"GROUP BY 절에 {columns_count}개의 컬럼이 사용되어 집계 성능이 저하될 수 있습니다.")
        
        # 9. 다수의 JOIN 확인
        join_count = len(re.findall(r"JOIN", sql_query, re.IGNORECASE))
        if join_count > 3:
            performance_warnings.append(f"{join_count}개의 JOIN이 사용되어 쿼리 복잡도가 높습니다. 필요한 JOIN만 사용하세요.")
        
        # 10. LIKE 패턴 확인
        like_patterns = re.findall(r"LIKE\s+'([^']*)'", sql_query, re.IGNORECASE)
        for pattern in like_patterns:
            if pattern.startswith("%"):
                performance_warnings.append(f"LIKE '{pattern}'와 같은 선행 와일드카드 패턴은 인덱스를 사용할 수 없어 성능이 저하될 수 있습니다.")
            elif pattern.startswith("_"):
                performance_warnings.append(f"LIKE '{pattern}'와 같은 선행 와일드카드 패턴은 인덱스를 사용할 수 없어 성능이 저하될 수 있습니다.")
        
        # 11. IN 절에 많은 값 확인
        in_clauses = re.findall(r"IN\s*\((.*?)\)", sql_query, re.IGNORECASE | re.DOTALL)
        for in_clause in in_clauses:
            values_count = len(re.split(r",\s*", in_clause))
            if values_count > 10:
                performance_warnings.append(f"IN 절에 {values_count}개의 값이 사용되어 성능이 저하될 수 있습니다. 임시 테이블이나 JOIN을 고려하세요.")
        
        # 12. OR 조건 확인
        or_count = len(re.findall(r"\bOR\b", sql_query, re.IGNORECASE))
        if or_count > 3:
            performance_warnings.append(f"{or_count}개의 OR 조건이 사용되어 인덱스 사용이 제한될 수 있습니다. UNION을 고려하세요.")
        
        # 13. 데이터베이스별 성능 이슈 확인
        if db_type == "mssql":
            # MS-SQL 특화 검사
            if re.search(r"FROM\s+\w+(?:\s+\w+)?(?!\s+WITH\s*\(\s*NOLOCK\s*\))", sql_query, re.IGNORECASE):
                performance_warnings.append("읽기 전용 쿼리에 WITH (NOLOCK) 힌트를 추가하면 동시성이 향상될 수 있습니다.")
            
            # 임시 테이블 사용 확인
            if re.search(r"#\w+", sql_query, re.IGNORECASE):
                performance_warnings.append("임시 테이블(#)은 tempdb 경합을 일으킬 수 있습니다. 필요한 경우에만 사용하세요.")
            
            # 테이블 변수 사용 확인
            if re.search(r"@\w+", sql_query, re.IGNORECASE):
                performance_warnings.append("테이블 변수(@)는 통계 정보가 제한되어 성능에 영향을 줄 수 있습니다.")
            
            # OPTION 힌트 확인
            if not re.search(r"OPTION\s*\(", sql_query, re.IGNORECASE):
                if join_count > 3 or subquery_count > 1:
                    performance_warnings.append("복잡한 쿼리에 OPTION 힌트(RECOMPILE, OPTIMIZE FOR 등)를 고려하세요.")
            
        elif db_type == "hana":
            # SAP HANA 특화 검사
            if re.search(r"LIKE\s+'%", sql_query, re.IGNORECASE):
                performance_warnings.append("LIKE '%...'와 같은 선행 와일드카드 패턴은 인덱스를 사용할 수 없어 성능이 저하될 수 있습니다.")
            
            # 문자열 함수 사용 확인
            string_functions = ["UPPER", "LOWER", "SUBSTRING", "REPLACE", "TRIM"]
            for func in string_functions:
                if re.search(rf"{func}\s*\(", sql_query, re.IGNORECASE):
                    performance_warnings.append(f"{func} 함수는 인덱스 사용을 방해할 수 있습니다. 필요한 경우에만 사용하세요.")
            
            # 계산 컬럼 확인
            if re.search(r"SELECT\s+.*?[\w.]+\s*[+\-*/]\s*[\w.]", sql_query, re.IGNORECASE):
                performance_warnings.append("SELECT 절에서 계산 컬럼은 성능에 영향을 줄 수 있습니다. 가능하면 미리 계산된 값을 사용하세요.")
        
        return performance_warnings
    
    def _apply_basic_optimizations(self, sql_query: str, db_type: str) -> Tuple[str, List[str]]:
        """
        기본 SQL 최적화 적용
        
        Args:
            sql_query (str): 최적화할 SQL 쿼리
            db_type (str): 데이터베이스 유형
            
        Returns:
            Tuple[str, List[str]]: (최적화된 SQL 쿼리, 최적화 설명 목록)
        """
        optimized_query = sql_query
        optimizations = []
        
        # 1. 불필요한 공백 및 줄바꿈 정리
        original_length = len(optimized_query)
        optimized_query = re.sub(r'\s+', ' ', optimized_query).strip()
        if len(optimized_query) < original_length:
            optimizations.append("불필요한 공백 및 줄바꿈을 제거했습니다.")
        
        # 2. 주요 SQL 키워드 대문자화
        keywords = ["SELECT", "FROM", "WHERE", "JOIN", "LEFT", "RIGHT", "INNER", "OUTER", 
                   "GROUP BY", "ORDER BY", "HAVING", "UNION", "INTERSECT", "EXCEPT"]
        
        for keyword in keywords:
            pattern = r'\b' + keyword.replace(' ', r'\s+') + r'\b'
            optimized_query = re.sub(pattern, keyword, optimized_query, flags=re.IGNORECASE)
        
        optimizations.append("SQL 키워드를 대문자화하여 가독성을 향상했습니다.")
        
        # 3. 데이터베이스별 최적화
        if db_type == "mssql":
            # MS-SQL 읽기 전용 쿼리에 NOLOCK 힌트 추가
            if "SELECT" in optimized_query and "FROM" in optimized_query:
                if "WITH (NOLOCK)" not in optimized_query.upper():
                    # FROM 절 뒤에 테이블 이름 찾기
                    from_pattern = r"FROM\s+([^\s,;()]+)"
                    from_match = re.search(from_pattern, optimized_query, re.IGNORECASE)
                    
                    if from_match:
                        table_name = from_match.group(1)
                        replacement = f"FROM {table_name} WITH (NOLOCK)"
                        optimized_query = re.sub(from_pattern, replacement, optimized_query, count=1, flags=re.IGNORECASE)
                        optimizations.append("읽기 전용 쿼리에 WITH (NOLOCK) 힌트를 추가했습니다.")
        
        elif db_type == "hana":
            # SAP HANA 최적화
            
            # 1. 힌트 추가 (SAP HANA는 /*+ ... */ 형식의 힌트 사용)
            if "SELECT" in optimized_query and not re.search(r"/\*\+.*?\*/", optimized_query):
                # 대용량 데이터 처리를 위한 병렬 처리 힌트 추가
                if re.search(r"GROUP BY|ORDER BY|JOIN", optimized_query, re.IGNORECASE):
                    optimized_query = optimized_query.replace("SELECT", "SELECT /*+ PARALLEL(4) */", 1)
                    optimizations.append("병렬 처리를 위한 PARALLEL 힌트를 추가했습니다.")
            
            # 2. LIKE 패턴 최적화
            like_patterns = re.findall(r"LIKE\s+'([^']*)'", optimized_query, re.IGNORECASE)
            for pattern in like_patterns:
                if pattern.startswith("%") and pattern.endswith("%"):
                    # LIKE '%text%' 패턴은 CONTAINS로 대체하면 더 효율적
                    old_pattern = f"LIKE '%{pattern[1:-1]}%'"
                    new_pattern = f"CONTAINS(*, '{pattern[1:-1]}')"
                    if re.search(rf"{old_pattern}", optimized_query, re.IGNORECASE):
                        optimized_query = re.sub(rf"{old_pattern}", new_pattern, optimized_query, flags=re.IGNORECASE)
                        optimizations.append(f"LIKE '%...%' 패턴을 CONTAINS 함수로 최적화했습니다.")
            
            # 3. 대용량 결과 제한
            if not re.search(r"LIMIT\s+\d+", optimized_query, re.IGNORECASE) and not re.search(r"TOP\s+\d+", optimized_query, re.IGNORECASE):
                # 결과 제한이 없는 경우 LIMIT 추가
                if re.search(r"ORDER BY", optimized_query, re.IGNORECASE):
                    optimized_query = re.sub(r"(ORDER BY.*?)$", r"\1 LIMIT 1000", optimized_query, flags=re.IGNORECASE)
                    optimizations.append("대용량 결과 제한을 위해 LIMIT 1000을 추가했습니다.")
                else:
                    optimized_query = optimized_query + " LIMIT 1000"
                    optimizations.append("대용량 결과 제한을 위해 LIMIT 1000을 추가했습니다.")
        
        return optimized_query, optimizations