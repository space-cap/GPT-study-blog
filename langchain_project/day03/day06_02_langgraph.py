import os
from dotenv import load_dotenv
from typing import TypedDict
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# 환경 변수 로드 (OPENAI_API_KEY 등)
load_dotenv()


# 상태 정의: 질문과 답변을 저장하는 TypedDict
class ChatState(TypedDict):
    question: str
    answer: str


# OpenAI LLM 초기화
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, verbose=True)

# 인메모리 캐시를 위한 MemorySaver 초기화
# 이를 통해 동일한 thread_id에서 상태가 유지됩니다
memory = MemorySaver()


# 노드 함수 정의
def generate_answer(state: ChatState) -> dict:
    """
    LLM을 호출하여 답변을 생성하는 노드 함수
    캐시가 적용되어 있어 동일한 질문에 대해서는 재실행되지 않습니다
    """
    print("\n>>>>> LLM 노드 실행! (이 메시지는 캐시되지 않았을 때만 보입니다) <<<<<")
    question = state["question"]

    # LLM 호출
    response = llm.invoke(question)

    # 상태 업데이트를 위한 딕셔너리 반환
    return {"answer": response.content}


# StateGraph 빌더 생성
builder = StateGraph(ChatState)

# 노드 추가: generate_answer 함수를 "generate_answer_node"라는 이름으로 등록
builder.add_node("generate_answer_node", generate_answer)

# 엣지 추가: 그래프 흐름 정의
builder.add_edge(START, "generate_answer_node")  # 시작 -> 답변 생성 노드
builder.add_edge("generate_answer_node", END)  # 답변 생성 노드 -> 종료

# 그래프 컴파일: checkpointer(MemorySaver)를 연결하여 캐싱 기능 활성화
graph = builder.compile(checkpointer=memory)

# 테스트 실행 코드
if __name__ == "__main__":
    # 스레드 ID를 포함한 설정
    # 동일한 thread_id에서는 상태가 유지되고 캐싱이 적용됩니다
    config = {"configurable": {"thread_id": "chat_session_1"}}

    print("=== 첫 번째 실행 (캐시 없음) ===")
    result1 = graph.invoke({"question": "파이썬이 무엇인가요?"}, config=config)
    print(f"답변: {result1['answer']}")

    print("\n=== 두 번째 실행 (동일한 질문, 캐시 적용) ===")
    result2 = graph.invoke({"question": "파이썬이 무엇인가요?"}, config=config)
    print(f"답변: {result2['answer']}")

    print("\n=== 세 번째 실행 (다른 질문, 캐시 없음) ===")
    result3 = graph.invoke({"question": "자바스크립트는 무엇인가요?"}, config=config)
    print(f"답변: {result3['answer']}")

    print("\n=== 네 번째 실행 (첫 번째 질문 반복, 캐시 적용) ===")
    result4 = graph.invoke({"question": "파이썬이 무엇인가요?"}, config=config)
    print(f"답변: {result4['answer']}")
