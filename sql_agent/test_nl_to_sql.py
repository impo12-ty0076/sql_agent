"""
자연어-SQL 변환 서비스 테스트 스크립트
"""
import asyncio
import json
import sys
import os
from typing import Dict, Any, List

# 현재 디렉토리를 시스템 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.llm.base import LLMConfig, LLMProvider
from backend.llm.openai_service import OpenAIService
from backend.llm.nl_to_sql_service import NLToSQLService


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


async def test_nl_to_sql_service():
    """자연어-SQL 변환 서비스 테스트"""
    print("자연어-SQL 변환 서비스 테스트 시작")
    
    # 모의 LLM 서비스로 테스트
    mock_llm_service = MockLLMService()
    nl_to_sql_service = NLToSQLService(mock_llm_service)
    
    # 자연어-SQL 변환 테스트
    result = await nl_to_sql_service.convert_nl_to_sql(
        user_id="test_user",
        natural_language="각 부서별 직원 수를 알려주세요",
        schema=TEST_SCHEMA,
        db_type="mssql"
    )
    
    print("\n1. 자연어-SQL 변환 결과:")
    print(f"SQL: {result['sql']}")
    print(f"설명: {result['explanation']}")
    print(f"대화 ID: {result['conversation_id']}")
    
    # 컨텍스트를 포함한 자연어-SQL 변환 테스트
    result2 = await nl_to_sql_service.convert_nl_to_sql(
        user_id="test_user",
        natural_language="직원이 가장 많은 부서는 어디인가요?",
        schema=TEST_SCHEMA,
        db_type="mssql",
        conversation_id=result['conversation_id']
    )
    
    print("\n2. 컨텍스트를 포함한 자연어-SQL 변환 결과:")
    print(f"SQL: {result2['sql']}")
    print(f"설명: {result2['explanation']}")
    print(f"대화 ID: {result2['conversation_id']}")
    
    # 대화 이력 조회 테스트
    history = nl_to_sql_service.get_conversation_history(
        user_id="test_user",
        conversation_id=result['conversation_id']
    )
    
    print("\n3. 대화 이력:")
    print(f"대화 항목 수: {len(history['history'])}")
    for i, item in enumerate(history['history']):
        print(f"\n항목 {i+1}:")
        print(f"질문: {item['question']}")
        print(f"응답: {item['answer'][:50]}...")
    
    # 스키마 프롬프트 생성 테스트
    prompt = nl_to_sql_service.create_schema_prompt(
        schema=TEST_SCHEMA,
        db_type="mssql"
    )
    
    print("\n4. 스키마 프롬프트 (일부):")
    print(prompt[:200] + "...")
    
    print("\n자연어-SQL 변환 서비스 테스트 완료")


if __name__ == "__main__":
    asyncio.run(test_nl_to_sql_service())