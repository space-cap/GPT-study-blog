import os
import uuid
from typing import Optional

import mysql.connector
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

# .env 파일에서 환경 변수 로드 (API 키, DB 정보 등)
load_dotenv()


# --- 1. 정보 '추출기'가 사용할 데이터 구조 ---
# 사용자의 답변에서 이름이나 전화번호를 추출하기 위한 Pydantic 모델입니다.
# 모든 필드를 Optional로 설정하여, 부분적인 정보만 있어도 추출할 수 있도록 합니다.
class PartialCustomerInfo(BaseModel):
    """고객의 이름 또는 전화번호 정보를 담는 데이터 구조입니다."""

    name: Optional[str] = Field(None, description="대화에서 추출한 고객의 이름")
    phone_number: Optional[str] = Field(
        None, description="대화에서 추출한 고객의 전화번호"
    )


def save_chat_log(session_id, user_message, bot_response):
    """
    대화 내용을 데이터베이스의 chatbot_log 테이블에 저장합니다.
    """
    try:
        # .env 파일에 설정된 정보로 데이터베이스에 연결합니다.
        db_connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
        )
        cursor = db_connection.cursor()

        # SQL INSERT 쿼리를 정의합니다.
        insert_query = """
        INSERT INTO chatbot_log (session_id, user_message, bot_response) 
        VALUES (%s, %s, %s)
        """
        log_data = (session_id, user_message, bot_response)

        # 쿼리를 실행하고 변경사항을 커밋합니다.
        cursor.execute(insert_query, log_data)
        db_connection.commit()

    except mysql.connector.Error as err:
        # 데이터베이스 오류 발생 시 메시지를 출력합니다.
        print(f"\n[DB 저장 오류] {err}")
    finally:
        # 연결을 안전하게 닫습니다.
        if "db_connection" in locals() and db_connection.is_connected():
            cursor.close()
            db_connection.close()


def run_chatbot():
    """
    대화의 상태를 관리하며 고객 정보를 수집하고, 대화 내용을 DB에 저장하는 챗봇을 실행합니다.
    """
    print(
        "🤖 안녕하세요! 스마일 치과 챗봇입니다. 무엇을 도와드릴까요? (종료하시려면 'exit'을 입력하세요)"
    )

    # --- 2. 챗봇 모델 및 설정 초기화 ---
    # 일반 대화용 LLM과 정보 추출용 LLM을 각각 설정합니다.
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    extraction_llm = llm.with_structured_output(PartialCustomerInfo)

    # 각 대화 세션을 구분하기 위한 고유 ID를 생성합니다.
    session_id = str(uuid.uuid4())

    # --- 3. '상태 관리자'가 사용할 저장 공간 ---
    # 수집된 고객 정보를 대화가 진행되는 동안 기억하는 딕셔너리입니다.
    collected_info = {
        "name": None,
        "phone_number": None,
        "reason": None,
    }

    # LLM이 대화의 맥락을 파악할 수 있도록 대화 기록을 저장하는 리스트입니다.
    chat_history = []

    # --- 메인 대화 루프 ---
    while True:
        # 목표(이름, 전화번호 수집)를 달성했는지 매번 확인합니다.
        if collected_info["name"] and collected_info["phone_number"]:
            print("\n✅ [상담 정보 수집 완료]")
            print(f"  - 고객명: {collected_info['name']}")
            print(f"  - 연락처: {collected_info['phone_number']}")
            print(f"  - 문의 사유: {collected_info['reason'] or 'N/A'}")

            final_message = "감사합니다! 전문 상담원이 곧 연락드리겠습니다."
            print(f"\n🤖 {final_message}")
            # 마지막 대화 내용을 데이터베이스에 저장하고 종료합니다.
            save_chat_log(session_id, "고객 정보 제공 완료", final_message)
            break

        # 사용자 입력을 받습니다.
        user_input = input("🙂: ")
        if user_input.lower() == "exit":
            print("🤖 상담을 종료합니다. 이용해주셔서 감사합니다.")
            save_chat_log(
                session_id, user_input, "상담을 종료합니다. 이용해주셔서 감사합니다."
            )
            break

        # 사용자의 첫 질문을 '문의 사유'로 저장합니다.
        if not collected_info["reason"]:
            collected_info["reason"] = user_input

        chat_history.append(HumanMessage(content=user_input))

        # --- 4. '정보 추출기' 실행 ---
        # 사용자의 마지막 답변에서 이름이나 연락처 정보가 있는지 추출을 시도합니다.
        try:
            extracted_data = extraction_llm.invoke([HumanMessage(content=user_input)])
            if extracted_data.name and not collected_info["name"]:
                collected_info["name"] = extracted_data.name
                print(f"🤖 [이름: {extracted_data.name} 확인되었습니다.]")
            if extracted_data.phone_number and not collected_info["phone_number"]:
                collected_info["phone_number"] = extracted_data.phone_number
                print(f"🤖 [연락처: {extracted_data.phone_number} 확인되었습니다.]")
        except Exception:
            # 추출할 정보가 없으면 조용히 넘어갑니다.
            pass

        # 정보 추출 후 목표를 달성했는지 다시 확인합니다.
        if collected_info["name"] and collected_info["phone_number"]:
            continue

        # --- 5. '응답 생성기' 실행 ---
        # 현재까지 수집된 정보(상태)를 시스템 프롬프트에 담아, 다음에 무엇을 물어볼지 LLM이 결정하게 합니다.
        system_prompt_for_response = f"""
        당신은 '스마일 치과'의 친절한 상담 챗봇입니다.
        당신의 목표는 고객의 이름과 전화번호를 수집하는 것입니다.

        [현재까지 수집된 정보]
        - 이름: {collected_info['name'] or '아직 모름'}
        - 전화번호: {collected_info['phone_number'] or '아직 모름'}

        [당신의 임무]
        - 위 정보를 바탕으로, 아직 수집되지 않은 정보를 고객에게 정중하게 물어보세요.
        - 만약 이름이 없다면, 이름을 물어보세요.
        - 만약 전화번호가 없다면, 전화번호를 물어보세요.
        - 고객이 다른 질문을 하면, "네, 그 부분은 전문 상담원이 자세히 안내해 드릴 거예요. 우선 연락처를 남겨주시겠어요?" 와 같이 부드럽게 응대하며 원래 목표로 돌아오세요.
        - 절대로 의학적 조언을 하지 마세요.
        """

        messages_for_response = [SystemMessage(content=system_prompt_for_response)]
        # 대화의 흐름을 파악할 수 있도록 최근 대화 내용을 함께 전달합니다.
        messages_for_response.extend(chat_history[-4:])

        ai_response = llm.invoke(messages_for_response)
        chat_history.append(ai_response)
        print(f"🤖: {ai_response.content}")

        # 매 대화 턴마다 로그를 데이터베이스에 저장합니다.
        save_chat_log(session_id, user_input, ai_response.content)


if __name__ == "__main__":
    run_chatbot()
