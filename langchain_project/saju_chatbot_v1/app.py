# saju_chatbot/app.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from chatbot.graph import SajuChatbotGraph
from chatbot.state import AgentState
from database.mysql_manager import MySQLManager
from typing import List
from uuid import uuid4
import uvicorn
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

app = FastAPI(
    title="사주팔자 챗봇 API",
    description="LangChain, LangGraph, OpenAI를 활용한 사주팔자 챗봇",
)

# 챗봇 그래프 초기화
saju_graph_app = SajuChatbotGraph().get_graph_app()

# MySQL Manager 초기화 (애플리케이션 시작 시 한 번)
mysql_manager = MySQLManager()


class ChatRequest(BaseModel):
    user_id: str
    session_id: str | None = None  # 세션 ID가 없으면 새로 생성
    message: str
    history: List[dict] = []  # 대화 기록 (optional)


@app.post("/chat/")
async def chat_with_saju_bot(request: ChatRequest):
    """
    사주팔자 챗봇과 대화합니다.
    """
    session_id = request.session_id if request.session_id else str(uuid4())
    logging.info(
        f"Received chat request from user_id: {request.user_id}, session_id: {session_id}"
    )

    # 대화 기록 구성 (LangGraph의 messages 필드에 맞게)
    messages = []
    # 이전 대화 기록이 있다면 추가
    for msg in request.history:
        if msg.get("role") == "user":
            messages.append(HumanMessage(content=msg.get("content", "")))
        elif msg.get("role") == "assistant":
            if msg.get(
                "tool_calls"
            ):  # LLM의 tool_calls가 있었다면 AIMessage with tool_calls
                tool_calls = msg["tool_calls"]
                # tool_calls는 {name, args, id} 형태가 필요
                messages.append(
                    AIMessage(content=msg.get("content", ""), tool_calls=tool_calls)
                )
            else:  # 일반 AIMessage
                messages.append(AIMessage(content=msg.get("content", "")))
        elif msg.get("role") == "tool":  # ToolMessage
            messages.append(
                ToolMessage(
                    content=msg.get("content", ""),
                    tool_call_id=msg.get("tool_call_id", ""),
                )
            )

    # 현재 사용자 메시지 추가
    messages.append(HumanMessage(content=request.message))

    # LangGraph 시작 상태 설정
    # 사용자의 생년월일시 정보가 이미 세션에 저장되어 있다면 여기서 로드하여 초기 상태에 넣어줄 수 있음
    initial_state_data = {
        "messages": messages,
        "session_id": session_id,
        "user_birth_datetime": None,
        "user_birth_is_lunar": None,
        "user_birth_is_leap_month": None,
        "saju_calculated_info": None,
        "saju_analyzed_info": None,
        "current_intent": None,
        "error_message": None,
    }

    # MySQL에서 세션 데이터 로드 (필요시)
    session_from_db = mysql_manager.get_user_session(session_id)
    if session_from_db and session_from_db.get("birth_datetime"):
        initial_state_data["user_birth_datetime"] = session_from_db["birth_datetime"]
        initial_state_data["user_birth_is_lunar"] = session_from_db["is_lunar"]
        initial_state_data["user_birth_is_leap_month"] = session_from_db[
            "is_leap_month"
        ]
        logging.info(
            f"Loaded existing session data for {session_id}: {session_from_db['birth_datetime']}"
        )

    try:
        # LangGraph 실행 (스트림을 사용하여 단계별로 처리)
        final_response_message = ""
        last_state = None

        # for state in saju_graph_app.stream(initial_state_data):
        #     if "__end__" not in state:
        #         last_state = state
        #     else:
        #         last_state = state["__end__"] # 최종 상태

        # 스트림 대신 한 번에 실행 (간단한 API 응답을 위해)
        final_state = saju_graph_app.invoke(initial_state_data)
        last_state = final_state

        if last_state and last_state.get("messages"):
            # 마지막 AIMessage 또는 ToolMessage를 찾아 사용자에게 응답
            for msg in reversed(last_state["messages"]):
                if isinstance(msg, AIMessage):
                    final_response_message = msg.content
                    break
                elif isinstance(msg, ToolMessage):
                    # ToolMessage가 있다면, 그 결과로 다시 LLM이 응답해야 함
                    # 여기서는 간단히 Tool 결과 자체를 보여주지만, 실제로는 LLM이 이를 해석해서 최종 답변해야 함
                    final_response_message = f"Tool Result: {msg.content}"
                    break

            # 최종 상태에서 사주 정보가 업데이트되었다면 MySQL에 저장
            if last_state.get("saju_calculated_info"):
                birth_dt = last_state["user_birth_datetime"]
                is_lunar = last_state["user_birth_is_lunar"]
                is_leap_month = last_state["user_birth_is_leap_month"]
                mysql_manager.save_user_session(
                    session_id, request.user_id, birth_dt, is_lunar, is_leap_month
                )
                logging.info(f"Saju info saved for session {session_id}.")

        if not final_response_message:
            final_response_message = "죄송합니다. 현재 요청을 처리할 수 없습니다."
            logging.warning(f"No final response message for session {session_id}.")

        # 응답 형태 변환 (history에 포함될 메시지 형식)
        response_messages_for_history = []
        for msg in last_state.get("messages", []):
            if isinstance(msg, HumanMessage):
                response_messages_for_history.append(
                    {"role": "user", "content": msg.content}
                )
            elif isinstance(msg, AIMessage):
                # tool_calls가 있다면 함께 반환
                if msg.tool_calls:
                    response_messages_for_history.append(
                        {
                            "role": "assistant",
                            "content": msg.content,
                            "tool_calls": [tc for tc in msg.tool_calls],
                        }
                    )
                else:
                    response_messages_for_history.append(
                        {"role": "assistant", "content": msg.content}
                    )
            elif isinstance(msg, ToolMessage):
                response_messages_for_history.append(
                    {
                        "role": "tool",
                        "content": msg.content,
                        "tool_call_id": msg.tool_call_id,
                    }
                )

        return {
            "session_id": session_id,
            "response": final_response_message,
            "full_history": response_messages_for_history,  # 전체 대화 기록 반환 (UI에서 관리용)
        }

    except Exception as e:
        logging.error(
            f"Error processing chat request for session {session_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 MySQL 연결 닫기"""
    mysql_manager.close()
    logging.info("Shutting down and closing MySQL connection.")


if __name__ == "__main__":
    # ChromaDB 초기화 (데이터 로딩) - 한 번만 실행되도록 설정
    from database.chroma_manager import ChromaManager

    chroma_manager_init = ChromaManager()

    # .env 파일에 OPENAI_API_KEY, MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB 설정 필요
    # 예시:
    # OPENAI_API_KEY="sk-..."
    # MYSQL_HOST="localhost"
    # MYSQL_USER="root"
    # MYSQL_PASSWORD="your_mysql_password"
    # MYSQL_DB="saju_chatbot_db"

    uvicorn.run(app, host="0.0.0.0", port=8000)
