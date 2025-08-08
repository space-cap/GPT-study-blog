import os
import uuid
import logging
from typing import Optional, Tuple, Dict, Any

import mysql.connector
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from utils.logging_config import setup_logging

# .env 파일에서 환경 변수 로드
load_dotenv()

# 로깅 설정 실행
setup_logging()


# --- 데이터 구조 정의 ---
class PartialCustomerInfo(BaseModel):
    """고객의 이름 또는 전화번호 정보를 담는 데이터 구조입니다."""

    name: Optional[str] = Field(None, description="대화에서 추출한 고객의 이름")
    phone_number: Optional[str] = Field(
        None, description="대화에서 추출한 고객의 전화번호"
    )


class ConsentInfo(BaseModel):
    """고객의 동의 여부를 판단하는 데이터 구조입니다."""

    agreed: bool = Field(
        description="고객이 긍정적으로 답변했는지 여부 (예, 네, 동의합니다 -> True)"
    )


# --- 전역 LLM 인스턴스 ---
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
info_extraction_llm = llm.with_structured_output(PartialCustomerInfo)
consent_extraction_llm = llm.with_structured_output(ConsentInfo)


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
        # [수정] inquiry_status를 함께 저장하도록 쿼리 변경
        insert_query = """
        INSERT INTO chatbot_inquiry (session_id, customer_name, phone_number, inquiry_reason, consent_agreed, inquiry_status) 
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        data = (
            inquiry_data["session_id"],
            inquiry_data["name"],
            inquiry_data["phone_number"],
            inquiry_data["reason"],
            "Y" if inquiry_data["consent_agreed"] else "N",
            "대기중",  # 기본 상태값 추가
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


def process_chat_turn(
    session_id: str, user_input: str, session_data: Dict[str, Any]
) -> Tuple[str, Dict[str, Any]]:
    """
    한 턴의 대화를 처리하고, 봇의 응답과 업데이트된 세션 데이터를 반환합니다.
    """
    collected_info = session_data["collected_info"]
    chat_history = session_data["chat_history"]

    # 사용자의 첫 질문을 '문의 사유'로 저장
    if not collected_info["reason"]:
        collected_info["reason"] = user_input

    chat_history.append(HumanMessage(content=user_input))

    # --- 정보 추출기 실행 ---
    try:
        if collected_info["name"] and collected_info["phone_number"]:
            consent_context = (
                chat_history[-2:] if len(chat_history) >= 2 else chat_history
            )
            extracted_consent = consent_extraction_llm.invoke(consent_context)
            if extracted_consent.agreed and not collected_info["consent_agreed"]:
                collected_info["consent_agreed"] = True
                logging.info(f"세션 [{session_id}]: 개인정보 동의 확인.")
        else:
            extracted_info = info_extraction_llm.invoke(
                [HumanMessage(content=user_input)]
            )
            if extracted_info.name and not collected_info["name"]:
                collected_info["name"] = extracted_info.name
                logging.info(f"세션 [{session_id}]: 이름 '{extracted_info.name}' 수집.")
            if extracted_info.phone_number and not collected_info["phone_number"]:
                collected_info["phone_number"] = extracted_info.phone_number
                logging.info(
                    f"세션 [{session_id}]: 연락처 '{extracted_info.phone_number}' 수집."
                )
    except Exception as e:
        logging.warning(f"세션 [{session_id}]: 정보 추출 중 예외 발생: {e}")
        pass

    # --- 최종 목표 달성 시 ---
    # [수정] 'reason'을 제외한 모든 필수값이 None이 아닌지 확인
    is_complete = all(
        value is not None for key, value in collected_info.items() if key != "reason"
    )
    if is_complete:
        final_message = (
            "감사합니다! 모든 정보가 확인되었습니다. 전문 상담원이 곧 연락드리겠습니다."
        )
        save_chat_log(session_id, "개인정보 수집 동의 완료", final_message)
        save_inquiry_to_db(collected_info)
        return final_message, session_data

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

    save_chat_log(session_id, user_input, ai_response.content)

    return ai_response.content, session_data
