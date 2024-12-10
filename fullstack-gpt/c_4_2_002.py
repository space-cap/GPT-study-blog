from dotenv import load_dotenv
import os

load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts.few_shot import FewShotChatMessagePromptTemplate
from langchain.callbacks import StreamingStdOutCallbackHandler
from langchain.prompts import ChatPromptTemplate

chat = ChatGoogleGenerativeAI(model="gemini-1.5-flash", 
                              temperature=0,
                              disable_streaming=False,
                              callbacks=[
                                  StreamingStdOutCallbackHandler(),
                              ])

examples = [
    {"country": "France", "answer": "Capital: Paris\nLanguage: French\nFood: Wine and Cheese\nCurrency: Euro"},
    {"country": "Italy", "answer": "Capital: Rome\nLanguage: Italian\nFood: Pizza and Pasta\nCurrency: Euro"}
]

example_prompt = ChatPromptTemplate.from_messages([
    ("human", "What do you know about {country}?"),
    ("ai", "{answer}")
])

few_shot_prompt = FewShotChatMessagePromptTemplate(
    examples=examples,
    example_prompt=example_prompt
)

final_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a geography expert, you give short answers."),
    few_shot_prompt,
    ("human", "What do you know about {country}?")
])

chain = final_prompt | chat
result = chain.invoke({"country": "Thailand"})
print(result.content)
