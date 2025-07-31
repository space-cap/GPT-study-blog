# saju_chatbot/chatbot/graph.py

from langgraph.graph import StateGraph, END
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from chatbot.state import AgentState
from chatbot.nodes import (
    call_llm,
    route_decision,
    call_tool,
    respond_to_user,
    update_saju_info,
)


class SajuChatbotGraph:
    def __init__(self):
        self.workflow = StateGraph(AgentState)

        # 1. 노드 정의
        self.workflow.add_node("call_llm", call_llm)  # LLM 호출
        self.workflow.add_node("call_tool", call_tool)  # LLM이 결정한 도구 호출
        self.workflow.add_node(
            "update_saju_info", update_saju_info
        )  # 도구 결과로 사주 정보 업데이트
        self.workflow.add_node(
            "respond_to_user", respond_to_user
        )  # 사용자에게 최종 응답

        # 2. 엣지(Edge) 정의
        # 시작 지점
        self.workflow.set_entry_point("call_llm")

        # LLM 호출 후, 어떤 길로 갈지 결정
        self.workflow.add_conditional_edges(
            "call_llm",
            route_decision,  # 라우팅 함수
            {
                "call_tool": "call_tool",  # LLM이 도구 호출을 원하면 call_tool 노드로
                "respond_to_user": "respond_to_user",  # LLM이 바로 응답을 원하면 respond_to_user 노드로
            },
        )

        # 도구 호출 후
        self.workflow.add_edge(
            "call_tool", "update_saju_info"
        )  # 도구 호출 결과를 바탕으로 사주 정보 업데이트
        self.workflow.add_edge(
            "update_saju_info", "call_llm"
        )  # 업데이트 후 다시 LLM 호출하여 최종 응답 생성 유도

        # 사용자에게 응답 후 종료
        self.workflow.add_edge("respond_to_user", END)

        # 3. 그래프 컴파일
        self.app = self.workflow.compile()

    def get_graph_app(self):
        return self.app


# 그래프 시각화 (선택 사항)
if __name__ == "__main__":
    saju_graph = SajuChatbotGraph()
    # 그래프를 이미지 파일로 저장 (graphviz 필요)
    # try:
    #     from IPython.display import Image, display
    #     display(Image(saju_graph.app.get_graph().draw_png()))
    # except ImportError:
    #     print("Graphviz is not installed. Skipping graph visualization.")
    #     print("Install with: pip install pygraphviz graphviz")

    print("LangGraph Saju Chatbot Workflow Compiled.")
    print("Example usage (run this in app.py):")
    print(
        """
    from langchain_core.messages import HumanMessage
    from uuid import uuid4
    
    session_id = str(uuid4()) # 고유한 세션 ID 생성
    
    inputs = {"messages": [HumanMessage(content="안녕하세요, 제 사주를 알려주세요. 1990년 5월 10일 오후 3시생이에요.")], "session_id": session_id}
    
    # for state in saju_graph.app.stream(inputs):
    #     if "__end__" not in state:
    #         print(state)
    #     else:
    #         print(state)
    """
    )
