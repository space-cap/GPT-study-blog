"""
LangGraph 워크플로우의 노드 함수들
각 노드는 대화 상태를 받아 처리하고 업데이트된 상태를 반환
"""

import json
import logging
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from agents.state import ConversationState
from agents.tools import (
    vector_search_tool,
    intent_classification_tool,
    data_validation_tool,
    database_tool,
)
from core.session_manager import SessionManager
from prompts.base_prompts import (
    SYSTEM_PROMPT,
    HOSPITAL_INFO_PROMPT,
    PRICE_INFO_PROMPT,
    GENERAL_CHAT_PROMPT,
)
from prompts.context_prompts import (
    INTENT_CLASSIFICATION_PROMPT,
    CONTEXT_AWARE_RESPONSE_PROMPT,
)
from prompts.consent_prompts import (
    CONSENT_EXPLANATION_PROMPT,
    PERSONAL_INFO_COLLECTION_PROMPT,
    VALIDATION_FEEDBACK_PROMPT,
)
from config import Config

logger = logging.getLogger(__name__)

# LLM 초기화
config = Config()
llm = ChatOpenAI(
    model=config.OPENAI_MODEL,
    temperature=config.OPENAI_TEMPERATURE,
    api_key=config.OPENAI_API_KEY,
)

session_manager = SessionManager()


def analyze_intent_node(state: ConversationState) -> ConversationState:
    """사용자 의도 분석 노드"""
    try:
        # 의도 분류 도구 사용
        intent_result = intent_classification_tool._run(state["user_message"])

        # 더 정확한 의도 분석을 위해 LLM도 활용
        prompt = INTENT_CLASSIFICATION_PROMPT.format(user_message=state["user_message"])
        response = llm.invoke([HumanMessage(content=prompt)])

        try:
            llm_result = json.loads(response.content)
            # LLM 결과와 도구 결과를 조합
            state["intent"] = llm_result.get("intent", intent_result["intent"])
            state["confidence"] = max(
                llm_result.get("confidence", 0), intent_result["confidence"]
            )
            state["extracted_keywords"] = list(
                set(
                    llm_result.get("extracted_keywords", [])
                    + intent_result["extracted_keywords"]
                )
            )
            state["requires_personal_info"] = llm_result.get(
                "requires_personal_info", intent_result["requires_personal_info"]
            )
        except:
            # LLM 결과 파싱 실패 시 도구 결과 사용
            state.update(intent_result)

        # 세션 업데이트
        session_manager.update_session(
            state["session_id"],
            {"intent": state["intent"], "conversation_stage": "intent_analyzed"},
        )

        logger.info(f"의도 분석 완료: {state['intent']}")
        return state

    except Exception as e:
        logger.error(f"의도 분석 오류: {e}")
        state["error_message"] = "의도 분석 중 오류가 발생했습니다."
        return state


def search_information_node(state: ConversationState) -> ConversationState:
    """정보 검색 노드"""
    try:
        search_type = "general"
        if state["intent"] == "hospital_info":
            search_type = "hospital"
        elif state["intent"] == "price_inquiry":
            search_type = "treatment"

        # 벡터 검색 실행
        search_results = vector_search_tool._run(state["user_message"], search_type)
        state["retrieved_context"] = search_results

        # 검색 결과를 파싱하여 구조화
        try:
            parsed_results = json.loads(search_results)
            state["search_results"] = parsed_results
        except:
            state["search_results"] = []

        logger.info(f"정보 검색 완료: {len(state['search_results'])}개 결과")
        return state

    except Exception as e:
        logger.error(f"정보 검색 오류: {e}")
        state["error_message"] = "정보 검색 중 오류가 발생했습니다."
        return state


