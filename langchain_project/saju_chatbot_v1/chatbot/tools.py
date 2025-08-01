# saju_chatbot/chatbot/tools.py

from langchain_core.tools import tool
from datetime import datetime
from core.saju_calculator import SajuCalculator
from core.saju_analyzer import SajuAnalyzer
from core.saju_interpreter import SajuInterpreter
from database.mysql_manager import MySQLManager
from database.chroma_manager import ChromaManager
from langchain_openai import ChatOpenAI
from config import OPENAI_API_KEY  # OpenAI API 키 로드

import json
from typing import Any


def serialize_safely(obj: Any) -> str:
    """객체를 안전하게 JSON 문자열로 직렬화합니다."""
    try:
        if hasattr(obj, "model_dump"):  # Pydantic v2
            return json.dumps(obj.model_dump(), ensure_ascii=False, default=str)
        elif hasattr(obj, "dict"):  # Pydantic v1
            return json.dumps(obj.dict(), ensure_ascii=False, default=str)
        elif isinstance(obj, dict):
            return json.dumps(obj, ensure_ascii=False, default=str)
        else:
            return json.dumps(str(obj), ensure_ascii=False)
    except Exception as e:
        # 직렬화 실패 시 안전한 fallback
        return json.dumps(
            {"error": True, "message": f"직렬화 오류: {str(e)}"},
            ensure_ascii=False,
        )


