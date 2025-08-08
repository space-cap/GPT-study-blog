import logging
import os


def setup_logging():
    """
    프로젝트 전반에 사용될 표준 로깅 설정을 구성합니다.
    로그는 콘솔과 파일에 모두 기록됩니다.
    """
    # 로그 파일을 저장할 logs 폴더가 없으면 생성합니다.
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # 로거를 설정합니다.
    # DEBUG 레벨 이상의 모든 로그를 처리하도록 설정합니다.
    # 실제 운영 환경에서는 INFO 레벨로 조정할 수 있습니다.
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        handlers=[
            logging.FileHandler("logs/chatbot.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    logging.info("로깅 설정이 완료되었습니다.")


if __name__ == "__main__":
    setup_logging()