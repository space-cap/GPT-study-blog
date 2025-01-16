import google.generativeai as genai
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

# 환경 변수 가져오기
gemini_api_key = os.getenv("Gemini_API_KEY")

# API 키 설정
genai.configure(api_key=gemini_api_key)

# 모델 생성
model = genai.GenerativeModel('gemini-1.5-flash')

# 투자 조언을 위한 프롬프트 설정
investment_prompt = """
당신은 투자 조언을 제공하는 AI 어시스턴트입니다. 사용자가 제공하는 공개 거래 회사에 대한 정보를 바탕으로 연구를 수행하고, 해당 주식을 매수해야 할지에 대한 조언을 제공합니다.

지시사항:
1. 사용자가 제공하는 회사 정보를 분석하세요.
2. 해당 회사의 재무 상태, 시장 동향, 경쟁 환경 등을 고려하세요.
3. 투자 위험과 잠재적 수익을 평가하세요.
4. 사용자에게 해당 주식 매수 여부에 대한 조언을 제공하세요.
5. 항상 투자에는 위험이 따른다는 점을 언급하세요.

사용자의 질문: {user_question}
"""

# 사용자 질문에 대한 응답 생성 함수
def get_investment_advice(user_question):
    response = model.generate_content(investment_prompt.format(user_question=user_question))
    return response.text

# 사용 예시
user_query = "애플(AAPL) 주식을 지금 사야 할까요?"
advice = get_investment_advice(user_query)
print(advice)
