import os
from typing import Optional

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

# .env 파일에서 환경 변수 로드 (OPENAI_API_KEY)
load_dotenv()


# --- 1. 정보 '추출기'가 사용할 데이터 구조 ---
# 이름, 전화번호 등 부분적인 정보만 담을 수 있도록 모든 필드를 Optional로 설정합니다.
class PartialCustomerInfo(BaseModel):
    """고객의 이름 또는 전화번호 정보를 담는 데이터 구조입니다."""

    name: Optional[str] = Field(None, description="대화에서 추출한 고객의 이름")
    phone_number: Optional[str] = Field(
        None, description="대화에서 추출한 고객의 전화번호"
    )


def run_chatbot():
    """
    대화의 상태를 관리하며 고객의 이름과 연락처를 수집하는 챗봇을 실행합니다.
    """
    print(
        "🤖 안녕하세요! 스마일 치과 챗봇입니다. 무엇을 도와드릴까요? (종료하시려면 'exit'을 입력하세요)"
    )

    # --- 2. 챗봇 모델 및 설정 초기화 ---
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    extraction_llm = llm.with_structured_output(PartialCustomerInfo)

    # --- 3. '상태 관리자'가 사용할 저장 공간 ---
    # 수집된 고객 정보를 기억하는 딕셔너리입니다.
    collected_info = {
        "name": None,
        "phone_number": None,
        "reason": None,
    }

    # 대화 기록을 저장할 리스트
    chat_history = []

    while True:
        # --- 최종 목표 달성 여부 확인 ---
        if collected_info["name"] and collected_info["phone_number"]:
            print("\n✅ [상담 정보 수집 완료]")
            print(f"  - 고객명: {collected_info['name']}")
            print(f"  - 연락처: {collected_info['phone_number']}")
            print(f"  - 문의 사유: {collected_info['reason'] or 'N/A'}")
            print("\n🤖 감사합니다! 전문 상담원이 곧 연락드리겠습니다.")
            break

        user_input = input("🙂: ")
        if user_input.lower() == "exit":
            print("🤖 상담을 종료합니다. 이용해주셔서 감사합니다.")
            break

        # 첫 질문을 '문의 사유'로 저장
        if not collected_info["reason"]:
            collected_info["reason"] = user_input

        chat_history.append(HumanMessage(content=user_input))

        # --- 4. '정보 추출기' 실행 ---
        # 사용자의 마지막 답변에서 이름이나 연락처를 추출 시도합니다.
        try:
            extracted_data = extraction_llm.invoke([HumanMessage(content=user_input)])
            if extracted_data.name and not collected_info["name"]:
                collected_info["name"] = extracted_data.name
                print(f"🤖 [이름: {extracted_data.name} 확인되었습니다.]")
            if extracted_data.phone_number and not collected_info["phone_number"]:
                collected_info["phone_number"] = extracted_data.phone_number
                print(f"🤖 [연락처: {extracted_data.phone_number} 확인되었습니다.]")
        except Exception:
            # 추출할 정보가 없으면 그냥 넘어갑니다.
            pass

        # 목표를 달성했는지 다시 확인
        if collected_info["name"] and collected_info["phone_number"]:
            continue

        # --- 5. '응답 생성기' 실행 ---
        # 현재까지 수집된 정보(상태)를 바탕으로, 다음에 무엇을 물어볼지 결정합니다.
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

        messages_for_response = [
            SystemMessage(content=system_prompt_for_response),
        ]
        # 대화의 흐름을 파악할 수 있도록 최근 대화 내용을 함께 전달합니다.
        messages_for_response.extend(chat_history[-4:])

        ai_response = llm.invoke(messages_for_response)
        chat_history.append(ai_response)
        print(f"🤖: {ai_response.content}")


if __name__ == "__main__":
    run_chatbot()
