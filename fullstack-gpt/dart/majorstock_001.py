'''
지분공시 종합정보
대량보유 상황보고 개발가이드
'''


import requests
import json
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# API 키 가져오기
dart_api_key = os.getenv('DART_API_KEY')


def get_major_stock_holdings(api_key, corp_code):
    url = "https://opendart.fss.or.kr/api/majorstock.json"
    params = {
        "crtfc_key": api_key,
        "corp_code": corp_code
    }

    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if data['status'] == '000':
            return data['list']
        else:
            print(f"Error: {data['message']}")
            return None
    else:
        print(f"HTTP Error: {response.status_code}")
        return None

def print_major_stock_holdings(holdings):
    if holdings:
        for item in holdings:
            print(f"접수번호: {item['rcept_no']}")
            print(f"접수일자: {item['rcept_dt']}")
            print(f"회사명: {item['corp_name']}")
            print(f"보고구분: {item['report_tp']}")
            print(f"대표보고자: {item['repror']}")
            print(f"보유주식등의 수: {item['stkqy']}")
            print(f"보유비율: {item['stkrt']}%")
            print(f"보고사유: {item['report_resn']}")
            print("-" * 50)
    else:
        print("No data available.")

# 메인 실행 부분
if __name__ == "__main__":
    api_key = dart_api_key  # 발급받은 API 키를 입력하세요
    corp_code = "00126380"  # 삼성전자의 고유번호 (예시)

    holdings = get_major_stock_holdings(api_key, corp_code)
    print_major_stock_holdings(holdings)



