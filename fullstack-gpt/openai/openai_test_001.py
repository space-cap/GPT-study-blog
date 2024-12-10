from dotenv import load_dotenv
import os

load_dotenv()
# openai_api_key = os.getenv("OPENAI_API_KEY")
# os.environ["OPENAI_API_KEY"] = openai_api_key

from langchain_openai import ChatOpenAI

chat = ChatOpenAI()
# b = chat.predict("How many planets are there?")
# print(b)

