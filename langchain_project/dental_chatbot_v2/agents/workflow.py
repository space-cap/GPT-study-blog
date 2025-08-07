"""
LangGraph 워크플로우 정의
대화 흐름을 관리하는 메인 워크플로우
"""

import logging
from langgraph.graph import StateGraph, END
from agents.state import ConversationState
from agents.nodes import (
    analyze_intent_node,
    search_information_node,
    generate_response_node,
    handle_consent_node,
    collect_personal_info_node,
)

logger = logging.getLogger(__name__)


def route_conversation(state: ConversationState) -> str:
    """대화 라우팅 함수 - 다음 노드 결정 (노드 함수가 아님)"""
    try:
        # 세션 데이터 가져오기
        from core.session_manager import SessionManager

        session_manager = SessionManager()
        session_data = session_manager.get_session(state["session_id"])

        # 오류가 있으면 일반 응답으로
        if state.get("error_message"):
            return "generate_response"

        # 의도가 없으면 의도 분석으로
        if not state.get("intent"):
            return "analyze_intent"

        # 예약 요청이고 동의가 필요한 경우
        if state["intent"] == "appointment_request" or state.get(
            "requires_personal_info", False
        ):
            if not session_data["consent_given"]:
                return "handle_consent"
            else:
                return "collect_personal_info"

        # 동의 과정 중이면 개인정보 수집으로
        if session_data["conversation_stage"] in [
            "consent_request",
            "info_collection",
            "collect_phone",
        ]:
            return "collect_personal_info"

        # 정보 검색이 필요한 경우
        if state["intent"] in ["hospital_info", "price_inquiry", "treatment_info"]:
            return "search_information"

        # 기본적으로 응답 생성
        return "generate_response"

    except Exception as e:
        logger.error(f"라우팅 오류: {e}")
        return "generate_response"


def create_chatbot_workflow():
    """치과 병원 챗봇 워크플로우 생성"""

    # StateGraph 생성
    workflow = StateGraph(ConversationState)

    # 노드 추가
    workflow.add_node("analyze_intent", analyze_intent_node)
    workflow.add_node("search_information", search_information_node)
    workflow.add_node("generate_response", generate_response_node)
    workflow.add_node("handle_consent", handle_consent_node)
    workflow.add_node("collect_personal_info", collect_personal_info_node)
    workflow.add_node("route_conversation", lambda state: state)  # ✅ 수정: 더미 노드

    # 엣지 추가 (흐름 정의)
    workflow.set_entry_point("route_conversation")

    # ✅ 수정: 조건부 라우팅 함수 분리
    workflow.add_conditional_edges(
        "route_conversation",
        route_conversation,  # 순수 라우팅 함수 (문자열 반환)
        {
            "analyze_intent": "analyze_intent",
            "search_information": "search_information",
            "generate_response": "generate_response",
            "handle_consent": "handle_consent",
            "collect_personal_info": "collect_personal_info",
        },
    )

    # 의도 분석 후 라우팅
    workflow.add_edge("analyze_intent", "route_conversation")

    # 정보 검색 후 응답 생성
    workflow.add_edge("search_information", "generate_response")

    # 동의 처리 후 종료
    workflow.add_edge("handle_consent", END)

    # 개인정보 수집 후 종료
    workflow.add_edge("collect_personal_info", END)

    # 응답 생성 후 종료
    workflow.add_edge("generate_response", END)

    # 워크플로우 컴파일
    app = workflow.compile()

    logger.info("챗봇 워크플로우 생성 완료")
    return app


# 워크플로우 인스턴스 (싱글톤)
chatbot_workflow = None


def get_chatbot_workflow():
    """워크플로우 인스턴스 반환 (싱글톤 패턴)"""
    global chatbot_workflow
    if chatbot_workflow is None:
        chatbot_workflow = create_chatbot_workflow()
    return chatbot_workflow
