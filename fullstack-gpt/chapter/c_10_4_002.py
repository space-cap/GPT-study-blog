from langchain_community.document_loaders import SitemapLoader

url = "https://deepmind.google/sitemap.xml"

loader = SitemapLoader(url)
loader.requests_per_second = 5
docs = loader.load()

print(docs)





