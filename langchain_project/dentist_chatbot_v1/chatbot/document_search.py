# document_search.py
def search_info(query, chroma_vectordb):
    # 실제 LangChain Retriever, Chroma 등을 여기에 연결
    docs = chroma_vectordb.similarity_search(query, top_k=2)
    # 예시: 문서 텍스트만 추출
    return [doc["content"] for doc in docs]
