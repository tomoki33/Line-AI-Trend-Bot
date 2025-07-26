from agent.search import search_and_summarize
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    query = input("検索クエリを入力してください: ")
    summary = search_and_summarize(query)
    print("要約結果:\n", summary)
