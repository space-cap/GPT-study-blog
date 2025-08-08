import uuid
from fastapi import FastAPI
from pydantic import BaseModel
from chatbot_logic import process_chat_turn

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="Smile Dental Chatbot API",
    description="고객 정보 수집을 위한 AI 챗봇 API",
    version="1.0.0",
)

# 세션 데이터를 서버 메모리에 저장하기 위한 딕셔너리
# 실제 프로덕션 환경에서는 Redis와 같은 외부 저장소를 사용하는 것이 좋습니다.
sessions = {}


# API 요청 본문을 위한 Pydantic 모델
class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str


# API 응답을 위한 Pydantic 모델
class ChatResponse(BaseModel):
    session_id: str
    response: str
    is_complete: bool  # 정보 수집이 완료되었는지 여부


@app.post("/chat", response_model=ChatResponse)
def chat_with_bot(request: ChatRequest):
    """
    챗봇과 대화를 주고받는 메인 API 엔드포인트입니다.
    """
    session_id = request.session_id or str(uuid.uuid4())

    # 세션이 없으면 새로 생성
    if session_id not in sessions:
        sessions[session_id] = {
            "collected_info": {
                "name": None,
                "phone_number": None,
                "reason": None,
                "consent_agreed": None,
            },
            "chat_history": [],
        }

    session_data = sessions[session_id]

    # 챗봇 로직을 호출하여 응답 생성
    ai_response, updated_session_data = process_chat_turn(
        session_id=session_id, user_input=request.message, session_data=session_data
    )

    # 세션 데이터 업데이트
    sessions[session_id] = updated_session_data

    # 정보 수집 완료 여부 확인
    collected_info = updated_session_data["collected_info"]
    is_complete = all(collected_info.values())

    return ChatResponse(
        session_id=session_id, response=ai_response, is_complete=is_complete
    )


@app.get("/")
def read_root():
    return {"message": "Smile Dental Chatbot API is running."}
