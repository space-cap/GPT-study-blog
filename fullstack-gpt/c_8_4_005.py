from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain_community.vectorstores import Chroma
from langchain.schema import HumanMessage, SystemMessage
from langchain.text_splitter import CharacterTextSplitter

# 텍스트 데이터 준비
text = """
LangChain은 대규모 언어 모델(LLMs)을 사용하여 애플리케이션을 만드는 개발자를 위한 프레임워크입니다.
이 프레임워크는 다양한 구성 요소를 제공하여 LLM 기반 애플리케이션의 개발을 간소화합니다.
LangChain을 사용하면 문서 분석, 요약, 챗봇 등 다양한 AI 애플리케이션을 쉽게 만들 수 있습니다.
"""

# 텍스트 분할
text_splitter = CharacterTextSplitter(chunk_size=100, chunk_overlap=0)
docs = text_splitter.create_documents([text])

# OllamaEmbeddings 초기화 및 벡터 저장소 생성
embeddings = OllamaEmbeddings(model="mistral:latest")
vectorstore = Chroma.from_documents(docs, embeddings)

# ChatOllama 초기화
chat_model = ChatOllama(model="mistral:latest")

# 사용자 질문
query = "LangChain의 주요 기능은 무엇인가요?"

# 관련 문서 검색
relevant_docs = vectorstore.similarity_search(query)

# 컨텍스트와 함께 ChatOllama에 질문
messages = [
    SystemMessage(content="다음 정보를 바탕으로 질문에 답하세요:"),
    HumanMessage(content=f"컨텍스트: {relevant_docs[0].page_content}\n\n질문: {query}")
]

response = chat_model(messages)

print("AI 응답:", response.content)
