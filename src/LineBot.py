import json
import os
import boto3

sqs_client = boto3.client('sqs')
SQS_QUEUE_URL = os.environ.get('SQS_QUEUE_URL')

def lambda_handler(event, context):
    """API Gatewayから呼び出される超軽量ハンドラ。SQSにメッセージを送信するだけ。"""
    # Warmerからの呼び出しの場合は何もしない
    if event.get("source") == "lambda-warmer":
        print("Warmed up!")
        return {'statusCode': 200, 'body': json.dumps('Warmed up!')}

    body = json.loads(event['body'])
    
    # SQSにLINEのイベントオブジェクト全体を送信
    sqs_client.send_message(
        QueueUrl=SQS_QUEUE_URL,
        MessageBody=json.dumps(body)
    )

    # 何も処理せず、すぐに200 OKを返すことでタイムアウトを絶対に防ぐ
    return {
        'statusCode': 200,
        'body': json.dumps('OK')
    }