"""
프롬프트 생성 및 처리 유틸리티

이 모듈은 LLM에 전송할 프롬프트를 생성하고 처리하는 유틸리티 함수를 제공합니다.
"""
from typing import Dict, Any, List, Optional, Union
import json


class PromptTemplate:
    """프롬프트 템플릿 클래스"""
    
    def __init__(self, template: str):
        """
        프롬프트 템플릿 초기화
        
        Args:
            template (str): 템플릿 문자열 (변수는 {variable_name} 형식으로 포함)
        """
        self.template = template
    
    def format(self, **kwargs) -> str:
        """
        템플릿에 변수 값을 채워 프롬프트 생성
        
        Args:
            **kwargs: 템플릿 변수에 매핑될 키워드 인자
            
        Returns:
            str: 포맷된 프롬프트
        """
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required template variable: {e}")


# SQL 생성을 위한 기본 프롬프트 템플릿
SQL_GENERATION_TEMPLATE = PromptTemplate("""
당신은 자연어를 SQL 쿼리로 변환하는 전문가입니다.
사용자의 질문을 분석하고 주어진 데이터베이스 스키마에 맞는 SQL 쿼리를 생성해주세요.

### 데이터베이스 스키마:
{schema_json}

### 데이터베이스 유형:
{db_type}

### 사용자 질문:
{question}

{context}

### 규칙:
1. 오직 SELECT 쿼리만 생성하세요 (INSERT, UPDATE, DELETE, DROP 등은 허용되지 않습니다).
2. 쿼리는 {db_type} 문법에 맞게 작성되어야 합니다.
3. 쿼리는 가능한 한 효율적이어야 합니다.
4. 필요한 경우 주석을 포함하여 쿼리의 각 부분을 설명하세요.

### 응답 형식:
```sql
-- 여기에 SQL 쿼리를 작성하세요
```

### 설명:
쿼리가 어떻게 사용자의 질문에 답하는지 간략히 설명하세요.
""")

# 컨텍스트 인식 SQL 생성을 위한 향상된 프롬프트 템플릿
ENHANCED_SQL_GENERATION_TEMPLATE = PromptTemplate("""
당신은 자연어를 SQL 쿼리로 변환하는 전문가입니다.
사용자의 질문을 분석하고 주어진 데이터베이스 스키마에 맞는 SQL 쿼리를 생성해주세요.
이전 대화 컨텍스트를 고려하여 사용자의 의도를 정확히 파악하세요.

### 데이터베이스 스키마:
{schema_json}

### 데이터베이스 유형:
{db_type}

### 사용자 질문:
{question}

{context}

### 스키마 분석:
1. 질문과 관련된 테이블을 식별하세요.
2. 테이블 간의 관계(외래 키)를 파악하세요.
3. 필요한 조인 조건을 결정하세요.
4. 필터링, 그룹화, 정렬 조건을 식별하세요.

### 규칙:
1. 오직 SELECT 쿼리만 생성하세요 (INSERT, UPDATE, DELETE, DROP 등은 허용되지 않습니다).
2. 쿼리는 {db_type} 문법에 맞게 작성되어야 합니다.
3. 쿼리는 가능한 한 효율적이어야 합니다.
4. 필요한 경우 주석을 포함하여 쿼리의 각 부분을 설명하세요.
5. 테이블 별칭을 사용하여 가독성을 높이세요.
6. 컬럼명이 모호할 수 있는 경우 테이블 별칭을 접두어로 사용하세요.

### 응답 형식:
```sql
-- 여기에 SQL 쿼리를 작성하세요
```

### 설명:
쿼리가 어떻게 사용자의 질문에 답하는지 간략히 설명하세요.
테이블 간의 관계, 필터링 조건, 집계 함수 등 주요 요소를 설명하세요.
""")


# 결과 요약을 위한 프롬프트 템플릿
RESULT_SUMMARY_TEMPLATE = PromptTemplate("""
당신은 데이터 분석 전문가입니다.
아래 제공된 SQL 쿼리 결과를 분석하고 주요 인사이트를 자연어로 요약해주세요.

### 원본 질문:
{question}

### 실행된 SQL 쿼리:
```sql
{sql_query}
```

### 쿼리 결과:
{result_json}

### 요약 지침:
1. 결과에서 주요 패턴, 추세, 이상치를 식별하세요.
2. 데이터의 핵심 인사이트를 3-5개 요약하세요.
3. 가능한 경우 수치를 포함하여 구체적으로 설명하세요.
4. 전문 용어보다는 일반 사용자가 이해할 수 있는 언어를 사용하세요.

### 응답 형식:
자연어로 된 요약을 제공하세요. 마크다운 형식을 사용하여 가독성을 높일 수 있습니다.
""")


