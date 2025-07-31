# saju_chatbot/core/saju_interpreter.py

import json
import os

class SajuInterpreter:
    def __init__(self, saju_rules_path='data/saju_rules.json', saju_terms_path='data/saju_terms.json'):
        self.rules = self._load_rules(saju_rules_path)
        self.terms = self._load_terms(saju_terms_path)
        self.llm = None # LangChain LLM (나중에 주입)

    def _load_rules(self, path):
        if not os.path.exists(path):
            print(f"Error: saju_rules.json not found at {path}. Please create it with detailed rules.")
            return {} # 실제로는 오류 처리 또는 기본값
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_terms(self, path):
        if not os.path.exists(path):
            print(f"Error: saju_terms.json not found at {path}. Please create it.")
            return {}
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def set_llm(self, llm):
        """외부에서 LangChain LLM을 주입합니다."""
        self.llm = llm

    def interpret_saju(self, analyzed_saju: dict, user_question: str = None) -> str:
        """
        분석된 사주 정보를 바탕으로 사용자에게 친화적인 해석을 제공합니다.
        LLM을 활용하여 보다 자연스럽고 풍부한 답변을 생성합니다.
        """
        if not self.llm:
            return "LLM이 설정되지 않았습니다. 챗봇 초기화 시 LLM을 설정해주세요."

        ohang_counts = analyzed_saju.get("ohang_counts", {})
        sipsung_results = analyzed_saju.get("sipsung_results", {})
        sinsal_results = analyzed_saju.get("sinsal_results", [])
        day_gan = analyzed_saju.get("day_gan", "")

        interpretation_parts = []

        # 1. 오행 설명
        ohang_summary = "당신의 사주에 나타난 오행의 분포는 다음과 같습니다: "
        for ohang, count in ohang_counts.items():
            ohang_summary += f"{self.terms['오행'].get(ohang, ohang)} {count}개, "
        ohang_summary = ohang_summary.strip(', ') + ". "
        interpretation_parts.append(ohang_summary)
        
        # 각 오행별 설명 추가
        for ohang, count in ohang_counts.items():
            if ohang in self.rules.get('오행설명', {}):
                interpretation_parts.append(f"{self.terms['오행'].get(ohang)}은(는) {self.rules['오행설명'][ohang]} 기운입니다.")

        # 2. 일간 설명
        if day_gan and day_gan in self.rules.get('일간설명', {}):
            interpretation_parts.append(f"당신의 일간은 '{self.terms['천간'].get(day_gan, day_gan)}'입니다. 이는 {self.rules['일간설명'][day_gan]} 성향을 가집니다.")
        elif day_gan:
            interpretation_parts.append(f"당신의 일간은 '{self.terms['천간'].get(day_gan, day_gan)}'입니다.")

        # 3. 십성 설명 (각 위치별 십성 표시)
        sipsung_summary = "사주팔자 각 기둥별 십성은 다음과 같습니다: "
        for k, v in sipsung_results.items():
            sipsung_summary += f"{k.replace('_', ' ')}에 {self.terms['십성'].get(v, v)}, "
        sipsung_summary = sipsung_summary.strip(', ') + "."
        interpretation_parts.append(sipsung_summary)

        # 4. 신살 설명
        if sinsal_results:
            sinsal_text = "또한 당신의 사주에는 다음과 같은 신살(神殺)이 보입니다: "
            for sinsal in sinsal_results:
                if sinsal in self.rules.get('신살', {}):
                    sinsal_text += f"{self.terms['신살'].get(sinsal, sinsal)} ({self.rules['신살'][sinsal]['설명']}), "
            sinsal_text = sinsal_text.strip(', ') + "."
            interpretation_parts.append(sinsal_text)
        
        # LLM에게 최종 해석을 요청할 프롬프트 구성
        base_prompt = "다음 사주 분석 결과를 바탕으로 고객에게 친절하고 상세하게 사주를 풀이해주세요. " \
                      "사주 용어는 너무 어렵지 않게 설명해주시고, 긍정적인 방향으로 해석해주세요.\n\n"
        
        analysis_text = "\n".join(interpretation_parts)
        
        # 사용자 질문이 있다면 추가
        if user_question:
            base_prompt += f"고객의 추가 질문: '{user_question}'도 답변에 포함해주세요.\n\n"

        prompt_with_analysis = base_prompt + "--- 사주 분석 결과 ---\n" + analysis_text + "\n--------------------"

        try:
            # LLM을 호출하여 최종 답변 생성
            response = self.llm.invoke(prompt_with_analysis)
            return response.content
        except Exception as e:
            print(f"LLM 호출 중 오류 발생: {e}")
            return "사주 해석 중 오류가 발생했습니다. 다시 시도해주세요."

if __name__ == "__main__":
    # 테스트를 위한 임시 LLM 설정 (실제로는 ChatOpenAI 사용)
    class MockLLM:
        def invoke(self, prompt):
            return type('MockResponse', (object,), {'content': f"Mock LLM Response for: {prompt}"})()

    interpreter = SajuInterpreter()
    interpreter.set_llm(MockLLM()) # 임시 Mock LLM 주입

    test_analyzed_saju = {
        "ohang_counts": {"木": 2, "火": 1, "土": 3, "金": 1, "水": 1},
        "sipsung_results": {
            "년주_천간": "편인", "년주_지지": "정재",
            "월주_천간": "정관", "월주_지지": "식신",
            "일주_천간": "비견/겁재 (일간 자신)", "일주_지지": "편재",
            "시주_천간": "정재", "시주_지지": "상관"
        },
        "sinsal_results": ["도화살", "역마살"],
        "day_gan": "丙"
    }
    
    # 임시 rules.json에 일간설명 추가
    example_rules = {
        "일간설명": {
            "丙": "양의 불 기운으로, 열정적이고 활동적이며 솔직한 성향을 가집니다."
        },
        "오행설명": {
            "木": "생장, 발전, 시작을 의미합니다. 인자하고 진취적인 성향이 있습니다.",
            "火": "열정, 활동, 빛을 의미합니다. 명랑하고 예의 바른 성향이 있습니다.",
            "土": "중용, 안정, 신뢰를 의미합니다. 포용력 있고 인내심 강한 성향이 있습니다.",
            "金": "정의, 의리, 결실을 의미합니다. 냉철하고 단호한 성향이 있습니다.",
            "水": "지혜, 유연, 비밀을 의미합니다. 총명하고 융통성 있는 성향이 있습니다."
        },
        "십성": {}, # analyzer와 동일하게 십성 정의 필요
        "신살": {
            "도화살": {"조건": "", "설명": "이성에게 인기가 많고 매력적이다."},
            "역마살": {"조건": "", "설명": "이동과 변화를 즐기며 역동적인 삶을 삽니다."}
        }
    }
    with open('data/saju_rules.json', 'w', encoding='utf-8') as f:
        json.dump(example_rules, f, ensure_ascii=False, indent=4)


    interpretation = interpreter.interpret_saju(test_analyzed_saju, user_question="제 직업운은 어떤가요?")
    print("\n--- 사주 해석 ---")
    print(interpretation)
    print("--------------------")
