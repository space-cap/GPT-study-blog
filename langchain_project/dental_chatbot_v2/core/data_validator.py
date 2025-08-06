"""
데이터 유효성 검증 모듈
사용자 입력 데이터의 형식과 유효성을 검증
"""

import re
import logging
from typing import Tuple, Dict, Any

logger = logging.getLogger(__name__)


class DataValidator:
    """데이터 유효성 검증 클래스"""

    def __init__(self):
        # 이름 유효성 검증 패턴 (한글 또는 영문, 2-10자)
        self.name_pattern = re.compile(r"^[가-힣a-zA-Z\s]{2,10}$")

        # 전화번호 유효성 검증 패턴 (010-0000-0000 형식)
        self.phone_patterns = [
            re.compile(r"^010-\d{4}-\d{4}$"),  # 하이픈 포함
            re.compile(r"^010\d{8}$"),  # 하이픈 없음
            re.compile(r"^01[016789]-\d{3,4}-\d{4}$"),  # 다른 통신사
            re.compile(r"^01[016789]\d{7,8}$"),  # 다른 통신사 하이픈 없음
        ]

    def validate_name(self, name: str) -> Tuple[bool, str]:
        """이름 유효성 검증"""
        if not name or not name.strip():
            return False, "이름을 입력해주세요."

        name = name.strip()

        if len(name) < 2:
            return False, "이름은 2자 이상 입력해주세요."

        if len(name) > 10:
            return False, "이름은 10자 이하로 입력해주세요."

        if not self.name_pattern.match(name):
            return False, "이름은 한글 또는 영문으로만 입력해주세요."

        logger.info(f"이름 유효성 검증 통과: {name}")
        return True, name

    def validate_phone(self, phone: str) -> Tuple[bool, str]:
        """전화번호 유효성 검증"""
        if not phone or not phone.strip():
            return False, "전화번호를 입력해주세요."

        phone = phone.strip().replace(" ", "")  # 공백 제거

        # 패턴 매칭 확인
        for pattern in self.phone_patterns:
            if pattern.match(phone):
                # 표준 형식으로 변환 (010-0000-0000)
                cleaned_phone = re.sub(r"[^\d]", "", phone)
                if len(cleaned_phone) == 11 and cleaned_phone.startswith("010"):
                    formatted_phone = (
                        f"{cleaned_phone[:3]}-{cleaned_phone[3:7]}-{cleaned_phone[7:]}"
                    )
                    logger.info(f"전화번호 유효성 검증 통과: {formatted_phone}")
                    return True, formatted_phone
                elif len(cleaned_phone) == 10 and cleaned_phone.startswith(
                    ("011", "016", "017", "018", "019")
                ):
                    formatted_phone = (
                        f"{cleaned_phone[:3]}-{cleaned_phone[3:6]}-{cleaned_phone[6:]}"
                    )
                    logger.info(f"전화번호 유효성 검증 통과: {formatted_phone}")
                    return True, formatted_phone
                elif len(cleaned_phone) == 11 and cleaned_phone.startswith(
                    ("011", "016", "017", "018", "019")
                ):
                    formatted_phone = (
                        f"{cleaned_phone[:3]}-{cleaned_phone[3:7]}-{cleaned_phone[7:]}"
                    )
                    logger.info(f"전화번호 유효성 검증 통과: {formatted_phone}")
                    return True, formatted_phone

        return False, "올바른 전화번호 형식이 아닙니다. (예: 010-1234-5678)"

    def validate_consent_response(self, response: str) -> Tuple[bool, bool]:
        """개인정보 수집 동의 응답 검증"""
        if not response or not response.strip():
            return False, False

        response = response.strip().lower()

        # 동의 표현들
        positive_responses = [
            "동의",
            "예",
            "yes",
            "y",
            "네",
            "좋습니다",
            "좋아요",
            "알겠습니다",
            "1",
        ]
        negative_responses = [
            "거부",
            "아니오",
            "no",
            "n",
            "아니요",
            "안됩니다",
            "거절",
            "2",
        ]

        # 부분 매칭 확인
        for pos in positive_responses:
            if pos in response:
                logger.info(f"개인정보 수집 동의: {response}")
                return True, True

        for neg in negative_responses:
            if neg in response:
                logger.info(f"개인정보 수집 거부: {response}")
                return True, False

        logger.warning(f"개인정보 동의 응답 불분명: {response}")
        return False, False

    def extract_personal_info_from_text(self, text: str) -> Dict[str, Any]:
        """텍스트에서 개인정보 추출 시도"""
        extracted = {"name": None, "phone": None}

        # 이름 추출 시도 (간단한 패턴)
        name_match = re.search(r"이름은?\s*([가-힣]{2,4})", text)
        if name_match:
            potential_name = name_match.group(1)
            is_valid, validated_name = self.validate_name(potential_name)
            if is_valid:
                extracted["name"] = validated_name

        # 전화번호 추출 시도
        phone_matches = re.findall(r"01[016789][\-\s]?\d{3,4}[\-\s]?\d{4}", text)
        for phone_match in phone_matches:
            is_valid, validated_phone = self.validate_phone(phone_match)
            if is_valid:
                extracted["phone"] = validated_phone
                break

        return extracted
