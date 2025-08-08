import os
import uuid
import logging
from typing import Optional, Tuple, Dict, Any

import mysql.connector
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

# .env 파일에서 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("chatbot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)


# --- 데이터 구조 정의 ---
class PartialCustomerInfo(BaseModel):
    name: Optional[str] = Field(None, description="대화에서 추출한 고객의 이름")
    phone_number: Optional[str] = Field(
        None, description="대화에서 추출한 고객의 전화번호"
    )


class ConsentInfo(BaseModel):
    agreed: bool = Field(
        description="고객이 긍정적으로 답변했는지 여부 (예, 네, 동의합니다 -> True)"
    )


# --- 전역 LLM 인스턴스 ---
# 애플리케이션 시작 시 한 번만 초기화하여 재사용합니다.
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
info_extraction_llm = llm.with_structured_output(PartialCustomerInfo)
consent_extraction_llm = llm.with_structured_output(ConsentInfo)


def save_chat_log(session_id, user_message, bot_response):
    """대화 내용을 데이터베이스에 저장합니다."""
    # ... (이전과 동일)


def save_inquiry_to_db(inquiry_data):
    """수집된 최종 문의 정보를 DB에 저장합니다."""
    # ... (이전과 동일)


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
    if all(collected_info.values()):
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
    """

    messages_for_response = [SystemMessage(content=system_prompt_for_response)]
    messages_for_response.extend(chat_history[-4:])

    ai_response = llm.invoke(messages_for_response)
    chat_history.append(ai_response)

    save_chat_log(session_id, user_input, ai_response.content)

    return ai_response.content, session_data
