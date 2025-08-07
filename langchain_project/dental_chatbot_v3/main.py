import os
from typing import Optional

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI

# .env 파일에서 환경 변수 로드 (OPENAI_API_KEY)
load_dotenv()


# --- 1. LLM이 추출할 데이터 구조 정의 (Pydantic 모델) ---
# 챗봇의 최종 목표는 이 구조에 맞춰 고객 정보를 추출하는 것입니다.
class CustomerInfo(BaseModel):
    """고객의 이름과 전화번호 정보를 담는 데이터 구조입니다."""

    name: str = Field(description="고객의 이름")
    phone_number: str = Field(description="고객의 전화번호")
    reason: Optional[str] = Field(
        description="고객이 문의한 간략한 사유 (예: 예약, 비용 문의 등)"
    )


def run_chatbot():
    """
    고객의 이름과 연락처를 수집하는 것을 목표로 하는 챗봇을 실행합니다.
    """
    print(
        "🤖 안녕하세요! 스마일 치과 챗봇입니다. 무엇을 도와드릴까요? (종료하시려면 'exit'을 입력하세요)"
    )

    # --- 2. 챗봇 모델 및 설정 초기화 ---
    # OpenAI의 gpt-4o-mini 모델을 사용하고, JSON 모드를 활성화하여 구조화된 데이터 추출을 용이하게 합니다.
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = llm.with_structured_output(CustomerInfo)

    # --- 3. 챗봇의 역할과 목표를 정의하는 시스템 프롬프트 ---
    system_prompt = """
    당신은 '스마일 치과'의 매우 친절하고 전문적인 상담 챗봇입니다. 
    당신의 가장 중요한 목표는 고객의 **이름**과 **전화번호**를 수집하여, 전문 상담원이 전화를 걸 수 있도록 하는 것입니다.

    대화 흐름은 다음과 같습니다:
    1. 항상 따뜻한 인사로 대화를 시작하고 무엇을 도와드릴지 물어보세요.
    2. 고객이 예약, 비용, 진료 등 어떤 질문을 하더라도, 당신의 대답은 항상 이름과 전화번호를 물어보는 것으로 이어져야 합니다. 
       예시: "네, 자세한 상담을 위해 성함과 연락처를 남겨주시겠어요? 전문 상담원이 확인 후 바로 연락드리겠습니다."
    3. 정중하지만 끈기 있게 목표를 달성해야 합니다. 고객이 이름만 알려주면 전화번호를 물어보고, 전화번호만 알려주면 이름을 물어보세요.
    4. 이름과 전화번호를 모두 얻기 전까지는 절대 `CustomerInfo` 형식으로 응답해서는 안 됩니다. 계속 대화를 이어가세요.
    5. 이름과 전화번호를 모두 성공적으로 얻었을 때만 `CustomerInfo` 형식으로 정보를 추출하여 응답을 종료하세요.
    6. 절대로 의학적인 질문에 직접 답변하지 마세요. 대신, "자세한 내용은 전문 상담원이 친절하게 안내해 드릴 예정입니다." 와 같이 응대하며 연락처를 요청하세요.
    """

    # 대화 기록을 저장할 리스트
    chat_history = [SystemMessage(content=system_prompt)]

    while True:
        try:
            user_input = input("🙂: ")
            if user_input.lower() == "exit":
                print("🤖 상담을 종료합니다. 이용해주셔서 감사합니다.")
                break

            # 사용자의 입력을 대화 기록에 추가
            chat_history.append(HumanMessage(content=user_input))

            # --- 4. 정보 추출 시도 ---
            # LLM에게 현재 대화 내용에서 CustomerInfo를 추출할 수 있는지 확인을 요청합니다.
            # 5번의 시도 안에 정보를 추출하지 못하면 일반 대화로 전환합니다.
            try:
                customer_info = structured_llm.invoke(
                    chat_history, config={"max_retries": 5}
                )

                # 정보 추출에 성공하면 목표 달성!
                print("\n✅ [상담 정보 수집 완료]")
                print(f"  - 고객명: {customer_info.name}")
                print(f"  - 연락처: {customer_info.phone_number}")
                print(f"  - 문의 사유: {customer_info.reason or 'N/A'}")
                print("\n🤖 감사합니다! 전문 상담원이 곧 연락드리겠습니다.")
                break

            except Exception as e:
                # 정보 추출에 실패하면 (아직 정보가 부족하면), 일반 대화를 계속합니다.
                ai_response = llm.invoke(chat_history)
                chat_history.append(ai_response)
                print(f"🤖: {ai_response.content}")

        except (KeyboardInterrupt, EOFError):
            print("\n🤖 상담을 종료합니다. 이용해주셔서 감사합니다.")
            break


if __name__ == "__main__":
    run_chatbot()
