# 1. 필요한 모듈 임포트
from langchain_openai import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 2. OpenAI LLM 객체 생성
llm = OpenAI(
    model="gpt-4o-mini",
    temperature=0.5,
    max_tokens=100,
    openai_api_key=os.getenv("OPENAI_API_KEY"),
)

# 3. PromptTemplate 생성
prompt_template = PromptTemplate(
    input_variables=["job"], template="당신은 {job}입니다. 오늘 할 일은?"
)

# 4. LLMChain 생성
chain = LLMChain(llm=llm, prompt=prompt_template)

# 5. 체인 실행 (invoke 사용)
try:
    result = chain.invoke({"job": "개발자"})
    output = result.get("text", "응답을 받지 못했습니다.")

    print("LLMChain 실행 완료!")
    print(f"생성된 응답: {output}")

except Exception as e:
    print(f"오류 발생: {e}")
