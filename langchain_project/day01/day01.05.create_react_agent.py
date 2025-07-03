from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools import Tool
from langchain_core.prompts import PromptTemplate
from langchain import hub
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# LLM 초기화 (ChatOpenAI 사용 권장)
llm = ChatOpenAI(
    model="gpt-4o-mini", temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY")
)


# 도구 함수 정의
import operator


def calculator(input_str: str) -> str:
    """
    간단한 수학 계산을 수행하는 도구
    """
    try:
        # 공백 제거
        cleaned_input = input_str.replace(" ", "")

        # eval() 함수는 문자열로 된 표현식을 직접 계산합니다.
        # 이 함수는 강력하지만, 사용자 입력을 직접 eval()에 전달할 때는 보안 위험(코드 주입)이 있습니다.
        # 이 예제에서는 LLM이 생성한 비교적 통제된 입력이므로 사용합니다.
        # 실제 프로덕션 환경에서는 더 안전한 라이브러리(예: asteval, numexpr)를 고려해야 합니다.

        result = eval(cleaned_input)
        return str(result)

    except (SyntaxError, TypeError, NameError):
        # eval()에서 발생할 수 있는 일반적인 오류 처리 (잘못된 수식 등)
        return "계산 오류: 올바른 수학 표현식이 아닙니다 (예: 5+3, 2*4)."
    except Exception as e:
        # 그 외 예상치 못한 오류
        return f"계산 중 알 수 없는 오류가 발생했습니다: {e}"


def weather_info(location: str) -> str:
    """
    날씨 정보를 제공하는 모의 도구 (실제로는 API 호출)
    """
    weather_data = {"서울": "맑음, 15°C", "부산": "흐림, 18°C", "제주": "비, 12°C"}
    return weather_data.get(location, f"{location}의 날씨 정보를 찾을 수 없습니다.")


# 도구 리스트 생성
tools = [
    Tool(
        name="Calculator",
        func=calculator,
        description="수학 계산을 수행합니다. 덧셈(+)과 곱셈(*) 연산을 지원합니다. 예: '5+3', '2*4'",
    ),
    Tool(
        name="Weather",
        func=weather_info,
        description="특정 지역의 날씨 정보를 제공합니다. 도시 이름을 입력하세요. 예: '서울', '부산', '제주'",
    ),
]

# ReAct 프롬프트 템플릿 정의 (필수 입력 키: tools, tool_names, agent_scratchpad)
prompt_template = """다음 질문에 최선을 다해 답변하세요. 다음 도구들을 사용할 수 있습니다:

{tools}

다음 형식을 사용하세요:

Question: 답변해야 할 입력 질문
Thought: 무엇을 해야 할지 항상 생각해보세요
Action: 취할 행동, [{tool_names}] 중 하나여야 합니다
Action Input: 행동에 대한 입력
Observation: 행동의 결과
... (이 Thought/Action/Action Input/Observation은 N번 반복될 수 있습니다)
Thought: 이제 최종 답변을 알았습니다
Final Answer: 원래 입력 질문에 대한 최종 답변

시작!

Question: {input}
Thought:{agent_scratchpad}"""

# 프롬프트 템플릿 생성
prompt = PromptTemplate.from_template(prompt_template)

# 또는 LangChain Hub에서 미리 정의된 프롬프트 사용 (권장)
# prompt = hub.pull("hwchase17/react")

# ReAct 에이전트 생성
agent = create_react_agent(
    llm=llm, tools=tools, prompt=prompt  # 사용할 LLM  # 도구 리스트  # 프롬프트 템플릿
)

# AgentExecutor로 에이전트 실행기 생성
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,  # 실행 과정 출력
    handle_parsing_errors=True,  # 파싱 오류 처리
)

# 에이전트 실행
if __name__ == "__main__":
    # 계산 질문
    result1 = agent_executor.invoke({"input": "5 더하기 3은 얼마인가요?"})
    print("결과 1:", result1["output"])

    # 날씨 질문
    result2 = agent_executor.invoke({"input": "서울 날씨는 어때요?"})
    print("결과 2:", result2["output"])
