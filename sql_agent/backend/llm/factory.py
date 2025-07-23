"""
LLM 서비스 팩토리

이 모듈은 LLM 서비스 인스턴스를 생성하고 관리하는 팩토리 클래스를 제공합니다.
"""
from typing import Dict, Any, Optional
import logging
from .base import LLMService, LLMConfig, LLMProvider
from .openai_service import OpenAIService


logger = logging.getLogger(__name__)


class LLMServiceFactory:
    """LLM 서비스 팩토리 클래스"""
    
    _instances: Dict[str, LLMService] = {}
    
    @classmethod
    def create_service(cls, config: LLMConfig) -> LLMService:
        """
        LLM 서비스 인스턴스 생성
        
        Args:
            config (LLMConfig): LLM 서비스 설정
            
        Returns:
            LLMService: LLM 서비스 인스턴스
            
        Raises:
            ValueError: 지원되지 않는 LLM 제공자인 경우
        """
        # 인스턴스 키 생성 (제공자 + 모델명)
        instance_key = f"{config.provider.value}_{config.model_name}"
        
        # 기존 인스턴스가 있으면 반환
        if instance_key in cls._instances:
            return cls._instances[instance_key]
        
        # 제공자에 따라 적절한 서비스 인스턴스 생성
        if config.provider == LLMProvider.OPENAI:
            service = OpenAIService(config)
        elif config.provider == LLMProvider.AZURE_OPENAI:
            # Azure OpenAI 서비스 구현 필요
            raise NotImplementedError("Azure OpenAI 서비스는 아직 구현되지 않았습니다.")
        elif config.provider == LLMProvider.HUGGINGFACE:
            # Hugging Face 서비스 구현 필요
            raise NotImplementedError("Hugging Face 서비스는 아직 구현되지 않았습니다.")
        elif config.provider == LLMProvider.ANTHROPIC:
            # Anthropic 서비스 구현 필요
            raise NotImplementedError("Anthropic 서비스는 아직 구현되지 않았습니다.")
        else:
            raise ValueError(f"지원되지 않는 LLM 제공자: {config.provider}")
        
        # 인스턴스 캐싱
        cls._instances[instance_key] = service
        
        return service
    
    @classmethod
    def get_service(cls, provider: LLMProvider, model_name: str) -> Optional[LLMService]:
        """
        캐시된 LLM 서비스 인스턴스 조회
        
        Args:
            provider (LLMProvider): LLM 제공자
            model_name (str): 모델 이름
            
        Returns:
            Optional[LLMService]: LLM 서비스 인스턴스 또는 None
        """
        instance_key = f"{provider.value}_{model_name}"
        return cls._instances.get(instance_key)
    
    @classmethod
    def clear_cache(cls) -> None:
        """캐시된 모든 LLM 서비스 인스턴스 제거"""
        cls._instances.clear()
        logger.info("LLM 서비스 캐시가 초기화되었습니다.")

def get_llm_service(provider: str = "openai", model_name: str = "gpt-4") -> LLMService:
    """
    LLM 서비스 인스턴스를 가져오는 편의 함수
    
    Args:
        provider (str): LLM 제공자 (기본값: "openai")
        model_name (str): 모델 이름 (기본값: "gpt-4")
        
    Returns:
        LLMService: LLM 서비스 인스턴스
    """
    provider_enum = LLMProvider(provider)
    config = LLMConfig(
        provider=provider_enum,
        model_name=model_name,
        api_key="",  # 실제 구현에서는 환경변수에서 가져와야 함
        temperature=0.7,
        max_tokens=2000
    )
    return LLMServiceFactory.create_service(config)