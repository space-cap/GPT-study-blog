from dotenv import load_dotenv
import os

load_dotenv()

from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-4o-mini")

model.invoke("Hello, world!")
