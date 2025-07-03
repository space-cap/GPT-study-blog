import os
from dotenv import load_dotenv
from langchain.agents import initialize_agent, Tool, AgentType

# from langchain.llms import OpenAI
from langchain_openai import OpenAI

load_dotenv()

# 개별 환경 변수 출력
api_key = os.getenv("OPENAI_API_KEY")
print(f"OPENAI_API_KEY: {api_key}")


def add(*x) -> str:
    # return str(lambda x: sum(map(int, x)))
    return str(sum(map(int, x)))
    # return str(sum(int(i) for i in x if i.isdigit()))


def lookup_population(city: str) -> str:
    data = {"서울": "9,515,000명", "부산": "3,343,000명"}
    return data.get(city.strip(), "정보 없음")


tools = [
    Tool(
        name="Add",
        func=lambda x: add(*x.split()),
        description="두 숫자를 더합니다 (예: '5 2')",
    ),
    Tool(
        name="PopulationLookup",
        func=lookup_population,
        description="도시명을 입력하면 인구를 알려줍니다.",
    ),
]
# llm = OpenAI(temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY"))
# 극도로 저렴한 설정 (기본 작업용)
llm = OpenAI(
    model_name="gpt-4o-mini",
    temperature=0,
    max_tokens=50,  # 매우 짧은 응답
    top_p=0.5,  # 토큰 선택 제한
    openai_api_key=os.getenv("OPENAI_API_KEY"),
)

agent = initialize_agent(
    tools=tools, llm=llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True
)

print("REAct 실행:")
# result = agent.invoke({"input": "5에 2를 더하고, 서울 인구도 알려줘"})
result = agent.invoke({"input": "5,2,3 더하고, 서울 인구도 알려줘"})
print(result["output"])
