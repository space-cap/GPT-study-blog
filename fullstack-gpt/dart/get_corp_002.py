import dart_fss as dart
from dotenv import load_dotenv
import os


# .env 파일에서 API 키 로드
load_dotenv()
api_key = os.getenv('DART_API_KEY')



# API 키 설정
dart.set_api_key(api_key)

# 기업 목록 가져오기
corp_list = dart.get_corp_list()

# 특정 기업의 정보 가져오기
corp = dart.get_corp('00126380')  # 삼성전자의 고유번호
