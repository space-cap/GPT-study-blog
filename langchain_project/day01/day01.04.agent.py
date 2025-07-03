from langchain_openai import OpenAI
from langchain.agents import initialize_agent, Tool, AgentType
import os
from dotenv import load_dotenv

load_dotenv()

llm = OpenAI(
    model_name="gpt-4o-mini",
    temperature=0,
    max_tokens=100,  # 토큰 수 증가
    openai_api_key=os.getenv("OPENAI_API_KEY"),
)


def calculator(input_str: str) -> str:
    try:
        num = float(input_str)
        return str(num**2)  # 숫자의 제곱을 반환
    except ValueError:
        return "유효한 숫자를 입력해주세요."


calculator_tool = Tool(
    name="Calculator",
    func=calculator,
    description="숫자의 제곱을 계산합니다.",
)

agent = initialize_agent(
    tools=[calculator_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,  # 디버깅을 위해 추가
)

# invoke 사용 (run은 deprecated)
result = agent.invoke({"input": "3의 제곱은?"})
print(result)
