import os
import uuid
import logging
from typing import Optional

import mysql.connector
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

# .env 파일에서 환경 변수 로드 (API 키, DB 정보 등)
load_dotenv()

# --- 로깅 설정 ---
# INFO 레벨 이상의 로그를 chatbot.log 파일과 콘솔에 함께 기록합니다.
# 더 자세한 디버그 로그를 보려면 level을 logging.DEBUG로 변경하세요.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("chatbot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)


# --- 1. 정보 '추출기'가 사용할 데이터 구조 ---
# 이름과 전화번호만 추출하도록 역할을 명확히 합니다.
class PartialCustomerInfo(BaseModel):
    """고객의 이름 또는 전화번호 정보를 담는 데이터 구조입니다."""

    name: Optional[str] = Field(None, description="대화에서 추출한 고객의 이름")
    phone_number: Optional[str] = Field(
        None, description="대화에서 추출한 고객의 전화번호"
    )


# 동의 여부만 판단하기 위한 별도의 데이터 구조를 만듭니다.
class ConsentInfo(BaseModel):
    """고객의 동의 여부를 판단하는 데이터 구조입니다."""

    agreed: bool = Field(
        description="고객이 긍정적으로 답변했는지 여부 (예, 네, 동의합니다 -> True)"
    )


def save_chat_log(session_id, user_message, bot_response):
    """대화 내용을 데이터베이스의 chatbot_log 테이블에 저장합니다."""
    try:
        db_connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
        )
        cursor = db_connection.cursor()
        insert_query = "INSERT INTO chatbot_log (session_id, user_message, bot_response) VALUES (%s, %s, %s)"
        cursor.execute(insert_query, (session_id, user_message, bot_response))
        db_connection.commit()
    except mysql.connector.Error as err:
        logging.error(f"[DB 저장 오류] chatbot_log 저장 실패: {err}")
    finally:
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
        insert_query = "INSERT INTO chatbot_inquiry (customer_name, phone_number, inquiry_reason, consent_agreed) VALUES (%s, %s, %s, %s)"
        data = (
            inquiry_data["name"],
            inquiry_data["phone_number"],
            inquiry_data["reason"],
            "Y" if inquiry_data["consent_agreed"] else "N",
        )
        cursor.execute(insert_query, data)
        db_connection.commit()
        logging.info(
            "[DB 저장 성공] 수집된 정보가 chatbot_inquiry 테이블에 저장되었습니다."
        )
    except mysql.connector.Error as err:
        logging.error(f"[DB 저장 오류] chatbot_inquiry 저장 실패: {err}")
    finally:
        if "db_connection" in locals() and db_connection.is_connected():
            cursor.close()
            db_connection.close()


