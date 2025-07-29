from typing_extensions import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import json


# 상태 정의
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_name: str


# 노드 함수들
def greet_user(state: ChatState) -> dict:
    """사용자 인사 노드"""
    print(f"전체 메시지: {state['messages']}")

    greeting = AIMessage(
        content=f"안녕하세요 {state['user_name']}님! 무엇을 도와드릴까요?"
    )
    return {"messages": [greeting]}


def process_question(state: ChatState) -> dict:
    """질문 처리 노드"""
    # 여러 방법으로 확인
    print(f"전체 메시지: {state['messages']}")

    # 로깅 사용
    import logging

    logging.basicConfig(level=logging.INFO)
    logging.info(f"전체 메시지: {state['messages']}")

    # 파일로 출력
    with open("debug.log", "a") as f:
        f.write(f"전체 메시지: {state['messages']}\n")

    last_message = state["messages"][-1]

    # 간단한 질문 처리 로직
    if "날씨" in last_message.content:
        response = AIMessage(
            content="죄송하지만 실시간 날씨 정보는 제공할 수 없습니다."
        )
    elif "안녕" in last_message.content or "hello" in last_message.content.lower():
        response = AIMessage(content="안녕하세요! 좋은 하루 되세요!")
    else:
        response = AIMessage(
            content=f"'{last_message.content}'에 대해 더 구체적으로 알려주시면 도움을 드릴 수 있습니다."
        )

    return {"messages": [response]}


def should_continue(state: ChatState) -> str:
    """대화 계속 여부 결정"""
    last_message = state["messages"][-1]
    print(f"마지막 메시지: {last_message}")
    print(f"마지막 메시지 타입: {type(last_message)}")

    if isinstance(last_message, HumanMessage):
        if "끝" in last_message.content or "bye" in last_message.content.lower():
            return "end"
        return "continue"

    return "end"


# 그래프 생성
def create_chat_graph():
    workflow = StateGraph(ChatState)

    # 노드 추가
    workflow.add_node("greet", greet_user)
    workflow.add_node("process", process_question)

    # 엣지 추가
    workflow.add_edge(START, "greet")
    workflow.add_conditional_edges(
        "greet", should_continue, {"continue": "process", "end": END}
    )
    workflow.add_conditional_edges(
        "process", should_continue, {"continue": "process", "end": END}
    )

    return workflow.compile()


# 실행 예제
def run_chat_example():
    app = create_chat_graph()

    # 초기 상태 설정
    initial_state = {
        "messages": [HumanMessage(content="안녕하세요!")],
        "user_name": "김철수",
    }

    print("=== 채팅 시작 ===")

    # 대화 시뮬레이션
    conversation = [
        "안녕하세요!",
        "오늘 날씨 어때요?",
        "감사합니다. 좋은 하루 되세요!",
        "끝",
    ]

    state = initial_state
    for user_input in conversation:
        print(f"사용자: {user_input}")

        # 사용자 메시지 추가
        state["messages"].append(HumanMessage(content=user_input))

        # 그래프 실행
        result = app.invoke(state)

        # 결과 출력
        for message in result["messages"]:
            if isinstance(message, AIMessage):
                print(f"AI: {message.content}")

        state = result
        print("-" * 50)


if __name__ == "__main__":
    run_chat_example()
