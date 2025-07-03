from langchain.agents import create_react_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from langchain_core.prompts import PromptTemplate
from typing import List, Dict
import json


class PlanAndExecuteAgent:
    """
    Plan-and-Execute 전략 구현
    특징: 복잡한 작업을 단계별로 계획하고 순차 실행
    """

    def __init__(self):
        # 계획 수립용 LLM (더 강력한 모델 사용 가능)
        self.planner_llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )

        # 실행용 LLM (빠른 모델 사용 가능)
        self.executor_llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )

        # 사용 가능한 도구들
        self.tools = [
            Tool(name="Calculator", func=calculator, description="수학 계산 수행"),
            Tool(name="Weather", func=weather_api, description="날씨 정보 조회"),
            Tool(
                name="Database",
                func=lambda query: database_query(*query.split(",")),
                description="데이터베이스 조회",
            ),
            Tool(
                name="Email",
                func=lambda params: email_sender(*params.split("|")),
                description="이메일 전송",
            ),
        ]

        # 실행용 에이전트 생성
        self.executor_agent = self._create_executor_agent()

    def _create_executor_agent(self):
        """실행 전용 에이전트 생성"""

        executor_prompt = PromptTemplate.from_template(
            """
당신은 주어진 단일 작업을 정확히 수행하는 실행 전문 에이전트입니다.

사용 가능한 도구: {tools}

다음 형식을 따라주세요:
Question: 수행할 작업
Thought: 어떤 도구를 사용할지 결정
Action: [{tool_names}] 중 하나
Action Input: 도구 입력값
Observation: 결과
Thought: 작업 완료 확인
Final Answer: 작업 결과

Question: {input}
Thought: {agent_scratchpad}"""
        )

        agent = create_react_agent(
            llm=self.executor_llm, tools=self.tools, prompt=executor_prompt
        )

        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=False,  # 실행 단계에서는 간결하게
            handle_parsing_errors=True,
            max_iterations=3,
        )

    def create_plan(self, user_query: str) -> List[Dict]:
        """
        사용자 질문을 분석하여 단계별 실행 계획 수립
        """

        planning_prompt = f"""
사용자 요청을 분석하여 단계별 실행 계획을 수립하세요.

사용 가능한 도구:
- Calculator: 수학 계산
- Weather: 날씨 조회
- Database: 데이터베이스 조회 (users, orders 테이블)
- Email: 이메일 전송

사용자 요청: {user_query}

다음 JSON 형식으로 계획을 작성하세요:
{{
    "analysis": "요청 분석 내용",
    "steps": [
        {{
            "step_number": 1,
            "description": "단계 설명",
            "tool": "사용할 도구",
            "input": "도구 입력값",
            "expected_output": "예상 결과"
        }},
        ...
    ],
    "final_goal": "최종 목표"
}}

복잡한 작업은 여러 단계로 나누고, 각 단계의 의존성을 고려하세요.
"""

        try:
            # 계획 수립 요청
            response = self.planner_llm.invoke(planning_prompt)

            # JSON 파싱 (실제로는 더 안전한 파싱 필요)
            plan_text = response.content

            # JSON 부분만 추출
            start_idx = plan_text.find("{")
            end_idx = plan_text.rfind("}") + 1
            json_text = plan_text[start_idx:end_idx]

            plan = json.loads(json_text)
            return plan

        except Exception as e:
            print(f"계획 수립 오류: {e}")
            # 기본 계획 반환
            return {
                "analysis": "계획 수립 실패",
                "steps": [
                    {
                        "step_number": 1,
                        "description": "사용자 요청 직접 처리",
                        "tool": "Calculator",
                        "input": user_query,
                        "expected_output": "결과",
                    }
                ],
                "final_goal": "사용자 요청 처리",
            }

    def execute_plan(self, plan: Dict) -> Dict:
        """
        수립된 계획을 단계별로 실행
        """

        print(f"=== 실행 계획 ===")
        print(f"분석: {plan['analysis']}")
        print(f"최종 목표: {plan['final_goal']}")
        print(f"총 {len(plan['steps'])}단계")

        execution_results = []
        context = {}  # 단계간 정보 공유용

        for step in plan["steps"]:
            step_num = step["step_number"]
            description = step["description"]
            tool = step["tool"]
            tool_input = step["input"]

            print(f"\n--- 단계 {step_num}: {description} ---")
            print(f"도구: {tool}")
            print(f"입력: {tool_input}")

            try:
                # 이전 단계 결과를 현재 입력에 반영
                if context and "{previous_result}" in tool_input:
                    tool_input = tool_input.replace(
                        "{previous_result}", str(context.get("last_result", ""))
                    )

                # 단계 실행
                result = self.executor_agent.invoke(
                    {"input": f"{tool} 도구를 사용하여 다음 작업 수행: {tool_input}"}
                )

                step_result = {
                    "step_number": step_num,
                    "description": description,
                    "tool": tool,
                    "input": tool_input,
                    "output": result["output"],
                    "success": True,
                }

                # 컨텍스트 업데이트
                context["last_result"] = result["output"]
                context[f"step_{step_num}_result"] = result["output"]

                print(f"결과: {result['output']}")

            except Exception as e:
                step_result = {
                    "step_number": step_num,
                    "description": description,
                    "tool": tool,
                    "input": tool_input,
                    "output": f"오류: {str(e)}",
                    "success": False,
                }

                print(f"오류: {e}")

            execution_results.append(step_result)

        return {
            "plan": plan,
            "execution_results": execution_results,
            "context": context,
        }

    def process_query(self, user_query: str) -> str:
        """
        사용자 질문을 계획-실행 방식으로 처리
        """

        print(f"=== Plan-and-Execute 처리 시작 ===")
        print(f"사용자 질문: {user_query}")

        # 1단계: 계획 수립
        plan = self.create_plan(user_query)

        # 2단계: 계획 실행
        execution_result = self.execute_plan(plan)

        # 3단계: 최종 답변 생성
        final_answer = self._generate_final_answer(user_query, execution_result)

        return final_answer

    def _generate_final_answer(self, user_query: str, execution_result: Dict) -> str:
        """실행 결과를 바탕으로 최종 답변 생성"""

        successful_steps = [
            step for step in execution_result["execution_results"] if step["success"]
        ]

        if not successful_steps:
            return "죄송합니다. 요청을 처리하는 중 오류가 발생했습니다."

        # 최종 답변 구성
        answer_parts = []
        answer_parts.append(f"요청하신 '{user_query}'에 대한 처리 결과입니다.")

        for step in successful_steps:
            answer_parts.append(f"- {step['description']}: {step['output']}")

        return "\n".join(answer_parts)


# Plan-and-Execute 에이전트 테스트
def test_plan_and_execute_agent():
    """Plan-and-Execute 에이전트 테스트 함수"""

    agent = PlanAndExecuteAgent()

    print("=== Plan-and-Execute 전략 테스트 ===")

    # 복잡한 다단계 작업들
    test_queries = [
        "users 테이블에서 서울에 사는 사용자를 찾고, 그 사용자의 나이에 10을 더한 값을 계산한 후, 결과를 admin@company.com에게 이메일로 보내주세요.",
        "서울과 부산의 날씨를 각각 조회하고, 두 도시의 기온 차이를 계산해주세요.",
        "orders 테이블에서 완료된 주문들의 총 금액을 계산하고, 그 결과가 100000보다 큰지 확인해주세요.",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*50}")
        print(f"테스트 {i}")
        print(f"{'='*50}")

        try:
            result = agent.process_query(query)
            print(f"\n=== 최종 답변 ===")
            print(result)

        except Exception as e:
            print(f"오류 발생: {e}")


if __name__ == "__main__":
    test_plan_and_execute_agent()


