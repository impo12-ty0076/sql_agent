"""
OpenAI LLM 서비스 구현

이 모듈은 OpenAI API를 사용하여 LLM 서비스 인터페이스를 구현합니다.
"""
from typing import Dict, Any, List, Optional, Tuple
import json
import asyncio
import logging
import numpy as np
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from .base import LLMService, LLMConfig, LLMProvider
from .prompt_utils import (
    SQL_GENERATION_TEMPLATE,
    RESULT_SUMMARY_TEMPLATE,
    PYTHON_CODE_GENERATION_TEMPLATE,
    create_schema_context,
    create_conversation_context,
    create_result_context,
    create_result_structure
)
from .response_utils import parse_llm_response, ResponseParsingError, ResponseValidationError


logger = logging.getLogger(__name__)


class OpenAIService(LLMService):
    """OpenAI API를 사용한 LLM 서비스 구현"""
    
    def __init__(self, config: LLMConfig):
        """
        OpenAI 서비스 초기화
        
        Args:
            config (LLMConfig): LLM 서비스 설정
        """
        super().__init__(config)
        
        # OpenAI 클라이언트 초기화
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.api_base if config.api_base else None,
            timeout=config.timeout
        )
    
    async def _call_openai_api(self, messages: List[Dict[str, str]]) -> str:
        """
        OpenAI API 호출
        
        Args:
            messages (List[Dict[str, str]]): 메시지 목록
            
        Returns:
            str: API 응답 텍스트
            
        Raises:
            Exception: API 호출 실패 시
        """
        try:
            response: ChatCompletion = await self.client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"OpenAI API 호출 실패: {str(e)}")
            raise
            
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        텍스트에 대한 임베딩 생성
        
        Args:
            texts (List[str]): 임베딩을 생성할 텍스트 목록
            
        Returns:
            List[List[float]]: 생성된 임베딩 목록
        """
        if not texts:
            return []
            
        try:
            # 텍스트 전처리
            processed_texts = [text.replace("\n", " ").strip() for text in texts]
            
            # 임베딩 생성
            response = await self.client.embeddings.create(
                model=self.config.embedding_model,
                input=processed_texts
            )
            
            # 응답에서 임베딩 추출
            embeddings = [item.embedding for item in response.data]
            
            return embeddings
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {str(e)}")
            # 오류 발생 시 임의의 임베딩 반환 (실제 구현에서는 적절한 오류 처리 필요)
            return [np.random.rand(1536).tolist() for _ in texts]
            
    async def generate_rag_response(self, query: str, context: str) -> str:
        """
        RAG 컨텍스트를 기반으로 응답 생성
        
        Args:
            query (str): 사용자 질의
            context (str): 검색된 문서 컨텍스트
            
        Returns:
            str: 생성된 응답
        """
        try:
            # 프롬프트 생성
            prompt = f"""
다음은 데이터베이스 스키마에 관한 정보입니다. 이 정보를 바탕으로 사용자의 질문에 답변해주세요.

### 컨텍스트:
{context}

### 질문:
{query}

