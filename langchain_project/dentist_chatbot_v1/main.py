# main.py
from chatbot.memory import UserSession
from chatbot.flow_control import handle_user_input

user_sessions = {}  # 간단 예시. 실제론 redis 등 세션 분산관리 권장


@app.post("/chat")
def chat_api(user_id: str, message: str):
    session = user_sessions.get(user_id) or UserSession(user_id)
    user_sessions[user_id] = session
    session.add_message("user", message)
    bot_response = handle_user_input(session, message, chroma_vectordb=None)
    session.add_message("bot", bot_response)
    return {"response": bot_response}
