import logging
import sys
from typing import Dict, Any
import json
from datetime import datetime

# 로깅 설정
def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    로거 설정
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 이미 핸들러가 설정되어 있으면 추가하지 않음
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

# 기본 로거 설정
logger = setup_logger("sql_agent")

def log_event(event_type: str, data: Dict[str, Any]) -> None:
    """
    이벤트 로깅
    """
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        **data
    }
    logger.info(json.dumps(log_data))

def log_error(error_type: str, error_message: str, details: Dict[str, Any] = None) -> None:
    """
    오류 로깅
    """
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "error_type": error_type,
        "error_message": error_message,
        "details": details or {}
    }
    logger.error(json.dumps(log_data))