# 1. OpenAI 모델을 사용하는 LLM(대형 언어 모델) 객체를 임포트
from langchain.llms import OpenAI

# 2. LLMChain 클래스: 프롬프트 + LLM 실행을 하나의 체인으로 묶는 객체
from langchain.chains import LLMChain

# 3. OpenAI LLM 객체 생성
# 기본적으로 OpenAI의 ChatGPT 또는 GPT-3.5/4 엔진을 사용
llm = OpenAI()

# 4. 앞서 만든 PromptTemplate과 LLM을 조합해 LLMChain 생성
prompt = "당신은 {job}입니다. 오늘 할 일은?"
chain = LLMChain(llm=llm, prompt=prompt)

# 5. 체인 실행: run() 함수에 dict 형태로 변수 주입
# 여기서는 job="개발자"라는 값을 {job}에 넣어 실행
output = chain.run({"job": "개발자"})

# 6. 결과
# 내부적으로 다음 프롬프트가 생성됨:
# → "당신은 개발자입니다. 오늘 할 일은?"
# 이 프롬프트가 LLM에 전달되고, 모델의 응답이 output 변수에 저장됨
print("LLMChain 실행 완료!")
print(f"생성된 프롬프트: {output}")

