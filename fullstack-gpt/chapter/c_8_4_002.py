from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

# ChatOllama 모델 초기화
chat_model = ChatOllama(model="mistral:latest")

# 시스템 메시지 설정 (선택사항)
system_message = SystemMessage(content="당신은 도움이 되는 AI 어시스턴트입니다.")

# 사용자 메시지 생성
user_message = HumanMessage(content="인공지능의 미래에 대해 간단히 설명해주세요.")

# 대화 실행
response = chat_model.invoke([system_message, user_message])

print("AI 응답:", response.content)

# 대화 계속하기
follow_up_message = HumanMessage(content="그렇다면 AI가 인간의 일자리를 대체할까요?")
follow_up_response = chat_model.invoke([system_message, user_message, response, follow_up_message])

print("\n추가 질문에 대한 AI 응답:", follow_up_response.content)

# 스트리밍 응답 받기
print("\n스트리밍 응답:")
for chunk in chat_model.stream("AI의 윤리적 사용에 대해 설명해주세요."):
    print(chunk.content, end="", flush=True)

