# saju_chatbot/chatbot/state.py

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from datetime import datetime


class AgentState(TypedDict):
    """
    LangGraph 에이전트의 상태를 정의합니다.
    이 상태는 그래프의 노드들 사이에서 전달되며, 대화의 맥락과 정보를 유지합니다.
    """

    # 사용자 입력 메시지 및 챗봇 응답 메시지 이력
    messages: Annotated[list, add_messages]

    # 사주 계산에 필요한 사용자 정보
    user_birth_datetime: Annotated[datetime | None, "사용자 생년월일시"]
    user_birth_is_lunar: Annotated[bool | None, "음력 여부"]
    user_birth_is_leap_month: Annotated[bool | None, "윤달 여부"]

    # 사주 계산 결과
    saju_calculated_info: Annotated[dict | None, "사주팔자 계산 결과"]

    # 사주 분석 결과
    saju_analyzed_info: Annotated[dict | None, "사주 오행, 십성, 신살 등 분석 결과"]

    # 사용자의 현재 의도 (예: 사주 풀이, 오늘 운세, 궁합 등)
    current_intent: Annotated[str | None, "사용자 의도"]

    # 에러 메시지 (처리 중 오류 발생 시)
    error_message: Annotated[str | None, "에러 메시지"]

    # 세션 ID (MySQL 등에서 사용자 세션 관리용)
    session_id: Annotated[str, "사용자 세션 ID"]
