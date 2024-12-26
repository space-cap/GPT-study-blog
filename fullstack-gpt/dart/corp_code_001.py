'''
삼성전자 주식의 고유번호를 알아내는 방법

'''


import dart_fss

# API 키 설정
api_key = "YOUR_API_KEY"
dart_fss.set_api_key(api_key)

# 기업 목록 가져오기
corp_list = dart_fss.get_corp_list()

# 삼성전자 검색
samsung = corp_list.find_by_name('삼성전자', exactly=True)[0]

# 고유번호 출력
print(f"삼성전자의 고유번호: {samsung.corp_code}")