# 파이썬 코드 생성을 위한 프롬프트 템플릿
PYTHON_CODE_GENERATION_TEMPLATE = PromptTemplate("""
당신은 데이터 분석 및 시각화 전문가입니다.
아래 제공된 SQL 쿼리 결과를 분석하고 시각화하는 파이썬 코드를 생성해주세요.

### 원본 질문:
{question}

### 실행된 SQL 쿼리:
```sql
{sql_query}
```

### 쿼리 결과 구조:
{result_structure}

### 분석 요청:
{analysis_request}

### 코드 생성 지침:
1. pandas를 사용하여 데이터를 처리하세요.
2. matplotlib, seaborn, plotly 중 적절한 라이브러리를 사용하여 시각화를 생성하세요.
3. 데이터 특성에 맞는 차트 유형을 선택하세요 (시계열 데이터는 선 그래프, 범주형 데이터는 막대 그래프 등).
4. 코드는 완전히 실행 가능해야 하며, 필요한 모든 import 문을 포함해야 합니다.
5. 코드에 주석을 추가하여 각 단계를 설명하세요.
6. 시각화에는 적절한 제목, 레이블, 범례를 포함하세요.

### 응답 형식:
```python
# 여기에 파이썬 코드를 작성하세요
```
""")


# SQL 검증 및 최적화를 위한 프롬프트 템플릿
SQL_VALIDATION_TEMPLATE = PromptTemplate("""
당신은 SQL 검증 및 최적화 전문가입니다.
아래 제공된 SQL 쿼리를 검증하고 최적화해주세요.

### 데이터베이스 유형:
{db_type}

### 데이터베이스 스키마:
{schema_json}

### SQL 쿼리:
```sql
{sql_query}
```

{error_context}

### 검증 및 최적화 지침:
1. 문법 오류가 있는지 확인하세요.
2. SQL 인젝션 위험이 있는지 확인하세요.
3. 테이블 및 컬럼 이름이 스키마와 일치하는지 확인하세요.
4. 쿼리 성능을 개선할 수 있는 방법을 제안하세요.
5. {db_type} 데이터베이스에 최적화된 쿼리를 작성하세요.
6. 필요한 경우 인덱스 사용을 제안하세요.

### 응답 형식:
```sql
-- 최적화된 SQL 쿼리
```

### 최적화 설명:
1. 발견된 문제점 목록
2. 적용된 최적화 목록
3. 추가 권장 사항
""")


def create_schema_context(schema: Dict[str, Any]) -> str:
    """
    DB 스키마 정보를 프롬프트에 포함할 수 있는 형식으로 변환
    
    Args:
        schema (Dict[str, Any]): DB 스키마 정보
        
    Returns:
        str: 포맷된 스키마 문자열
    """
    try:
        return json.dumps(schema, ensure_ascii=False, indent=2)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Failed to serialize schema: {e}")


def create_conversation_context(context: List[Dict[str, Any]]) -> str:
    """
    대화 컨텍스트를 프롬프트에 포함할 수 있는 형식으로 변환
    
    Args:
        context (List[Dict[str, Any]]): 대화 컨텍스트 (이전 질의 및 응답)
        
    Returns:
        str: 포맷된 컨텍스트 문자열
    """
    if not context:
        return ""
    
    formatted_context = "### 이전 대화 컨텍스트:\n"
    for i, entry in enumerate(context):
        if "question" in entry:
            formatted_context += f"사용자 ({i+1}): {entry['question']}\n"
        if "answer" in entry:
            formatted_context += f"시스템 ({i+1}): {entry['answer']}\n"
            # 메타데이터가 있으면 추가 정보 포함
            if "metadata" in entry and entry["metadata"]:
                if "explanation" in entry["metadata"] and entry["metadata"]["explanation"]:
                    formatted_context += f"설명 ({i+1}): {entry['metadata']['explanation']}\n"
    
    formatted_context += "\n### 컨텍스트 활용 지침:\n"
    formatted_context += "1. 이전 대화를 참고하여 현재 질문의 맥락을 파악하세요.\n"
    formatted_context += "2. 이전 질문에서 언급된 테이블, 필드, 조건 등을 현재 질문에 적용하세요.\n"
    formatted_context += "3. 사용자가 이전 질문을 참조하는 경우 (예: '그 중에서', '이전 결과에서') 이전 쿼리를 기반으로 새 쿼리를 생성하세요.\n"
    
    return formatted_context


def create_result_context(result: Dict[str, Any]) -> str:
    """
    쿼리 결과를 프롬프트에 포함할 수 있는 형식으로 변환
    
    Args:
        result (Dict[str, Any]): 쿼리 실행 결과
        
    Returns:
        str: 포맷된 결과 문자열
    """
    try:
        # 결과가 너무 큰 경우 일부만 포함
        if "rows" in result and len(result["rows"]) > 100:
            truncated_result = result.copy()
            truncated_result["rows"] = result["rows"][:100]
            truncated_result["truncated"] = True
            truncated_result["total_row_count"] = len(result["rows"])
            return json.dumps(truncated_result, ensure_ascii=False, indent=2)
        else:
            return json.dumps(result, ensure_ascii=False, indent=2)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Failed to serialize result: {e}")


def create_result_structure(result: Dict[str, Any]) -> str:
    """
    쿼리 결과의 구조만 프롬프트에 포함할 수 있는 형식으로 변환
    
    Args:
        result (Dict[str, Any]): 쿼리 실행 결과
        
    Returns:
        str: 포맷된 결과 구조 문자열
    """
    try:
        structure = {
            "columns": result.get("columns", []),
            "row_count": result.get("row_count", 0),
            "sample_rows": result.get("rows", [])[:5] if "rows" in result else []
        }
        return json.dumps(structure, ensure_ascii=False, indent=2)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Failed to serialize result structure: {e}")