from langchain.agents import create_structured_chat_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain.tools import StructuredTool
from langchain_core.prompts import ChatPromptTemplate
from langchain import hub
from pydantic import BaseModel, Field
from typing import Optional
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# LLM 초기화
llm = ChatOpenAI(
    model="gpt-4o-mini", temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY")
)


# 복잡한 입력을 위한 Pydantic 모델 정의
class EmailInput(BaseModel):
    """이메일 전송을 위한 입력 모델"""

    recipient: str = Field(description="수신자 이메일 주소")
    subject: str = Field(description="이메일 제목")
    body: str = Field(description="이메일 본문")
    priority: Optional[str] = Field(
        default="normal", description="우선순위: low, normal, high"
    )


class DatabaseQuery(BaseModel):
    """데이터베이스 쿼리를 위한 입력 모델"""

    table: str = Field(description="조회할 테이블 이름")
    columns: str = Field(description="조회할 컬럼들 (쉼표로 구분)")
    condition: Optional[str] = Field(default=None, description="WHERE 조건 (선택사항)")


class FileOperation(BaseModel):
    """파일 작업을 위한 입력 모델"""

    operation: str = Field(description="작업 유형: read, write, delete")
    filename: str = Field(description="파일 이름")
    content: Optional[str] = Field(
        default=None, description="파일 내용 (write 작업시 필요)"
    )


# 구조화된 도구 함수들 정의
def send_email(
    recipient: str, subject: str, body: str, priority: str = "normal"
) -> str:
    """
    이메일을 전송하는 함수 (실제로는 SMTP 서버 연결)
    """
    return f"이메일 전송 완료:\n수신자: {recipient}\n제목: {subject}\n우선순위: {priority}\n본문 길이: {len(body)}자"


def query_database(table: str, columns: str, condition: str = None) -> str:
    """
    데이터베이스를 조회하는 함수 (실제로는 DB 연결)
    """
    # 모의 데이터베이스 응답
    mock_data = {
        "users": [
            {"id": 1, "name": "김철수", "email": "kim@example.com"},
            {"id": 2, "name": "이영희", "email": "lee@example.com"},
        ],
        "orders": [
            {"id": 101, "user_id": 1, "amount": 50000, "status": "completed"},
            {"id": 102, "user_id": 2, "amount": 30000, "status": "pending"},
        ],
    }

    if table in mock_data:
        result = f"테이블 '{table}'에서 컬럼 '{columns}' 조회 결과:\n"
        if condition:
            result += f"조건: {condition}\n"
        result += str(mock_data[table])
        return result
    else:
        return f"테이블 '{table}'을 찾을 수 없습니다."


def file_operation(operation: str, filename: str, content: str = None) -> str:
    """
    파일 작업을 수행하는 함수 (실제로는 파일 시스템 접근)
    """
    if operation == "read":
        return f"파일 '{filename}' 읽기 완료 (모의 내용: 'Hello World')"
    elif operation == "write":
        if content:
            return f"파일 '{filename}'에 {len(content)}자 내용 쓰기 완료"
        else:
            return "쓰기 작업에는 content 매개변수가 필요합니다."
    elif operation == "delete":
        return f"파일 '{filename}' 삭제 완료"
    else:
        return f"지원하지 않는 작업: {operation}"


# StructuredTool로 도구들 생성
tools = [
    StructuredTool.from_function(
        func=send_email,
        name="SendEmail",
        description="이메일을 전송합니다. 수신자, 제목, 본문이 필요하며 우선순위는 선택사항입니다.",
        args_schema=EmailInput,
    ),
    StructuredTool.from_function(
        func=query_database,
        name="QueryDatabase",
        description="데이터베이스에서 데이터를 조회합니다. 테이블명과 컬럼명이 필요하며 조건은 선택사항입니다.",
        args_schema=DatabaseQuery,
    ),
    StructuredTool.from_function(
        func=file_operation,
        name="FileOperation",
        description="파일 작업(읽기/쓰기/삭제)을 수행합니다. 작업 유형과 파일명이 필요합니다.",
        args_schema=FileOperation,
    ),
]

# LangChain Hub에서 구조화된 채팅 에이전트 프롬프트 가져오기
prompt = hub.pull("hwchase17/structured-chat-agent")

# 또는 커스텀 프롬프트 정의
# prompt = ChatPromptTemplate.from_messages([
#     ("system", "당신은 도움이 되는 AI 어시스턴트입니다. 다음 도구들을 사용할 수 있습니다:\n\n{tools}\n\n"
#                "도구 이름: {tool_names}\n\n"
#                "JSON 형식으로 응답하세요."),
#     ("human", "{input}"),
#     ("assistant", "{agent_scratchpad}")
# ])

# 구조화된 채팅 에이전트 생성
agent = create_structured_chat_agent(
    llm=llm,  # 사용할 LLM
    tools=tools,  # 구조화된 도구 리스트
    prompt=prompt,  # 프롬프트 템플릿
)

# AgentExecutor로 에이전트 실행기 생성
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,  # 실행 과정 출력
    handle_parsing_errors=True,  # 파싱 오류 처리
    max_iterations=3,  # 최대 반복 횟수 제한
    return_intermediate_steps=False,  # 기본값은 False, 중간 단계 결과 반환 여부
)

# 구조화된 채팅 에이전트 실행
if __name__ == "__main__":
    # 복잡한 이메일 전송 요청
    result1 = agent_executor.invoke(
        {
            "input": "john@example.com에게 '프로젝트 업데이트'라는 제목으로 '이번 주 진행 상황을 공유드립니다.'라는 내용의 높은 우선순위 이메일을 보내주세요."
        }
    )
    print("결과 1:", result1["output"])

    # 데이터베이스 조회 요청
    result2 = agent_executor.invoke(
        {"input": "users 테이블에서 name과 email 컬럼을 조회해주세요."}
    )
    print("결과 2:", result2["output"])

    # 파일 작업 요청
    result3 = agent_executor.invoke(
        {"input": "test.txt 파일에 'Hello LangChain!'이라는 내용을 써주세요."}
    )
    print("결과 3:", result3["output"])
