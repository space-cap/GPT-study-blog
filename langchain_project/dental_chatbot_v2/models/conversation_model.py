"""
대화 데이터 모델 정의
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class Message(BaseModel):
    """개별 메시지 모델"""

    role: str  # 'user' or 'bot'
    message: str
    timestamp: str
    intent: Optional[str] = None
    confidence: Optional[float] = None


class ConversationSession(BaseModel):
    """대화 세션 모델"""

    session_id: str
    user_info: Dict[str, Any] = {}
    messages: List[Message] = []
    current_stage: str = "greeting"
    consent_status: bool = False
    created_at: str
    updated_at: str

    def add_message(
        self, role: str, message: str, intent: str = None, confidence: float = None
    ):
        """메시지 추가"""
        msg = Message(
            role=role,
            message=message,
            timestamp=datetime.now().isoformat(),
            intent=intent,
            confidence=confidence,
        )
        self.messages.append(msg)
        self.updated_at = datetime.now().isoformat()

    def get_recent_messages(self, limit: int = 5) -> List[Message]:
        """최근 메시지 반환"""
        return self.messages[-limit:]


class IntentResult(BaseModel):
    """의도 분석 결과 모델"""

    intent: str
    confidence: float
    extracted_keywords: List[str]
    requires_personal_info: bool = False


class SearchResult(BaseModel):
    """검색 결과 모델"""

    content: str
    source: str
    category: str
    score: Optional[float] = None
