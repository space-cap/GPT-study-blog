from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI

chat = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.prompts import PromptTemplate, ChatPromptTemplate

template = PromptTemplate.from_template(
    "What is the distance between {country_a} and {country_b}.",
)

prompt = template.format(country_a="Mexico", country_b="Thailand")

response = chat.invoke(prompt)
print(response.content)
