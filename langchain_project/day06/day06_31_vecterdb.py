from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import TextLoader

# OpenAI API 키 설정 (환경변수 또는 직접 입력)
import os
from dotenv import load_dotenv

load_dotenv()

# os.environ["OPENAI_API_KEY"] = ""
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 1. 임베딩 모델 초기화
# OpenAI의 text-embedding-ada-002 모델 사용
embeddings = OpenAIEmbeddings()

# 2. 샘플 텍스트 데이터 준비
sample_texts = [
    "LangChain은 대규모 언어 모델을 활용한 애플리케이션 개발 프레임워크입니다.",
    "벡터 데이터베이스는 텍스트를 수치형 벡터로 변환하여 저장합니다.",
    "RAG는 검색 증강 생성으로, 외부 지식을 활용해 답변을 생성합니다.",
    "임베딩은 텍스트의 의미를 고차원 벡터 공간에 표현하는 기술입니다.",
]

# 3. 벡터 스토어 생성 및 문서 추가
vectorstore = Chroma.from_texts(
    texts=sample_texts,  # 저장할 텍스트 리스트
    embedding=embeddings,  # 사용할 임베딩 모델
    persist_directory="./chroma_db",  # 데이터베이스 저장 경로
)

print("벡터 스토어가 성공적으로 생성되었습니다!")
