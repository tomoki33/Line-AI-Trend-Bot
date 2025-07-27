import json
import os
import boto3
import logging

# ロギングのセットアップ
logger = logging.getLogger()
logger.setLevel(logging.INFO)

sqs_client = boto3.client('sqs')
SQS_QUEUE_URL = os.environ.get('SQS_QUEUE_URL')

def lambda_handler(event, context):
    """API Gatewayから呼び出される超軽量ハンドラ。SQSにメッセージを送信するだけ。"""
    
    logger.info(f"--- API Handler Lambda Started ---")
    logger.info(f"Received event: {json.dumps(event)}")

    # Warmerからの呼び出し、またはbodyキーが存在しないリクエスト（LINEの検証など）を安全に処理
    if 'body' not in event:
        logger.info("Request without 'body' received (likely a warmer or verification). Skipping.")
        return {'statusCode': 200, 'body': json.dumps('OK')}

    try:
        body = json.loads(event['body'])
        
        # LINEのWebhook検証リクエストはeventsが空なので、ここで処理を終了して200を返す
        if not body.get('events'):
            logger.info("Verified webhook. Skipping SQS send.")
            return {'statusCode': 200, 'body': json.dumps('OK')}

        # SQSキューのURLが取得できているか確認
        if not SQS_QUEUE_URL:
            logger.error("SQS_QUEUE_URL environment variable is not set.")
            # 失敗してもLINEには200を返す
            return {'statusCode': 200, 'body': json.dumps('Internal configuration error')}

        logger.info(f"Attempting to send message to SQS queue: {SQS_QUEUE_URL}")
        
        # SQSにLINEのイベントオブジェクト全体を送信
        sqs_client.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(body)
        )
        
        logger.info("Successfully sent message to SQS.")

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        # エラーが発生しても、LINEにはタイムアウトさせないために200を返す
        return {'statusCode': 200, 'body': json.dumps('Error processing request')}

    logger.info("--- API Handler Lambda Finished ---")
    # 何も処理せず、すぐに200 OKを返すことでタイムアウトを絶対に防ぐ
    return {
        'statusCode': 200,
        'body': json.dumps('OK')
    }