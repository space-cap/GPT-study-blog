# hanspell 라이브러리에서 SpellChecker 클래스를 가져옵니다.
from hanspell import spell_checker

# 교정할 문장을 준비합니다.
# "아버지가방에들어가신다" -> 띄어쓰기 오류
# "않돼는건없다" -> '않'과 '안', '돼'와 '되' 맞춤법 오류
# "감기 빨리 낳으세요" -> '낳으세요'와 '나으세요' 문맥 오류
original_sentence = "아버지가방에들어가신다.않돼는건없다.감기 빨리 낳으세요."

# spell_checker.check() 함수를 사용하여 맞춤법을 검사하고 결과를 받습니다.
# 이 함수는 Result 객체를 반환합니다.
result = spell_checker.check(original_sentence)

# Result 객체에서 교정된 문장을 확인합니다.
corrected_sentence = result.checked
print(f"교정 전: {original_sentence}")
print(f"교정 후: {corrected_sentence}")

print("\n--- 상세 교정 내용 ---")
# result.words 딕셔너리를 통해 어떤 단어가 어떻게 교정되었는지 상세하게 확인할 수 있습니다.
for original_word, corrected_info in result.words.items():
    # corrected_info[0]은 교정 상태를 나타내는 코드, [1]은 교정 제안 단어입니다.
    # 여기서는 간단히 원본 단어와 교정 제안 단어만 출력합니다.
    # 예: {'않돼는건없다': (2, '안 되는 건 없다')}
    print(f"'{original_word}' -> '{corrected_info[1]}'")
