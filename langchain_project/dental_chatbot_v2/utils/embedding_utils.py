"""
임베딩 관련 유틸리티 함수들
"""

import numpy as np
import logging
from typing import List
from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)


class EmbeddingUtils:
    """임베딩 관련 유틸리티 클래스"""

    def __init__(self, model_name: str = "jhgan/ko-sroberta-multitask"):
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

    def get_embedding(self, text: str) -> List[float]:
        """텍스트의 임베딩 벡터 생성"""
        try:
            return self.embeddings.embed_query(text)
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {e}")
            return []

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """두 텍스트 간 유사도 계산"""
        try:
            emb1 = np.array(self.get_embedding(text1))
            emb2 = np.array(self.get_embedding(text2))

            # 코사인 유사도 계산
            similarity = np.dot(emb1, emb2) / (
                np.linalg.norm(emb1) * np.linalg.norm(emb2)
            )
            return float(similarity)
        except Exception as e:
            logger.error(f"유사도 계산 실패: {e}")
            return 0.0

    def find_most_similar(
        self, query: str, candidates: List[str], top_k: int = 3
    ) -> List[tuple]:
        """가장 유사한 텍스트 찾기"""
        similarities = []
        query_emb = np.array(self.get_embedding(query))

        for candidate in candidates:
            candidate_emb = np.array(self.get_embedding(candidate))
            similarity = np.dot(query_emb, candidate_emb) / (
                np.linalg.norm(query_emb) * np.linalg.norm(candidate_emb)
            )
            similarities.append((candidate, float(similarity)))

        # 유사도 기준 정렬
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
