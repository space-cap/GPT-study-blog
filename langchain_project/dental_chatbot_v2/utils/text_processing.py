"""
텍스트 처리 유틸리티 함수들
"""

import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """텍스트 정리 (공백, 특수문자 등)"""
    if not text:
        return ""

    # 불필요한 공백 제거
    text = re.sub(r"\s+", " ", text.strip())

    # 특수 문자 정리 (기본적인 문장 부호는 유지)
    text = re.sub(r"[^\w\s가-힣.,!?()-]", "", text)

    return text


def extract_keywords(text: str, min_length: int = 2) -> List[str]:
    """텍스트에서 키워드 추출"""
    if not text:
        return []

    # 한글 단어 추출
    korean_words = re.findall(r"[가-힣]{2,}", text)

    # 영어 단어 추출
    english_words = re.findall(r"[a-zA-Z]{2,}", text)

    # 길이 필터링
    keywords = [
        word for word in korean_words + english_words if len(word) >= min_length
    ]

    # 중복 제거
    return list(set(keywords))


def format_price(price: int) -> str:
    """가격 포맷팅 (천 단위 콤마)"""
    return f"{price:,}원"


def truncate_text(text: str, max_length: int = 100) -> str:
    """텍스트 길이 제한"""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def is_question(text: str) -> bool:
    """질문 문장인지 판단"""
    question_indicators = [
        "?",
        "인가",
        "인지",
        "나요",
        "까요",
        "어디",
        "언제",
        "무엇",
        "어떻게",
        "왜",
        "얼마",
    ]
    return any(indicator in text for indicator in question_indicators)


def format_conversation_history(
    messages: List[Dict[str, Any]], max_messages: int = 5
) -> str:
    """대화 히스토리 포맷팅"""
    if not messages:
        return "대화 히스토리가 없습니다."

    recent_messages = messages[-max_messages:]
    formatted = []

    for msg in recent_messages:
        role = "사용자" if msg.get("role") == "user" else "상담사"
        message = msg.get("message", "")
        formatted.append(f"{role}: {message}")

    return "\n".join(formatted)


def extract_phone_number(text: str) -> str:
    """텍스트에서 전화번호 추출"""
    phone_patterns = [
        r"01[016789][\-\s]?\d{3,4}[\-\s]?\d{4}",
        r"010\d{8}",
        r"01[016789]\d{7,8}",
    ]

    for pattern in phone_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group()

    return ""


def normalize_phone_number(phone: str) -> str:
    """전화번호 정규화 (010-0000-0000 형식)"""
    # 숫자만 추출
    digits = re.sub(r"[^\d]", "", phone)

    if len(digits) == 11 and digits.startswith("010"):
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    elif len(digits) == 10:
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"

    return phone
