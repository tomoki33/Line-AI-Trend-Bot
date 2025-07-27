# LINE AI Bot - 開発者向けガイド

このドキュメントは、LINE AI Botのセットアップ、アーキテクチャ、およびデプロイ手順について説明します。

## 目次

-   [システムアーキテクチャ](#-システムアーキテクチャ)
-   [セットアップ](#-セットアップ)
-   [LINE公式アカウントの設定](#-line公式アカウントの設定-重要)
-   [デプロイ手順](#-デプロイ手順-コード修正後など)
-   [初回のみの環境構築](#-初回のみの環境構築)

## 🏛️ システムアーキテクチャ

このBotは、LINEからのリクエストに対する即時応答性と、時間のかかるAI処理を両立させるため、SQSを介した非同期処理アーキテクチャを採用しています。

```
[LINEユーザー] -> [LINE Platform] -> [API Gateway] -> [APIハンドラLambda] -> [SQSキュー]
                                                                                |
                                                                                V
                                                                            [ワーカーLambda] -> (Web検索 & AI要約) -> [LINE Platform] -> [LINEユーザー]
```

-   **APIハンドラLambda (`line_bot_api_handler.py`)**: LINEからのWebhookリクエストを受け取り、即座にSQSキューにタスクを投入して`200 OK`を返す、超軽量な関数。LINEのタイムアウトを確実に回避します。
-   **SQSキュー**: 処理すべきタスクを一時的に保持するメッセージキュー。
-   **ワーカーLambda (`worker.py`)**: SQSキューをトリガーとして起動する**AIエージェント**。受け取ったタスク（ユーザーの質問）に基づき、Web検索とAIによる要約という一連のアクションを実行し、結果をユーザーに返します。
-   **Lambda Warmer (EventBridge)**: APIハンドラLambdaのコールドスタートを防ぐため、1分ごとにLambdaを呼び出し、常にウォーム状態を維持します。

## セットアップ

1.  **リポジトリのクローン**:
    ```sh
    git clone <repository-url>
    cd linebot
    ```

2.  **.envファイルの作成**:
    `.env.example`ファイルを参考に、`.env`ファイルを作成し、各種APIキーを記述します。
    ```sh
    cp .env.example .env
    # .envファイルを編集
    ```

3.  **Python仮想環境のセットアップ**:
    ```sh
    python3 -m venv venv
    source venv/bin/activate  # Windowsなら venv\Scripts\activate
    pip install -r requirements.txt
    ```

## ✅ LINE公式アカウントの設定 (重要)

LINE Botが正しく応答しない場合、以下の設定を確認してください。
1. [LINE Official Account Manager](https://www.linebiz.com/jp/login/)にログイン
2. 対象のアカウントを選択し、左メニューの「**応答設定**」を開く
3. **応答モード**を「**Bot**」に設定する
4. **詳細設定** > **応答メッセージ**を「**オフ**」に設定する

## 🚀 デプロイ手順 (コード修正後など)

**注意**: Dockerコマンドはプロジェクトのルートディレクトリ (`linebot/`) で、AWS CLI/Terraformコマンドは `terraform/` ディレクトリで実行します。

### 1. AWSアカウントIDの確認と設定
ターミナルで以下のコマンドを実行し、12桁のアカウントIDをコピーします。
```sh
aws sts get-caller-identity --query Account --output text
```
以降のコマンドの `<ACCOUNT_ID>` を、コピーしたIDに置き換えてください。

### 2. ECRログイン
1時間に1回程度、実行が必要です。
```sh
aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin 783764601888.dkr.ecr.ap-northeast-1.amazonaws.com
```

### 3. Dockerイメージのビルドとプッシュ (ルートディレクトリで実行)
```sh
# ビルド (buildxを使い、x86_64プラットフォームを強制)
docker buildx build --platform linux/amd64 -t line-bot-repo --load .

# タグ付け
docker tag line-bot-repo:latest 783764601888.dkr.ecr.ap-northeast-1.amazonaws.com/line-bot-repo:latest

# プッシュ
docker push 783764601888.dkr.ecr.ap-northeast-1.amazonaws.com/line-bot-repo:latest
```

### 4. Lambda関数のコードを更新 (ルートディレクトリで実行)
**Pythonコードを修正した場合は、このコマンドを実行します。**
```sh
# APIハンドラLambdaを更新
aws lambda update-function-code --function-name line-bot-api-handler-function --image-uri 783764601888.dkr.ecr.ap-northeast-1.amazonaws.com/line-bot-repo:latest

# ワーカーLambdaを更新
aws lambda update-function-code --function-name line-bot-worker-function --image-uri 783764601888.dkr.ecr.ap-northeast-1.amazonaws.com/line-bot-repo:latest
```

### 5. インフラ設定の更新 (terraform/ ディレクトリで実行)
**main.tfを修正した場合のみ、このコマンドを実行します。**
```sh
cd terraform
# 最初に一度、またはプロバイダ設定変更後に実行
terraform init

# インフラのデプロイ/更新
terraform apply \
  -var="line_channel_access_token=$(grep LINE_CHANNEL_ACCESS_TOKEN ../.env | cut -d '=' -f2)" \
  -var="openai_api_key=$(grep OPENAI_API_KEY ../.env | cut -d '=' -f2)" \
  -var="google_api_key=$(grep GOOGLE_API_KEY ../.env | cut -d '=' -f2)" \
  -var="google_cse_id=$(grep GOOGLE_CSE_ID ../.env | cut -d '=' -f2)"

# ルートディレクトリに戻る
cd ..
```

---
## 🛠️ 初回のみの環境構築

### buildxのセットアップ (Apple Silicon Macなど)
buildx用の新しいビルダーを作成し、有効化します。このコマンドはプロジェクトで一度だけ実行すればOKです。
```sh
docker buildx create --name mybuilder --use
docker buildx inspect --bootstrap
```

---
## 🐛 トラブルシューティング

### "EntityAlreadyExists" や "RepositoryAlreadyExistsException" エラーが発生する
-   **原因**: ディレクトリ構成の変更により、Terraformが新しい場所（`terraform/`）で新しい状態管理ファイル（`.tfstate`）を使い始めたため、AWS上にすでに存在するリソースを認識できなくなっています。
-   **解決策**: ルートディレクトリにある古い状態管理ファイル (`terraform.tfstate`) を、新しい `terraform/` ディリクトリに移動させます。
    1. プロジェクトのルートディレクトリ (`linebot/`) に移動します。
    2. 以下のコマンドで状態ファイルを移動します。
    ```sh
    mv terraform.tfstate terraform/
    mv terraform.tfstate.backup terraform/
    ```
    3. `terraform/` ディレクトリに移動し、`init` と `apply` を再実行します。
    ```sh
    cd terraform
    terraform init
    terraform apply \
      -var="line_channel_access_token=$(grep LINE_CHANNEL_ACCESS_TOKEN ../.env | cut -d '=' -f2)" \
      -var="openai_api_key=$(grep OPENAI_API_KEY ../.env | cut -d '=' -f2)" \
      -var="google_api_key=$(grep GOOGLE_API_KEY ../.env | cut -d '=' -f2)" \
      -var="google_cse_id=$(grep GOOGLE_CSE_ID ../.env | cut -d '=' -f2)"
    ```

### "Error loading webview: Could not register service worker" が表示される
