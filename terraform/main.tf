provider "aws" {
  region = "ap-northeast-1" # 東京リージョン
}

# 1. Dockerイメージを保存するためのECRリポジトリを作成
resource "aws_ecr_repository" "line_bot_repo" {
  name                 = "line-bot-repo"
  image_tag_mutability = "MUTABLE"
}

# --- ここから変更 ---

# 2. Lambda実行用のIAMロール (1つに再統合)
resource "aws_iam_role" "lambda_exec_role" {
  name = "line-bot-lambda-exec-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# 3. 必要なポリシーをすべて1つのロールにアタッチ
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_sqs_execution" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaSQSQueueExecutionRole"
}

# --- ここまで変更 ---

# 4a. SQSキューを作成
resource "aws_sqs_queue" "line_bot_queue" {
  name                       = "line-bot-task-queue"
  visibility_timeout_seconds = 300 # ワーカーLambdaのタイムアウト(300秒)と合わせる
}

# 4b. APIハンドラLambda関数
resource "aws_lambda_function" "line_bot_api_handler" {
  function_name = "line-bot-api-handler-function"
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.line_bot_repo.repository_url}:latest"
  role          = aws_iam_role.lambda_exec_role.arn # 修正
  timeout       = 30
  memory_size   = 2048

  image_config {
    # このLambdaは「LineBot.py」の「lambda_handler」を呼び出すように指示
    command = ["LineBot.lambda_handler"]
  }

  environment {
    variables = {
      SQS_QUEUE_URL = aws_sqs_queue.line_bot_queue.id
    }
  }
}

# --- Provisioned Concurrencyとエイリアスの設定を削除 ---

# --- Warmer関連のリソースをすべて削除 ---

# 4c. ワーカーLambda関数
resource "aws_lambda_function" "line_bot_worker" {
  function_name = "line-bot-worker-function"
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.line_bot_repo.repository_url}:latest"
  role          = aws_iam_role.lambda_exec_role.arn # 修正
  timeout       = 300
  memory_size   = 2048

  image_config {
    # こちらのLambdaは「worker.py」の「lambda_handler」を呼び出すように指示
    command = ["worker.lambda_handler"]
  }

  environment {
    variables = {
      LINE_CHANNEL_ACCESS_TOKEN = var.line_channel_access_token
      OPENAI_API_KEY            = var.openai_api_key
      GOOGLE_API_KEY            = var.google_api_key
      GOOGLE_CSE_ID             = var.google_cse_id
    }
  }
}

# 4d. SQSキューとワーカーLambdaを接続
resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = aws_sqs_queue.line_bot_queue.arn
  function_name    = aws_lambda_function.line_bot_worker.arn
}

# 4e. LambdaがSQSを操作するためのIAMポリシー
resource "aws_iam_policy" "sqs_policy" {
  name = "line-bot-sqs-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = "sqs:SendMessage"
        Effect   = "Allow"
        Resource = aws_sqs_queue.line_bot_queue.arn
      },
      {
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Effect   = "Allow"
        Resource = aws_sqs_queue.line_bot_queue.arn
      }
    ]
  })
}

# SQSポリシーを統合ロールにアタッチ
resource "aws_iam_role_policy_attachment" "sqs_attachment" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.sqs_policy.arn
}

# 5. API Gateway (HTTP API) を作成
resource "aws_apigatewayv2_api" "line_bot_api" {
  name          = "line-bot-api"
  protocol_type = "HTTP"
}

# 6. API GatewayとLambdaの統合を設定
resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id                   = aws_apigatewayv2_api.line_bot_api.id
  integration_type         = "AWS_PROXY"
  payload_format_version = "2.0" # この行を追加して、正しいイベント形式を保証する
  # 統合先をエイリアスではなく、関数そのものに戻す
  integration_uri          = aws_lambda_function.line_bot_api_handler.invoke_arn
}

# 7. API Gatewayのルートを設定 (POST /webhook)
resource "aws_apigatewayv2_route" "line_bot_route" {
  api_id    = aws_apigatewayv2_api.line_bot_api.id
  route_key = "POST /webhook"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

# 8. API Gatewayのステージを作成 (デプロイ)
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.line_bot_api.id
  name        = "$default"
  auto_deploy = true
}

# 9. API GatewayがLambdaを呼び出す権限を付与
resource "aws_lambda_permission" "api_gw_permission" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  # 権限付与の対象をエイリアスではなく、関数そのものに戻す
  function_name = aws_lambda_function.line_bot_api_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.line_bot_api.execution_arn}/*/*"
}

# 10. Webhook URLを出力
output "webhook_url" {
  value = "${aws_apigatewayv2_stage.default.invoke_url}/webhook"
}