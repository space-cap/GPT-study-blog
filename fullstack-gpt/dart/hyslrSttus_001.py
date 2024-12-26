'''
회사 정보를 가지고 와서
사업 보고서 가지고 오기

안 된다.
'''


import dart_fss as dart
import os
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv

# .env 파일에서 API 키 로드
load_dotenv()
api_key = os.getenv('DART_API_KEY')

# API 키 설정
dart.set_api_key(api_key)

def initialize_db():
    conn = sqlite3.connect('corp_list.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS corp_list (
            corp_code TEXT PRIMARY KEY,
            corp_name TEXT,
            stock_code TEXT,
            modify_date TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    conn.commit()
    conn.close()

def update_corp_list():
    conn = sqlite3.connect('corp_list.db')
    cursor = conn.cursor()

    cursor.execute("SELECT value FROM metadata WHERE key='last_update'")
    result = cursor.fetchone()
    last_update = datetime.strptime(result[0], '%Y-%m-%d') if result else None

    if not last_update or datetime.now() - last_update > timedelta(days=7):
        print("기업 목록을 업데이트합니다.")
        corp_list = dart.get_corp_list()

        cursor.execute("DELETE FROM corp_list")

        for corp in corp_list:
            cursor.execute(
                "INSERT INTO corp_list (corp_code, corp_name, stock_code, modify_date) VALUES (?, ?, ?, ?)",
                (corp.corp_code, corp.corp_name, corp.stock_code, corp.modify_date)
            )

        cursor.execute("REPLACE INTO metadata (key, value) VALUES ('last_update', ?)", (datetime.now().strftime('%Y-%m-%d'),))
        conn.commit()
    else:
        print("기존 기업 목록을 사용합니다.")

    conn.close()

def get_corp_info(corp_name):
    conn = sqlite3.connect('corp_list.db')
    cursor = conn.cursor()

    cursor.execute("SELECT corp_code, stock_code FROM corp_list WHERE corp_name = ?", (corp_name,))
    result = cursor.fetchone()

    conn.close()

    if result:
        return {'corp_code': result[0], 'stock_code': result[1]}
    else:
        print(f"기업 '{corp_name}'을(를) 찾을 수 없습니다.")
        return None

# 데이터베이스 초기화 및 업데이트
initialize_db()
update_corp_list()

# 삼성전자 정보 가져오기
company_info = get_corp_info('한중엔시에스')

if company_info:
    print(company_info['corp_code'])
    # dart-fss 객체 생성
    reports = dart.api.info.hyslr_sttus(company_info['corp_code'], '2023', '11011')

    # 최대주주 정보 출력
    if reports:
        print("최대주주 정보:")
        print(reports)
    else:
        print("최대주주 정보를 찾을 수 없습니다.")
else:
    print("기업 정보를 찾을 수 없습니다.")



