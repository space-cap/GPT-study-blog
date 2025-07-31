# saju_chatbot/config.py

import os
from dotenv import load_dotenv

load_dotenv()  # .env 파일에서 환경 변수 로드

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# MySQL Database 설정
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")
MYSQL_DB = os.getenv("MYSQL_DB", "saju_chatbot_db")

# ChromaDB 설정 (로컬 파일 시스템 사용)
CHROMA_PERSIST_DIRECTORY = "./chroma_db"

# Embedding Model 설정 (HuggingFace)
EMBEDDING_MODEL_NAME = "jhgan/ko-sroberta-multitask"  # 한국어 임베딩 모델로 변경 고려
EMBEDDING_MODEL_DEVICE = "cpu"
