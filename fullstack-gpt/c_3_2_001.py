from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI

chat = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.prompts import PromptTemplate, ChatPromptTemplate

template = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a geography expert. And you only reply in Italian."),
        ("ai", "Ciao, mi chiamo Paolo!"),
        ("human", "What is the distance between Mexico and Thailand. Also, what is your name?")
    ]
)

prompt = template.format(country_a="Seoul", country_b="Tokyo")

response = chat.invoke(prompt)
print(response.content)
