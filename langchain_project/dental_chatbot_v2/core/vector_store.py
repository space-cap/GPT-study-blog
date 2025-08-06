"""
Chroma 벡터 저장소 관리 모듈
병원 정보와 진료 항목을 벡터 형태로 저장하고 검색 기능 제공[8][13]
"""

import os
import logging
from typing import List
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from core.database import DatabaseManager
from config import Config

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Chroma 벡터 스토어 관리 클래스"""

    def __init__(self):
        self.config = Config()
        self.embeddings = None
        self.vector_store = None
        self._initialize_embeddings()
        self._initialize_vector_store()

    def _initialize_embeddings(self):
        """HuggingFace 임베딩 모델 초기화"""
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=self.config.EMBEDDING_MODEL_NAME,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
            logger.info(f"임베딩 모델 로드 완료: {self.config.EMBEDDING_MODEL_NAME}")
        except Exception as e:
            logger.error(f"임베딩 모델 로드 실패: {e}")
            raise

    def _initialize_vector_store(self):
        """Chroma 벡터 스토어 초기화"""
        try:
            # 기존 벡터 스토어가 있으면 로드, 없으면 생성
            if os.path.exists(self.config.CHROMA_PERSIST_DIRECTORY):
                self.vector_store = Chroma(
                    collection_name=self.config.CHROMA_COLLECTION_NAME,
                    persist_directory=self.config.CHROMA_PERSIST_DIRECTORY,
                    embedding_function=self.embeddings,
                )
                logger.info("기존 벡터 스토어 로드 완료")
            else:
                self.vector_store = Chroma(
                    persist_directory=self.config.CHROMA_PERSIST_DIRECTORY,
                    embedding_function=self.embeddings,
                )
                logger.info("새 벡터 스토어 생성 완료")

        except Exception as e:
            logger.error(f"벡터 스토어 초기화 실패: {e}")
            raise

    def load_hospital_info(self):
        """about_us 폴더의 병원 정보 텍스트 파일들을 벡터 스토어에 로드"""
        documents = []
        about_us_path = "about_us"

        if not os.path.exists(about_us_path):
            logger.warning(f"{about_us_path} 폴더가 존재하지 않습니다.")
            return

        try:
            # about_us 폴더의 모든 txt 파일 처리
            txt_files = [
                "인사말.txt",
                "미소진의특별함.txt",
                "진료안내.txt",
                "의료진소개.txt",
                "병원둘러보기.txt",
                "오시는길.txt",
            ]

            for filename in txt_files:
                filepath = os.path.join(about_us_path, filename)
                if os.path.exists(filepath):
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read().strip()

                    doc = Document(
                        page_content=content,
                        metadata={
                            "source": filename,
                            "category": "hospital_info",
                            "type": filename.replace(".txt", ""),
                        },
                    )
                    documents.append(doc)
                    logger.info(f"병원 정보 로드: {filename}")
                else:
                    logger.warning(f"파일을 찾을 수 없습니다: {filepath}")

            if documents:
                self.vector_store.add_documents(documents)
                logger.info(
                    f"병원 정보 {len(documents)}개 문서 벡터 스토어에 추가 완료"
                )

        except Exception as e:
            logger.error(f"병원 정보 로드 실패: {e}")

    def load_treatment_info(self):
        """MySQL의 진료 항목 정보를 벡터 스토어에 로드"""
        try:
            db_manager = DatabaseManager()
            treatments = db_manager.get_treatment_prices()

            documents = []
            for treatment in treatments:
                # 진료 항목 정보를 자연스러운 텍스트로 변환
                content = f"""
                치료명: {treatment['name']}
                분류: {treatment['category']}
                가격: {treatment['price']:,}원
                설명: {treatment['description']}
                """

                doc = Document(
                    page_content=content.strip(),
                    metadata={
                        "source": "treatment_database",
                        "category": "treatment_price",
                        "treatment_name": treatment["name"],
                        "treatment_category": treatment["category"],
                        "price": treatment["price"],
                    },
                )
                documents.append(doc)

            if documents:
                self.vector_store.add_documents(documents)
                logger.info(f"진료 항목 {len(documents)}개 벡터 스토어에 추가 완료")

        except Exception as e:
            logger.error(f"진료 항목 로드 실패: {e}")

    def search_similar(
        self, query: str, k: int = 3, filter_dict: dict = None
    ) -> List[Document]:
        """유사도 기반 문서 검색"""
        try:
            if filter_dict:
                results = self.vector_store.similarity_search(
                    query, k=k, filter=filter_dict
                )
            else:
                results = self.vector_store.similarity_search(query, k=k)

            logger.info(f"검색 쿼리: '{query}', 결과: {len(results)}개")
            return results

        except Exception as e:
            logger.error(f"벡터 검색 실패: {e}")
            return []

    def search_treatment_prices(self, query: str, k: int = 5) -> List[Document]:
        """진료 비용 정보 검색"""
        return self.search_similar(
            query, k=k, filter_dict={"category": "treatment_price"}
        )

    def search_hospital_info(self, query: str, k: int = 3) -> List[Document]:
        """병원 정보 검색"""
        return self.search_similar(
            query, k=k, filter_dict={"category": "hospital_info"}
        )

    def initialize_data(self):
        """초기 데이터 로드 (시스템 시작 시 호출)"""
        logger.info("벡터 스토어 데이터 초기화 시작...")
        self.load_hospital_info()
        self.load_treatment_info()
        logger.info("벡터 스토어 데이터 초기화 완료")
