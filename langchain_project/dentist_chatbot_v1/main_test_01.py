# main.py

from fastapi import FastAPI
from pydantic import BaseModel
import fakeredis
import pymysql
import re

from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

# --- fakeredis 기반 세션(동의, 이름, 번호 등) 관리 ---
r = fakeredis.FakeStrictRedis()


class UserSession:
    def __init__(self, user_id):
        self.user_id = user_id
        self.history = []
        self.profile = {}
        self.consent_given = False

    @classmethod
    def load(cls, user_id):
        raw = r.get(f"session:{user_id}")
        if raw:
            import json

            data = json.loads(raw)
            obj = cls(user_id)
            obj.history = data.get("history", [])
            obj.profile = data.get("profile", {})
            obj.consent_given = data.get("consent_given", False)
            return obj
        return cls(user_id)

    def save(self):
        import json

        r.set(
            f"session:{self.user_id}",
            json.dumps(
                {
                    "history": self.history,
                    "profile": self.profile,
                    "consent_given": self.consent_given,
                }
            ),
        )

    def add_message(self, speaker, msg):
        self.history.append({"role": speaker, "content": msg})
        if len(self.history) > 10:
            self.history = self.history[-10:]

    def set_profile(self, key, value):
        self.profile[key] = value

    def give_consent(self):
        self.consent_given = True


# --- Chroma(벡터DB) 및 임베딩 함수 ---
chroma = Chroma(
    collection_name="dental_clinic_kr",
    embedding_function=HuggingFaceEmbeddings(model_name="jhgan/ko-sroberta-multitask"),
    persist_directory="./chroma_db",
)


def search_info(query):
    docs = chroma.similarity_search(query, k=2)
    return (
        "\n".join([doc.page_content for doc in docs])
        if docs
        else "관련 정보를 찾지 못했습니다."
    )


# --- 리드(이름, 전화번호) MySQL 저장 함수 ---
def save_lead_to_mysql(name, phone):
    # DB 정보는 실제 환경에 맞게 수정!
    conn = pymysql.connect(
        host="localhost",
        user="test",
        password="test",
        db="clinicdb",
        charset="utf8mb4",
        autocommit=True,
    )
    with conn.cursor() as cur:
        cur.execute("INSERT INTO leads (name, phone) VALUES (%s, %s)", (name, phone))
    conn.close()


import os
from dotenv import load_dotenv

load_dotenv()


# --- OpenAI LLM 준비 (API Key 꼭 넣기!) ---
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)


# --- 유저 입력 대화 흐름 분기 함수 ---
def handle_user_input(user_id, user_input):
    session = UserSession.load(user_id)
    session.add_message("user", user_input)

    yes_terms = ["네", "동의", "예", "yes", "수락", "ok", "ㅇㅇ"]
    no_terms = ["아니요", "거부", "싫어요", "노", "n", "거절"]

    # 1. 개인정보 수집동의가 우선
    if not session.consent_given:
        if any(term in user_input.lower() for term in yes_terms):
            session.give_consent()
            session.save()
            return "동의해주셔서 감사합니다. 이름을 입력해 주세요."
        elif any(term in user_input.lower() for term in no_terms):
            session.save()
            return (
                "개인정보 수집에 동의하지 않으셨으므로 예약/접수는 불가합니다.\n"
                "필요하다면 정보 안내는 계속 도와드릴 수 있습니다!"
            )
        else:
            session.save()
            return "상담 예약을 원하시면 개인정보 수집 및 이용에 동의해 주세요. ('네' 또는 '동의' 입력)"

    # 2. 이름 입력
    if "이름" not in session.profile:
        name = user_input.strip()
        if not (2 <= len(name) <= 10):
            session.save()
            return "성함을 2~10자로 입력해 주세요. 예시: 홍길동"
        session.set_profile("이름", name)
        session.save()
        return "연락받으실 전화번호(010-xxxx-xxxx)를 입력해 주세요."

    # 3. 전화번호 입력
    if "전화번호" not in session.profile:
        phone = user_input.replace(" ", "")
        if not re.match(r"^01[016789][-]?\d{3,4}[-]?\d{4}$", phone):
            session.save()
            return "전화번호 형식이 올바르지 않습니다. 예: 010-1234-5678"
        session.set_profile("전화번호", phone)
        save_lead_to_mysql(session.profile["이름"], phone)
        session.save()
        return f"{session.profile.get('이름')}님, 접수가 완료되었습니다! 필요시 상담원이 연락드릴 수 있습니다."

    # 4. 이후 정보 탐색/일반 질의응답 (벡터DB+LLM)
    context = (
        f"너는 치과병원 상담 챗봇이야. 사용자의 대화: {session.history}\n"
        f"저장 프로필: {session.profile}\n"
        f"병원 정보: {search_info(user_input)}"
    )
    response = llm.invoke(
        [
            {"role": "system", "content": context},
            {"role": "user", "content": user_input},
        ]
    ).content
    session.add_message("assistant", response)
    session.save()
    return response


# --- FastAPI 설정, 엔드포인트 ---
app = FastAPI()


class ChatMessage(BaseModel):
    user_id: str
    message: str


@app.post("/chat")
async def chat_api(item: ChatMessage):
    answer = handle_user_input(item.user_id, item.message)
    return {"response": answer}


# --- (로컬실행: uvicorn main:app --reload --port 8080) ---
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8088, reload=True)
