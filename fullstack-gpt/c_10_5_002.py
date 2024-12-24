import os
from langchain_community.document_loaders import SitemapLoader
from langchain_community.document_transformers import BeautifulSoupTransformer

# USER_AGENT 환경 변수 설정
os.environ['USER_AGENT'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# SitemapLoader 초기화
loader = SitemapLoader(
    "https://developers.cloudflare.com/sitemap-0.xml",
    filter_urls=["ai-gateway"],
    parsing_function=BeautifulSoupTransformer().transform_documents
)
loader.requests_per_second = 2

# 문서 로드
docs = loader.load()

# 결과 출력
if docs:
    print(f"{len(docs)}개의 AI Gateway 관련 문서를 찾았습니다.")
    for doc in docs:
        print(f"URL: {doc.metadata['source']}")
        print(f"내용 미리보기: {doc.page_content[:200]}...")
        print("-" * 50)
else:
    print("AI Gateway 관련 문서를 찾지 못했습니다.")
