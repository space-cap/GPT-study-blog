# core.py
from langchain_openai import ChatOpenAI

SYSTEM_PROMPT = """
너는 치과병원 챗봇이다. 반드시 개인정보는 동의 후 수집할 것. 의료상 판단은 피하고 상담 연결을 제안하라.
"""


def build_context(session, search_info=None):
    context = f"""
{SYSTEM_PROMPT}
[대화기록]:
{[item for item in session.history]}

[사용자 정보]:
{session.profile}

[검색 정보]:
{search_info or "N/A"}
"""
    return context


def get_llm_response(session, user_input, chroma_vectordb):
    # RAG용 정보 검색
    search_contexts = search_info(user_input, chroma_vectordb)
    combined_context = build_context(session, search_contexts)
    llm = ChatOpenAI(model="gpt-4", temperature=0.3)

    messages = [
        {"role": "system", "content": combined_context},
        {"role": "user", "content": user_input},
    ]
    return llm.invoke(messages).content
