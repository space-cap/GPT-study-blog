import os
from dotenv import load_dotenv
from typing import TypedDict
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.pregel import NodeBuilder

# 환경 변수 로드
load_dotenv()


class ChatState(TypedDict):
    question: str
    answer: str


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, verbose=True)
memory = MemorySaver()


# 노드 함수 정의
def generate_answer(state: ChatState) -> dict:
    """LLM을 호출하여 답변을 생성하는 노드 함수"""
    print("\n>>>>> LLM 노드 실행! (이 메시지는 캐시되지 않았을 때만 보입니다) <<<<<")
    question = state["question"]
    response = llm.invoke(question)
    return {"answer": response.content}


# 캐시 키 생성 함수
def get_cache_key(state: ChatState, config: dict) -> str:
    """캐시 키를 생성하는 함수 - 질문을 기반으로 캐시 키 생성"""
    return f"question:{state['question']}"


# NodeBuilder를 사용한 캐싱 노드 생성
cached_node_builder = NodeBuilder(generate_answer).cache(get_cache_key)

# StateGraph 빌더 생성
builder = StateGraph(ChatState)

# 캐시가 적용된 노드 추가
builder.add_node("generate_answer_node", cached_node_builder.build())
builder.add_edge(START, "generate_answer_node")
builder.add_edge("generate_answer_node", END)

# 그래프 컴파일 (checkpointer는 상태 유지용)
graph = builder.compile(checkpointer=memory)

# 테스트 실행
if __name__ == "__main__":
    config = {"configurable": {"thread_id": "chat_session_1"}}

    print("=== 첫 번째 실행 (캐시 없음) ===")
    result1 = graph.invoke({"question": "파이썬이 무엇인가요?"}, config=config)
    print(f"답변: {result1['answer'][:50]}...")

    print("\n=== 두 번째 실행 (동일한 질문, 캐시 적용) ===")
    result2 = graph.invoke({"question": "파이썬이 무엇인가요?"}, config=config)
    print(f"답변: {result2['answer'][:50]}...")

    print("\n=== 세 번째 실행 (다른 질문, 캐시 없음) ===")
    result3 = graph.invoke({"question": "자바스크립트는 무엇인가요?"}, config=config)
    print(f"답변: {result3['answer'][:50]}...")
