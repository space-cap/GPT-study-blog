# flow_control.py
def handle_user_input(session, user_input, chroma_vectordb):
    # 1. 개인정보 동의가 없는 경우 무조건 동의부터 유도
    if not session.consent_given:
        if "동의" in user_input:
            session.give_consent()
            return "동의해주셔서 감사합니다. 이름을 입력해주세요."
        else:
            return "상담 예약을 위해 개인정보 수집 및 이용에 동의해주실 수 있나요? (네/아니요)"

    # 2. 동의받았으면 이름, 전화번호→ 리드 저장
    if "이름" not in session.profile:
        session.set_profile("이름", user_input)
        return "연락받으실 전화번호를 입력해주세요."
    if "전화번호" not in session.profile:
        session.set_profile("전화번호", user_input)
        # TODO: 리드 DB에 저장
        return "접수가 완료되었습니다! 필요시 추가 안내나 상담원을 연결해드릴게요."

    # 3. 평소 질의응답(정보 탐색+LLM)
    bot_answer = get_llm_response(session, user_input, chroma_vectordb)
    return bot_answer
