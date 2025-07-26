#!/bin/bash

echo "🎵 YouTube MP3 ダウンローダー - ローカル版"
echo "=================================="

# Python環境の確認
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3がインストールされていません"
    echo "Homebrewでインストールしてください: brew install python"
    exit 1
fi

# Node.jsの確認
if ! command -v node &> /dev/null; then
    echo "❌ Node.jsがインストールされていません"
    echo "Homebrewでインストールしてください: brew install node"
    exit 1
fi

# FFmpegの確認（yt-dlpで音声変換に必要）
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  FFmpegがインストールされていません"
    echo "音声変換のためにインストールしてください: brew install ffmpeg"
    read -p "FFmpegなしで続行しますか？ (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Python仮想環境の作成・アクティベート
if [ ! -d "venv" ]; then
    echo "📦 Python仮想環境を作成中..."
    python3 -m venv venv
fi

echo "🔧 Python仮想環境をアクティベート中..."
source venv/bin/activate

# Python依存関係のインストール
echo "📥 Python依存関係をインストール中..."
pip install -r requirements-local.txt

# Node.js依存関係のインストール
if [ ! -d "node_modules" ]; then
    echo "📥 Node.js依存関係をインストール中..."
    npm install
fi

# ダウンロードディレクトリの作成
mkdir -p downloads

echo "🚀 アプリケーションを起動中..."
echo ""
echo "バックエンドサーバー: http://127.0.0.1:8000"
echo "フロントエンド: http://localhost:5173"
echo ""
echo "終了するには Ctrl+C を押してください"
echo ""

# バックエンドとフロントエンドを並行起動
python3 app.py &
BACKEND_PID=$!

npm run dev &
FRONTEND_PID=$!

# 終了時のクリーンアップ
cleanup() {
    echo ""
    echo "🛑 アプリケーションを終了中..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# プロセスが終了するまで待機
wait 