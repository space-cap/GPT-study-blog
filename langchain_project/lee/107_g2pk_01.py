# g2pk 라이브러리에서 맞춤법 교정기 클래스를 가져옵니다.
from g2pk import G2p

# --- 1. 규칙 기반 교정 설정 (보조 교정기) ---
# 이 사전은 g2pk가 처리하기 전, 가장 먼저 적용됩니다.
# g2pk가 놓치거나, 꼭 특정 단어로 바꿔야 하는 '특별 규칙'만 최소한으로 추가해서 관리합니다.
custom_corrections = {
    "설": "서울",  # '설'이라는 단어를 무조건 '서울'로 교정
    "넘": "너무",  # 자주 쓰는 줄임말을 표준어로 교정
    # 필요시 이곳에 계속 추가...
}


# 사용자 정의 규칙을 적용하는 함수
def apply_custom_rules(text, rules):
    """
    사전에 정의된 규칙에 따라 텍스트의 특정 단어를 교체합니다.

    Args:
        text (str): 원본 텍스트
        rules (dict): {'오타': '정상 단어'} 형태의 교정 규칙 사전

    Returns:
        str: 교정 규칙이 적용된 텍스트
    """
    # 딕셔너리에 있는 모든 규칙에 대해 한 번씩 text.replace를 실행합니다.
    for wrong, correct in rules.items():
        text = text.replace(wrong, correct)
    return text


# --- 2. 메인 교정기 준비 ---
# g2pk 객체를 생성합니다. 이 객체가 대부분의 일반적인 맞춤법 교정을 담당합니다.
g2p = G2p()


# --- 3. 최종 교정 함수 (하이브리드 방식) ---
def correct_sentence(text):
    """
    사용자 정의 규칙과 g2pk를 순차적으로 적용하여 문장을 최종 교정합니다.

    Args:
        text (str): 교정할 원본 문장

    Returns:
        str: 최종 교정된 문장
    """
    # 1단계: 가장 우선순위가 높은 사용자 정의 규칙을 먼저 적용합니다.
    # 이렇게 하면 g2pk가 "설" 같은 단어를 다른 단어로 바꾸는 것을 방지할 수 있습니다.
    text_after_custom_rules = apply_custom_rules(text, custom_corrections)

    # 2단계: 1차 교정된 문장을 g2pk에 넣어 일반적인 맞춤법 전체를 교정합니다.
    final_corrected_text = g2p(text_after_custom_rules)

    return final_corrected_text


# --- 4. 실행 및 테스트 ---
if __name__ == "__main__":
    # 테스트할 문장. '설'과 '넘', 그리고 '않좋네요'라는 두 종류의 오류가 포함됨
    original_sentence = "대한민국의 수도는 설이고, 날씨가 넘 않좋네요."

    # 위에서 만든 최종 교정 함수를 호출합니다.
    corrected_sentence = correct_sentence(original_sentence)

    # 결과를 출력합니다.
    print(f"원본 문장: {original_sentence}")
    print(f"최종 교정: {corrected_sentence}")
    print("-" * 30)

    # 다른 예시
    original_sentence_2 = "이 영화 넘 잼있어요."
    corrected_sentence_2 = correct_sentence(original_sentence_2)
    print(f"원본 문장: {original_sentence_2}")
    print(f"최종 교정: {corrected_sentence_2}")
