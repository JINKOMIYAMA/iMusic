#!/bin/bash

# YouTube M4A Converter 起動スクリプト

echo "YouTube M4A Converter を起動中..."

# プロジェクトディレクトリに移動
cd /Users/apple/Desktop/youtube-m4a-converter

# 仮想環境をアクティベート
if [ -d "venv" ]; then
    echo "仮想環境をアクティベート中..."
    source venv/bin/activate
fi

# 依存関係チェック
echo "依存関係をチェック中..."
pip install -r requirements.txt > /dev/null 2>&1

# アプリケーション起動
echo "アプリケーションを起動中..."
echo "ブラウザで http://127.0.0.1:8000 にアクセスしてください"
echo "停止するには Ctrl+C を押してください"
echo ""

python app.py 