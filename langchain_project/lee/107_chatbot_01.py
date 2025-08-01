import os
from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from typing import Annotated, List
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage

# --- 1. 환경 설정 및 초기화 ---
# OpenAI API 키를 설정합니다. 실제 환경에서는 환경 변수를 사용하는 것이 안전합니다.
# os.environ["OPENAI_API_KEY"] = "YOUR_OPENAI_API_KEY"

# --- 2. 샘플 데이터 준비 ---
# 실제로는 MySQL 데이터베이스에서 청년 정책 데이터를 로드해야 합니다.
# 여기서는 간단한 예시를 위해 Document 객체 리스트를 직접 생성합니다.
policy_documents = [
    Document(
        page_content="청년 주거 안정 지원 정책은 청년들의 월세 부담을 줄여주기 위해 월 20만원씩, 최대 12개월간 월세를 지원하는 제도입니다.",
        metadata={"policy_id": "housing_001", "category": "주거"},
    ),
    Document(
        page_content="청년 취업 도약 장려금은 미취업 청년의 취업 초기 비용 부담을 완화하고, 장기 근속을 유도하기 위해 2년간 최대 1,200만원을 지원합니다.",
        metadata={"policy_id": "employment_001", "category": "취업"},
    ),
    Document(
        page_content="청년 마음 건강 지원 사업은 심리적 어려움을 겪는 청년들에게 전문 심리 상담 서비스를 제공하여 정신 건강 증진을 돕습니다. 1:1 초기 상담 후 맞춤형 프로그램을 연계합니다.",
        metadata={"policy_id": "health_001", "category": "건강"},
    ),
    Document(
        page_content="경기도 청년 교통비 지원 사업은 대중교통 이용 빈도가 높은 청년들의 경제적 부담을 덜어주기 위해 연간 최대 24만원의 교통비를 지원합니다.",
        metadata={"policy_id": "transport_001", "category": "교통"},
    ),
]

# --- 3. 임베딩 모델 및 벡터 저장소 설정 ---
# HuggingFace의 한국어 임베딩 모델을 사용하여 텍스트를 벡터로 변환합니다.
# 'distiluse-base-multilingual-cased-v1'은 다국어 지원 모델로 한국어 처리에도 준수한 성능을 보입니다.
embedding_model = HuggingFaceEmbeddings(
    model_name="distiluse-base-multilingual-cased-v1"
)

# Chroma 벡터 저장소를 초기화하고, 준비된 정책 문서를 임베딩하여 저장합니다.
# 실제 애플리케이션에서는 영구 저장을 위해 경로를 지정할 수 있습니다.
vectorstore = Chroma.from_documents(
    documents=policy_documents, embedding=embedding_model
)

# 검색기(Retriever)를 생성합니다. 상위 2개의 관련 문서를 가져오도록 설정합니다.
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})


# --- 4. LangGraph 상태 정의 ---
# 그래프의 각 노드를 거치면서 데이터가 저장되고 전달될 상태(State)를 정의합니다.
class ChatbotState(TypedDict):
    # add_messages는 대화 기록을 편리하게 관리해주는 유틸리티입니다.
    messages: Annotated[list, add_messages]

    # 사용자의 원본 질문
    original_question: str

    # LLM이 오타와 맞춤법을 수정한 질문
    corrected_question: str

    # 벡터 저장소에서 검색된 관련 정책 문서
    documents: List[Document]


# --- 5. LangGraph 노드(Node) 함수 정의 ---
# 각 노드는 그래프의 특정 작업을 수행하는 함수입니다.


def correct_query_node(state: ChatbotState) -> dict:
    """사용자의 질문에서 오타나 문법 오류를 수정하는 노드"""
    print("--- 1. 질문 수정 노드 실행 ---")
    user_message = state["messages"][-1].content

    # LLM을 사용하여 질문을 수정하도록 요청
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    correction_prompt = f"""다음 질문의 오타나 문법 오류를 수정해주세요. 다른 설명 없이 수정된 질문만 반환해주세요.
    질문: "{user_message}"
    """
    corrected_question = llm.invoke(correction_prompt).content.strip()

    print(f"원본 질문: {user_message}")
    print(f"수정된 질문: {corrected_question}")

    return {
        "original_question": user_message,
        "corrected_question": corrected_question,
    }


