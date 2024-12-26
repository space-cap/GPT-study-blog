'''
지분공시 종합정보
대량보유 상황보고 개발가이드
'''


import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# API 키 가져오기
api_key = os.getenv('API_KEY')

# API 키 사용 예시
print(f"API Key: {api_key}")


