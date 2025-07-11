import time
import psutil
import numpy as np
from typing import List, Dict, Tuple
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.evaluation import load_evaluator
import matplotlib.pyplot as plt
import pandas as pd 

# OpenAI API 키 설정 (환경변수 또는 직접 입력)
import os
from dotenv import load_dotenv

load_dotenv()

class ChunkSizeOptimizer:
    """청크 크기 최적화를 위한 실험 클래스"""

    def __init__(self, pdf_path: str, test_queries: List[str]):
        """
        초기화
        Args:
            pdf_path: PDF 파일 경로
            test_queries: 테스트용 질문 리스트
        """
        self.pdf_path = pdf_path
        self.test_queries = test_queries
        self.results = []
        self.embeddings = OpenAIEmbeddings()

    def load_and_split_document(self, chunk_size: int, chunk_overlap: int) -> List:
        """
        문서 로드 및 청크 분할
        Args:
            chunk_size: 청크 크기
            chunk_overlap: 오버랩 크기
        Returns:
            분할된 문서 청크 리스트
        """
        # PDF 문서 로드
        loader = PyPDFLoader(self.pdf_path)
        documents = loader.load()

        # 텍스트 분할기 설정
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""],  # 분할 우선순위
            length_function=len,  # 길이 측정 함수
        )

        # 문서 분할
        chunks = text_splitter.split_documents(documents)
        return chunks

    def create_vectorstore(self, chunks: List) -> FAISS:
        """
        벡터 스토어 생성
        Args:
            chunks: 문서 청크 리스트
        Returns:
            FAISS 벡터 스토어
        """
        # 벡터 스토어 생성 시간 측정
        start_time = time.time()
        vectorstore = FAISS.from_documents(chunks, self.embeddings)
        creation_time = time.time() - start_time

        return vectorstore, creation_time

    def evaluate_retrieval_quality(self, vectorstore: FAISS, k: int = 3) -> Dict:
        """
        검색 품질 평가
        Args:
            vectorstore: 벡터 스토어
            k: 검색할 문서 수
        Returns:
            평가 결과 딕셔너리
        """
        retrieval_times = []
        relevance_scores = []

        for query in self.test_queries:
            # 검색 시간 측정
            start_time = time.time()
            docs = vectorstore.similarity_search(query, k=k)
            retrieval_time = time.time() - start_time
            retrieval_times.append(retrieval_time)

            # 관련성 점수 계산 (간단한 키워드 매칭 기반)
            relevance_score = self._calculate_relevance_score(query, docs)
            relevance_scores.append(relevance_score)

        return {
            "avg_retrieval_time": np.mean(retrieval_times),
            "avg_relevance_score": np.mean(relevance_scores),
            "retrieval_times": retrieval_times,
            "relevance_scores": relevance_scores,
        }

    def _calculate_relevance_score(self, query: str, docs: List) -> float:
        """
        관련성 점수 계산 (키워드 기반 간단 구현)
        Args:
            query: 검색 쿼리
            docs: 검색된 문서들
        Returns:
            관련성 점수 (0-1)
        """
        query_words = set(query.lower().split())
        total_score = 0

        for doc in docs:
            doc_words = set(doc.page_content.lower().split())
            # 교집합 비율로 관련성 측정
            intersection = len(query_words.intersection(doc_words))
            union = len(query_words.union(doc_words))
            score = intersection / union if union > 0 else 0
            total_score += score

        return total_score / len(docs) if docs else 0

    def measure_memory_usage(self) -> float:
        """
        현재 메모리 사용량 측정
        Returns:
            메모리 사용량 (MB)
        """
        process = psutil.Process()
        memory_info = process.memory_info()
        return memory_info.rss / 1024 / 1024  # MB 단위

    def run_experiment(
        self, chunk_sizes: List[int], chunk_overlaps: List[int]
    ) -> pd.DataFrame:
        """
        청크 크기 실험 실행
        Args:
            chunk_sizes: 테스트할 청크 크기 리스트
            chunk_overlaps: 테스트할 오버랩 크기 리스트
        Returns:
            실험 결과 DataFrame
        """
        print("청크 크기 최적화 실험 시작...")

        for chunk_size in chunk_sizes:
            for chunk_overlap in chunk_overlaps:
                if chunk_overlap >= chunk_size:
                    continue  # 오버랩이 청크 크기보다 클 수 없음

                print(
                    f"실험 중: chunk_size={chunk_size}, chunk_overlap={chunk_overlap}"
                )

                # 메모리 사용량 측정 시작
                memory_before = self.measure_memory_usage()

                try:
                    # 문서 분할
                    chunks = self.load_and_split_document(chunk_size, chunk_overlap)

                    # 벡터 스토어 생성
                    vectorstore, creation_time = self.create_vectorstore(chunks)

                    # 검색 품질 평가
                    eval_results = self.evaluate_retrieval_quality(vectorstore)

                    # 메모리 사용량 측정 종료
                    memory_after = self.measure_memory_usage()
                    memory_used = memory_after - memory_before

                    # 결과 저장
                    result = {
                        "chunk_size": chunk_size,
                        "chunk_overlap": chunk_overlap,
                        "num_chunks": len(chunks),
                        "avg_chunk_length": np.mean(
                            [len(chunk.page_content) for chunk in chunks]
                        ),
                        "vectorstore_creation_time": creation_time,
                        "avg_retrieval_time": eval_results["avg_retrieval_time"],
                        "avg_relevance_score": eval_results["avg_relevance_score"],
                        "memory_used_mb": memory_used,
                        "efficiency_score": eval_results["avg_relevance_score"]
                        / eval_results["avg_retrieval_time"],
                    }

                    self.results.append(result)

                except Exception as e:
                    print(f"실험 실패: {e}")
                    continue

        # 결과를 DataFrame으로 변환
        results_df = pd.DataFrame(self.results)
        return results_df

    def visualize_results(self, results_df: pd.DataFrame):
        """
        실험 결과 시각화
        Args:
            results_df: 실험 결과 DataFrame
        """

        # 한글 폰트 설정
        plt.rcParams['font.family'] = 'Malgun Gothic'  # Windows
        # plt.rcParams['font.family'] = 'AppleGothic'  # macOS
        # plt.rcParams['font.family'] = 'NanumGothic'  # 나눔고딕이 설치된 경우

        # 마이너스 기호 깨짐 방지
        plt.rcParams['axes.unicode_minus'] = False

        fig, axes = plt.subplots(2, 2, figsize=(15, 12))

        # 1. 청크 크기별 관련성 점수
        axes[0, 0].scatter(results_df["chunk_size"], results_df["avg_relevance_score"])
        axes[0, 0].set_xlabel("청크 크기")
        axes[0, 0].set_ylabel("평균 관련성 점수")
        axes[0, 0].set_title("청크 크기 vs 관련성 점수")

        # 2. 청크 크기별 검색 시간
        axes[0, 1].scatter(results_df["chunk_size"], results_df["avg_retrieval_time"])
        axes[0, 1].set_xlabel("청크 크기")
        axes[0, 1].set_ylabel("평균 검색 시간 (초)")
        axes[0, 1].set_title("청크 크기 vs 검색 시간")

        # 3. 청크 크기별 메모리 사용량
        axes[1, 0].scatter(results_df["chunk_size"], results_df["memory_used_mb"])
        axes[1, 0].set_xlabel("청크 크기")
        axes[1, 0].set_ylabel("메모리 사용량 (MB)")
        axes[1, 0].set_title("청크 크기 vs 메모리 사용량")

        # 4. 효율성 점수
        axes[1, 1].scatter(results_df["chunk_size"], results_df["efficiency_score"])
        axes[1, 1].set_xlabel("청크 크기")
        axes[1, 1].set_ylabel("효율성 점수")
        axes[1, 1].set_title("청크 크기 vs 효율성 점수")

        plt.tight_layout()
        plt.show()

    def find_optimal_settings(self, results_df: pd.DataFrame) -> Dict:
        """
        최적 설정 찾기
        Args:
            results_df: 실험 결과 DataFrame
        Returns:
            최적 설정 딕셔너리
        """
        # 가중 점수 계산 (관련성 70%, 속도 20%, 메모리 10%)
        normalized_relevance = (
            results_df["avg_relevance_score"] / results_df["avg_relevance_score"].max()
        )
        normalized_speed = (1 / results_df["avg_retrieval_time"]) / (
            1 / results_df["avg_retrieval_time"]
        ).max()
        normalized_memory = (1 / results_df["memory_used_mb"]) / (
            1 / results_df["memory_used_mb"]
        ).max()

        weighted_score = (
            normalized_relevance * 0.7
            + normalized_speed * 0.2
            + normalized_memory * 0.1
        )

        # 최고 점수 인덱스 찾기
        best_idx = weighted_score.idxmax()
        best_result = results_df.loc[best_idx]

        return {
            "optimal_chunk_size": best_result["chunk_size"],
            "optimal_chunk_overlap": best_result["chunk_overlap"],
            "weighted_score": weighted_score[best_idx],
            "performance_metrics": best_result.to_dict(),
        }


