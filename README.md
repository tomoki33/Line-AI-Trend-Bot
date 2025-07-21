## 仮想環境立ち上げ
cd /Users/tomoki33/Desktop/linebot
python3 -m venv venv
source venv/bin/activate  # Windowsなら venv\Scripts\activate
pip install -r requirements.txt

## ローカル実行
python test_search.py