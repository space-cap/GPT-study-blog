from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain.tools import StructuredTool
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import Optional


# OpenAI Functions용 입력 스키마 정의
class CalculatorInput(BaseModel):
    """계산기 입력 스키마"""

    expression: str = Field(description="계산할 수식 (예: '5+3', '2**3', 'sqrt(16)')")


class WeatherInput(BaseModel):
    """날씨 조회 입력 스키마"""

    city: str = Field(description="날씨를 조회할 도시 이름")


class DatabaseInput(BaseModel):
    """데이터베이스 쿼리 입력 스키마"""

    table: str = Field(description="조회할 테이블 이름")
    query_type: str = Field(default="select", description="쿼리 타입")
    condition: Optional[str] = Field(default=None, description="검색 조건")


class EmailInput(BaseModel):
    """이메일 전송 입력 스키마"""

    recipient: str = Field(description="수신자 이메일 주소")
    subject: str = Field(description="이메일 제목")
    body: str = Field(description="이메일 본문")


def create_openai_functions_agent_example():
    """
    OpenAI Functions 전략을 사용한 에이전트 구현
    특징: 구조화된 JSON 형태로 정확한 함수 호출, 높은 정확도
    """

    # LLM 초기화 (OpenAI Functions 지원 모델 필요)
    llm = ChatOpenAI(
        model="gpt-4o-mini", temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    # StructuredTool로 함수 정의 (스키마 기반)
    tools = [
        StructuredTool.from_function(
            func=calculator,
            name="calculator",
            description="수학 계산을 수행합니다. 복잡한 수식도 지원합니다.",
            args_schema=CalculatorInput,
        ),
        StructuredTool.from_function(
            func=weather_api,
            name="weather_api",
            description="지정된 도시의 현재 날씨 정보를 조회합니다.",
            args_schema=WeatherInput,
        ),
        StructuredTool.from_function(
            func=database_query,
            name="database_query",
            description="데이터베이스에서 정보를 조회합니다.",
            args_schema=DatabaseInput,
        ),
        StructuredTool.from_function(
            func=email_sender,
            name="email_sender",
            description="지정된 수신자에게 이메일을 전송합니다.",
            args_schema=EmailInput,
        ),
    ]

    # OpenAI Functions용 프롬프트 (간결하고 명확)
    functions_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """당신은 도움이 되는 AI 어시스턴트입니다. 
사용자의 요청을 분석하고 적절한 도구를 사용하여 작업을 수행하세요.
각 도구는 정확한 매개변수를 필요로 하므로 주의깊게 입력값을 준비하세요.

사용 가능한 도구:
- calculator: 수학 계산
- weather_api: 날씨 조회  
- database_query: 데이터베이스 조회
- email_sender: 이메일 전송

복잡한 작업은 단계별로 나누어 처리하세요.""",
            ),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )

    # OpenAI Functions 에이전트 생성
    agent = create_openai_functions_agent(llm=llm, tools=tools, prompt=functions_prompt)

    # 에이전트 실행기 생성
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=5,
        return_intermediate_steps=True,
    )

    return agent_executor


# OpenAI Functions 에이전트 테스트
def test_openai_functions_agent():
    """OpenAI Functions 에이전트 테스트 함수"""

    agent_executor = create_openai_functions_agent_example()

    print("=== OpenAI Functions 전략 테스트 ===")

    # 정확한 매개변수가 필요한 복잡한 작업들
    test_queries = [
        "2의 10제곱을 계산하고, 그 결과가 1000보다 큰지 확인해주세요.",
        "서울 날씨를 확인하고, 비가 오면 우산 챙기라는 내용으로 user@example.com에게 이메일을 보내주세요.",
        "users 테이블에서 나이가 30 이상인 사용자를 찾아주세요.",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n--- 테스트 {i} ---")
        print(f"질문: {query}")

        try:
            result = agent_executor.invoke({"input": query})
            print(f"답변: {result['output']}")

            # 함수 호출 분석
            print("\n호출된 함수들:")
            for j, (action, observation) in enumerate(result["intermediate_steps"]):
                print(f"  {j+1}. {action.tool}({action.tool_input})")
                print(f"     결과: {observation}")

        except Exception as e:
            print(f"오류 발생: {e}")


if __name__ == "__main__":
    test_openai_functions_agent()