# 3. 실제 사용 예제
def main():
    """메인 실행 함수"""

    # 테스트 쿼리 정의 (실제 사용 시 도메인에 맞게 수정)
    test_queries = [
        "배터리 수명은 어떻게 되나요?",
        "카메라 설정 방법을 알려주세요",
        "무선 연결 문제 해결 방법",
        "화면 밝기 조절하는 방법",
        "앱 설치 및 삭제 방법",
    ]

    # 최적화 클래스 초기화
    optimizer = ChunkSizeOptimizer(
        pdf_path="day07/SM-F741N_UG_15_Kor_Rev.1.0_250410.pdf",  # 실제 경로로 수정
        test_queries=test_queries,
    )

    # 실험할 청크 크기와 오버랩 설정
    chunk_sizes = [200, 500, 800, 1000, 1200, 1500, 2000]
    chunk_overlaps = [50, 100, 150, 200, 250]

    # 실험 실행
    results_df = optimizer.run_experiment(chunk_sizes, chunk_overlaps)

    # 결과 출력
    print("\n=== 실험 결과 ===")
    print(results_df.head(10))

    # 최적 설정 찾기
    optimal_settings = optimizer.find_optimal_settings(results_df)
    print(f"\n=== 최적 설정 ===")
    print(f"최적 청크 크기: {optimal_settings['optimal_chunk_size']}")
    print(f"최적 오버랩: {optimal_settings['optimal_chunk_overlap']}")
    print(f"가중 점수: {optimal_settings['weighted_score']:.4f}")

    # 결과 시각화
    optimizer.visualize_results(results_df)

    # 결과를 CSV로 저장
    results_df.to_csv("chunk_optimization_results.csv", index=False)
    print("\n결과가 'chunk_optimization_results.csv'에 저장되었습니다.")


if __name__ == "__main__":
    main()
