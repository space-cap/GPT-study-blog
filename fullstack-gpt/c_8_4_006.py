from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import RetrievalQA
from langchain.text_splitter import CharacterTextSplitter

# 문서 준비
documents = [
    "인공지능(AI)은 인간의 학습능력, 추론능력, 지각능력을 인공적으로 구현한 컴퓨터 프로그램 또는 이를 포함한 컴퓨터 시스템을 말합니다.",
    "머신러닝은 AI의 한 분야로, 데이터로부터 학습하여 성능을 향상시키는 알고리즘과 통계적 모델을 연구하는 분야입니다.",
    "딥러닝은 머신러닝의 한 종류로, 인공 신경망을 기반으로 하는 학습 알고리즘입니다."
]

# 텍스트 분할
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
texts = text_splitter.split_documents(documents)

# Ollama 임베딩 초기화
embeddings = OllamaEmbeddings(model="mistral:latest")

# FAISS 벡터 저장소 생성
vectorstore = FAISS.from_texts(texts, embeddings)

# ChatOllama 모델 초기화
chat_model = ChatOllama(model="mistral:latest")

# 프롬프트 템플릿 정의
prompt_template = ChatPromptTemplate.from_template(
    "다음 질문에 대해 주어진 컨텍스트를 바탕으로 답변해주세요: {question}\n\n컨텍스트: {context}"
)

# RetrievalQA 체인 생성
qa_chain = RetrievalQA.from_chain_type(
    chat_model,
    retriever=vectorstore.as_retriever(),
    chain_type_kwargs={"prompt": prompt_template}
)

# 질문 및 답변
question = "인공지능과 머신러닝의 차이점은 무엇인가요?"
result = qa_chain.invoke({"query": question})

print(f"질문: {question}")
print(f"답변: {result['result']}")
