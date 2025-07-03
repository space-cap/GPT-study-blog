from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI LLM 객체 생성
llm = OpenAI(
    model="gpt-4o-mini",
    temperature=0,
    max_tokens=100,
    openai_api_key=os.getenv("OPENAI_API_KEY"),
)

# PromptTemplate 생성
prompt_template = PromptTemplate(
    input_variables=["job"], template="당신은 {job}입니다. 오늘 할 일은?"
)

# 완성된 프롬프트 확인
input_data = {"job": "개발자"}
formatted_prompt = prompt_template.format(**input_data)

print("🔍 프롬프트 분석")
print(f"템플릿: {prompt_template.template}")
print(f"변수: {prompt_template.input_variables}")
print(f"완성된 프롬프트: '{formatted_prompt}'")

# 파이프라인 방식으로 체인 생성
chain = prompt_template | llm

# 실행
output = chain.invoke(input_data)

print("현대적인 체인 실행 완료!")
print(f"생성된 응답: {output}")
