import dart_fss as dart
import os
import pickle
from datetime import datetime, timedelta
from dotenv import load_dotenv

# .env 파일에서 API 키 로드
load_dotenv()
api_key = os.getenv('DART_API_KEY')

# API 키 설정
dart.set_api_key(api_key)

def load_or_update_corp_list():
    file_name = 'corp_list.pkl'
    update_interval = timedelta(days=7)  # 7일마다 업데이트

    if os.path.exists(file_name):
        with open(file_name, 'rb') as f:
            saved_data = pickle.load(f)
        last_update = saved_data['last_update']
        corp_list = saved_data['corp_list']

        if datetime.now() - last_update < update_interval:
            print("기존 기업 목록을 사용합니다.")
            return corp_list

    print("기업 목록을 업데이트합니다.")
    corp_list = dart.get_corp_list()
    with open(file_name, 'wb') as f:
        pickle.dump({
            'last_update': datetime.now(),
            'corp_list': corp_list
        }, f)
    
    return corp_list

# 기업 목록 로드 또는 업데이트
corp_list = load_or_update_corp_list()

# 삼성전자 검색
samsung = corp_list.find_by_corp_name('삼성전자', exactly=True)[0]

# 검색 결과 출력
print(f"회사명: {samsung.corp_name}")
print(f"종목코드: {samsung.stock_code}")
print(f"고유번호: {samsung.corp_code}")
