import json
from agent.search import search_and_summarize
from utils.line import push_to_line

def lambda_handler(event, context):
    """SQSから呼び出されるワーカーLambda"""
    
    for record in event['Records']:
        # SQSメッセージのbodyからLINEのイベントオブジェクトを取得
        line_body = json.loads(record['body'])
        line_events = line_body.get('events', [])

        for line_event in line_events:
            if line_event.get('type') == 'message' and line_event['message'].get('type') == 'text':
                user_id = line_event['source']['userId']
                user_message = line_event['message']['text']
                
                # 1. まず「処理中」メッセージをプッシュ通知で送信
                push_to_line(user_id, "AIが情報を検索・要約中です。しばらくお待ちください...")

                # 2. 時間のかかるAI処理を実行
                response_message = search_and_summarize(user_message)
                
                # 3. 処理結果をプッシュ通知で送信
                push_to_line(user_id, response_message)
    
    return {
        'statusCode': 200,
        'body': json.dumps('OK')
    }
