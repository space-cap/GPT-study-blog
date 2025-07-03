# LangChain의 PromptTemplate 모듈을 import
from langchain.prompts import PromptTemplate

# 1. 프롬프트 템플릿 정의
# 문자열 안에 {job}이라는 변수를 포함해, 다양한 직업에 따라 문장을 동적으로 생성할 수 있게 함
template = "당신은 {job}입니다. 오늘 할 일은?"

# 2. PromptTemplate 객체 생성
# 위에서 정의한 template 문자열을 기반으로 PromptTemplate 객체를 생성
prompt = PromptTemplate.from_template(template)

# 3. 템플릿에 변수 주입 (job="요리사")
# prompt.format(...)을 호출하면, 템플릿 내 {job} 부분이 "요리사"로 치환되어 최종 문장이 만들어짐
formatted_prompt = prompt.format(job="요리사")

# 4. 결과
# formatted_prompt는 아래와 같은 문자열을 반환:
# "당신은 요리사입니다. 오늘 할 일은?"
print("프롬프트 템플릿 생성 완료!")
print(f"생성된 프롬프트: {formatted_prompt}")

