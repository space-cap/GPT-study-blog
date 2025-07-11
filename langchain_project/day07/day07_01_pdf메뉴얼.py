# 필요한 라이브러리 임포트
from langchain_community.document_loaders import PyPDFLoader  # PDF 로더
from langchain_text_splitters import RecursiveCharacterTextSplitter  # 텍스트 분할
from langchain_openai import OpenAIEmbeddings, ChatOpenAI  # 임베딩 & LLM
from langchain_community.vectorstores import FAISS  # 벡터 DB
from langchain_core.prompts import ChatPromptTemplate  # 프롬프트 엔지니어링
from langchain.chains import create_retrieval_chain  # RAG 체인
from langchain.chains.combine_documents import create_stuff_documents_chain

# OpenAI API 키 설정 (환경변수 또는 직접 입력)
import os
from dotenv import load_dotenv

load_dotenv()


# 1. 문서 로드 (예: 제품 설명서 PDF)
loader = PyPDFLoader(
    r"day07\SM-F741N_UG_15_Kor_Rev.1.0_250410.pdf"
)  # 실제 매뉴얼 URL로 교체
docs = loader.load()
print(f"로드된 문서 개수: {len(docs)}")

# 2. 텍스트 분할 (청크 생성)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,  # 청크 크기(토큰)
    chunk_overlap=200,  # 오버랩으로 문맥 유지
    separators=["\n\n", "\n", " "],  # 분할 기준
)
chunks = text_splitter.split_documents(docs)
print(f"생성된 청크 개수: {len(chunks)}")

# 3. 임베딩 & 벡터 DB 저장
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")  # 저렴한 임베딩 모델
vector_db = FAISS.from_documents(chunks, embeddings)  # 메모리 기반 DB

# 4. 검색기 설정 (Top-k 유사 청크 검색)
retriever = vector_db.as_retriever(search_kwargs={"k": 3})  # 상위 3개 문서 반환

# 5. 프롬프트 템플릿 (핵심!)
prompt_template = """
<system>
너는 제품 지원 전문가야. 아래 제공된 문서를 바탕으로 질문에 답변해.
- 모르는 내용은 '확인 후 답변드리겠습니다'라고 응답
- 답변은 3문장 이내로 간결하게
- 문서 내용만 참조하고 추측하지 마
</system>

<참조 문서>
{context}
</참조 문서>

<질문>
{input}
</질문>
"""
prompt = ChatPromptTemplate.from_template(prompt_template)

# 6. LLM 모델 초기화 (gpt-3.5-turbo)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, verbose=True)

# 7. RAG 체인 구성
document_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, document_chain)

# 8. 사용자 질의 처리
question = "데이터 절약 모드?"
response = rag_chain.invoke({"input": question})

# 9. 결과 출력
print("### 최종 답변 ###")
print(response["answer"])

print("\n### 참조 문서 (출처) ###")
for i, doc in enumerate(response["context"]):
    print(f"[문서 {i+1}] {doc.metadata['page']}페이지: {doc.page_content[:100]}...")
