"""
LLM 응답 파싱 및 검증 유틸리티

이 모듈은 LLM의 응답을 파싱하고 검증하는 유틸리티 함수를 제공합니다.
"""
from typing import Dict, Any, List, Optional, Tuple, Union
import re
import json


class ResponseParsingError(Exception):
    """LLM 응답 파싱 중 발생한 오류"""
    pass


class ResponseValidationError(Exception):
    """LLM 응답 검증 중 발생한 오류"""
    pass


def extract_sql_from_response(response: str) -> str:
    """
    LLM 응답에서 SQL 쿼리 추출
    
    Args:
        response (str): LLM의 응답 텍스트
        
    Returns:
        str: 추출된 SQL 쿼리
        
    Raises:
        ResponseParsingError: SQL 쿼리를 추출할 수 없는 경우
    """
    # SQL 코드 블록 패턴 (```sql ... ``` 또는 ```...```)
    sql_pattern = r"```(?:sql)?\s*(.*?)\s*```"
    
    # 여러 줄 모드로 패턴 검색
    matches = re.findall(sql_pattern, response, re.DOTALL)
    
    if not matches:
        raise ResponseParsingError("SQL 쿼리를 응답에서 찾을 수 없습니다.")
    
    # 첫 번째 일치 항목 반환
    return matches[0].strip()


def extract_python_code_from_response(response: str) -> str:
    """
    LLM 응답에서 파이썬 코드 추출
    
    Args:
        response (str): LLM의 응답 텍스트
        
    Returns:
        str: 추출된 파이썬 코드
        
    Raises:
        ResponseParsingError: 파이썬 코드를 추출할 수 없는 경우
    """
    # 파이썬 코드 블록 패턴 (```python ... ``` 또는 ```...```)
    python_pattern = r"```(?:python)?\s*(.*?)\s*```"
    
    # 여러 줄 모드로 패턴 검색
    matches = re.findall(python_pattern, response, re.DOTALL)
    
    if not matches:
        raise ResponseParsingError("파이썬 코드를 응답에서 찾을 수 없습니다.")
    
    # 첫 번째 일치 항목 반환
    return matches[0].strip()


def extract_insights_from_response(response: str) -> List[str]:
    """
    LLM 응답에서 인사이트 목록 추출
    
    Args:
        response (str): LLM의 응답 텍스트
        
    Returns:
        List[str]: 추출된 인사이트 목록
    """
    # 마크다운 목록 항목 패턴 (- 또는 * 또는 숫자. 로 시작하는 줄)
    insight_pattern = r"(?:^|\n)(?:\d+\.|\*|\-)\s*(.*?)(?:\n|$)"
    
    # 패턴 검색
    matches = re.findall(insight_pattern, response)
    
    # 목록 항목이 없으면 전체 텍스트를 하나의 인사이트로 처리
    if not matches:
        # 빈 줄로 분할하고 빈 문자열 제거
        paragraphs = [p.strip() for p in response.split("\n\n") if p.strip()]
        return paragraphs
    
    return [match.strip() for match in matches]


def validate_sql_query(query: str, allowed_operations: List[str] = ["SELECT"]) -> Tuple[bool, Optional[str]]:
    """
    SQL 쿼리 검증
    
    Args:
        query (str): 검증할 SQL 쿼리
        allowed_operations (List[str], optional): 허용된 SQL 작업 목록
        
    Returns:
        Tuple[bool, Optional[str]]: (유효성 여부, 오류 메시지)
    """
    # 쿼리가 비어있는지 확인
    if not query or not query.strip():
        return False, "SQL 쿼리가 비어 있습니다."
    
    # 주석 제거
    query_without_comments = re.sub(r"--.*?(\n|$)", "", query)
    query_without_comments = re.sub(r"/\*.*?\*/", "", query_without_comments, flags=re.DOTALL)
    
    # 첫 번째 단어 추출 (SQL 작업)
    first_word_match = re.search(r"^\s*(\w+)", query_without_comments)
    if not first_word_match:
        return False, "SQL 쿼리에서 작업을 식별할 수 없습니다."
    
    operation = first_word_match.group(1).upper()
    
    # 허용된 작업인지 확인
    if operation not in allowed_operations:
        return False, f"SQL 작업 '{operation}'은(는) 허용되지 않습니다. 허용된 작업: {', '.join(allowed_operations)}"
    
    # 기본 SQL 인젝션 패턴 확인
    injection_patterns = [
        r";\s*\w+",  # 세미콜론 뒤에 다른 명령
        r"--",       # 인라인 주석
        r"/\*.*?\*/", # 블록 주석
        r"UNION\s+ALL", # UNION ALL
        r"UNION\s+SELECT", # UNION SELECT
        r"DROP\s+TABLE", # DROP TABLE
        r"DELETE\s+FROM", # DELETE FROM
        r"INSERT\s+INTO", # INSERT INTO
        r"UPDATE\s+\w+\s+SET", # UPDATE SET
        r"EXEC\s*\(", # EXEC(
        r"EXECUTE\s*\(" # EXECUTE(
    ]
    
    for pattern in injection_patterns:
        if re.search(pattern, query_without_comments, re.IGNORECASE):
            return False, f"SQL 쿼리에 잠재적인 SQL 인젝션 패턴이 포함되어 있습니다: {pattern}"
    
    return True, None


