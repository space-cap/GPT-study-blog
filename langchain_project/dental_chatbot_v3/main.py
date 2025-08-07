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
    """고객의 이름, 전화번호, 동의 여부 정보를 담는 데이터 구조입니다."""

    name: Optional[str] = Field(None, description="대화에서 추출한 고객의 이름")
    phone_number: Optional[str] = Field(
        None, description="대화에서 추출한 고객의 전화번호"
    )
    consent_agreed: Optional[bool] = Field(
        None, description="고객의 개인정보 수집 동의 여부 (예, 네, 동의합니다 -> True)"
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


def save_inquiry_to_db(inquiry_data):
    """수집된 최종 문의 정보를 chatbot_inquiry 테이블에 저장합니다."""
    try:
        db_connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
        )
        cursor = db_connection.cursor()

        insert_query = """
        INSERT INTO chatbot_inquiry (customer_name, phone_number, inquiry_reason, consent_agreed) 
        VALUES (%s, %s, %s, %s)
        """
        data = (
            inquiry_data["name"],
            inquiry_data["phone_number"],
            inquiry_data["reason"],
            "Y" if inquiry_data["consent_agreed"] else "N",
        )

        cursor.execute(insert_query, data)
        db_connection.commit()
        print("\n[DB 저장 성공] 수집된 정보가 chatbot_inquiry 테이블에 저장되었습니다.")

    except mysql.connector.Error as err:
        print(f"\n[DB 저장 오류] {err}")
    finally:
        if "db_connection" in locals() and db_connection.is_connected():
            cursor.close()
            db_connection.close()


def run_chatbot():
    """상태를 관리하며 고객 정보를 수집하고, 최종 결과를 DB에 저장하는 챗봇을 실행합니다."""
    print(
        "🤖 안녕하세요! 스마일 치과 챗봇입니다. 무엇을 도와드릴까요? (종료하시려면 'exit'을 입력하세요)"
    )

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    extraction_llm = llm.with_structured_output(PartialCustomerInfo)
    session_id = str(uuid.uuid4())

    collected_info = {
        "name": None,
        "phone_number": None,
        "reason": None,
        "consent_agreed": None,  # 동의 여부 상태 추가
    }
    chat_history = []

    while True:
        # --- 최종 목표 달성 여부 확인 ---
        if (
            collected_info["name"]
            and collected_info["phone_number"]
            and collected_info["consent_agreed"]
        ):
            print("\n✅ [상담 정보 수집 완료]")
            print(f"  - 고객명: {collected_info['name']}")
            print(f"  - 연락처: {collected_info['phone_number']}")
            print(f"  - 문의 사유: {collected_info['reason'] or 'N/A'}")

            final_message = "감사합니다! 모든 정보가 확인되었습니다. 전문 상담원이 곧 연락드리겠습니다."
            print(f"\n🤖 {final_message}")

            save_chat_log(session_id, "개인정보 수집 동의 완료", final_message)
            save_inquiry_to_db(collected_info)  # 최종 정보 DB 저장
            break

        user_input = input("🙂: ")
        if user_input.lower() == "exit":
            print("🤖 상담을 종료합니다. 이용해주셔서 감사합니다.")
            save_chat_log(session_id, user_input, "상담 종료")
            break

        if not collected_info["reason"]:
            collected_info["reason"] = user_input

        chat_history.append(HumanMessage(content=user_input))

        # --- 정보 추출기 실행 ---
        try:
            extracted_data = extraction_llm.invoke([HumanMessage(content=user_input)])
            if extracted_data.name and not collected_info["name"]:
                collected_info["name"] = extracted_data.name
                print(f"🤖 [이름: {extracted_data.name} 확인되었습니다.]")
            if extracted_data.phone_number and not collected_info["phone_number"]:
                collected_info["phone_number"] = extracted_data.phone_number
                print(f"🤖 [연락처: {extracted_data.phone_number} 확인되었습니다.]")
            if extracted_data.consent_agreed and not collected_info["consent_agreed"]:
                collected_info["consent_agreed"] = True
                print(f"🤖 [개인정보 수집 및 이용에 동의해주셨습니다.]")
        except Exception:
            pass

        if (
            collected_info["name"]
            and collected_info["phone_number"]
            and collected_info["consent_agreed"]
        ):
            continue

        # --- 응답 생성기 실행 ---
        next_prompt = ""
        if not collected_info["name"]:
            next_prompt = "정확한 상담을 위해 성함을 알려주시겠어요?"
        elif not collected_info["phone_number"]:
            next_prompt = "상담원이 연락드릴 수 있도록 전화번호를 남겨주시겠어요?"
        elif not collected_info["consent_agreed"]:
            next_prompt = "마지막으로, 원활한 상담을 위해 개인정보 수집 및 이용에 동의하시나요? (예/아니오)"

        system_prompt_for_response = f"""
        당신은 '스마일 치과'의 친절한 상담 챗봇입니다. 당신의 목표는 고객 정보를 수집하는 것입니다.
        [현재까지 수집된 정보]
        - 이름: {collected_info['name'] or '아직 모름'}
        - 전화번호: {collected_info['phone_number'] or '아직 모름'}
        - 개인정보 동의: {'동의함' if collected_info['consent_agreed'] else '아직 안 함'}

        [당신의 임무]
        - "{next_prompt}" 이 질문을 중심으로 고객에게 자연스럽고 친절하게 응답하세요.
        - 고객이 다른 질문을 하면, "네, 그 부분은 전문 상담원이 자세히 안내해 드릴 거예요." 라고 부드럽게 응대한 후, 원래 목표 질문으로 돌아오세요.
        """

        messages_for_response = [SystemMessage(content=system_prompt_for_response)]
        messages_for_response.extend(chat_history[-4:])

        ai_response = llm.invoke(messages_for_response)
        chat_history.append(ai_response)
        print(f"🤖: {ai_response.content}")

        save_chat_log(session_id, user_input, ai_response.content)


if __name__ == "__main__":
    run_chatbot()
