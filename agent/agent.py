from agent.search import search_and_summarize

def answer_user(user_message):
    """ユーザの質問に対してWeb検索・要約・AI回答を行う"""
    search_summary = search_and_summarize(user_message)
    # 必要に応じてAIモデルで追加生成処理
    return search_summary
