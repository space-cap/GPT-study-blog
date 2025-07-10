import os
from dotenv import load_dotenv
from typing import TypedDict
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import CachePolicy
from langgraph.cache.memory import InMemoryCache

load_dotenv()


class ChatState(TypedDict):
    question: str
    answer: str


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, verbose=True)
memory = MemorySaver()


def generate_answer(state: ChatState) -> dict:
    """LLM을 호출하여 답변을 생성하는 노드 함수"""
    print("\n>>>>> LLM 노드 실행! (이 메시지는 캐시되지 않았을 때만 보입니다) <<<<<")
    question = state["question"]
    response = llm.invoke(question)
    return {"answer": response.content}


# StateGraph 빌더 생성
builder = StateGraph(ChatState)

# CachePolicy를 사용한 노드 추가
builder.add_node(
    "generate_answer_node",
    generate_answer,
    cache_policy=CachePolicy(ttl=120),  # 120초 TTL
)

# 엣지 추가: 그래프 흐름 정의
builder.add_edge(START, "generate_answer_node")  # 시작 -> 답변 생성 노드
builder.add_edge("generate_answer_node", END)  # 답변 생성 노드 -> 종료

# InMemoryCache를 사용하여 컴파일
graph = builder.compile(checkpointer=memory, cache=InMemoryCache())

# 테스트 실행
if __name__ == "__main__":
    config = {"configurable": {"thread_id": "chat_session_1"}}

    print("=== 첫 번째 실행 (캐시 없음) ===")
    result1 = graph.invoke({"question": "파이썬이 무엇인가요?"}, config=config)
    print(f"답변: {result1['answer'][:50]}...")

    print("\n=== 두 번째 실행 (동일한 질문, 캐시 적용) ===")
    result2 = graph.invoke({"question": "파이썬이 무엇인가요?"}, config=config)
    print(f"답변: {result2['answer'][:50]}...")