### 지침:
1. 컨텍스트에 제공된 정보만 사용하여 답변하세요.
2. 컨텍스트에 없는 정보에 대해서는 모른다고 솔직하게 답변하세요.
3. 답변은 명확하고 간결하게 작성하세요.
4. 가능한 경우 테이블, 컬럼, 관계 등의 구체적인 정보를 포함하세요.
5. 답변에 사용된 정보의 출처를 명시하세요.
"""
            
            # API 호출
            messages = [
                {"role": "system", "content": "당신은 데이터베이스 스키마 전문가입니다."},
                {"role": "user", "content": prompt}
            ]
            
            response_text = await self._call_openai_api(messages)
            
            return response_text
            
        except Exception as e:
            logger.error(f"RAG 응답 생성 중 오류 발생: {str(e)}")
            return "죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다."
    
    async def generate_sql(self, natural_language: str, schema: Dict[str, Any], db_type: str, context: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        자연어를 SQL로 변환
        
        Args:
            natural_language (str): 자연어 질의
            schema (Dict[str, Any]): DB 스키마 정보
            db_type (str): 데이터베이스 유형 ('mssql' 또는 'hana')
            context (List[Dict[str, Any]], optional): 대화 컨텍스트
            
        Returns:
            Dict[str, Any]: 생성된 SQL 및 메타데이터
        """
        try:
            # 스키마 및 컨텍스트 포맷
            schema_json = create_schema_context(schema)
            context_text = create_conversation_context(context or [])
            
            # 프롬프트 생성
            prompt = SQL_GENERATION_TEMPLATE.format(
                schema_json=schema_json,
                db_type=db_type,
                question=natural_language,
                context=context_text
            )
            
            # API 호출
            messages = [
                {"role": "system", "content": "당신은 자연어를 SQL로 변환하는 전문가입니다."},
                {"role": "user", "content": prompt}
            ]
            
            response_text = await self._call_openai_api(messages)
            
            # 응답 파싱
            parsed_response = parse_llm_response(response_text, "sql")
            
            return {
                "sql": parsed_response["sql"],
                "explanation": parsed_response.get("explanation", ""),
                "original_question": natural_language,
                "db_type": db_type
            }
            
        except ResponseParsingError as e:
            logger.error(f"SQL 생성 응답 파싱 실패: {str(e)}")
            raise
        except ResponseValidationError as e:
            logger.error(f"SQL 생성 응답 검증 실패: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"SQL 생성 중 오류 발생: {str(e)}")
            raise
    
    async def summarize_results(self, query_result: Dict[str, Any], natural_language: str, sql_query: str) -> Dict[str, Any]:
        """
        쿼리 결과 요약
        
        Args:
            query_result (Dict[str, Any]): 쿼리 실행 결과
            natural_language (str): 원본 자연어 질의
            sql_query (str): 실행된 SQL 쿼리
            
        Returns:
            Dict[str, Any]: 요약 및 인사이트
        """
        try:
            # 결과 포맷
            result_json = create_result_context(query_result)
            
            # 프롬프트 생성
            prompt = RESULT_SUMMARY_TEMPLATE.format(
                question=natural_language,
                sql_query=sql_query,
                result_json=result_json
            )
            
            # API 호출
            messages = [
                {"role": "system", "content": "당신은 데이터 분석 전문가입니다."},
                {"role": "user", "content": prompt}
            ]
            
            response_text = await self._call_openai_api(messages)
            
            # 응답 파싱
            parsed_response = parse_llm_response(response_text, "summary")
            
            return {
                "summary": parsed_response["summary"],
                "insights": parsed_response.get("insights", []),
                "original_question": natural_language
            }
            
        except ResponseParsingError as e:
            logger.error(f"결과 요약 응답 파싱 실패: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"결과 요약 중 오류 발생: {str(e)}")
            raise
    
    async def generate_python_code(self, query_result: Dict[str, Any], natural_language: str, sql_query: str, analysis_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        데이터 분석 및 시각화를 위한 파이썬 코드 생성
        
        Args:
            query_result (Dict[str, Any]): 쿼리 실행 결과
            natural_language (str): 원본 자연어 질의
            sql_query (str): 실행된 SQL 쿼리
            analysis_request (Dict[str, Any]): 분석 요청 정보
            
        Returns:
            Dict[str, Any]: 생성된 파이썬 코드 및 메타데이터
        """
        try:
            # 결과 구조 포맷
            result_structure = create_result_structure(query_result)
            
            # 분석 요청 정보 포맷
            analysis_request_str = json.dumps(analysis_request, ensure_ascii=False, indent=2)
            
            # 프롬프트 생성
            prompt = PYTHON_CODE_GENERATION_TEMPLATE.format(
                question=natural_language,
                sql_query=sql_query,
                result_structure=result_structure,
                analysis_request=analysis_request_str
            )
            
            # API 호출
            messages = [
                {"role": "system", "content": "당신은 데이터 분석 및 시각화 전문가입니다."},
                {"role": "user", "content": prompt}
            ]
            
            response_text = await self._call_openai_api(messages)
            
            # 응답 파싱
            parsed_response = parse_llm_response(response_text, "python")
            
            return {
                "code": parsed_response["code"],
                "explanation": parsed_response.get("explanation", ""),
                "original_question": natural_language
            }
            
        except ResponseParsingError as e:
            logger.error(f"파이썬 코드 생성 응답 파싱 실패: {str(e)}")
            raise
        except ResponseValidationError as e:
            logger.error(f"파이썬 코드 생성 응답 검증 실패: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"파이썬 코드 생성 중 오류 발생: {str(e)}")
            raise
    
    async def validate_and_fix_sql(self, sql_query: str, schema: Dict[str, Any], db_type: str, error_message: Optional[str] = None) -> Tuple[str, bool]:
        """
        SQL 쿼리 검증 및 수정
        
        Args:
            sql_query (str): 검증할 SQL 쿼리
            schema (Dict[str, Any]): DB 스키마 정보
            db_type (str): 데이터베이스 유형 ('mssql' 또는 'hana')
            error_message (Optional[str], optional): 이전 실행에서 발생한 오류 메시지
            
        Returns:
            Tuple[str, bool]: (수정된 SQL 쿼리, 수정 여부)
        """
        # 오류 메시지가 없으면 수정 불필요
        if not error_message:
            return sql_query, False
        
        try:
            # 스키마 포맷
            schema_json = create_schema_context(schema)
            
            # 프롬프트 생성
            prompt = f"""
다음 SQL 쿼리를 검증하고 수정해주세요.

### 데이터베이스 유형:
{db_type}

### 데이터베이스 스키마:
{schema_json}

### SQL 쿼리:
```sql
{sql_query}
```

### 실행 중 발생한 오류:
{error_message}

### 지침:
1. 오류의 원인을 파악하고 수정하세요.
2. {db_type} 문법에 맞게 쿼리를 수정하세요.
3. 테이블 및 컬럼 이름이 스키마와 일치하는지 확인하세요.
4. 수정된 쿼리만 SQL 코드 블록 안에 제공하세요.

### 응답 형식:
```sql
-- 수정된 SQL 쿼리
```
"""
            
            # API 호출
            messages = [
                {"role": "system", "content": "당신은 SQL 전문가입니다."},
                {"role": "user", "content": prompt}
            ]
            
            response_text = await self._call_openai_api(messages)
            
            # 응답 파싱
            parsed_response = parse_llm_response(response_text, "sql")
            fixed_sql = parsed_response["sql"]
            
            # 원본과 동일한지 확인
            is_modified = fixed_sql.strip() != sql_query.strip()
            
            return fixed_sql, is_modified
            
        except ResponseParsingError as e:
            logger.error(f"SQL 검증 응답 파싱 실패: {str(e)}")
            # 오류 발생 시 원본 쿼리 반환
            return sql_query, False
        except ResponseValidationError as e:
            logger.error(f"SQL 검증 응답 검증 실패: {str(e)}")
            # 오류 발생 시 원본 쿼리 반환
            return sql_query, False
        except Exception as e:
            logger.error(f"SQL 검증 중 오류 발생: {str(e)}")
            # 오류 발생 시 원본 쿼리 반환
            return sql_query, False
    
    async def get_model_info(self) -> Dict[str, Any]:
        """
        LLM 모델 정보 조회
        
        Returns:
            Dict[str, Any]: 모델 정보 (제공자, 모델명, 기능 등)
        """
        return {
            "provider": self.config.provider.value,
            "model_name": self.config.model_name,
            "capabilities": [
                "sql_generation",
                "result_summarization",
                "python_code_generation",
                "sql_validation"
            ],
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature
        }