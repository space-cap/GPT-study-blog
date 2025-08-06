"""
메인 실행 파일
시스템 초기화 및 데이터 로딩을 담당
"""

import logging
from utils.logging_config import setup_logging
from core.database import DatabaseManager
from core.vector_store import VectorStoreManager
from core.session_manager import SessionManager
from agents.workflow import get_chatbot_workflow
from config import Config


def initialize_system():
    """시스템 초기화"""
    config = Config()

    # 로깅 설정
    setup_logging(
        log_level="INFO" if not config.DEBUG else "DEBUG", log_file="dental_chatbot.log"
    )

    logger = logging.getLogger(__name__)
    logger.info("=== 치과병원 챗봇 시스템 초기화 시작 ===")

    try:
        # 데이터베이스 연결 테스트
        logger.info("데이터베이스 연결 확인...")
        db_manager = DatabaseManager()

        # 벡터 스토어 초기화 및 데이터 로드
        logger.info("벡터 스토어 초기화...")
        vector_manager = VectorStoreManager()
        vector_manager.initialize_data()

        # 세션 관리자 초기화
        logger.info("세션 관리자 초기화...")
        session_manager = SessionManager()

        # 워크플로우 초기화
        logger.info("LangGraph 워크플로우 초기화...")
        workflow = get_chatbot_workflow()

        logger.info("=== 시스템 초기화 완료 ===")
        return True

    except Exception as e:
        logger.error(f"시스템 초기화 실패: {e}")
        return False


def main():
    """메인 함수"""
    success = initialize_system()

    if success:
        print("✅ 치과병원 챗봇 시스템이 성공적으로 초기화되었습니다.")
        print("FastAPI 서버를 시작하려면 다음 명령어를 사용하세요:")
        print("uvicorn app:app --reload --host 0.0.0.0 --port 8000")
    else:
        print("❌ 시스템 초기화에 실패했습니다. 로그를 확인해주세요.")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
