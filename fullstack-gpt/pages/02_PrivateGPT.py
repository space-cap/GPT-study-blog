import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.document_loaders import TextLoader
from langchain.embeddings import CacheBackedEmbeddings, OllamaEmbeddings
from langchain.storage import LocalFileStore
from langchain.text_splitter import CharacterTextSplitter
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnableLambda, RunnablePassthrough
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain.callbacks.base import BaseCallbackHandler
import streamlit as st
from langchain.chat_models import ChatOllama
import faiss


st.set_page_config(
    page_title="DocumentGPT",
    page_icon="📃",
)

class ChatCallbackHandler(BaseCallbackHandler):
    
    def __init__(self):
        self.message_box = st.empty()
        self.message = ""
    
    def on_llm_start(self, *args, **kwargs):
        print("LLM 생성 시작...")

    def on_llm_end(self, *args, **kwargs):
        save_message(self.message, "ai")
        print("\nLLM 생성 완료!")

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        print(f"새로운 토큰: {token}", end="", flush=True)
        self.message += token
        self.message_box.markdown(self.message + "▌")
        

handler = ChatCallbackHandler()

llm = ChatOllama(
    model="mistral:latest",
    temperature=0.1,
    streaming=True,
    )

@st.cache_resource(show_spinner="Embedding file...")
def embed_file(file):
    file_content = file.read()
    file_path = f"./.cache/files/{file.name}"
    with open(file_path, "wb") as f:
        f.write(file_content)
    cache_dir = LocalFileStore(f"./.cache/embeddings/{file.name}")
    splitter = CharacterTextSplitter.from_tiktoken_encoder(
        separator="\n",
        chunk_size=600,
        chunk_overlap=100,
    )
    loader = TextLoader(file_path)
    docs = loader.load_and_split(text_splitter=splitter)
    embeddings = OllamaEmbeddings(model="mistral:latest")

    #vector = embeddings.embed_query("Test query")
    #st.markdown(len(vector))
    # 차원 수 설정
    embedding_dim = len(embeddings.embed_query("Sample text"))
    

    cached_embeddings = CacheBackedEmbeddings.from_bytes_store(embeddings, cache_dir)
    # vectorstore = FAISS.from_documents(docs, cached_embeddings, index=index_dim)
    
    
    # 수정된 부분
    vectorstore = FAISS(
        embedding_function=cached_embeddings,
        index=faiss.IndexFlatL2(embedding_dim),
    )

    # 문서 추가
    vectorstore.add_documents(docs)
        
    
    retriever = vectorstore.as_retriever()

    return retriever


def save_message(message, role):
    st.session_state["messages"].append({"message": message, "role": role})


def send_message(message, role, save=True):
    with st.chat_message(role):
        st.markdown(message)
    if save:
        save_message(message, role)


def paint_history():
    for message in st.session_state["messages"]:
        send_message(
            message["message"],
            message["role"],
            save=False,
        )


def format_docs(docs):
    return "\n\n".join(document.page_content for document in docs)


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            Answer the question using ONLY the following context. If you don't know the answer just say you don't know. DON'T make anything up.
            
            Context: {context}
            """,
        ),
        ("human", "{question}"),
    ]
)


st.title("PrivateGPT")

st.markdown(
    """
Welcome!
            
Use this chatbot to ask questions to an AI about your files!

Upload your files on the sidebar.
"""
)

with st.sidebar:
    file = st.file_uploader(
        "Upload a .txt .pdf or .docx file",
        type=["pdf", "txt", "docx"],
    )

if file:
    retriever = embed_file(file)
    send_message("I'm ready! Ask away!", "ai", save=False)
    paint_history()
    message = st.chat_input("Ask anything about your file...")
    if message:
        send_message(message, "human")
        chain = (
            {
                "context": retriever | RunnableLambda(format_docs),
                "question": RunnablePassthrough(),
            }
            | prompt
            | llm
        )
        with st.chat_message("ai"):
            response = st.empty()
            full_response = ""
            for chunk in chain.stream(message):
                full_response += chunk.content
                response.markdown(full_response)
            save_message(full_response, "ai")
            # st.write_stream(chunk.content for chunk in chain.stream(message))
            #response = chain.invoke(message, config={"callbacks": [handler]})
            #print(response.content)
            
        # 최종 결과 표시
        # st.subheader("최종 답변:")
        # st.write(response.content)
            
else:
    st.session_state["messages"] = []


