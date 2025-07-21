from llama_index.readers.simple_web import SimpleWebPageReader
from langchain.text_splitter import CharacterTextSplitter

def search_and_summarize(query):
    # 例: 指定サイトリスト
    sites = [
        "https://www.aitimes.com/",
        "https://www.artificialintelligence-news.com/"
    ]
    docs = []
    for site in sites:
        docs += SimpleWebPageReader().load_data([site + f"?q={query}"])
    text = "\n".join([d.text for d in docs])
    # 要約処理（ここでは単純に先頭部分を返す例）
    splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=0)
    chunks = splitter.split_text(text)
    summary = chunks[0] if chunks else "情報が見つかりませんでした。"
    return summary