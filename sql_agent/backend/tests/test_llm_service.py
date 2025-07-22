"""
LLM 서비스 테스트

이 모듈은 LLM 서비스 인터페이스 및 구현에 대한 테스트를 제공합니다.
"""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any, List

from sql_agent.backend.llm import (
    LLMService,
    LLMConfig,
    LLMProvider,
    LLMServiceFactory,
    OpenAIService,
    ResponseParsingError,
    ResponseValidationError
)


# 테스트용 스키마 데이터
TEST_SCHEMA = {
    "schemas": [
        {
            "name": "dbo",
            "tables": [
                {
                    "name": "employees",
                    "columns": [
                        {"name": "employee_id", "type": "INT", "nullable": False},
                        {"name": "first_name", "type": "VARCHAR(50)", "nullable": False},
                        {"name": "last_name", "type": "VARCHAR(50)", "nullable": False},
                        {"name": "email", "type": "VARCHAR(100)", "nullable": True},
                        {"name": "hire_date", "type": "DATE", "nullable": False},
                        {"name": "department_id", "type": "INT", "nullable": True}
                    ],
                    "primaryKey": ["employee_id"],
                    "foreignKeys": [
                        {
                            "columns": ["department_id"],
                            "referenceTable": "departments",
                            "referenceColumns": ["department_id"]
                        }
                    ]
                },
                {
                    "name": "departments",
                    "columns": [
                        {"name": "department_id", "type": "INT", "nullable": False},
                        {"name": "department_name", "type": "VARCHAR(100)", "nullable": False},
                        {"name": "location_id", "type": "INT", "nullable": True}
                    ],
                    "primaryKey": ["department_id"],
                    "foreignKeys": []
                }
            ]
        }
    ]
}

# 테스트용 쿼리 결과 데이터
TEST_QUERY_RESULT = {
    "columns": [
        {"name": "department_name", "type": "VARCHAR"},
        {"name": "employee_count", "type": "INT"}
    ],
    "rows": [
        ["인사", 5],
        ["영업", 8],
        ["개발", 12],
        ["마케팅", 4]
    ],
    "row_count": 4,
    "truncated": False
}


class TestLLMConfig:
    """LLM 설정 테스트"""
    
    def test_llm_config_initialization(self):
        """LLMConfig 초기화 테스트"""
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model_name="gpt-4",
            api_key="test-api-key",
            api_base="https://api.openai.com/v1",
            max_tokens=2000,
            temperature=0.3
        )
        
        assert config.provider == LLMProvider.OPENAI
        assert config.model_name == "gpt-4"
        assert config.api_key == "test-api-key"
        assert config.api_base == "https://api.openai.com/v1"
        assert config.max_tokens == 2000
        assert config.temperature == 0.3


