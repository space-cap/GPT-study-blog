"""
FastAPI 웹 애플리케이션
챗봇과의 HTTP API 인터페이스 제공
"""

import uuid
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, Any

from agents.workflow import get_chatbot_workflow
from agents.state import ConversationState
from core.session_manager import SessionManager
from utils.logging_config import setup_logging
from config import Config

# 로깅 설정
setup_logging()
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="치과병원 챗봇 API", description="미소진 치과병원 상담 챗봇", version="1.0.0"
)

# 정적 파일 및 템플릿 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 전역 변수
config = Config()
session_manager = SessionManager()
chatbot_workflow = get_chatbot_workflow()


# 요청/응답 모델
class ChatRequest(BaseModel):
    message: str
    session_id: str = None


class ChatResponse(BaseModel):
    message: str
    session_id: str
    conversation_stage: str
    requires_action: bool = False
    action_type: str = None


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """홈페이지 (채팅 인터페이스)"""
    return templates.TemplateResponse("chat.html", {"request": request})


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """채팅 API 엔드포인트"""
    try:
        # 세션 ID 생성 또는 기존 세션 사용
        session_id = request.session_id or str(uuid.uuid4())

        # 세션 데이터 가져오기
        session_data = session_manager.get_session(session_id)

        # ConversationState 생성
        state = ConversationState(
            session_id=session_id,
            user_message=request.message,
            bot_response="",
            messages=[],
            intent=None,
            confidence=0.0,
            extracted_keywords=[],
            conversation_stage=session_data["conversation_stage"],
            requires_personal_info=False,
            consent_given=session_data["consent_given"],
            collected_info=session_data["collected_info"],
            retrieved_context="",
            search_results=[],
            prompt_context={},
            created_at=session_data["created_at"],
            updated_at=datetime.now().isoformat(),
            error_message=None,
            retry_count=0,
        )

        # 워크플로우 실행
        result = chatbot_workflow.invoke(state)

        # 응답 생성
        response = ChatResponse(
            message=result["bot_response"],
            session_id=session_id,
            conversation_stage=result["conversation_stage"],
            requires_action=result.get("requires_personal_info", False),
            action_type=(
                "personal_info_collection"
                if result.get("requires_personal_info", False)
                else None
            ),
        )

        logger.info(f"채팅 응답 생성 완료: {session_id}")
        return response

    except Exception as e:
        logger.error(f"채팅 처리 오류: {e}")
        raise HTTPException(status_code=500, detail="채팅 처리 중 오류가 발생했습니다.")


@app.get("/session/{session_id}")
async def get_session_info(session_id: str) -> Dict[str, Any]:
    """세션 정보 조회"""
    try:
        session_data = session_manager.get_session(session_id)
        return {
            "session_id": session_id,
            "conversation_stage": session_data["conversation_stage"],
            "consent_given": session_data["consent_given"],
            "collected_info": session_data["collected_info"],
            "created_at": session_data["created_at"],
        }
    except Exception as e:
        logger.error(f"세션 정보 조회 오류: {e}")
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")


@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """세션 삭제"""
    try:
        session_manager.clear_session(session_id)
        return {"message": "세션이 삭제되었습니다."}
    except Exception as e:
        logger.error(f"세션 삭제 오류: {e}")
        raise HTTPException(status_code=500, detail="세션 삭제 중 오류가 발생했습니다.")


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
    }


@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    logger.info("FastAPI 서버 시작")


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    logger.info("FastAPI 서버 종료")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host=config.HOST, port=config.PORT, reload=config.DEBUG)
