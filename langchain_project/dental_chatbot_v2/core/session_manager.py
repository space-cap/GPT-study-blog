"""
Redis 세션 관리 모듈
사용자 대화 상태와 수집된 정보를 관리
"""

import json
import logging
from typing import Dict, Any, Optional, List
import fakeredis
from config import Config

logger = logging.getLogger(__name__)


class SessionManager:
    """FakeRedis를 사용한 세션 관리 클래스"""

    def __init__(self):
        self.config = Config()
        self.redis_client = fakeredis.FakeRedis(decode_responses=True)
        self.prefix = self.config.REDIS_PREFIX
        logger.info("세션 관리자 초기화 완료")

    def _get_key(self, session_id: str, key_type: str) -> str:
        """Redis 키 생성"""
        return f"{self.prefix}{session_id}:{key_type}"

    def create_session(self, session_id: str) -> Dict[str, Any]:
        """새 세션 생성"""
        session_data = {
            "session_id": session_id,
            "conversation_stage": "greeting",
            "intent": None,
            "consent_given": False,
            "collected_info": {"name": None, "phone": None, "symptoms": None},
            "chat_history": [],
            "created_at": str(__import__("datetime").datetime.now()),
        }

        self._save_session_data(session_id, session_data)
        logger.info(f"새 세션 생성: {session_id}")
        return session_data

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 데이터 조회"""
        try:
            session_key = self._get_key(session_id, "session")
            data = self.redis_client.get(session_key)

            if data:
                return json.loads(data)
            else:
                # 세션이 없으면 새로 생성
                return self.create_session(session_id)

        except Exception as e:
            logger.error(f"세션 조회 실패 {session_id}: {e}")
            return self.create_session(session_id)

    def _save_session_data(self, session_id: str, session_data: Dict[str, Any]):
        """세션 데이터 저장"""
        try:
            session_key = self._get_key(session_id, "session")
            self.redis_client.setex(
                session_key,
                3600,  # 1시간 TTL
                json.dumps(session_data, ensure_ascii=False),
            )
        except Exception as e:
            logger.error(f"세션 저장 실패 {session_id}: {e}")

    def update_session(
        self, session_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """세션 데이터 업데이트"""
        session_data = self.get_session(session_id)

        for key, value in updates.items():
            if key == "collected_info" and isinstance(value, dict):
                session_data["collected_info"].update(value)
            else:
                session_data[key] = value

        session_data["updated_at"] = str(__import__("datetime").datetime.now())
        self._save_session_data(session_id, session_data)

        logger.info(f"세션 업데이트: {session_id}")
        return session_data

    def add_message_to_history(self, session_id: str, role: str, message: str):
        """대화 히스토리에 메시지 추가"""
        session_data = self.get_session(session_id)

        session_data["chat_history"].append(
            {
                "role": role,
                "message": message,
                "timestamp": str(__import__("datetime").datetime.now()),
            }
        )

        # 히스토리 길이 제한 (최근 20개 메시지만 유지)
        if len(session_data["chat_history"]) > 20:
            session_data["chat_history"] = session_data["chat_history"][-20:]

        self._save_session_data(session_id, session_data)

    def get_chat_history(self, session_id: str, limit: int = 10) -> str:
        """대화 히스토리를 문자열로 반환"""
        session_data = self.get_session(session_id)
        history = session_data.get("chat_history", [])

        if not history:
            return "대화 히스토리가 없습니다."

        # 최근 limit개 메시지만 반환
        recent_history = history[-limit:]

        formatted_history = []
        for msg in recent_history:
            role = "사용자" if msg["role"] == "user" else "상담사"
            formatted_history.append(f"{role}: {msg['message']}")

        return "\n".join(formatted_history)

    def clear_session(self, session_id: str):
        """세션 삭제"""
        try:
            session_key = self._get_key(session_id, "session")
            self.redis_client.delete(session_key)
            logger.info(f"세션 삭제: {session_id}")
        except Exception as e:
            logger.error(f"세션 삭제 실패 {session_id}: {e}")

    def get_all_sessions(self) -> List[str]:
        """모든 활성 세션 ID 목록 반환"""
        try:
            pattern = f"{self.prefix}*:session"
            keys = self.redis_client.keys(pattern)
            session_ids = [
                key.replace(f"{self.prefix}", "").replace(":session", "")
                for key in keys
            ]
            return session_ids
        except Exception as e:
            logger.error(f"세션 목록 조회 실패: {e}")
            return []
