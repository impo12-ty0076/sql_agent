"""
자연어-SQL 변환 서비스의 컨텍스트 인식 기능 테스트 스크립트
"""
import asyncio
import json
import sys
import os
from typing import Dict, Any, List
from datetime import datetime

# 현재 디렉토리를 시스템 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.llm.base import LLMConfig, LLMProvider
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
                        {"name": "salary", "type": "DECIMAL(10,2)", "nullable": False},
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
                    "foreignKeys": [
                        {
                            "columns": ["location_id"],
                            "referenceTable": "locations",
                            "referenceColumns": ["location_id"]
                        }
                    ]
                },
                {
                    "name": "locations",
                    "columns": [
                        {"name": "location_id", "type": "INT", "nullable": False},
                        {"name": "city", "type": "VARCHAR(100)", "nullable": False},
                        {"name": "country", "type": "VARCHAR(100)", "nullable": False}
                    ],
                    "primaryKey": ["location_id"],
                    "foreignKeys": []
                }
            ]
        }
    ]
}


class ContextAwareMockLLMService:
    """컨텍스트 인식 테스트용 LLM 서비스 모의 객체"""
    
    async def generate_sql(self, natural_language, schema, db_type, context=None):
        """SQL 생성 모의 메서드 - 컨텍스트에 따라 다른 응답 반환"""
        
        # 컨텍스트가 없는 첫 번째 질의
        if not context:
            return {
                "sql": "SELECT d.department_name, COUNT(e.employee_id) AS employee_count FROM dbo.departments d LEFT JOIN dbo.employees e ON d.department_id = e.department_id GROUP BY d.department_name ORDER BY employee_count DESC",
                "explanation": "이 쿼리는 각 부서별 직원 수를 계산하여 직원 수가 많은 순서대로 정렬합니다.",
                "original_question": natural_language,
                "db_type": db_type
            }
        
        # 컨텍스트가 있는 후속 질의
        if "가장 많은" in natural_language or "최대" in natural_language:
            return {
                "sql": "SELECT TOP 1 d.department_name, COUNT(e.employee_id) AS employee_count FROM dbo.departments d LEFT JOIN dbo.employees e ON d.department_id = e.department_id GROUP BY d.department_name ORDER BY employee_count DESC",
                "explanation": "이 쿼리는 직원 수가 가장 많은 부서를 찾기 위해 이전 쿼리에 TOP 1을 추가하고 직원 수 내림차순으로 정렬합니다.",
                "original_question": natural_language,
                "db_type": db_type
            }
        
        if "평균 급여" in natural_language:
            return {
                "sql": "SELECT d.department_name, AVG(e.salary) AS avg_salary FROM dbo.departments d LEFT JOIN dbo.employees e ON d.department_id = e.department_id GROUP BY d.department_name ORDER BY avg_salary DESC",
                "explanation": "이 쿼리는 각 부서별 평균 급여를 계산하여 평균 급여가 높은 순서대로 정렬합니다.",
                "original_question": natural_language,
                "db_type": db_type
            }
        
        if "위치" in natural_language or "지역" in natural_language or "어디" in natural_language:
            return {
                "sql": "SELECT d.department_name, l.city, l.country FROM dbo.departments d JOIN dbo.locations l ON d.location_id = l.location_id ORDER BY d.department_name",
                "explanation": "이 쿼리는 각 부서의 위치(도시 및 국가)를 조회합니다.",
                "original_question": natural_language,
                "db_type": db_type
            }
        
        # 기본 응답
        return {
            "sql": "SELECT * FROM dbo.employees",
            "explanation": "기본 쿼리입니다.",
            "original_question": natural_language,
            "db_type": db_type
        }


async def test_context_aware_nl_to_sql():
    """컨텍스트 인식 자연어-SQL 변환 서비스 테스트"""
    print("컨텍스트 인식 자연어-SQL 변환 서비스 테스트 시작")
    
    # 컨텍스트 인식 모의 LLM 서비스로 테스트
    mock_llm_service = ContextAwareMockLLMService()
    nl_to_sql_service = NLToSQLService(mock_llm_service)
    
    # 대화 시나리오 테스트
    conversation_id = f"test_conversation_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    user_id = "test_user"
    
    # 첫 번째 질의: 부서별 직원 수
    print("\n1. 첫 번째 질의: 부서별 직원 수")
    result1 = await nl_to_sql_service.convert_nl_to_sql(
        user_id=user_id,
        natural_language="각 부서별 직원 수를 알려주세요",
        schema=TEST_SCHEMA,
        db_type="mssql",
        conversation_id=conversation_id
    )
    print(f"SQL: {result1['sql']}")
    print(f"설명: {result1['explanation']}")
    
    # 두 번째 질의: 직원이 가장 많은 부서
    print("\n2. 두 번째 질의: 직원이 가장 많은 부서 (컨텍스트 활용)")
    result2 = await nl_to_sql_service.convert_nl_to_sql(
        user_id=user_id,
        natural_language="직원이 가장 많은 부서는 어디인가요?",
        schema=TEST_SCHEMA,
        db_type="mssql",
        conversation_id=conversation_id
    )
    print(f"SQL: {result2['sql']}")
    print(f"설명: {result2['explanation']}")
    
    # 세 번째 질의: 부서별 평균 급여
    print("\n3. 세 번째 질의: 부서별 평균 급여 (새로운 주제)")
    result3 = await nl_to_sql_service.convert_nl_to_sql(
        user_id=user_id,
        natural_language="각 부서의 평균 급여는 얼마인가요?",
        schema=TEST_SCHEMA,
        db_type="mssql",
        conversation_id=conversation_id
    )
    print(f"SQL: {result3['sql']}")
    print(f"설명: {result3['explanation']}")
    
    # 네 번째 질의: 부서 위치
    print("\n4. 네 번째 질의: 부서 위치 (스키마 관계 활용)")
    result4 = await nl_to_sql_service.convert_nl_to_sql(
        user_id=user_id,
        natural_language="각 부서는 어디에 위치해 있나요?",
        schema=TEST_SCHEMA,
        db_type="mssql",
        conversation_id=conversation_id
    )
    print(f"SQL: {result4['sql']}")
    print(f"설명: {result4['explanation']}")
    
    # 대화 이력 조회
    print("\n5. 전체 대화 이력:")
    history = nl_to_sql_service.get_conversation_history(
        user_id=user_id,
        conversation_id=conversation_id
    )
    
    for i, item in enumerate(history['history']):
        print(f"\n대화 {i+1}:")
        print(f"질문: {item['question']}")
        print(f"SQL: {item['answer']}")
    
    print("\n컨텍스트 인식 자연어-SQL 변환 서비스 테스트 완료")


if __name__ == "__main__":
    asyncio.run(test_context_aware_nl_to_sql())