def generate_response_node(state: ConversationState) -> ConversationState:
    """응답 생성 노드"""
    try:
        session_data = session_manager.get_session(state["session_id"])
        chat_history = session_manager.get_chat_history(state["session_id"])

        # 의도별 적절한 프롬프트 선택
        if state["intent"] == "hospital_info" and state["search_results"]:
            prompt = HOSPITAL_INFO_PROMPT.format(
                context=state["retrieved_context"], question=state["user_message"]
            )
        elif state["intent"] == "price_inquiry" and state["search_results"]:
            prompt = PRICE_INFO_PROMPT.format(
                price_info=state["retrieved_context"], question=state["user_message"]
            )
        else:
            # 컨텍스트 인식 응답 생성
            prompt = CONTEXT_AWARE_RESPONSE_PROMPT.format(
                intent=state["intent"],
                conversation_stage=session_data["conversation_stage"],
                collected_info=json.dumps(
                    session_data["collected_info"], ensure_ascii=False
                ),
                consent_status=session_data["consent_given"],
                retrieved_context=state["retrieved_context"],
                user_message=state["user_message"],
                chat_history=chat_history,
            )

        # LLM을 통한 응답 생성
        response = llm.invoke([HumanMessage(content=prompt)])
        state["bot_response"] = response.content

        # 대화 히스토리에 추가
        session_manager.add_message_to_history(
            state["session_id"], "user", state["user_message"]
        )
        session_manager.add_message_to_history(
            state["session_id"], "bot", state["bot_response"]
        )

        logger.info(f"응답 생성 완료: {state['session_id']}")
        return state

    except Exception as e:
        logger.error(f"응답 생성 오류: {e}")
        state["bot_response"] = (
            "죄송합니다. 시스템 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        )
        return state


def handle_consent_node(state: ConversationState) -> ConversationState:
    """개인정보 수집 동의 처리 노드"""
    try:
        session_data = session_manager.get_session(state["session_id"])

        if not session_data["consent_given"]:
            # 동의 안내 메시지 생성
            prompt = CONSENT_EXPLANATION_PROMPT.format(
                user_message=state["user_message"]
            )
            response = llm.invoke([HumanMessage(content=prompt)])
            state["bot_response"] = response.content

            # 대화 단계 업데이트
            session_manager.update_session(
                state["session_id"], {"conversation_stage": "consent_request"}
            )
        else:
            # 이미 동의를 받은 경우 개인정보 수집 단계로
            state["conversation_stage"] = "info_collection"

        logger.info(f"동의 처리: {state['session_id']}")
        return state

    except Exception as e:
        logger.error(f"동의 처리 오류: {e}")
        state["error_message"] = "동의 처리 중 오류가 발생했습니다."
        return state


def collect_personal_info_node(state: ConversationState) -> ConversationState:
    """개인정보 수집 노드"""
    try:
        session_data = session_manager.get_session(state["session_id"])
        collected_info = session_data["collected_info"]

        # 동의 응답 처리
        if session_data["conversation_stage"] == "consent_request":
            validation_result = data_validation_tool._run(
                "consent", state["user_message"]
            )

            if validation_result["is_valid"]:
                if validation_result["validated_data"]:  # 동의
                    session_manager.update_session(
                        state["session_id"],
                        {
                            "consent_given": True,
                            "consent_timestamp": datetime.now().isoformat(),
                            "conversation_stage": "info_collection",
                        },
                    )
                    state["bot_response"] = (
                        "개인정보 수집에 동의해주셔서 감사합니다. 이제 상담을 위해 기본 정보를 수집하겠습니다.\n\n먼저 성함을 알려주시겠어요?"
                    )
                else:  # 거부
                    state["bot_response"] = (
                        "개인정보 수집에 동의하지 않으시는군요. 그렇다면 일반적인 병원 정보나 진료 안내는 언제든 도와드릴 수 있습니다. 다른 궁금한 점이 있으시면 말씀해주세요!"
                    )
                    session_manager.update_session(
                        state["session_id"], {"conversation_stage": "general_inquiry"}
                    )
            else:
                state["bot_response"] = (
                    "동의 여부를 명확히 말씀해주시겠어요? '동의합니다' 또는 '동의하지 않습니다'로 답변해주세요."
                )

        # 이름 수집
        elif not collected_info["name"]:
            if state["user_message"].strip():
                validation_result = data_validation_tool._run(
                    "name", state["user_message"]
                )

                if validation_result["is_valid"]:
                    session_manager.update_session(
                        state["session_id"],
                        {
                            "collected_info": {
                                "name": validation_result["validated_data"]
                            },
                            "conversation_stage": "collect_phone",
                        },
                    )
                    state["bot_response"] = (
                        f"{validation_result['validated_data']}님, 만나서 반갑습니다! 이제 연락처를 알려주시겠어요? (예: 010-1234-5678)"
                    )
                else:
                    prompt = VALIDATION_FEEDBACK_PROMPT.format(
                        input_type="name",
                        user_input=state["user_message"],
                        validation_result=validation_result["message"],
                    )
                    response = llm.invoke([HumanMessage(content=prompt)])
                    state["bot_response"] = response.content
            else:
                state["bot_response"] = "성함을 입력해주세요."

        # 전화번호 수집
        elif not collected_info["phone"]:
            validation_result = data_validation_tool._run(
                "phone", state["user_message"]
            )

            if validation_result["is_valid"]:
                session_manager.update_session(
                    state["session_id"],
                    {
                        "collected_info": {
                            "phone": validation_result["validated_data"]
                        },
                        "conversation_stage": "info_complete",
                    },
                )

                # 수집 완료 메시지
                name = (
                    collected_info["name"]
                    if collected_info["name"]
                    else session_manager.get_session(state["session_id"])[
                        "collected_info"
                    ]["name"]
                )
                state["bot_response"] = (
                    f"{name}님의 연락처가 등록되었습니다.\n\n상담 신청이 완료되었으며, 곧 담당자가 연락드릴 예정입니다. 추가로 궁금한 사항이나 특별히 상담받고 싶은 내용이 있으시면 말씀해주세요!"
                )

                # 데이터베이스에 저장
                customer_data = {
                    "name": name,
                    "phone": validation_result["validated_data"],
                    "consent_date": session_data.get(
                        "consent_timestamp", datetime.now().isoformat()
                    ),
                    "symptoms": (
                        state["user_message"]
                        if len(state["user_message"]) > 20
                        else None
                    ),
                }

                db_result = database_tool._run("save_customer", customer_data)
                if not db_result["success"]:
                    logger.error(f"고객 정보 저장 실패: {state['session_id']}")
            else:
                prompt = VALIDATION_FEEDBACK_PROMPT.format(
                    input_type="phone",
                    user_input=state["user_message"],
                    validation_result=validation_result["message"],
                )
                response = llm.invoke([HumanMessage(content=prompt)])
                state["bot_response"] = response.content

        # 추가 정보 수집 (선택사항)
        else:
            state["bot_response"] = (
                "감사합니다! 다른 궁금한 사항이 있으시면 언제든 말씀해주세요."
            )
            session_manager.update_session(
                state["session_id"], {"conversation_stage": "completed"}
            )

        logger.info(f"개인정보 수집 처리: {state['session_id']}")
        return state

    except Exception as e:
        logger.error(f"개인정보 수집 오류: {e}")
        state["error_message"] = "개인정보 수집 중 오류가 발생했습니다."
        return state


# def route_conversation_node(state: ConversationState) -> str:
#     """대화 라우팅 노드 - 다음 노드 결정"""
#     try:
#         session_data = session_manager.get_session(state["session_id"])

#         # 오류가 있으면 일반 응답으로
#         if state.get("error_message"):
#             return "generate_response"

#         # 의도가 없으면 의도 분석으로
#         if not state.get("intent"):
#             return "analyze_intent"

#         # 예약 요청이고 동의가 필요한 경우
#         if state["intent"] == "appointment_request" or state["requires_personal_info"]:
#             if not session_data["consent_given"]:
#                 return "handle_consent"
#             else:
#                 return "collect_personal_info"

#         # 동의 과정 중이면 개인정보 수집으로
#         if session_data["conversation_stage"] in [
#             "consent_request",
#             "info_collection",
#             "collect_phone",
#         ]:
#             return "collect_personal_info"

#         # 정보 검색이 필요한 경우
#         if state["intent"] in ["hospital_info", "price_inquiry", "treatment_info"]:
#             return "search_information"

#         # 기본적으로 응답 생성
#         return "generate_response"

#     except Exception as e:
#         logger.error(f"라우팅 오류: {e}")
#         return "generate_response"
