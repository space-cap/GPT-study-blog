import uuid
from chatbot_logic import process_chat_turn


def run_console_chatbot():
    """
    콘솔 환경에서 챗봇 로직을 테스트하기 위한 실행 함수입니다.
    """
    # 1. 세션 초기화
    # 각 실행마다 새로운 대화 세션을 시작합니다.
    session_id = str(uuid.uuid4())
    session_data = {
        "collected_info": {
            "name": None,
            "phone_number": None,
            "reason": None,
            "consent_agreed": None,
        },
        "chat_history": [],
    }

    print(f"--- 새로운 콘솔 챗봇 세션을 시작합니다 (ID: {session_id}) ---")
    print(
        "🤖 안녕하세요! 스마일 치과 챗봇입니다. 무엇을 도와드릴까요? (종료하시려면 'exit'을 입력하세요)"
    )

    # 2. 메인 대화 루프
    while True:
        user_input = input("🙂: ")
        if user_input.lower() == "exit":
            print("🤖 상담을 종료합니다.")
            break

        # 3. 챗봇 로직 호출
        # 사용자의 입력과 현재 세션 데이터를 chatbot_logic으로 보내 응답을 받습니다.
        ai_response, updated_session_data = process_chat_turn(
            session_id=session_id, user_input=user_input, session_data=session_data
        )

        # 4. 세션 데이터 업데이트
        session_data = updated_session_data

        print(f"🤖: {ai_response}")

        # 5. 목표 달성 여부 확인 후 종료
        collected_info = session_data["collected_info"]
        if all(collected_info.values()):
            print("--- 챗봇의 정보 수집 목표가 달성되어 세션을 종료합니다. ---")
            break


if __name__ == "__main__":
    run_console_chatbot()
