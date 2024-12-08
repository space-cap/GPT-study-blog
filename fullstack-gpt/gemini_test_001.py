from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

# 환경 변수 가져오기
openai_api_key = os.getenv("Gemini_API_KEY")

# 확인
print(f"OpenAI API Key: {openai_api_key}")

import google.generativeai as genai

genai.configure(api_key="YOUR_API_KEY")
model = genai.GenerativeModel("gemini-1.5-flash")
response = model.generate_content("Explain how AI works")
print(response.text)