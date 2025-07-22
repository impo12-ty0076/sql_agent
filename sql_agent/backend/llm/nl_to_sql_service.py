"""
자연어-SQL 변환 서비스

이 모듈은 자연어 질의를 SQL 쿼리로 변환하는 서비스를 구현합니다.
DB 스키마 정보를 활용한 프롬프트 생성, 자연어 질의를 SQL로 변환하는 로직,
컨텍스트 관리 및 대화 이력 처리 기능을 제공합니다.
"""
from typing import Dict, Any, List, Optional, Tuple
import json
import logging
import asyncio
from datetime import datetime

from .base import LLMService
from .prompt_utils import (
    create_schema_context,
    create_conversation_context,
    SQL_GENERATION_TEMPLATE,
    ENHANCED_SQL_GENERATION_TEMPLATE
)
from .response_utils import parse_llm_response, ResponseParsingError, ResponseValidationError


logger = logging.getLogger(__name__)


class NLToSQLService:
    """자연어-SQL 변환 서비스 클래스"""
    
    def __init__(self, llm_service: LLMService):
        """
        자연어-SQL 변환 서비스 초기화
        
        Args:
            llm_service (LLMService): LLM 서비스 인스턴스
        """
        self.llm_service = llm_service
        self.conversation_history: Dict[str, List[Dict[str, Any]]] = {}
    
    async def convert_nl_to_sql(
        self,
        user_id: str,
        natural_language: str,
        schema: Dict[str, Any],
        db_type: str,
        conversation_id: Optional[str] = None,
        max_context_items: int = 5
    ) -> Dict[str, Any]:
        """
        자연어 질의를 SQL로 변환
        
        Args:
            user_id (str): 사용자 ID
            natural_language (str): 자연어 질의
            schema (Dict[str, Any]): DB 스키마 정보
            db_type (str): 데이터베이스 유형 ('mssql' 또는 'hana')
            conversation_id (Optional[str], optional): 대화 ID
            max_context_items (int, optional): 컨텍스트에 포함할 최대 이전 대화 항목 수
            
        Returns:
            Dict[str, Any]: 생성된 SQL 및 메타데이터
        """
        try:
            # 대화 ID가 없으면 새로 생성
            if not conversation_id:
                conversation_id = f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 대화 컨텍스트 가져오기
            context = self._get_conversation_context(user_id, conversation_id, max_context_items)
            
            # LLM 서비스를 통해 SQL 생성
            result = await self.llm_service.generate_sql(
                natural_language=natural_language,
                schema=schema,
                db_type=db_type,
                context=context
            )
            
            # 대화 이력에 추가
            self._add_to_conversation_history(
                user_id=user_id,
                conversation_id=conversation_id,
                question=natural_language,
                answer=result["sql"],
                metadata={
                    "db_type": db_type,
                    "timestamp": datetime.now().isoformat(),
                    "explanation": result.get("explanation", "")
                }
            )
            
            # 결과에 대화 ID 추가
            result["conversation_id"] = conversation_id
            
            return result
            
        except ResponseParsingError as e:
            logger.error(f"SQL 생성 응답 파싱 실패: {str(e)}")
            raise
        except ResponseValidationError as e:
            logger.error(f"SQL 생성 응답 검증 실패: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"자연어-SQL 변환 중 오류 발생: {str(e)}")
            raise
    
    def _get_conversation_context(
        self,
        user_id: str,
        conversation_id: str,
        max_items: int = 5
    ) -> List[Dict[str, Any]]:
        """
        대화 컨텍스트 가져오기
        
        Args:
            user_id (str): 사용자 ID
            conversation_id (str): 대화 ID
            max_items (int, optional): 최대 항목 수
            
        Returns:
            List[Dict[str, Any]]: 대화 컨텍스트
        """
        # 사용자 대화 이력 가져오기
        user_history = self.conversation_history.get(user_id, {})
        
        # 대화 ID에 해당하는 이력 가져오기
        conversation = user_history.get(conversation_id, [])
        
        # 최근 항목만 반환 (최대 max_items개)
        return conversation[-max_items:] if conversation else []
    
    def _add_to_conversation_history(
        self,
        user_id: str,
        conversation_id: str,
        question: str,
        answer: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        대화 이력에 항목 추가
        
        Args:
            user_id (str): 사용자 ID
            conversation_id (str): 대화 ID
            question (str): 사용자 질문
            answer (str): 시스템 응답
            metadata (Optional[Dict[str, Any]], optional): 추가 메타데이터
        """
        # 사용자 대화 이력 초기화 (없는 경우)
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = {}
        
        # 대화 ID에 해당하는 이력 초기화 (없는 경우)
        if conversation_id not in self.conversation_history[user_id]:
            self.conversation_history[user_id][conversation_id] = []
        
        # 대화 항목 생성
        conversation_item = {
            "question": question,
            "answer": answer,
            "timestamp": datetime.now().isoformat()
        }
        
        # 메타데이터 추가 (있는 경우)
        if metadata:
            conversation_item["metadata"] = metadata
        
        # 대화 이력에 추가
        self.conversation_history[user_id][conversation_id].append(conversation_item)
    
    def get_conversation_history(
        self,
        user_id: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        사용자의 대화 이력 조회
        
        Args:
            user_id (str): 사용자 ID
            conversation_id (Optional[str], optional): 대화 ID (None이면 모든 대화 반환)
            
        Returns:
            Dict[str, Any]: 대화 이력
        """
        # 사용자 대화 이력 가져오기
        user_history = self.conversation_history.get(user_id, {})
        
        # 특정 대화 ID가 지정된 경우
        if conversation_id:
            return {
                "conversation_id": conversation_id,
                "history": user_history.get(conversation_id, [])
            }
        
        # 모든 대화 반환
        return {
            "conversations": [
                {
                    "conversation_id": conv_id,
                    "history": history
                }
                for conv_id, history in user_history.items()
            ]
        }
    
    def clear_conversation_history(
        self,
        user_id: str,
        conversation_id: Optional[str] = None
    ) -> None:
        """
        대화 이력 삭제
        
        Args:
            user_id (str): 사용자 ID
            conversation_id (Optional[str], optional): 대화 ID (None이면 모든 대화 삭제)
        """
        # 사용자 대화 이력이 없으면 아무 작업도 하지 않음
        if user_id not in self.conversation_history:
            return
        
        # 특정 대화 ID가 지정된 경우
        if conversation_id and conversation_id in self.conversation_history[user_id]:
            del self.conversation_history[user_id][conversation_id]
        # 모든 대화 삭제
        elif not conversation_id:
            del self.conversation_history[user_id]
    
    def create_schema_prompt(self, schema: Dict[str, Any], db_type: str) -> str:
        """
        DB 스키마 정보를 활용한 프롬프트 생성
        
        Args:
            schema (Dict[str, Any]): DB 스키마 정보
            db_type (str): 데이터베이스 유형 ('mssql' 또는 'hana')
            
        Returns:
            str: 생성된 프롬프트
        """
        # 스키마 및 DB 유형 포맷
        schema_json = create_schema_context(schema)
        
        # 프롬프트 생성
        prompt = f"""
### 데이터베이스 스키마:
{schema_json}

### 데이터베이스 유형:
{db_type}

### 규칙:
1. 오직 SELECT 쿼리만 생성하세요 (INSERT, UPDATE, DELETE, DROP 등은 허용되지 않습니다).
2. 쿼리는 {db_type} 문법에 맞게 작성되어야 합니다.
3. 쿼리는 가능한 한 효율적이어야 합니다.
4. 필요한 경우 주석을 포함하여 쿼리의 각 부분을 설명하세요.
"""
        
        return prompt