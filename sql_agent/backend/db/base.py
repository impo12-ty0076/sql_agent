from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class DBConnector(ABC):
    """
    데이터베이스 커넥터의 기본 인터페이스
    모든 DB 커넥터는 이 클래스를 상속해야 함
    """
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        데이터베이스에 연결
        
        Returns:
            bool: 연결 성공 여부
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        데이터베이스 연결 종료
        
        Returns:
            bool: 연결 종료 성공 여부
        """
        pass
    
    @abstractmethod
    async def is_connected(self) -> bool:
        """
        현재 연결 상태 확인
        
        Returns:
            bool: 연결 상태
        """
        pass
    
    @abstractmethod
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        SQL 쿼리 실행
        
        Args:
            query (str): 실행할 SQL 쿼리
            params (Dict[str, Any], optional): 쿼리 파라미터
            
        Returns:
            Dict[str, Any]: 쿼리 실행 결과
        """
        pass
    
    @abstractmethod
    async def get_schema(self) -> Dict[str, Any]:
        """
        데이터베이스 스키마 정보 조회
        
        Returns:
            Dict[str, Any]: 스키마 정보
        """
        pass