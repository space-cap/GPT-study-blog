import dart_fss as dart
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os


# .env 파일에서 API 키 로드
load_dotenv()
api_key = os.getenv('DART_API_KEY')




# API 키 설정
dart.set_api_key(api_key)

def get_insider_trading(corp_code, start_date=None, end_date=None):
    # 날짜가 지정되지 않은 경우 기본값 설정 (최근 1년)
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y%m%d')

    try:
        # 내부자거래 정보 조회
        insider_trades = dart.api.info.insider_trading(
            corp_code=corp_code,
            start_date=start_date,
            end_date=end_date
        )
        return insider_trades
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        return None

# 사용 예시
corp_code = '00126380'  # 삼성전자의 고유번호
insider_trades = get_insider_trading(corp_code)

if insider_trades:
    for trade in insider_trades['list']:
        print(f"보고자: {trade['repror']}")
        print(f"보고자 관계: {trade['relation']}")
        print(f"보고일자: {trade['report_date']}")
        print(f"거래일자: {trade['trading_date']}")
        print(f"거래주식수: {trade['trading_quantity']}")
        print(f"거래단가: {trade['trading_price']}")
        print(f"거래후 보유주식수: {trade['after_quantity']}")
        print("---")
else:
    print("내부자거래 정보를 가져오는데 실패했습니다.")
