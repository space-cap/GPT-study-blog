from dotenv import load_dotenv
import os

load_dotenv()

from langchain_openai import ChatOpenAI

chat = ChatOpenAI(temperature=0.1)

from langchain.schema import HumanMessage, AIMessage, SystemMessage

messages = [
    SystemMessage(
        content="You are a geography expert. And you only reply in Italian.",
    ),
    AIMessage(content="Ciao, mi chiamo Paolo!"),
    HumanMessage(content="What is the distance between Mexico and Thailand. Also, what is your name?")
]
