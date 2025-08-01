from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


class SmartCache:
    def __init__(self):
        # HuggingFace 임베딩 모델 로드
        self.model = SentenceTransformer(
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        self.cache = {}  # {question: {'embedding': vector, 'answer': answer}}
        self.similarity_threshold = 0.85

    def get_embedding(self, text):
        """텍스트를 임베딩 벡터로 변환"""
        return self.model.encode([text])[0]

    def find_similar_question(self, question):
        """유사한 질문 찾기"""
        question_embedding = self.get_embedding(question)

        best_similarity = 0
        best_match = None

        for cached_question, data in self.cache.items():
            # 코사인 유사도 계산
            similarity = cosine_similarity([question_embedding], [data["embedding"]])[
                0
            ][0]

            if similarity > best_similarity and similarity >= self.similarity_threshold:
                best_similarity = similarity
                best_match = (cached_question, data["answer"], similarity)

        return best_match

    def get_or_set(self, question, answer_func):
        """캐시에서 답변 조회 또는 새로 생성"""
        # 1. 유사한 질문 검색
        similar = self.find_similar_question(question)

        if similar:
            cached_question, answer, similarity = similar
            print(f"캐시 적중! 유사도: {similarity:.3f}")
            print(f"원본 질문: {cached_question}")
            return answer

        # 2. 캐시 미스 - 새로운 답변 생성
        answer = answer_func(question)

        # 3. 캐시에 저장
        self.cache[question] = {
            "embedding": self.get_embedding(question),
            "answer": answer,
        }

        return answer


# 사용 예시
cache = SmartCache()

# 첫 번째 질문
answer1 = cache.get_or_set("오늘 날씨가 어때?", lambda q: "맑습니다")

# 유사한 질문 - 캐시에서 답변 가져옴
answer2 = cache.get_or_set("오늘 날씨 어떻게 되나요?", lambda q: "새로 생성됨")
# 출력: 캐시 적중! 유사도: 0.892
