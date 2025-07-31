# saju_chatbot/core/saju_analyzer.py

import json
import os


class SajuAnalyzer:
    def __init__(self, saju_rules_path="data/saju_rules.json"):
        self.gan_ohang = {  # 천간 오행
            "甲": "木",
            "乙": "木",
            "丙": "火",
            "丁": "火",
            "戊": "土",
            "己": "土",
            "庚": "金",
            "辛": "金",
            "壬": "水",
            "癸": "水",
        }
        self.ji_ohang = {  # 지지 오행
            "子": "水",
            "丑": "土",
            "寅": "木",
            "卯": "木",
            "辰": "土",
            "巳": "火",
            "午": "火",
            "未": "土",
            "申": "金",
            "酉": "金",
            "戌": "土",
            "亥": "水",
        }
        self.ji_janggan = {  # 지장간
            "子": ["壬", "癸"],
            "丑": ["己", "辛", "癸"],
            "寅": ["戊", "丙", "甲"],
            "卯": ["甲", "乙"],
            "辰": ["戊", "乙", "癸"],
            "巳": ["戊", "庚", "丙"],
            "午": ["丙", "己", "丁"],
            "未": ["丁", "乙", "己"],
            "申": ["戊", "壬", "庚"],
            "酉": ["庚", "辛"],
            "戌": ["戊", "辛", "丁"],
            "亥": ["戊", "甲", "壬"],
        }
        self.ohang_sangsaeng = {  # 오행 상생
            "木": "火",
            "火": "土",
            "土": "金",
            "金": "水",
            "水": "木",
        }
        self.ohang_sangguk = {  # 오행 상극
            "木": "土",
            "土": "水",
            "水": "火",
            "火": "金",
            "金": "木",
        }

        self.sipsung_rules = self._load_siju_rules(saju_rules_path)  # 십성 규칙 로드

    def _load_siju_rules(self, path):
        """사주 해석 규칙을 JSON 파일에서 로드합니다."""
        if not os.path.exists(path):
            print(f"Error: saju_rules.json not found at {path}. Please create it.")
            # 예시 데이터 생성 (실제 사용 시에는 상세한 데이터 필요)
            example_data = {
                "십성": {
                    "비견": {
                        "오행": "일간과 같은 오행",
                        "음양": "일간과 같은 음양",
                        "설명": "나와 같은 오행, 형제, 친구. 자존심, 독립성.",
                    },
                    "겁재": {
                        "오행": "일간과 같은 오행",
                        "음양": "일간과 다른 음양",
                        "설명": "경쟁자, 재물 경쟁, 투쟁심.",
                    },
                    # ... 모든 십성 정의
                },
                "신살": {
                    "도화살": {
                        "조건": "년지/일지 기준 자오묘유",
                        "설명": "이성에게 인기가 많고 매력적이다.",
                    },
                    # ... 모든 신살 정의
                },
                "오행설명": {
                    "木": "생장, 발전, 시작을 의미합니다. 인자하고 진취적인 성향이 있습니다.",
                    # ... 모든 오행 설명
                },
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(example_data, f, ensure_ascii=False, indent=4)
            return example_data
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def analyze_saju(self, saju_info: dict):
        """
        사주 정보를 바탕으로 오행, 십성, 신살 등을 분석합니다.
        """
        day_gan = saju_info["day_ganji"][0]  # 일간 (예: 丙寅의 丙)
        year_gan = saju_info["year_ganji"][0]
        month_gan = saju_info["month_ganji"][0]
        time_gan = saju_info["time_ganji"][0]

        year_ji = saju_info["year_ganji"][1]
        month_ji = saju_info["month_ganji"][1]
        day_ji = saju_info["day_ganji"][1]
        time_ji = saju_info["time_ganji"][1]

        # 1. 오행 분석
        ohang_counts = {}
        all_gans = [year_gan, month_gan, day_gan, time_gan]
        all_jis = [year_ji, month_ji, day_ji, time_ji]

        # 천간 오행
        for gan in all_gans:
            ohang = self.gan_ohang.get(gan)
            if ohang:
                ohang_counts[ohang] = ohang_counts.get(ohang, 0) + 1
        # 지지 오행 (본기 기준 또는 지장간 포함)
        for ji in all_jis:
            ohang = self.ji_ohang.get(ji)
            if ohang:
                ohang_counts[ohang] = ohang_counts.get(ohang, 0) + 1
        # TODO: 지장간 오행도 포함하여 더 정밀하게 계산

        # 2. 십성 분석 (일간 기준)
        sipsung_results = {}
        siju_mapping = {  # 사주팔자의 각 위치에 대한 십성 매핑 (개념적)
            "년주_천간": self._get_sipsung(day_gan, year_gan),
            "년주_지지": self._get_sipsung(
                day_gan, self.ji_ohang.get(year_ji)
            ),  # 지지의 본기 오행으로 십성
            "월주_천간": self._get_sipsung(day_gan, month_gan),
            "월주_지지": self._get_sipsung(day_gan, self.ji_ohang.get(month_ji)),
            "일주_천간": "비견/겁재 (일간 자신)",  # 일간은 십성 계산에서 제외
            "일주_지지": self._get_sipsung(day_gan, self.ji_ohang.get(day_ji)),
            "시주_천간": self._get_sipsung(day_gan, time_gan),
            "시주_지지": self._get_sipsung(day_gan, self.ji_ohang.get(time_ji)),
        }
        # 실제로는 각 십성의 개수, 강약 등을 계산해야 함.
        # 지장간 십성도 계산하여 포함.

        # 3. 신살 분석 (복잡하므로 예시는 간단히)
        sinsal_results = []
        if (day_ji in ["子", "午", "卯", "酉"]) or (
            year_ji in ["子", "午", "卯", "酉"]
        ):
            sinsal_results.append("도화살")
        # TODO: 더 많은 신살 로직 추가

        return {
            "ohang_counts": ohang_counts,
            "sipsung_results": siju_mapping,  # 실제로는 각 십성의 종합적 정보
            "sinsal_results": sinsal_results,
            "day_gan": day_gan,  # 일간은 중요하므로 포함
        }

    def _get_sipsung(self, ilgan: str, target: str):
        """일간과 대상 천간/오행의 십성을 계산합니다. (매우 간략화된 예시)"""
        # 일간의 오행
        ilgan_ohang = self.gan_ohang.get(ilgan)
        # 대상의 오행 (천간이거나 지지의 본기 오행)
        target_ohang = (
            self.gan_ohang.get(target) if target in self.gan_ohang else target
        )  # target이 천간이거나 오행

        # 일간의 음양
        ilgan_yinyang = self._get_yinyang(ilgan)
        # 대상의 음양
        target_yinyang = (
            self._get_yinyang(target) if target in self.gan_ohang else "양"
        )  # 임시

        # 십성 계산 로직 (매우 간략화)
        if ilgan_ohang == target_ohang:
            return "비견" if ilgan_yinyang == target_yinyang else "겁재"
        elif (
            self.ohang_sangsaeng.get(target_ohang) == ilgan_ohang
        ):  # 대상이 나를 생하는 경우 (인성)
            return "편인" if ilgan_yinyang != target_yinyang else "정인"
        elif (
            self.ohang_sangsaeng.get(ilgan_ohang) == target_ohang
        ):  # 내가 대상을 생하는 경우 (식상)
            return "식신" if ilgan_yinyang == target_yinyang else "상관"
        elif (
            self.ohang_sangguk.get(ilgan_ohang) == target_ohang
        ):  # 내가 대상을 극하는 경우 (재성)
            return "편재" if ilgan_yinyang != target_yinyang else "정재"
        elif (
            self.ohang_sangguk.get(target_ohang) == ilgan_ohang
        ):  # 대상이 나를 극하는 경우 (관성)
            return "편관" if ilgan_yinyang != target_yinyang else "정관"
        return "알 수 없음"

    def _get_yinyang(self, char: str):
        """천간/지지 음양 판단 (간략화)"""
        if char in ["甲", "丙", "戊", "庚", "壬", "子", "寅", "辰", "午", "申", "戌"]:
            return "양"
        elif char in ["乙", "丁", "己", "辛", "癸", "丑", "卯", "巳", "未", "酉", "亥"]:
            return "음"
        return ""


if __name__ == "__main__":
    analyzer = SajuAnalyzer()
    test_saju_info = {
        "year_ganji": "甲子",
        "month_ganji": "乙丑",
        "day_ganji": "丙寅",  # 일간이 丙 (병화, 양화)
        "time_ganji": "丁卯",
        "gan_list": ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"],
        "ji_list": [
            "子",
            "丑",
            "寅",
            "卯",
            "辰",
            "巳",
            "午",
            "未",
            "申",
            "酉",
            "戌",
            "亥",
        ],
    }
    analysis_result = analyzer.analyze_saju(test_saju_info)
    print("분석 결과:", analysis_result)
