import dart_fss as dart
import os
from dotenv import load_dotenv

# .env 파일에서 API 키 로드
load_dotenv()
api_key = os.getenv('DART_API_KEY')

# API 키 설정
dart.set_api_key(api_key)

# 기업 목록 가져오기
corp_list = dart.get_corp_list()

# 삼성전자 검색
samsung = corp_list.find_by_corp_name('삼성전자', exactly=True)[0]

# 검색 결과 출력
print(f"회사명: {samsung.corp_name}")
print(f"종목코드: {samsung.stock_code}")
print(f"고유번호: {samsung.corp_code}")
