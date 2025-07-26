# 🤖 AIリサーチャーBot

![Bot Banner](https://user-images.githubusercontent.com/8409099/200548054-882e3262-843a-439a-a4a9-635346a75791.png)

**AIリサーチャーBot**は、あなたの代わりに最新の情報をWebで検索し、その内容をAIが分かりやすく要約して教えてくれる、あなたの専属アシスタントです。

## ✨ 主な機能

-   **🌐 Web検索機能**: 入力されたキーワードに基づいて、関連性の高い情報をWebから収集します。
-   **🧠 AIによる要約**: 収集した情報を強力なAIが分析し、重要なポイントを簡潔にまとめて返信します。
-   **💬 対話形式のインターフェース**: いつものLINEのトーク画面で、気軽に質問するだけで利用できます。

## 使い方

使い方はとても簡単です！

1.  このLINE公式アカウントを「友だち追加」します。
2.  トーク画面で、知りたいことや調べてほしいことをメッセージで送信します。

これだけで、Botが自動的にリサーチを開始します。

> **💡 ヒント**
> 「〇〇について教えて」「〇〇とは？」のように、具体的な質問をすると、より精度の高い回答が得られます。

## 🗣️ 会話の例

**あなた:**
`最近の円安の原因と今後の見通しについて教えて`

**AIリサーチャーBot:**
`AIが情報を検索・要約中です。しばらくお待ちください...`

**(しばらくして)**

**AIリサーチャーBot:**
`最近の円安の主な原因は、日米の金利差の拡大にあります。アメリカがインフレ抑制のために利上げを続ける一方、日本は金融緩和を維持しているため、ドルを買って円を売る動きが加速しています。今後の見通しについては、専門家の間でも意見が分かれていますが、...`

## ⚠️ ご利用にあたっての注意

-   AIによる要約処理には、数十秒〜1分程度の時間がかかる場合があります。最初に「処理中です」というメッセージが届きますので、そのままお待ちください。
-   生成される情報は、Web上のデータを元にしたAIによる要約であり、その正確性を保証するものではありません。重要な判断を行う際は、必ず複数の情報源をご確認ください。

---

## 仮想環境立ち上げ
cd /Users/tomoki33/Desktop/linebot
python3 -m venv venv
source venv/bin/activate  # Windowsなら venv\Scripts\activate
pip install -r requirements.txt

## ローカル実行
python test_search.py

## LINE Official Account Managerの設定 (重要)
LINE Botが正しく応答しない場合、以下の設定を確認してください。
1. [LINE Official Account Manager](https://www.linebiz.com/jp/login/)にログイン
2. 対象のアカウントを選択し、左メニューの「**応答設定**」を開く
3. **応答モード**を「**Bot**」に設定する
4. **詳細設定** > **応答メッセージ**を「**オフ**」に設定する

## デプロイ手順 (コード修正後など)

### 1. AWSアカウントIDの確認と設定
# ターミナルで以下のコマンドを実行し、12桁のアカウントIDをコピーします。
aws sts get-caller-identity --query Account --output text

# 以下のコマンドの <ACCOUNT_ID> を、コピーしたIDに置き換えてください。

### 2. ECRログイン
# 1時間に1回程度、実行が必要です。
aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.ap-northeast-1.amazonaws.com

### 3. Dockerイメージのビルドとプッシュ
# ビルド (buildxを使い、x86_64プラットフォームを強制)
docker buildx build --platform linux/amd64 -t line-bot-repo --load .

# タグ付け
docker tag line-bot-repo:latest <ACCOUNT_ID>.dkr.ecr.ap-northeast-1.amazonaws.com/line-bot-repo:latest

# プッシュ
docker push <ACCOUNT_ID>.dkr.ecr.ap-northeast-1.amazonaws.com/line-bot-repo:latest

### 4. Terraformの適用
terraform apply \
  -var="line_channel_access_token=$(grep LINE_CHANNEL_ACCESS_TOKEN .env | cut -d '=' -f2)" \
  -var="openai_api_key=$(grep OPENAI_API_KEY .env | cut -d '=' -f2)" \
  -var="google_api_key=$(grep GOOGLE_API_KEY .env | cut -d '=' -f2)" \
  -var="google_cse_id=$(grep GOOGLE_CSE_ID .env | cut -d '=' -f2)"

---
### 初回のみ：ビルド環境のセットアップ
# buildx用の新しいビルダーを作成し、有効化します (このコマンドはプロジェクトで一度だけ実行すればOKです)
docker buildx create --name mybuilder --use
docker buildx inspect --bootstrap

