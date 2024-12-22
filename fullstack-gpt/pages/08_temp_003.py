import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.document_loaders import UnstructuredFileLoader
from langchain.text_splitter import CharacterTextSplitter
import json
import os
from langchain.retrievers import WikipediaRetriever
from langchain.schema import BaseOutputParser, output_parser




@st.cache_resource(show_spinner="Loading file...")
def split_file(file):
    file_content = file.read()
    file_path = f"./.cache/quiz_files/{file.name}"
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    loader = UnstructuredFileLoader(file_path)
    documents = loader.load()
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    docs = text_splitter.split_documents(documents)
    return docs


@st.cache_resource(show_spinner="Searching Wikipedia...")
def wiki_search(term):
    retriever = WikipediaRetriever(top_k_results=5)
    docs = retriever.get_relevant_documents(term)
    return docs


@st.cache_resource(show_spinner="Making quiz...")
def run_quiz_chain(_docs, topic):
    # 전체 텍스트 결합
    full_text = " ".join([doc.page_content for doc in docs])
    
    # LLM을 사용하여 문제 생성
    response = llm.invoke(prompt.format(text=full_text))
    cleaned_string = response.content.replace('```', '').replace('json', '', 1).strip()
    
    # JSON 파싱
    questions_json = json.loads(cleaned_string)
    return questions_json


with st.sidebar:
    docs = None
    topic = None
    choice = st.selectbox(
        "Choose what you want to use.",
        (
            "File",
            "Wikipedia Article",
        ),
    )
    if choice == "File":
        file = st.file_uploader(
            "Upload a .docx , .txt or .pdf file",
            type=["pdf", "txt", "docx"],
        )
        if file:
            docs = split_file(file)
    else:
        topic = st.text_input("Search Wikipedia...")
        if topic:
            docs = wiki_search(topic)


# LLM 모델 초기화
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.1,)

# 프롬프트 템플릿 정의
template = """
다음 텍스트를 기반으로 4지선다형 문제 10개를 만들어주세요:

{text}

문제와 답변을 다음 JSON 형식으로 제공해주세요:
{{ "questions": [
            {{
                "question": "What is the color of the ocean?",
                "answers": [
                        {{
                            "answer": "Red",
                            "correct": false
                        }},
                        {{
                            "answer": "Yellow",
                            "correct": false
                        }},
                        {{
                            "answer": "Green",
                            "correct": false
                        }},
                        {{
                            "answer": "Blue",
                            "correct": true
                        }},
                ]
            }},
        ...
    ]
}}
"""

prompt = ChatPromptTemplate.from_template(template)

# Streamlit 앱
st.title("QuizGPT")


if not docs:
    st.markdown(
        """
    Welcome to QuizGPT.
                
    I will make a quiz from Wikipedia articles or files you upload to test your knowledge and help you study.
                
    Get started by uploading a file or searching on Wikipedia in the sidebar.
    """
    )
else:
    questions_json = run_quiz_chain(docs, topic if topic else file.name)
    
    # 결과 표시
    st.json(questions_json)
    
    # 문제 및 선택지 표시
    with st.form("questions_form"):
        for question in questions_json["questions"]:
            st.write(question["question"])
            value = st.radio(
                "Select an option.",
                [answer["answer"] for answer in question["answers"]],
                index=None,
            )
            if {"answer": value, "correct": True} in question["answers"]:
                st.success("Correct!")
            elif value is not None:
                st.error("Wrong!")
        button = st.form_submit_button()

        