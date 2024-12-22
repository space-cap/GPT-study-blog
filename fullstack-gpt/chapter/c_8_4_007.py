import os
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import RetrievalQA
from langchain_text_splitters import CharacterTextSplitter

# 파일에서 문서 읽기
file_path = "./files/chapter_one.txt"

try:
    with open(file_path, "r", encoding="utf-8") as file:
        document_content = file.read()
except FileNotFoundError:
    print(f"파일을 찾을 수 없습니다: {file_path}")
    exit(1)
except IOError:
    print(f"파일을 읽는 중 오류가 발생했습니다: {file_path}")
    exit(1)

# 텍스트 분할
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
texts = text_splitter.create_documents([document_content])

# Ollama 임베딩 초기화
embeddings = OllamaEmbeddings(model="mistral:latest")

# FAISS 벡터 저장소 생성
vectorstore = FAISS.from_documents(texts, embeddings)

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
question = "이 문서의 주요 내용은 무엇인가요?"
result = qa_chain.invoke({"query": question})

print(f"질문: {question}")
print(f"답변: {result['result']}")
