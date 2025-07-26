import os
import requests
from bs4 import BeautifulSoup
from llama_index.readers.web import SimpleWebPageReader
from langchain.text_splitter import CharacterTextSplitter
from openai import OpenAI
from langchain_google_community import GoogleSearchAPIWrapper

def search_and_summarize(user_query):
    # 0. ユーザーの質問から英語の検索キーワードを生成
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "ユーザーの質問から、Web検索に最適な英語のキーワードを3〜5語で抽出してください。"},
                {"role": "user", "content": user_query}
            ]
        )
        search_keywords = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating keywords: {e}")
        search_keywords = "AI latest news" # フォールバック

    # 1. LangChainのGoogle検索ツールで関連性の高い記事URLを取得
    search = GoogleSearchAPIWrapper()
    
    # 優先して検索するサイトのリスト
    priority_site_queries = [
        f"site:techcrunch.com {search_keywords}",
        f"site:venturebeat.com {search_keywords}",
        f"site:artificialintelligence-news.com {search_keywords}",
    ]
    
    links = []
    # まずは優先サイトから検索
    for site_query in priority_site_queries:
        try:
            results = search.results(site_query, num_results=2)
            for result in results:
                if "link" in result:
                    links.append(result["link"])
        except Exception as e:
            print(f"Error during priority site search for '{site_query}': {e}")
            continue

    # 優先サイトで見つからなかった場合のみ、ウェブ全体を検索する
    if not links:
        print("--- No results from priority sites. Falling back to general web search. ---")
        try:
            results = search.results(search_keywords, num_results=4) # 汎用検索では少し多めに取得
            for result in results:
                if "link" in result:
                    links.append(result["link"])
        except Exception as e:
            print(f"Error during general web search: {e}")

    if not links:
        return "関連する情報が見つかりませんでした。"

    print("--- 取得した記事のURL ---")
    for link in links:
        print(link)
    print("------------------------")

    # 2. 記事本文を取得 (BeautifulSoupを使用)
    all_text = ""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    for link in links:
        try:
            response = requests.get(link, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            # 主要なコンテンツが含まれていそうなタグからテキストを抽出
            main_content = soup.find('article') or soup.find('main') or soup.body
            if main_content:
                all_text += main_content.get_text(separator='\n', strip=True) + "\n\n"
        except requests.RequestException as e:
            print(f"Error fetching page content from {link}: {e}")
            continue

    text = all_text.strip()

    # テキストが取得できたか確認
    if not text:
        return "記事の本文を取得できませんでした。サイトがbot対策をしている可能性があります。"

    # 3. OpenAI GPTで要約・翻訳
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    
    # テキストが長すぎる場合、分割して要約
    splitter = CharacterTextSplitter(chunk_size=4000, chunk_overlap=200)
    chunks = splitter.split_text(text)

    summary = ""
    try:
        for chunk in chunks[:3]: # 最初の3チャンクを要約対象とする
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "以下の英語のテキストを、AIの最新動向として重要なポイントを抽出し、日本語で簡潔に要約してください。"},
                    {"role": "user", "content": f"元の質問: {user_query}\n\nテキスト:\n{chunk}"}
                ]
            )
            summary += response.choices[0].message.content + "\n"
    except Exception as e:
        print(f"Error with OpenAI API: {e}")
        return "AIによる要約中にエラーが発生しました。"

    return summary.strip() if summary else "要約を生成できませんでした。"