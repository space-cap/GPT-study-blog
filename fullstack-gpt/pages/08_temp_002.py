import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.document_loaders import UnstructuredFileLoader
from langchain.text_splitter import CharacterTextSplitter
import json
import os

# 문서 로드 및 분할
loader = UnstructuredFileLoader("./files/chapter_one.txt")
documents = loader.load()
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
texts = text_splitter.split_documents(documents)

# LLM 모델 초기화
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.1,)

# 프롬프트 템플릿 정의
template = """
다음 텍스트를 기반으로 4지선다형 문제 10개를 만들어주세요:

{text}

문제와 답변을 다음 JSON 형식으로 제공해주세요:
{{
    "questions": [
        {{
            "question": "문제 내용",
            "options": ["A. 선택지1", "B. 선택지2", "C. 선택지3", "D. 선택지4"],
            "correct_answer": "정답 번호 (A, B, C, D 중 하나)"
        }},
        ...
    ]
}}
"""

prompt = ChatPromptTemplate.from_template(template)

# Streamlit 앱
st.title("4지선다형 문제 생성기")

if st.button("문제 생성"):
    with st.spinner("문제를 생성 중입니다..."):
        # 전체 텍스트 결합
        full_text = " ".join([doc.page_content for doc in texts])
        
        # LLM을 사용하여 문제 생성
        #response = llm(prompt.format_messages(text=full_text))
        response = llm.invoke(prompt.format(text=full_text))
        # cleaned_string = response.content.replace('json', '', 1).strip()
        cleaned_string = response.content.replace('```', '').replace('json', '', 1).strip()
        #st.text("lee")
        # st.text(cleaned_string)
        
        # JSON 파싱
        questions_json = json.loads(cleaned_string)
        
        # 결과 표시
        st.json(questions_json)
        
        # 문제 및 선택지 표시
        for i, q in enumerate(questions_json["questions"], 1):
            st.subheader(f"문제 {i}")
            st.write(q["question"])
            for option in q["options"]:
                st.write(option)
            st.write(f"정답: {q['correct_answer']}")
            st.write("---")

        