class TestOpenAIService:
    """OpenAI 서비스 테스트"""
    
    @pytest.fixture
    def openai_service(self):
        """OpenAI 서비스 인스턴스 생성"""
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model_name="gpt-4",
            api_key="test-api-key"
        )
        return OpenAIService(config)
    
    @pytest.mark.asyncio
    @patch("sql_agent.backend.llm.openai_service.AsyncOpenAI")
    async def test_generate_sql(self, mock_openai, openai_service):
        """SQL 생성 테스트"""
        # AsyncOpenAI 클라이언트 모의 객체 설정
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        
        # chat.completions.create 메서드 모의 설정
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """
다음은 요청하신 SQL 쿼리입니다:

```sql
SELECT d.department_name, COUNT(e.employee_id) AS employee_count
FROM dbo.departments d
LEFT JOIN dbo.employees e ON d.department_id = e.department_id
GROUP BY d.department_name
ORDER BY employee_count DESC;
```

이 쿼리는 각 부서별 직원 수를 계산하여 직원 수가 많은 순서대로 정렬합니다.
"""
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # 함수 호출
        result = await openai_service.generate_sql(
            natural_language="각 부서별 직원 수를 알려주세요",
            schema=TEST_SCHEMA,
            db_type="mssql"
        )
        
        # 결과 검증
        assert "sql" in result
        assert "explanation" in result
        assert "original_question" in result
        assert "db_type" in result
        assert "SELECT" in result["sql"]
        assert "department_name" in result["sql"]
        assert "employee_count" in result["sql"]
        assert result["db_type"] == "mssql"
    
    @pytest.mark.asyncio
    @patch("sql_agent.backend.llm.openai_service.AsyncOpenAI")
    async def test_summarize_results(self, mock_openai, openai_service):
        """결과 요약 테스트"""
        # AsyncOpenAI 클라이언트 모의 객체 설정
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        
        # chat.completions.create 메서드 모의 설정
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """
# 부서별 직원 수 분석

분석 결과, 다음과 같은 인사이트를 확인할 수 있습니다:

1. 개발 부서가 12명으로 가장 많은 직원을 보유하고 있습니다.
2. 영업 부서는 8명으로 두 번째로 큰 부서입니다.
3. 인사 부서와 마케팅 부서는 각각 5명과 4명으로 상대적으로 작은 규모입니다.
4. 전체 직원 수는 29명입니다.
"""
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # 함수 호출
        result = await openai_service.summarize_results(
            query_result=TEST_QUERY_RESULT,
            natural_language="각 부서별 직원 수를 알려주세요",
            sql_query="SELECT department_name, COUNT(*) AS employee_count FROM employees GROUP BY department_name"
        )
        
        # 결과 검증
        assert "summary" in result
        assert "insights" in result
        assert "original_question" in result
        assert len(result["insights"]) > 0
        assert "개발 부서" in result["summary"]
        assert "12명" in result["summary"]
    
    @pytest.mark.asyncio
    @patch("sql_agent.backend.llm.openai_service.AsyncOpenAI")
    async def test_generate_python_code(self, mock_openai, openai_service):
        """파이썬 코드 생성 테스트"""
        # AsyncOpenAI 클라이언트 모의 객체 설정
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        
        # chat.completions.create 메서드 모의 설정
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """
다음은 부서별 직원 수를 시각화하는 파이썬 코드입니다:

```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 데이터 준비
data = {
    'department_name': ['인사', '영업', '개발', '마케팅'],
    'employee_count': [5, 8, 12, 4]
}

# DataFrame 생성
df = pd.DataFrame(data)

# 시각화
plt.figure(figsize=(10, 6))
sns.barplot(x='department_name', y='employee_count', data=df)
plt.title('부서별 직원 수')
plt.xlabel('부서명')
plt.ylabel('직원 수')
plt.xticks(rotation=0)
plt.tight_layout()

# 결과 표시
plt.show()
```

이 코드는 부서별 직원 수를 막대 그래프로 시각화합니다.
"""
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # 함수 호출
        result = await openai_service.generate_python_code(
            query_result=TEST_QUERY_RESULT,
            natural_language="각 부서별 직원 수를 알려주세요",
            sql_query="SELECT department_name, COUNT(*) AS employee_count FROM employees GROUP BY department_name",
            analysis_request={"visualization_type": "bar"}
        )
        
        # 결과 검증
        assert "code" in result
        assert "explanation" in result
        assert "original_question" in result
        assert "import pandas" in result["code"]
        assert "import matplotlib" in result["code"]
        assert "plt.figure" in result["code"]
    
    @pytest.mark.asyncio
    @patch("sql_agent.backend.llm.openai_service.AsyncOpenAI")
    async def test_validate_and_fix_sql(self, mock_openai, openai_service):
        """SQL 검증 및 수정 테스트"""
        # AsyncOpenAI 클라이언트 모의 객체 설정
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        
        # chat.completions.create 메서드 모의 설정
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """
오류를 수정한 SQL 쿼리입니다:

```sql
SELECT d.department_name, COUNT(e.employee_id) AS employee_count
FROM dbo.departments d
LEFT JOIN dbo.employees e ON d.department_id = e.department_id
GROUP BY d.department_name
ORDER BY employee_count DESC;
```
"""
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # 함수 호출
        original_sql = """
SELECT d.department_name, COUNT(e.employee_id) AS employee_count
FROM dbo.departments d
LEFT JOIN dbo.employee e ON d.department_id = e.department_id
GROUP BY d.department_name
ORDER BY employee_count DESC;
"""
        fixed_sql, is_modified = await openai_service.validate_and_fix_sql(
            sql_query=original_sql,
            schema=TEST_SCHEMA,
            db_type="mssql",
            error_message="Invalid object name 'dbo.employee'."
        )
        
        # 결과 검증
        assert is_modified
        assert "dbo.employees" in fixed_sql
        assert "dbo.employee" not in fixed_sql
    
    @pytest.mark.asyncio
    async def test_get_model_info(self, openai_service):
        """모델 정보 조회 테스트"""
        # 함수 호출
        result = await openai_service.get_model_info()
        
        # 결과 검증
        assert "provider" in result
        assert "model_name" in result
        assert "capabilities" in result
        assert result["provider"] == "openai"
        assert result["model_name"] == "gpt-4"
        assert "sql_generation" in result["capabilities"]
        assert "result_summarization" in result["capabilities"]
        assert "python_code_generation" in result["capabilities"]


class TestLLMServiceFactory:
    """LLM 서비스 팩토리 테스트"""
    
    def setup_method(self):
        """각 테스트 전 설정"""
        # 테스트 전 캐시 초기화
        LLMServiceFactory.clear_cache()
    
    def test_create_service(self):
        """서비스 생성 테스트"""
        # OpenAI 서비스 생성
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model_name="gpt-4",
            api_key="test-api-key"
        )
        service = LLMServiceFactory.create_service(config)
        
        # 결과 검증
        assert isinstance(service, OpenAIService)
        assert service.config.provider == LLMProvider.OPENAI
        assert service.config.model_name == "gpt-4"
        assert service.config.api_key == "test-api-key"
    
    def test_get_service(self):
        """캐시된 서비스 조회 테스트"""
        # 서비스 생성
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model_name="gpt-4",
            api_key="test-api-key"
        )
        service1 = LLMServiceFactory.create_service(config)
        
        # 캐시에서 조회
        service2 = LLMServiceFactory.get_service(LLMProvider.OPENAI, "gpt-4")
        
        # 결과 검증
        assert service1 is service2
    
    def test_clear_cache(self):
        """캐시 초기화 테스트"""
        # 서비스 생성
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model_name="gpt-4",
            api_key="test-api-key"
        )
        LLMServiceFactory.create_service(config)
        
        # 캐시 초기화
        LLMServiceFactory.clear_cache()
        
        # 캐시에서 조회
        service = LLMServiceFactory.get_service(LLMProvider.OPENAI, "gpt-4")
        
        # 결과 검증
        assert service is None
    
    def test_unsupported_provider(self):
        """지원되지 않는 제공자 테스트"""
        # 지원되지 않는 제공자로 설정
        config = LLMConfig(
            provider=LLMProvider.AZURE_OPENAI,  # 아직 구현되지 않음
            model_name="gpt-4",
            api_key="test-api-key"
        )
        
        # 예외 발생 확인
        with pytest.raises(NotImplementedError):
            LLMServiceFactory.create_service(config)