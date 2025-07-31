# saju_chatbot/database/mysql_manager.py

import mysql.connector
from mysql.connector import Error
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB
from datetime import datetime


class MySQLManager:
    def __init__(self):
        self.connection = None
        try:
            self.connection = mysql.connector.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DB,
            )
            if self.connection.is_connected():
                db_Info = self.connection.get_server_info()
                print("MySQL Server version: ", db_Info)
                cursor = self.connection.cursor()
                cursor.execute("SELECT DATABASE();")
                record = cursor.fetchone()
                print("Connected to database: ", record)
                self._create_tables()
        except Error as e:
            print(f"Error while connecting to MySQL: {e}")

    def _create_tables(self):
        """필요한 테이블들을 생성합니다."""
        cursor = self.connection.cursor()
        # 사용자 세션 관리를 위한 테이블 (예시)
        user_session_table_query = """
        CREATE TABLE IF NOT EXISTS user_sessions (
            session_id VARCHAR(255) PRIMARY KEY,
            user_id VARCHAR(255) UNIQUE,
            birth_datetime DATETIME,
            is_lunar BOOLEAN,
            is_leap_month BOOLEAN,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        );
        """
        # 챗봇 대화 기록 (필요시)
        conversation_history_table_query = """
        CREATE TABLE IF NOT EXISTS conversation_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(255),
            role ENUM('user', 'assistant'),
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES user_sessions(session_id)
        );
        """
        try:
            cursor.execute(user_session_table_query)
            cursor.execute(conversation_history_table_query)
            self.connection.commit()
            print("Tables checked/created successfully.")
        except Error as e:
            print(f"Error creating tables: {e}")
        finally:
            cursor.close()

    def get_user_session(self, session_id: str):
        """세션 ID로 사용자 세션 정보를 조회합니다."""
        cursor = self.connection.cursor(dictionary=True)
        query = "SELECT * FROM user_sessions WHERE session_id = %s"
        cursor.execute(query, (session_id,))
        record = cursor.fetchone()
        cursor.close()
        return record

    def save_user_session(
        self,
        session_id: str,
        user_id: str,
        birth_datetime: datetime = None,
        is_lunar: bool = None,
        is_leap_month: bool = None,
    ):
        """사용자 세션 정보를 저장 또는 업데이트합니다."""
        cursor = self.connection.cursor()
        query = """
        INSERT INTO user_sessions (session_id, user_id, birth_datetime, is_lunar, is_leap_month)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            birth_datetime = VALUES(birth_datetime),
            is_lunar = VALUES(is_lunar),
            is_leap_month = VALUES(is_leap_month),
            last_updated = CURRENT_TIMESTAMP;
        """
        try:
            cursor.execute(
                query, (session_id, user_id, birth_datetime, is_lunar, is_leap_month)
            )
            self.connection.commit()
            print(f"Session {session_id} saved/updated successfully.")
        except Error as e:
            print(f"Error saving user session: {e}")
        finally:
            cursor.close()

    def close(self):
        """데이터베이스 연결을 닫습니다."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("MySQL connection closed.")


# 테스트 코드 (실제 사용 시에는 이 부분을 app.py 등에서 호출)
if __name__ == "__main__":
    mysql_manager = MySQLManager()

    # .env 파일에 MySQL 설정 추가 필요:
    # MYSQL_HOST=localhost
    # MYSQL_USER=root
    # MYSQL_PASSWORD=your_password
    # MYSQL_DB=saju_chatbot_db

    # 세션 저장 예시
    from datetime import datetime

    session_id_test = "test_session_123"
    user_id_test = "user_abc"
    birth_dt_test = datetime(1990, 10, 20, 10, 30)
    mysql_manager.save_user_session(
        session_id_test, user_id_test, birth_dt_test, False, False
    )

    # 세션 조회 예시
    session_data = mysql_manager.get_user_session(session_id_test)
    if session_data:
        print(f"Retrieved session: {session_data}")
    else:
        print(f"Session {session_id_test} not found.")

    mysql_manager.close()
