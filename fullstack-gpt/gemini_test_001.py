from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

# 환경 변수 가져오기
gemini_api_key = os.getenv("Gemini_API_KEY")

# 확인
# print(f"API Key: {gemini_api_key}")

import google.generativeai as genai

genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel("gemini-1.5-flash")
response = model.generate_content("대한민국의 수도는?")
print(response.text)
