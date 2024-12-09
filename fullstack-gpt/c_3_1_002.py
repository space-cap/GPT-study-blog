from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI

chat = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

from langchain.schema import HumanMessage, AIMessage, SystemMessage

messages = [
    SystemMessage(
        content="You are a geography expert. And you only reply in Italian.",
    ),
    AIMessage(content="Ciao, mi chiamo Paolo!"),
    HumanMessage(content="What is the distance between Mexico and Thailand. Also, what is your name?")
]

response = chat.invoke(messages)
print(response.content)
