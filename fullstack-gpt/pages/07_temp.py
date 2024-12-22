import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.document_loaders import UnstructuredFileLoader
from langchain.text_splitter import CharacterTextSplitter
import os

# Google API 키 설정
# os.environ["GOOGLE_API_KEY"] = "your_google_api_key_here"

# 파일 로드
loader = UnstructuredFileLoader("./files/chapter_one.txt")
documents = loader.load()

# 텍스트 분할
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
texts = text_splitter.split_documents(documents)

# Google Generative AI 모델 초기화
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.1,)

# 프롬프트 템플릿 정의
template = """
다음 텍스트를 바탕으로 4지선다형 문제 1개를 만들어주세요:

{text}

문제와 선택지, 그리고 정답을 다음 형식으로 제공해주세요:
문제: (문제 내용)
A. (선택지 A)
B. (선택지 B)
C. (선택지 C)
D. (선택지 D)
정답: (정답 선택지)
"""

prompt = ChatPromptTemplate.from_template(template)

# Streamlit 앱
st.title("4지선다형 문제 생성기")

if st.button("문제 생성"):
    questions = []
    for i in range(10):  # 10개의 문제 생성
        # 랜덤하게 텍스트 청크 선택
        text_chunk = texts[i % len(texts)].page_content
        
        # 문제 생성
        response = llm.invoke(prompt.format(text=text_chunk))
        questions.append(response.content)
    
    # 생성된 문제 표시
    for i, question in enumerate(questions, 1):
        st.subheader(f"문제 {i}")
        st.write(question)
        st.markdown("---")
