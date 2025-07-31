# saju_chatbot/database/chroma_manager.py

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from config import CHROMA_PERSIST_DIRECTORY, EMBEDDING_MODEL_NAME
import os


class ChromaManager:
    def __init__(self):
        # HuggingFace 임베딩 모델 로드
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

        # ChromaDB 클라이언트 초기화
        # persist_directory를 지정하여 데이터가 파일 시스템에 저장되도록 함
        self.vectorstore = Chroma(
            collection_name="saju_knowledge",
            embedding_function=self.embeddings,
            persist_directory=CHROMA_PERSIST_DIRECTORY,
        )
        self._initialize_knowledge_base()

    def _initialize_knowledge_base(self):
        """
        사주 관련 지식 문서들을 ChromaDB에 초기 로드합니다.
        이는 챗봇이 사주 풀이를 할 때 참고할 배경 지식이 됩니다.
        실제로는 `data/saju_rules.json` 등의 내용을 Document 형태로 변환하여 저장합니다.
        """
        # 데이터가 이미 있는지 확인 (간단한 방법)
        # collection_count = self.vectorstore._client.get_or_create_collection("saju_knowledge").count()
        # if collection_count > 0:
        #     print("ChromaDB already contains data. Skipping initial load.")
        #     return

        print("Initializing ChromaDB knowledge base...")
        docs_to_add = []

        # 예시: 사주 용어 설명을 문서로 추가
        # 실제로는 `data/saju_rules.json` 및 `data/saju_terms.json`을 파싱하여 추가
        saju_terms_path = "data/saju_terms.json"
        if os.path.exists(saju_terms_path):
            import json

            with open(saju_terms_path, "r", encoding="utf-8") as f:
                saju_terms = json.load(f)

            for category, terms in saju_terms.items():
                for term, description in terms.items():
                    content = f"{category} - {term}: {description}"
                    docs_to_add.append(
                        Document(
                            page_content=content,
                            metadata={"category": category, "term": term},
                        )
                    )

        saju_rules_path = "data/saju_rules.json"
        if os.path.exists(saju_rules_path):
            import json

            with open(saju_rules_path, "r", encoding="utf-8") as f:
                saju_rules = json.load(f)

            # 오행 설명 추가
            for ohang, desc in saju_rules.get("오행설명", {}).items():
                content = f"오행 {ohang}에 대한 설명: {desc}"
                docs_to_add.append(
                    Document(
                        page_content=content,
                        metadata={"type": "오행설명", "name": ohang},
                    )
                )

            # 십성 설명 추가
            for sipsung, details in saju_rules.get("십성", {}).items():
                content = f"십성 {sipsung}은 {details.get('설명', '')}"
                docs_to_add.append(
                    Document(
                        page_content=content,
                        metadata={"type": "십성설명", "name": sipsung},
                    )
                )

            # 신살 설명 추가
            for sinsal, details in saju_rules.get("신살", {}).items():
                content = f"신살 {sinsal}은 {details.get('설명', '')}"
                docs_to_add.append(
                    Document(
                        page_content=content,
                        metadata={"type": "신살설명", "name": sinsal},
                    )
                )

            # 일간 설명 추가
            for ilgan, desc in saju_rules.get("일간설명", {}).items():
                content = f"일간 {ilgan}에 대한 설명: {desc}"
                docs_to_add.append(
                    Document(
                        page_content=content,
                        metadata={"type": "일간설명", "name": ilgan},
                    )
                )

        if docs_to_add:
            self.vectorstore.add_documents(docs_to_add)
            print(f"Added {len(docs_to_add)} documents to ChromaDB.")
        else:
            print("No documents to add to ChromaDB.")

    def retrieve_knowledge(self, query: str, k: int = 3) -> list[Document]:
        """
        주어진 쿼리와 관련된 지식 문서들을 ChromaDB에서 검색합니다.
        """
        # LangChain의 검색 인터페이스 활용
        retriever = self.vectorstore.as_retriever(search_kwargs={"k": k})
        docs = retriever.invoke(query)
        return docs

    def add_document(self, document: Document):
        """단일 문서를 ChromaDB에 추가합니다."""
        self.vectorstore.add_documents([document])
        self.vectorstore.persist()


# 테스트 코드
if __name__ == "__main__":
    chroma_manager = ChromaManager()

    # 쿼리 예시
    query = "도화살이 뭔가요?"
    retrieved_docs = chroma_manager.retrieve_knowledge(query)
    print(f"\nRetrieved documents for '{query}':")
    for doc in retrieved_docs:
        print(f"- Content: {doc.page_content[:100]}...")
        print(f"  Metadata: {doc.metadata}")

    query_ohang = "나무의 기운은 어떤 특징이 있나요?"
    retrieved_docs_ohang = chroma_manager.retrieve_knowledge(query_ohang)
    print(f"\nRetrieved documents for '{query_ohang}':")
    for doc in retrieved_docs_ohang:
        print(f"- Content: {doc.page_content[:100]}...")
        print(f"  Metadata: {doc.metadata}")
