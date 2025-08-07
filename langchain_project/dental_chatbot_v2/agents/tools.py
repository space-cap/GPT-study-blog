"""
LangGraph 에이전트에서 사용할 도구들 정의
"""

import json
import logging
from typing import Dict, Any, List, Optional
from langchain.tools import BaseTool
from core.vector_store import VectorStoreManager
from core.session_manager import SessionManager
from core.data_validator import DataValidator
from core.database import DatabaseManager

logger = logging.getLogger(__name__)


class VectorSearchTool(BaseTool):
    """벡터 검색 도구"""

    name: str = "vector_search"
    description: str = "병원 정보나 치료 정보를 검색합니다."

    # ✅ 수정: Pydantic 필드로 정의
    vector_manager: Optional[VectorStoreManager] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # ✅ 수정: object.__setattr__ 사용
        object.__setattr__(self, "vector_manager", VectorStoreManager())

    def _run(self, query: str, search_type: str = "general") -> str:
        """벡터 검색 실행"""
        try:
            if search_type == "hospital":
                results = self.vector_manager.search_hospital_info(query)
            elif search_type == "treatment":
                results = self.vector_manager.search_treatment_prices(query)
            else:
                results = self.vector_manager.search_similar(query)

            if not results:
                return "관련 정보를 찾을 수 없습니다."

            context = []
            for doc in results:
                context.append(
                    {
                        "content": doc.page_content,
                        "source": doc.metadata.get("source", ""),
                        "category": doc.metadata.get("category", ""),
                    }
                )

            return json.dumps(context, ensure_ascii=False)

        except Exception as e:
            logger.error(f"벡터 검색 오류: {e}")
            return "검색 중 오류가 발생했습니다."


class IntentClassificationTool(BaseTool):
    """사용자 의도 분류 도구"""

    name: str = "classify_intent"
    description: str = "사용자 메시지의 의도를 분류합니다."

    def _run(self, user_message: str) -> Dict[str, Any]:
        """의도 분류 실행"""
        # 간단한 키워드 기반 의도 분류
        message = user_message.lower()

        if any(word in message for word in ["안녕", "안녕하세요", "처음", "반갑"]):
            return {
                "intent": "greeting",
                "confidence": 0.9,
                "extracted_keywords": ["인사"],
                "requires_personal_info": False,
            }
        elif any(
            word in message for word in ["위치", "주소", "찾아가", "어디", "오시는길"]
        ):
            return {
                "intent": "hospital_info",
                "confidence": 0.8,
                "extracted_keywords": ["위치", "주소"],
                "requires_personal_info": False,
            }
        elif any(word in message for word in ["가격", "비용", "얼마", "요금"]):
            return {
                "intent": "price_inquiry",
                "confidence": 0.8,
                "extracted_keywords": ["가격", "비용"],
                "requires_personal_info": False,
            }
        elif any(word in message for word in ["예약", "상담", "진료", "치료받고싶"]):
            return {
                "intent": "appointment_request",
                "confidence": 0.9,
                "extracted_keywords": ["예약", "상담"],
                "requires_personal_info": True,
            }
        else:
            return {
                "intent": "general_question",
                "confidence": 0.6,
                "extracted_keywords": [],
                "requires_personal_info": False,
            }


class DataValidationTool(BaseTool):
    """데이터 유효성 검증 도구"""

    name: str = "validate_data"
    description: str = "사용자 입력 데이터의 유효성을 검증합니다."

    # ✅ 수정: Pydantic 필드로 정의
    validator: Optional[DataValidator] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # ✅ 수정: object.__setattr__ 사용
        object.__setattr__(self, "validator", DataValidator())

    def _run(self, data_type: str, data_value: str) -> Dict[str, Any]:
        """데이터 유효성 검증 실행"""
        try:
            if data_type == "name":
                is_valid, result = self.validator.validate_name(data_value)
            elif data_type == "phone":
                is_valid, result = self.validator.validate_phone(data_value)
            elif data_type == "consent":
                is_valid, result = self.validator.validate_consent_response(data_value)
            else:
                return {
                    "is_valid": False,
                    "message": "지원하지 않는 데이터 타입입니다.",
                }

            return {
                "is_valid": is_valid,
                "validated_data": result if is_valid else None,
                "message": result if not is_valid else "유효한 데이터입니다.",
            }

        except Exception as e:
            logger.error(f"데이터 검증 오류: {e}")
            return {"is_valid": False, "message": "검증 중 오류가 발생했습니다."}


class DatabaseTool(BaseTool):
    """데이터베이스 작업 도구"""

    name: str = "database_operation"
    description: str = "데이터베이스에 고객 정보를 저장합니다."

    # ✅ 수정: Pydantic 필드로 정의
    db_manager: Optional[DatabaseManager] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # ✅ 수정: object.__setattr__ 사용
        object.__setattr__(self, "db_manager", DatabaseManager())

    def _run(self, operation: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """데이터베이스 작업 실행"""
        try:
            if operation == "save_customer":
                success = self.db_manager.save_customer_info(data)
                return {
                    "success": success,
                    "message": (
                        "고객 정보가 저장되었습니다."
                        if success
                        else "저장 중 오류가 발생했습니다."
                    ),
                }
            else:
                return {"success": False, "message": "지원하지 않는 작업입니다."}

        except Exception as e:
            logger.error(f"데이터베이스 작업 오류: {e}")
            return {"success": False, "message": "데이터베이스 오류가 발생했습니다."}


# 도구 인스턴스 생성
vector_search_tool = VectorSearchTool()
intent_classification_tool = IntentClassificationTool()
data_validation_tool = DataValidationTool()
database_tool = DatabaseTool()

# 도구 리스트 (LangGraph에서 사용)
AVAILABLE_TOOLS = [
    vector_search_tool,
    intent_classification_tool,
    data_validation_tool,
    database_tool,
]