def retrieve_documents_node(state: ChatbotState) -> dict:
    """수정된 질문을 바탕으로 관련 정책 문서를 검색하는 노드"""
    print("--- 2. 문서 검색 노드 실행 ---")
    corrected_question = state["corrected_question"]
    documents = retriever.invoke(corrected_question)
    print(f"검색된 문서 수: {len(documents)}개")
    return {"documents": documents}


def generate_answer_node(state: ChatbotState) -> dict:
    """검색된 문서를 바탕으로 사용자에게 답변을 생성하는 노드"""
    print("--- 3. 답변 생성 노드 실행 ---")
    corrected_question = state["corrected_question"]
    documents = state["documents"]

    # 검색된 문서 내용을 컨텍스트로 합침
    context = "\n\n".join([doc.page_content for doc in documents])

    # RAG(검색 증강 생성) 프롬프트
    rag_prompt = f"""당신은 '청년정책 안내 챗봇'입니다. 주어진 정책 정보를 바탕으로 사용자의 질문에 친절하고 명확하게 답변해주세요.
    
    [정책 정보]
    {context}
    
    [사용자 질문]
    {corrected_question}
    
    답변:
    """

    llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
    answer = llm.invoke(rag_prompt).content
    print(f"생성된 답변: {answer}")

    return {"messages": [AIMessage(content=answer)]}


def fallback_node(state: ChatbotState) -> dict:
    """관련 문서를 찾지 못했을 때 사용자에게 안내 메시지를 반환하는 노드"""
    print("--- 3a. 대체 답변 노드 실행 ---")
    answer = "죄송합니다, 문의하신 내용과 관련된 청년 정책을 찾을 수 없었습니다. 다른 질문이 있으시면 말씀해주세요."
    return {"messages": [AIMessage(content=answer)]}


# --- 6. 조건부 엣지(Conditional Edge) 로직 정의 ---
# 문서 검색 결과에 따라 다음 노드를 결정하는 함수입니다.
def decide_generation_path(state: ChatbotState) -> str:
    """문서 검색 결과 유무에 따라 '답변 생성' 또는 '대체 답변' 노드로 분기"""
    if state["documents"]:
        # 검색된 문서가 있으면 답변 생성 노드로 이동
        return "generate_answer"
    else:
        # 검색된 문서가 없으면 대체 답변 노드로 이동
        return "fallback"


# --- 7. 그래프 구성 및 컴파일 ---
workflow = StateGraph(ChatbotState)

# 노드 추가
workflow.add_node("correct_query", correct_query_node)
workflow.add_node("retrieve_documents", retrieve_documents_node)
workflow.add_node("generate_answer", generate_answer_node)
workflow.add_node("fallback", fallback_node)

# 엣지(연결) 설정
workflow.set_entry_point("correct_query")
workflow.add_edge("correct_query", "retrieve_documents")

# 조건부 엣지 설정
workflow.add_conditional_edges(
    "retrieve_documents",
    decide_generation_path,
    {
        "generate_answer": "generate_answer",
        "fallback": "fallback",
    },
)

workflow.add_edge("generate_answer", END)
workflow.add_edge("fallback", END)

# 그래프 컴파일
app = workflow.compile()


# --- 8. 챗봇 실행 ---
def run_chatbot(question: str):
    """챗봇을 실행하고 최종 답변을 출력하는 함수"""
    print(f"\n===== 새로운 질문: {question} =====")

    # 그래프 실행
    # HumanMessage를 리스트에 담아 초기 상태를 설정합니다.
    final_state = app.invoke({"messages": [HumanMessage(content=question)]})

    # 최종 답변(AIMessage) 출력
    print("\n[최종 답변]")
    print(final_state["messages"][-1].content)
    print("=" * 30)


# 예시 1: 오타가 있는 질문 (정상적으로 답변 생성)
run_chatbot("청년 주거 안정을 위한 정채기 있나요?")

# 예시 2: 관련 없는 질문 (대체 답변으로 연결)
run_chatbot("오늘 날씨 어때?")

# 예시 3: 다른 정책 질문
run_chatbot("취업하는데 도움이 될만한거 있어?")
