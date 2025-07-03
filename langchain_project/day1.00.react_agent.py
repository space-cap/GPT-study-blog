import os
from dotenv import load_dotenv
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.llms import OpenAI

load_dotenv()

# 개별 환경 변수 출력
api_key = os.getenv("OPENAI_API_KEY")
print(f"OPENAI_API_KEY: {api_key}")


def add(x: str, y: str) -> str:
    return str(float(x) + float(y))


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
llm = OpenAI(temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY"))
agent = initialize_agent(
    tools=tools, llm=llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True
)

print("REAct 실행:")
result = agent.invoke({"input": "5에 2를 더하고, 서울 인구도 알려줘"})
print(result["output"])

