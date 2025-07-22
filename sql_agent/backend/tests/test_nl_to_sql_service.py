"""
자연어-SQL 변환 서비스 테스트

이 모듈은 자연어-SQL 변환 서비스에 대한 테스트를 제공합니다.
"""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any, List
from datetime import datetime

from sql_agent.backend.llm import (
    LLMService,
    LLMConfig,
    LLMProvider,
    OpenAIService,
    NLToSQLService
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


class MockLLMService:
    """테스트용 LLM 서비스 모의 객체"""
    
    async def generate_sql(self, natural_language, schema, db_type, context=None):
        """SQL 생성 모의 메서드"""
        return {
            "sql": "SELECT d.department_name, COUNT(e.employee_id) AS employee_count FROM dbo.departments d LEFT JOIN dbo.employees e ON d.department_id = e.department_id GROUP BY d.department_name ORDER BY employee_count DESC",
            "explanation": "이 쿼리는 각 부서별 직원 수를 계산하여 직원 수가 많은 순서대로 정렬합니다.",
            "original_question": natural_language,
            "db_type": db_type
        }


class TestNLToSQLService:
    """자연어-SQL 변환 서비스 테스트"""
    
    @pytest.fixture
    def nl_to_sql_service(self):
        """자연어-SQL 변환 서비스 인스턴스 생성"""
        mock_llm_service = MockLLMService()
        return NLToSQLService(mock_llm_service)
    
    @pytest.mark.asyncio
    async def test_convert_nl_to_sql(self, nl_to_sql_service):
        """자연어-SQL 변환 테스트"""
        # 함수 호출
        result = await nl_to_sql_service.convert_nl_to_sql(
            user_id="test_user",
            natural_language="각 부서별 직원 수를 알려주세요",
            schema=TEST_SCHEMA,
            db_type="mssql"
        )
        
        # 결과 검증
        assert "sql" in result
        assert "explanation" in result
        assert "original_question" in result
        assert "db_type" in result
        assert "conversation_id" in result
        assert "SELECT" in result["sql"]
        assert "department_name" in result["sql"]
        assert "employee_count" in result["sql"]
        assert result["db_type"] == "mssql"
    
    @pytest.mark.asyncio
    async def test_convert_nl_to_sql_with_context(self, nl_to_sql_service):
        """컨텍스트를 포함한 자연어-SQL 변환 테스트"""
        # 첫 번째 질의
        await nl_to_sql_service.convert_nl_to_sql(
            user_id="test_user",
            natural_language="각 부서별 직원 수를 알려주세요",
            schema=TEST_SCHEMA,
            db_type="mssql",
            conversation_id="test_conversation"
        )
        
        # 두 번째 질의 (동일한 대화 ID 사용)
        result = await nl_to_sql_service.convert_nl_to_sql(
            user_id="test_user",
            natural_language="직원이 가장 많은 부서는 어디인가요?",
            schema=TEST_SCHEMA,
            db_type="mssql",
            conversation_id="test_conversation"
        )
        
        # 결과 검증
        assert "sql" in result
        assert "explanation" in result
        assert "original_question" in result
        assert "db_type" in result
        assert "conversation_id" in result
        assert result["conversation_id"] == "test_conversation"
    
    def test_get_conversation_history(self, nl_to_sql_service):
        """대화 이력 조회 테스트"""
        # 대화 이력에 항목 추가
        nl_to_sql_service._add_to_conversation_history(
            user_id="test_user",
            conversation_id="test_conversation",
            question="각 부서별 직원 수를 알려주세요",
            answer="SELECT d.department_name, COUNT(e.employee_id) AS employee_count FROM dbo.departments d LEFT JOIN dbo.employees e ON d.department_id = e.department_id GROUP BY d.department_name ORDER BY employee_count DESC",
            metadata={"db_type": "mssql"}
        )
        
        # 대화 이력 조회
        history = nl_to_sql_service.get_conversation_history(
            user_id="test_user",
            conversation_id="test_conversation"
        )
        
        # 결과 검증
        assert "conversation_id" in history
        assert "history" in history
        assert len(history["history"]) == 1
        assert history["history"][0]["question"] == "각 부서별 직원 수를 알려주세요"
        assert "SELECT" in history["history"][0]["answer"]
        assert "metadata" in history["history"][0]
        assert history["history"][0]["metadata"]["db_type"] == "mssql"
    
    def test_clear_conversation_history(self, nl_to_sql_service):
        """대화 이력 삭제 테스트"""
        # 대화 이력에 항목 추가
        nl_to_sql_service._add_to_conversation_history(
            user_id="test_user",
            conversation_id="test_conversation",
            question="각 부서별 직원 수를 알려주세요",
            answer="SELECT d.department_name, COUNT(e.employee_id) AS employee_count FROM dbo.departments d LEFT JOIN dbo.employees e ON d.department_id = e.department_id GROUP BY d.department_name ORDER BY employee_count DESC"
        )
        
        # 대화 이력 삭제
        nl_to_sql_service.clear_conversation_history(
            user_id="test_user",
            conversation_id="test_conversation"
        )
        
        # 대화 이력 조회
        history = nl_to_sql_service.get_conversation_history(
            user_id="test_user",
            conversation_id="test_conversation"
        )
        
        # 결과 검증
        assert len(history["history"]) == 0
    
    def test_create_schema_prompt(self, nl_to_sql_service):
        """스키마 프롬프트 생성 테스트"""
        # 프롬프트 생성
        prompt = nl_to_sql_service.create_schema_prompt(
            schema=TEST_SCHEMA,
            db_type="mssql"
        )
        
        # 결과 검증
        assert "데이터베이스 스키마" in prompt
        assert "데이터베이스 유형" in prompt
        assert "mssql" in prompt
        assert "규칙" in prompt
        assert "SELECT" in prompt