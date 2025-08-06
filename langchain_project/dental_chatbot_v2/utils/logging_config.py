"""
로깅 설정 모듈
"""

import logging
import sys
from datetime import datetime


def setup_logging(log_level: str = "INFO", log_file: str = None):
    """로깅 설정 초기화"""

    # 로그 레벨 설정
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # 로그 포맷 설정
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # 기존 핸들러 제거
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 콘솔 핸들러 추가
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 파일 핸들러 추가 (옵션)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # 특정 라이브러리 로그 레벨 조정
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)

    logging.info("로깅 시스템 초기화 완료")
