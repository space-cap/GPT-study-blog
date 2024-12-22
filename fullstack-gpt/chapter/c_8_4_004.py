from langchain_community.chat_models import ChatOllama
from langchain.schema import HumanMessage, SystemMessage

# ChatOllama 초기화
chat_model = ChatOllama(model="mistral:latest")

# 대화 생성
messages = [
    SystemMessage(content="당신은 도움이 되는 AI 어시스턴트입니다."),
    HumanMessage(content="LangChain에 대해 간단히 설명해주세요.")
]

response = chat_model(messages)

print("AI 응답:", response.content)
