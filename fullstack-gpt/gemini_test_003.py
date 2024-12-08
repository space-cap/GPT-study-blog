from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

# 환경 변수 가져오기
gemini_api_key = os.getenv("Gemini_API_KEY")

from langchain_google_vertexai import ChatVertexAI

model = ChatVertexAI(model="gemini-1.5-flash", google_api_key=gemini_api_key)