def validate_python_code(code: str) -> Tuple[bool, Optional[str]]:
    """
    파이썬 코드 검증
    
    Args:
        code (str): 검증할 파이썬 코드
        
    Returns:
        Tuple[bool, Optional[str]]: (유효성 여부, 오류 메시지)
    """
    # 코드가 비어있는지 확인
    if not code or not code.strip():
        return False, "파이썬 코드가 비어 있습니다."
    
    # 기본 구문 검사
    try:
        compile(code, "<string>", "exec")
    except SyntaxError as e:
        return False, f"파이썬 코드에 구문 오류가 있습니다: {str(e)}"
    
    # 금지된 모듈 및 함수 확인
    forbidden_imports = [
        "os", "subprocess", "sys", "shutil", "socket", "requests",
        "__import__", "eval", "exec", "compile", "open"
    ]
    
    for forbidden in forbidden_imports:
        # import 문 확인
        if re.search(rf"import\s+{forbidden}", code) or re.search(rf"from\s+{forbidden}\s+import", code):
            return False, f"보안상의 이유로 '{forbidden}' 모듈 사용이 금지되어 있습니다."
        
        # 함수 호출 확인 (eval, exec 등)
        if forbidden in ["eval", "exec", "compile", "__import__", "open"]:
            if re.search(rf"\b{forbidden}\s*\(", code):
                return False, f"보안상의 이유로 '{forbidden}' 함수 사용이 금지되어 있습니다."
    
    # 허용된 데이터 분석 및 시각화 라이브러리
    allowed_imports = [
        "pandas", "numpy", "matplotlib", "seaborn", "plotly",
        "scipy", "statsmodels", "sklearn", "math", "datetime",
        "json", "collections", "itertools", "functools", "re"
    ]
    
    # 허용되지 않은 import 확인
    import_pattern = r"import\s+(\w+)|from\s+(\w+)"
    for match in re.finditer(import_pattern, code):
        module = match.group(1) or match.group(2)
        if module and module not in allowed_imports and module not in ["typing", "warnings"]:
            return False, f"'{module}' 모듈은 허용 목록에 없습니다. 허용된 모듈: {', '.join(allowed_imports)}"
    
    return True, None


def parse_llm_response(response: str, response_type: str) -> Dict[str, Any]:
    """
    LLM 응답 파싱
    
    Args:
        response (str): LLM의 응답 텍스트
        response_type (str): 응답 유형 ('sql', 'summary', 'python')
        
    Returns:
        Dict[str, Any]: 파싱된 응답
        
    Raises:
        ResponseParsingError: 응답을 파싱할 수 없는 경우
        ResponseValidationError: 응답이 유효하지 않은 경우
    """
    try:
        if response_type == "sql":
            sql = extract_sql_from_response(response)
            is_valid, error_msg = validate_sql_query(sql)
            
            if not is_valid:
                raise ResponseValidationError(f"SQL 검증 실패: {error_msg}")
            
            # 설명 추출 (SQL 코드 블록 이후의 텍스트)
            explanation = ""
            sql_block_pattern = r"```(?:sql)?\s*.*?\s*```"
            explanation_text = re.sub(sql_block_pattern, "", response, flags=re.DOTALL).strip()
            if explanation_text:
                explanation = explanation_text
            
            return {
                "sql": sql,
                "explanation": explanation
            }
            
        elif response_type == "summary":
            insights = extract_insights_from_response(response)
            return {
                "summary": response,
                "insights": insights
            }
            
        elif response_type == "python":
            code = extract_python_code_from_response(response)
            is_valid, error_msg = validate_python_code(code)
            
            if not is_valid:
                raise ResponseValidationError(f"파이썬 코드 검증 실패: {error_msg}")
            
            # 설명 추출 (Python 코드 블록 이외의 텍스트)
            explanation = ""
            code_block_pattern = r"```(?:python)?\s*.*?\s*```"
            explanation_text = re.sub(code_block_pattern, "", response, flags=re.DOTALL).strip()
            if explanation_text:
                explanation = explanation_text
            
            return {
                "code": code,
                "explanation": explanation
            }
            
        else:
            raise ValueError(f"지원되지 않는 응답 유형: {response_type}")
            
    except ResponseParsingError as e:
        raise ResponseParsingError(f"응답 파싱 실패: {str(e)}")
    except ResponseValidationError as e:
        raise ResponseValidationError(f"응답 검증 실패: {str(e)}")
    except Exception as e:
        raise ResponseParsingError(f"예상치 못한 오류: {str(e)}")