from langchain.agents import create_react_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from langchain_core.prompts import PromptTemplate


def create_react_agent_example():
    """
    REAct 전략을 사용한 에이전트 구현
    특징: 사고 과정이 명확히 드러나며, 단계별 추론 가능
    """

    # LLM 초기화
    llm = ChatOpenAI(
        model="gpt-4o-mini", temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    # REAct용 도구 정의 (설명이 매우 중요!)
    tools = [
        Tool(
            name="Calculator",
            func=calculator,
            description="수학 계산을 수행합니다. 사칙연산, 제곱, 제곱근을 지원합니다. 예: '5+3', '2**3', 'sqrt(16)'",
        ),
        Tool(
            name="Weather",
            func=weather_api,
            description="도시별 날씨 정보를 조회합니다. 한국 주요 도시 지원. 예: '서울', '부산', '제주'",
        ),
        Tool(
            name="Database",
            func=lambda query: database_query(*query.split(",")),
            description="데이터베이스에서 정보를 조회합니다. 형식: 'table_name,query_type,condition'. 예: 'users,select,서울'",
        ),
        Tool(
            name="Email",
            func=lambda params: email_sender(*params.split("|")),
            description="이메일을 전송합니다. 형식: 'recipient|subject|body'. 예: 'user@example.com|안녕하세요|메시지 내용'",
        ),
    ]

    # REAct 프롬프트 템플릿 (사고 과정을 명시적으로 유도)
    react_prompt = PromptTemplate.from_template(
        """
당신은 도움이 되는 AI 어시스턴트입니다. 다음 도구들을 사용할 수 있습니다:

{tools}

다음 형식을 정확히 따라주세요:

Question: 답변해야 할 질문
Thought: 무엇을 해야 할지 생각해보세요
Action: 사용할 도구 이름 [{tool_names}] 중 하나
Action Input: 도구에 전달할 입력값
Observation: 도구 실행 결과
... (필요시 Thought/Action/Action Input/Observation 반복)
Thought: 이제 최종 답변을 준비할 수 있습니다
Final Answer: 사용자 질문에 대한 최종 답변

중요: 각 단계에서 왜 그 도구를 선택했는지 명확히 설명하세요.

Question: {input}
Thought: {agent_scratchpad}"""
    )

    # REAct 에이전트 생성
    agent = create_react_agent(llm=llm, tools=tools, prompt=react_prompt)

    # 에이전트 실행기 생성
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,  # 사고 과정 출력
        handle_parsing_errors=True,  # 파싱 오류 자동 처리
        max_iterations=5,  # 최대 반복 횟수
        return_intermediate_steps=True,  # 중간 단계 반환
    )

    return agent_executor


# REAct 에이전트 테스트
def test_react_agent():
    """REAct 에이전트 테스트 함수"""

    agent_executor = create_react_agent_example()

    print("=== REAct 전략 테스트 ===")

    # 복합 질문 테스트
    test_queries = [
        "5의 제곱에 3을 더한 값을 계산하고, 그 결과를 이메일로 admin@company.com에게 '계산 결과'라는 제목으로 보내주세요.",
        "서울과 부산의 날씨를 비교해서 알려주세요.",
        "users 테이블에서 서울에 사는 사용자 정보를 조회해주세요.",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n--- 테스트 {i} ---")
        print(f"질문: {query}")

        try:
            result = agent_executor.invoke({"input": query})
            print(f"답변: {result['output']}")

            # 중간 단계 분석
            print("\n사용된 도구들:")
            for j, (action, observation) in enumerate(result["intermediate_steps"]):
                print(f"  {j+1}. {action.tool}: {action.tool_input}")

        except Exception as e:
            print(f"오류 발생: {e}")


if __name__ == "__main__":
    test_react_agent()