def make_serializable(obj: Any) -> Any:
    """객체를 직렬화 가능한 형태로 변환합니다."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, "model_dump"):
        return obj.model_dump()
    elif hasattr(obj, "dict"):
        return obj.dict()
    elif isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_serializable(item) for item in obj]
    else:
        return obj


# 전역 인스턴스 (어플리케이션 시작 시 한 번만 초기화)
saju_calculator = SajuCalculator()
saju_analyzer = SajuAnalyzer()
mysql_manager = MySQLManager()
chroma_manager = ChromaManager()
# LLM 초기화 (tool 내부에서 직접 접근하기 위함)
llm_for_tools = ChatOpenAI(model="gpt-4o", temperature=0.7, api_key=OPENAI_API_KEY)
saju_interpreter = SajuInterpreter()
saju_interpreter.set_llm(llm_for_tools)  # Interpreter에 LLM 주입


@tool
def calculate_and_analyze_saju(
    birth_year: int,
    birth_month: int,
    birth_day: int,
    birth_hour: int,
    is_lunar: bool = False,
    is_leap_month: bool = False,
) -> str:
    """
    주어진 생년월일시 (양력 또는 음력)를 바탕으로 사주팔자를 계산하고, 오행, 십성, 신살 등을 분석합니다.
    입력: birth_year (년), birth_month (월), birth_day (일), birth_hour (시), is_lunar (음력 여부, 기본값 False), is_leap_month (윤달 여부, 기본값 False)
    출력: 사주팔자 계산 결과 및 분석 결과 (딕셔너리 형태)
    """
    try:
        # 시간은 입력 시에 0-23시 기준으로 통일
        birth_datetime = datetime(birth_year, birth_month, birth_day, birth_hour, 0)

        # 1. 사주팔자 계산
        saju_info = saju_calculator.calculate_saju(
            birth_datetime, is_lunar, is_leap_month
        )

        # 2. 사주 분석
        analyzed_info = saju_analyzer.analyze_saju(saju_info)

        # 직렬화 가능한 형태로 변환
        result = {
            "saju_info": make_serializable(saju_info),
            "analyzed_info": make_serializable(analyzed_info),
        }

        return serialize_safely(result)
    except Exception as e:
        error_result = {
            "error": True,
            "message": f"사주 계산 및 분석 중 오류가 발생했습니다: {str(e)}",
        }
        return serialize_safely(error_result)


@tool
def get_saju_interpretation(analyzed_saju_info: dict = None, user_question: str = None) -> str:
    """
    분석된 사주 정보를 바탕으로 사용자에게 친절하고 상세한 사주 풀이를 제공합니다.
    추가적인 사용자 질문이 있다면 그에 대한 답변도 포함합니다.
    입력: analyzed_saju_info (사주 분석 결과 딕셔너리), user_question (사용자의 추가 질문, 선택 사항)
    출력: 사주 풀이 텍스트 (문자열)
    """
    try:
        # 사주 정보가 없는 경우 처리
        if not analyzed_saju_info:
            return "사주 해석을 위해서는 먼저 생년월일시 정보가 필요합니다. 태어난 연도, 월, 일, 시간을 알려주세요."
        
        # Interpreter는 이미 LLM을 가지고 있으므로 바로 호출
        interpretation = saju_interpreter.interpret_saju(
            analyzed_saju_info, user_question
        )
        return interpretation
    except Exception as e:
        return f"사주 해석 중 오류가 발생했습니다: {e}"


@tool
def retrieve_saju_knowledge(query: str) -> str:
    """
    사주 관련 질문에 대해 ChromaDB에서 관련 지식을 검색하여 제공합니다.
    입력: query (검색할 질문 또는 키워드)
    출력: 검색된 관련 지식 문서 내용 (문자열)
    """
    try:
        docs = chroma_manager.retrieve_knowledge(query, k=5)  # 상위 5개 문서 검색
        if not docs:
            return "죄송합니다, 해당 질문에 대한 사주 지식을 찾을 수 없습니다."

        # 검색된 문서 내용을 하나의 문자열로 결합
        knowledge_summary = "\n\n".join([doc.page_content for doc in docs])
        return knowledge_summary
    except Exception as e:
        return f"사주 지식 검색 중 오류가 발생했습니다: {e}"


@tool
def save_user_session_data(
    session_id: str,
    user_id: str,
    birth_year: int = None,
    birth_month: int = None,
    birth_day: int = None,
    birth_hour: int = None,
    is_lunar: bool = None,
    is_leap_month: bool = None,
) -> str:
    """
    사용자의 세션 데이터를 MySQL에 저장하거나 업데이트합니다.
    주로 생년월일시와 같은 사주 계산에 필요한 정보를 저장하는 데 사용됩니다.
    입력: session_id, user_id, birth_year, birth_month, birth_day, birth_hour, is_lunar, is_leap_month
    출력: 성공 여부 및 메시지
    """
    try:
        birth_datetime = None
        if all(
            arg is not None for arg in [birth_year, birth_month, birth_day, birth_hour]
        ):
            birth_datetime = datetime(birth_year, birth_month, birth_day, birth_hour, 0)

        mysql_manager.save_user_session(
            session_id, user_id, birth_datetime, is_lunar, is_leap_month
        )
        result = {
            "status": "success",
            "message": "사용자 세션 정보가 성공적으로 저장되었습니다.",
        }
        return serialize_safely(result)
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"사용자 세션 정보 저장 중 오류 발생: {str(e)}",
        }
        return serialize_safely(error_result)


@tool
def get_user_session_data(session_id: str) -> str:
    """
    MySQL에서 주어진 세션 ID에 해당하는 사용자 세션 데이터를 조회합니다.
    입력: session_id
    출력: 사용자 세션 데이터 (딕셔너리 형태) 또는 None
    """
    try:
        session_data = mysql_manager.get_user_session(session_id)
        if session_data:
            # 안전한 직렬화 처리
            serializable_data = make_serializable(session_data)
            result = {"status": "success", "data": serializable_data}
        else:
            result = {
                "status": "not_found",
                "message": f"세션 ID {session_id}에 해당하는 데이터가 없습니다.",
            }

        return serialize_safely(result)
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"세션 데이터 조회 중 오류 발생: {str(e)}",
        }
        return serialize_safely(error_result)


# 모든 도구들을 리스트로 묶어 LangGraph에서 사용
tools = [
    calculate_and_analyze_saju,
    get_saju_interpretation,
    retrieve_saju_knowledge,
    save_user_session_data,
    get_user_session_data,
]
