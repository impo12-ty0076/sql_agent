from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum


class LLMProvider(str, Enum):
    """지원되는 LLM 제공자"""
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    HUGGINGFACE = "huggingface"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"


class LLMConfig:
    """LLM 서비스 설정"""
    
    def __init__(
        self,
        provider: LLMProvider,
        model_name: str,
        api_key: str,
        api_base: Optional[str] = None,
        api_version: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.2,
        timeout: int = 60,
        embedding_model: Optional[str] = None,
        **kwargs
    ):
        """
        LLM 서비스 설정 초기화
        
        Args:
            provider (LLMProvider): LLM 제공자
            model_name (str): 모델 이름
            api_key (str): API 키
            api_base (Optional[str], optional): API 기본 URL
            api_version (Optional[str], optional): API 버전
            max_tokens (int, optional): 최대 토큰 수
            temperature (float, optional): 온도 (창의성 조절)
            timeout (int, optional): 요청 타임아웃 (초)
            embedding_model (Optional[str], optional): 임베딩 모델 이름
            **kwargs: 추가 설정
        """
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key
        self.api_base = api_base
        self.api_version = api_version
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.embedding_model = embedding_model or "text-embedding-ada-002"  # 기본 임베딩 모델
        self.additional_config = kwargs


class LLMService(ABC):
    """
    LLM 서비스의 기본 인터페이스
    모든 LLM 서비스는 이 클래스를 상속해야 함
    """
    
    def __init__(self, config: LLMConfig):
        """
        LLM 서비스 초기화
        
        Args:
            config (LLMConfig): LLM 서비스 설정
        """
        self.config = config
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def get_model_info(self) -> Dict[str, Any]:
        """
        LLM 모델 정보 조회
        
        Returns:
            Dict[str, Any]: 모델 정보 (제공자, 모델명, 기능 등)
        """
        pass
        
    @abstractmethod
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        텍스트에 대한 임베딩 생성
        
        Args:
            texts (List[str]): 임베딩을 생성할 텍스트 목록
            
        Returns:
            List[List[float]]: 생성된 임베딩 목록
        """
        pass
        
    def get_embeddings_sync(self, texts: List[str]) -> List[List[float]]:
        """
        텍스트에 대한 임베딩 생성 (동기 버전)
        
        Args:
            texts (List[str]): 임베딩을 생성할 텍스트 목록
            
        Returns:
            List[List[float]]: 생성된 임베딩 목록
        """
        import asyncio
        return asyncio.run(self.get_embeddings(texts))
        
    @abstractmethod
    async def generate_rag_response(self, query: str, context: str) -> str:
        """
        RAG 컨텍스트를 기반으로 응답 생성
        
        Args:
            query (str): 사용자 질의
            context (str): 검색된 문서 컨텍스트
            
        Returns:
            str: 생성된 응답
        """
        pass