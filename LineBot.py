import json
from agent.agent import answer_user
from utils.line import reply_to_line

def lambda_handler(event, context):
    # LINE Webhookからのリクエストを取得
    body = json.loads(event['body'])
    events = body.get('events', [])
    
    for event in events:
        if event['type'] == 'message' and event['message']['type'] == 'text':
            user_message = event['message']['text']
            reply_token = event['replyToken']

            # AIエージェントで応答生成
            response_message = answer_user(user_message)

            # LINEに返信
            reply_to_line(reply_token, response_message)

    return {
        'statusCode': 200,
        'body': json.dumps('OK')
    }