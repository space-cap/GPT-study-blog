from langchain_community.embeddings import OllamaEmbeddings

# OllamaEmbeddings 초기화
embeddings = OllamaEmbeddings(model="mistral:latest")

# 텍스트 임베딩 생성
text = "LangChain은 대규모 언어 모델을 사용한 애플리케이션 개발을 위한 프레임워크입니다."
embedding = embeddings.embed_query(text)

print(f"임베딩 차원: {len(embedding)}")
print(f"임베딩의 처음 5개 값: {embedding[:5]}")
