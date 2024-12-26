'''
삼성전자 주식의 고유번호를 알아내는 방법

'''


import dart_fss
import os
from dotenv import load_dotenv


# .env 파일 로드
load_dotenv()

# API 키 가져오기
dart_api_key = os.getenv('DART_API_KEY')

# API 키 설정
dart_fss.set_api_key(dart_api_key)

# 기업 목록 가져오기
corp_list = dart_fss.get_corp_list()

# 삼성전자 검색
samsung = corp_list.find_by_name('삼성전자', exactly=True)[0]

# 고유번호 출력
print(f"삼성전자의 고유번호: {samsung.corp_code}")