def run_chatbot():
    """상태를 관리하며 고객 정보를 수집하고, 최종 결과를 DB에 저장하는 챗봇을 실행합니다."""
    logging.info("=" * 20 + " 새로운 챗봇 세션 시작 " + "=" * 20)
    print(
        "🤖 안녕하세요! 스마일 치과 챗봇입니다. 무엇을 도와드릴까요? (종료하시려면 'exit'을 입력하세요)"
    )

    # --- 2. 챗봇 모델 및 설정 초기화 ---
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    info_extraction_llm = llm.with_structured_output(PartialCustomerInfo)
    consent_extraction_llm = llm.with_structured_output(ConsentInfo)

    # 각 대화 세션을 구분하기 위한 고유 ID를 생성합니다.
    session_id = str(uuid.uuid4())
    logging.info(f"세션 ID 생성: {session_id}")

    # --- 3. '상태 관리자'가 사용할 저장 공간 ---
    # 수집된 고객 정보를 대화가 진행되는 동안 기억하는 딕셔너리입니다.
    collected_info = {
        "name": None,
        "phone_number": None,
        "reason": None,
        "consent_agreed": None,
    }
    # LLM이 대화의 맥락을 파악할 수 있도록 대화 기록을 저장하는 리스트입니다.
    chat_history = []

    # --- 메인 대화 루프 ---
    while True:
        # 목표(이름, 전화번호, 동의)를 달성했는지 매번 확인합니다.
        if (
            collected_info["name"]
            and collected_info["phone_number"]
            and collected_info["consent_agreed"]
        ):
            logging.info("\n✅ [상담 정보 수집 완료]")
            logging.info(f"  - 고객명: {collected_info['name']}")
            logging.info(f"  - 연락처: {collected_info['phone_number']}")
            logging.info(f"  - 문의 사유: {collected_info['reason'] or 'N/A'}")

            final_message = "감사합니다! 모든 정보가 확인되었습니다. 전문 상담원이 곧 연락드리겠습니다."
            print(f"\n🤖 {final_message}")

            save_chat_log(session_id, "개인정보 수집 동의 완료", final_message)
            save_inquiry_to_db(collected_info)
            break

        # 사용자 입력을 받습니다.
        user_input = input("🙂: ")
        if user_input.lower() == "exit":
            logging.info("상담을 종료합니다. 이용해주셔서 감사합니다.")
            save_chat_log(session_id, user_input, "상담 종료")
            break

        # 사용자의 첫 질문을 '문의 사유'로 저장합니다.
        if not collected_info["reason"]:
            collected_info["reason"] = user_input

        chat_history.append(HumanMessage(content=user_input))

        # --- 4. '정보 추출기' 실행 (상태에 따라 다른 추출기 사용) ---
        try:
            # 이름과 전화번호가 모두 수집된 상태에서는 '동의' 여부를 추출합니다.
            if collected_info["name"] and collected_info["phone_number"]:
                consent_context = (
                    chat_history[-2:] if len(chat_history) >= 2 else chat_history
                )
                extracted_consent = consent_extraction_llm.invoke(consent_context)
                if extracted_consent.agreed and not collected_info["consent_agreed"]:
                    collected_info["consent_agreed"] = True
                    logging.info("🤖 [개인정보 수집 및 이용에 동의해주셨습니다.]")
            # 아직 이름이나 전화번호를 수집 중인 상태에서는 해당 정보만 추출합니다.
            else:
                extracted_info = info_extraction_llm.invoke(
                    [HumanMessage(content=user_input)]
                )
                if extracted_info.name and not collected_info["name"]:
                    collected_info["name"] = extracted_info.name
                    logging.info(f"🤖 [이름: {extracted_info.name} 확인되었습니다.]")
                if extracted_info.phone_number and not collected_info["phone_number"]:
                    collected_info["phone_number"] = extracted_info.phone_number
                    logging.info(
                        f"🤖 [연락처: {extracted_info.phone_number} 확인되었습니다.]"
                    )
        except Exception as e:
            logging.warning(f"정보 추출 중 예외 발생: {e}")
            pass

        # 정보 추출 후 목표를 달성했는지 다시 확인합니다.
        if (
            collected_info["name"]
            and collected_info["phone_number"]
            and collected_info["consent_agreed"]
        ):
            continue

        # --- 5. '응답 생성기' 실행 ---
        # 다음에 무엇을 물어볼지 결정합니다.
        next_prompt = ""
        if not collected_info["name"]:
            next_prompt = "정확한 상담을 위해 성함을 알려주시겠어요?"
        elif not collected_info["phone_number"]:
            next_prompt = "상담원이 연락드릴 수 있도록 전화번호를 남겨주시겠어요?"
        elif not collected_info["consent_agreed"]:
            next_prompt = "마지막으로, 원활한 상담을 위해 개인정보 수집 및 이용에 동의하시나요? (예/아니오)"

        # 현재까지 수집된 정보(상태)를 시스템 프롬프트에 담아, 다음에 무엇을 물어볼지 LLM이 결정하게 합니다.
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

        # 매 대화 턴마다 로그를 데이터베이스에 저장합니다.
        save_chat_log(session_id, user_input, ai_response.content)


if __name__ == "__main__":
    run_chatbot()
    logging.info("=" * 20 + " 챗봇 세션 종료 " + "=" * 20)
    