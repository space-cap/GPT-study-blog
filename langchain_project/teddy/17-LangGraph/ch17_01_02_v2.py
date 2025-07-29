from typing_extensions import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
)


class AdvancedChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    context: dict


def message_processor(state: AdvancedChatState) -> dict:
    """다양한 메시지 타입을 처리하는 함수"""
    last_message = state["messages"][-1]

    responses = []

    if isinstance(last_message, HumanMessage):
        # 사용자 메시지 처리
        ai_response = AIMessage(
            content=f"사용자 메시지를 받았습니다: {last_message.content}"
        )
        responses.append(ai_response)

    elif isinstance(last_message, SystemMessage):
        # 시스템 메시지 처리
        print(f"시스템 메시지: {last_message.content}")

    elif isinstance(last_message, ToolMessage):
        # 도구 메시지 처리
        ai_response = AIMessage(
            content=f"도구 실행 결과를 처리했습니다: {last_message.content}"
        )
        responses.append(ai_response)

    return {"messages": responses}


# 사용 예제
def test_message_types():
    state = AdvancedChatState(messages=[], context={})

    # 다양한 메시지 타입 추가
    test_messages = [
        SystemMessage(content="시스템 초기화 완료"),
        HumanMessage(content="안녕하세요!"),
        ToolMessage(content="검색 결과: 날씨 정보", tool_call_id="search_1"),
    ]

    for msg in test_messages:
        # 메시지 추가 (add_messages 함수가 자동으로 처리)
        state["messages"].append(msg)

        # 메시지 처리
        result = message_processor(state)

        # 응답 메시지들을 상태에 추가
        if result["messages"]:
            state["messages"].extend(result["messages"])

    # 최종 메시지 출력
    print("=== 최종 메시지 히스토리 ===")
    for i, msg in enumerate(state["messages"]):
        print(f"{i+1}. {type(msg).__name__}: {msg.content}")


if __name__ == "__main__":
    test_message_types()
