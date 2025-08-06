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
    route_conversation_node,
)

logger = logging.getLogger(__name__)


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
    workflow.add_node("route_conversation", route_conversation_node)

    # 엣지 추가 (흐름 정의)
    workflow.set_entry_point("route_conversation")

    # 라우팅 노드에서 조건부 분기
    workflow.add_conditional_edges(
        "route_conversation",
        lambda x: route_conversation_node(x),  # 라우팅 함수
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
