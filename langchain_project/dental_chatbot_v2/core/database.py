"""
MySQL 데이터베이스 연결 및 관리 모듈
"""

import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from config import Config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """MySQL 데이터베이스 관리 클래스"""

    def __init__(self):
        self.config = Config()
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()

    def _initialize_database(self):
        """데이터베이스 연결 초기화"""
        try:
            self.engine = create_engine(
                self.config.mysql_url,
                pool_pre_ping=True,
                pool_recycle=300,
                echo=self.config.DEBUG,
            )
            self.SessionLocal = sessionmaker(bind=self.engine)

            # 연결 테스트
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))

            logger.info("데이터베이스 연결 성공")
        except SQLAlchemyError as e:
            logger.error(f"데이터베이스 연결 실패: {e}")
            raise

    def get_treatment_prices(self):
        """진료 항목 및 비용 정보 조회"""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(
                    text(
                        """
                    SELECT treatment_name, price, description, category
                    FROM treatment_prices
                    ORDER BY category, treatment_name
                """
                    )
                )

                treatments = []
                for row in result:
                    treatments.append(
                        {
                            "name": row[0],
                            "price": row[1],
                            "description": row[2],
                            "category": row[3],
                        }
                    )

                logger.info(f"진료 항목 {len(treatments)}개 조회 완료")
                return treatments

        except SQLAlchemyError as e:
            logger.error(f"진료 항목 조회 실패: {e}")
            return []

    def save_customer_info(self, customer_data):
        """고객 정보 저장"""
        try:
            with self.engine.connect() as connection:
                connection.execute(
                    text(
                        """
                    INSERT INTO customers (name, phone, consent_date, symptoms, created_at)
                    VALUES (:name, :phone, :consent_date, :symptoms, NOW())
                """
                    ),
                    customer_data,
                )
                connection.commit()

                logger.info(f"고객 정보 저장 완료: {customer_data['name']}")
                return True

        except SQLAlchemyError as e:
            logger.error(f"고객 정보 저장 실패: {e}")
            return False

    def get_session(self):
        """데이터베이스 세션 반환"""
        return self.SessionLocal()

    def close(self):
        """데이터베이스 연결 종료"""
        if self.engine:
            self.engine.dispose()
            logger.info("데이터베이스 연결 종료")
