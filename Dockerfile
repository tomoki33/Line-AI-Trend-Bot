# AWS Lambda公式のPythonベースイメージを使用 (x86_64プラットフォームを強制)
FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.11

# 依存ライブラリをインストール
COPY requirements.txt ./

# ★★★ ここから変更 ★★★
# C/C++コンパイラをインストールして、numpyなどのライブラリをビルドできるようにする
RUN yum install gcc gcc-c++ -y
# ★★★ ここまで変更 ★★★

RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー (srcディレクトリを丸ごとコピー)
COPY src/ ./

# Lambdaハンドラを指定 (デフォルトは使わないのでコメントアウトしてもOK)
# CMD [ "line_bot_api_handler.lambda_handler" ]
