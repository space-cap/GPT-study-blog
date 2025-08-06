"""
LangGraph 대화 상태 정의
"""

from typing import Annotated, List, Dict, Any, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class ConversationState(TypedDict):
    """대화 상태를 정의하는 TypedDict"""

    # 기본 정보
    session_id: str
    user_message: str
    bot_response: str

    # 메시지 히스토리 (LangGraph의 메시지 관리 기능 사용)
    messages: Annotated[List, add_messages]

    # 사용자 의도 및 컨텍스트
    intent: Optional[str]
    confidence: float
    extracted_keywords: List[str]

    # 대화 진행 상태
    # 인사 → 정보 문의 → 동의 절차 → 정보 수집 → 완료
    conversation_stage: (
        str  # greeting, info_inquiry, consent_process, info_collection, completion
    )
    requires_personal_info: bool

    # 개인정보 수집 관련
    consent_given: bool
    consent_timestamp: Optional[str]

    # 수집된 정보
    collected_info: Dict[str, Any]

    # 검색 관련
    retrieved_context: str
    search_results: List[Dict[str, Any]]

    # 응답 생성 관련
    prompt_context: Dict[str, Any]

    # 메타데이터
    created_at: str
    updated_at: str

    # 오류 처리
    error_message: Optional[str]
    retry_count: int
