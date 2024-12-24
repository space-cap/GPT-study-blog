import os
from langchain_community.document_loaders import SitemapLoader
from langchain_community.document_transformers import BeautifulSoupTransformer


def parse_page(soup):
    header = soup.find("header")
    footer = soup.find("footer")
    if header:
        header.decompose()
    if footer:
        footer.decompose()
    return (
        str(soup.get_text())
        .replace("\n", " ")
        .replace("\xa0", " ")
        .replace("CloseSearch Submit Blog", "")
    )


# SitemapLoader 초기화
loader = SitemapLoader(
    "https://developers.cloudflare.com/sitemap-0.xml",
    filter_urls=[
            r"^(.*\/ai-gateway\/).*",
        ],
    parsing_function=parse_page,
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
