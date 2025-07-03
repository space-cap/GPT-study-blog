from langchain_community.agent_toolkits import JsonToolkit, create_json_agent
from langchain_community.tools.json.tool import JsonSpec
from langchain_openai import OpenAI
import json
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# LLM 초기화 (JSON 에이전트는 OpenAI 텍스트 모델 사용)
llm = OpenAI(temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY"))

# 샘플 JSON 데이터 생성 (실제로는 파일에서 로드)
sample_data = {
    "company": {
        "name": "TechCorp",
        "founded": 2010,
        "employees": [
            {
                "id": 1,
                "name": "김철수",
                "department": "개발팀",
                "salary": 5000,
                "skills": ["Python", "JavaScript", "React"],
            },
            {
                "id": 2,
                "name": "이영희",
                "department": "마케팅팀",
                "salary": 4500,
                "skills": ["Marketing", "Analytics", "SEO"],
            },
            {
                "id": 3,
                "name": "박민수",
                "department": "개발팀",
                "salary": 5500,
                "skills": ["Java", "Spring", "Docker"],
            },
        ],
        "departments": {
            "개발팀": {"budget": 100000, "projects": ["웹앱 개발", "API 서버 구축"]},
            "마케팅팀": {"budget": 50000, "projects": ["브랜드 캠페인", "SEO 최적화"]},
        },
    }
}

# 실제 파일에서 JSON 로드하는 경우
# with open('company_data.json', 'r', encoding='utf-8') as f:
#     sample_data = json.load(f)

# JsonSpec 생성 (JSON 구조 분석을 위한 스펙)
json_spec = JsonSpec(
    dict_=sample_data,  # 분석할 JSON 데이터
    max_value_length=4000,  # 값의 최대 길이 제한
)

# JsonToolkit 생성 (JSON 탐색 도구들의 집합)
json_toolkit = JsonToolkit(spec=json_spec)

# JSON 에이전트 생성
json_agent_executor = create_json_agent(
    llm=llm,  # 사용할 LLM
    toolkit=json_toolkit,  # JSON 도구 키트
    verbose=True,  # 실행 과정 출력
    handle_parsing_errors=True,  # 파싱 오류 처리
)

# JSON 에이전트 실행
if __name__ == "__main__":
    # 직원 정보 질문
    result1 = json_agent_executor.invoke(
        {"input": "개발팀에서 일하는 직원들의 이름과 급여를 알려주세요."}
    )
    print("결과 1:", result1["output"])

    # 부서별 예산 질문
    result2 = json_agent_executor.invoke({"input": "각 부서의 예산은 얼마인가요?"})
    print("결과 2:", result2["output"])

    # 특정 직원의 스킬 질문
    result3 = json_agent_executor.invoke(
        {"input": "김철수가 가진 기술 스택은 무엇인가요?"}
    )
    print("결과 3:", result3["output"])

# JSON 도구키트에 포함된 개별 도구들 확인
print("\n사용 가능한 JSON 도구들:")
for tool in json_toolkit.get_tools():
    print(f"- {tool.name}: {tool.description}")
