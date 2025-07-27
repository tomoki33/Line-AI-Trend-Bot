import json
import logging

# ロギングのセットアップ
logger = logging.getLogger()
logger.setLevel(logging.INFO)

from agent.search import search_and_summarize
from utils.line import push_to_line

def lambda_handler(event, context):
    """SQSから呼び出されるワーカーLambda"""
    
    logger.info("--- Worker Lambda Started ---")
    logger.info(f"Received event: {json.dumps(event)}")

    for record in event['Records']:
        try:
            logger.info(f"Processing SQS record: {record.get('messageId')}")
            
            # SQSメッセージのbodyからLINEのイベントオブジェクトを取得
            line_body = json.loads(record['body'])
            logger.info(f"Parsed SQS message body: {json.dumps(line_body)}")
            
            line_events = line_body.get('events', [])
            if not line_events:
                logger.warning("No 'events' found in message body. Skipping.")
                continue

            for line_event in line_events:
                logger.info(f"Processing LINE event type: {line_event.get('type')}")
                if line_event.get('type') == 'message' and line_event['message'].get('type') == 'text':
                    user_id = line_event['source']['userId']
                    user_message = line_event['message']['text']
                    
                    logger.info(f"Sending 'in progress' message to user: {user_id}")
                    push_to_line(user_id, "AIが情報を検索・要約中です。しばらくお待ちください...")

                    logger.info(f"Starting AI agent for user message: {user_message}")
                    response_message = search_and_summarize(user_message)
                    
                    logger.info(f"Sending final response to user: {user_id}")
                    push_to_line(user_id, response_message)
                else:
                    logger.info("Event is not a text message. Skipping.")
        
        except Exception as e:
            logger.error(f"An error occurred while processing a record: {e}", exc_info=True)

    logger.info("--- Worker Lambda Finished ---")
    return {
        'statusCode': 200,
        'body': json.dumps('OK')
    }
