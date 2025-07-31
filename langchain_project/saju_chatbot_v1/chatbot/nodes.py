# saju_chatbot/chatbot/nodes.py

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from chatbot.state import AgentState
from chatbot.tools import (
    tools,
    saju_analyzer,
    saju_calculator,
    saju_interpreter,
)  # 전역 인스턴스 가져오기
from config import OPENAI_API_KEY
from datetime import datetime
import json

# LLM 초기화 (Node 내부에서 호출하기 위함)
llm = ChatOpenAI(model="gpt-4o", temperature=0.7, api_key=OPENAI_API_KEY)


def call_llm(state: AgentState):
    """
    LLM을 호출하여 사용자의 의도를 파악하고, 필요한 경우 도구를 사용하도록 유도합니다.
    """
    messages = state["messages"]

    # 디버깅을 위한 메시지 타입 확인
    print(f"Messages count: {len(messages)}")
    for i, msg in enumerate(messages):
        print(
            f"Message {i}: type={type(msg)}, content_type={type(getattr(msg, 'content', None))}"
        )

    try:
        response = llm.invoke(messages)
        return {"messages": [response]}
    except Exception as e:
        print(f"Error in call_llm: {e}")
        return {
            "messages": [AIMessage(content=f"LLM 호출 중 오류가 발생했습니다: {e}")]
        }


def route_decision(state: AgentState):
    """
    LLM의 응답을 바탕으로 다음 노드를 결정합니다.
    """
    latest_message = state["messages"][-1]

    if latest_message.tool_calls:
        # LLM이 도구 호출을 결정했다면, 도구 호출 노드로 이동
        return "call_tool"

    # 챗봇이 사용자에게 질문하거나 정보를 제공하는 경우
    # 여기서는 간단히 'respond_to_user'로 라우팅하지만, 더 복잡한 대화 흐름은 추가 조건 필요
    return "respond_to_user"


def call_tool(state: AgentState):
    """
    LLM이 결정한 도구를 실행하고 결과를 상태에 업데이트합니다.
    """
    latest_message = state["messages"][-1]
    tool_calls = latest_message.tool_calls

    tool_results = []
    for tool_call in tool_calls:
        try:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            # 정의된 도구 중에서 해당 이름의 도구 찾기
            selected_tool = next((t for t in tools if t.name == tool_name), None)

            if selected_tool:
                print(f"Calling tool: {tool_name} with args: {tool_args}")
                result = selected_tool.invoke(tool_args)
                print(f"Tool result: {result}")
                tool_results.append(
                    ToolMessage(content=str(result), tool_call_id=tool_call["id"])
                )
            else:
                tool_results.append(
                    ToolMessage(
                        content=f"Error: Tool '{tool_name}' not found.",
                        tool_call_id=tool_call["id"],
                    )
                )
        except Exception as e:
            tool_results.append(
                ToolMessage(
                    content=f"Error calling tool {tool_name}: {e}",
                    tool_call_id=tool_call["id"],
                )
            )

    return {"messages": tool_results}


def respond_to_user(state: AgentState):
    """
    최종적으로 사용자에게 응답을 생성하고 반환합니다.
    LLM이 직접 생성한 메시지이거나, 도구 호출 결과를 바탕으로 생성된 메시지일 수 있습니다.
    """
    latest_message = state["messages"][-1]

    # 만약 마지막 메시지가 ToolMessage라면, 다시 LLM을 호출하여 응답을 생성하도록 할 수 있음
    # 이 예시에서는 ToolMessage 다음에 바로 LLM이 응답하도록 Graph를 구성할 예정

    # 사용자에게 응답할 메시지를 선택
    final_response_message = latest_message

    # 사주 계산/분석/해석 결과가 있다면 이를 활용하여 LLM이 답변하도록 다시 LLM 호출
    if state.get("saju_calculated_info") and state.get("saju_analyzed_info"):
        analyzed_info = state["saju_analyzed_info"]
        user_input_message = ""
        # 사용자 질문이 있었는지 확인하고 넘겨줌
        for msg in state["messages"]:
            if isinstance(msg, HumanMessage):
                user_input_message = msg.content
                break

        # 사주 해석 도구를 사용하여 최종 답변 생성
        # 이 부분을 LLM이 ToolCall로 결정하도록 할 수도 있고, 노드에서 직접 호출할 수도 있습니다.
        # 여기서는 노드에서 직접 호출하여 LLM에게 최종 답변을 생성하도록 유도합니다.

        # 사주 해석 함수를 바로 호출하기보다, LLM에게 해석을 요청하는 프롬프트로 다시 넘겨주는 것이 더 유연
        # 예를 들어, "당신의 사주 정보는 [정보]입니다. 이에 대해 상세하게 풀이해주세요."

        # 하지만 tools.py에 있는 get_saju_interpretation을 직접 호출하는 시나리오도 가능
        # 이 경우, LLM의 개입이 줄어들어 미리 정의된 해석을 더 많이 따를 수 있음

        # 여기서는 LLM이 직접 최종 응답을 생성하도록 유도하기 위해
        # 이전 분석 결과를 바탕으로 'saju_interpreter'의 'interpret_saju' 메소드를 직접 호출
        # (이는 LangGraph의 노드 설계에 따라 달라질 수 있음)

        try:
            # LangGraph의 Flow에서 ToolCall이 발생했으므로, 여기서 다시 Tool을 부르는 것보다는
            # ToolCall의 결과를 LLM에게 다시 넘겨줘서 최종 답변을 받도록 하는 것이 일반적
            # 이 'respond_to_user' 노드는 LLM이 최종 응답을 생성하는 역할을 맡아야 함.
            # 따라서 'call_llm' 노드에서 생성된 메시지를 그대로 사용하거나,
            # tool_results를 바탕으로 LLM에게 다시 질의하여 최종 답변을 생성해야 합니다.

            # 현재 상태의 모든 메시지를 다시 LLM에게 전달하여 최종 사용자 응답 생성
            final_llm_response = llm.invoke(state["messages"])
            return {"messages": [final_llm_response]}

        except Exception as e:
            return {
                "messages": [
                    AIMessage(
                        content=f"사주 해석 결과를 제공하는 중 오류가 발생했습니다: {e}"
                    )
                ]
            }

    return {"messages": [final_response_message]}


def update_saju_info(state: AgentState):
    """
    사주 계산 및 분석 도구의 결과가 있으면 상태를 업데이트합니다.
    """
    latest_message = state["messages"][-1]

    # ToolMessage가 있다면 그 내용을 파싱하여 상태 업데이트
    if isinstance(latest_message, ToolMessage) and latest_message.tool_call_id:
        try:
            tool_result = json.loads(latest_message.content)
            if "saju_info" in tool_result and "analyzed_info" in tool_result:
                print(
                    f"Updating state with saju_calculated_info and saju_analyzed_info: {tool_result['analyzed_info']}"
                )
                return {
                    "saju_calculated_info": tool_result["saju_info"],
                    "saju_analyzed_info": tool_result["analyzed_info"],
                }
            elif "error" in tool_result:
                return {"error_message": tool_result["message"]}
        except json.JSONDecodeError:
            print(f"Failed to decode tool result: {latest_message.content}")
            return {"error_message": "도구 결과 파싱 중 오류 발생."}
    return {}  # 변경사항 없음
