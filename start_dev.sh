#!/bin/bash

# YouTube M4A変換アプリケーション開発環境起動スクリプト
echo "🎵 YouTube M4A変換アプリケーション起動中..."

# 色付きメッセージ用の関数
print_info() {
    echo -e "\033[36m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[32m[SUCCESS]\033[0m $1"
}

print_error() {
    echo -e "\033[31m[ERROR]\033[0m $1"
}

print_warning() {
    echo -e "\033[33m[WARNING]\033[0m $1"
}

# 必要なコマンドの存在確認
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 コマンドが見つかりません。インストールしてください。"
        exit 1
    fi
}

# 仮想環境の確認と作成
setup_python_env() {
    print_info "Python環境をセットアップ中..."
    
    # 仮想環境が存在しない場合は作成
    if [ ! -d "venv" ]; then
        print_info "仮想環境を作成中..."
        python3 -m venv venv
    fi
    
    # 仮想環境をアクティベート
    source venv/bin/activate
    
    # 依存関係をインストール
    if [ -f "requirements.txt" ]; then
        print_info "Python依存関係をインストール中..."
        pip install -r requirements.txt > /dev/null 2>&1
    fi
    
    print_success "Python環境のセットアップ完了"
}

# Node.js環境のセットアップ
setup_node_env() {
    print_info "Node.js環境をセットアップ中..."
    
    # node_modulesが存在しない場合はインストール
    if [ ! -d "node_modules" ]; then
        print_info "Node.js依存関係をインストール中..."
        npm install > /dev/null 2>&1
    fi
    
    print_success "Node.js環境のセットアップ完了"
}

# 既存のプロセスを停止
cleanup_processes() {
    print_info "既存のプロセスをクリーンアップ中..."
    
    # ポート8000と5173を使用しているプロセスを停止
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    lsof -ti:5173 | xargs kill -9 2>/dev/null || true
    
    # python app.pyプロセスを停止
    pkill -f "python app.py" 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true
    
    sleep 2
    print_success "クリーンアップ完了"
}

# メイン処理
main() {
    print_info "YouTube M4A変換アプリケーション開発環境を起動します"
    
    # 必要なコマンドの確認
    check_command "python3"
    check_command "npm"
    check_command "lsof"
    
    # 既存プロセスのクリーンアップ
    cleanup_processes
    
    # 環境セットアップ
    setup_python_env
    setup_node_env
    
    print_info "サーバーを起動中..."
    
    # バックエンド（FastAPI）を起動
    source venv/bin/activate
    python app.py &
    BACKEND_PID=$!
    
    # 少し待ってからフロントエンドを起動
    sleep 3
    
    # フロントエンド（React + Vite）を起動
    npm run dev &
    FRONTEND_PID=$!
    
    # 起動完了メッセージ
    sleep 5
    echo ""
    echo "🎉 起動完了！"
    echo ""
    echo "📱 フロントエンド: http://localhost:5173"
    echo "🔧 バックエンドAPI: http://localhost:8000"
    echo ""
    echo "💡 使用方法:"
    echo "   1. ブラウザで http://localhost:5173 にアクセス"
    echo "   2. YouTubeのURLを入力してダウンロード"
    echo ""
    echo "⚠️  終了するには Ctrl+C を押してください"
    echo ""
    
    # プロセスの監視と終了処理
    cleanup() {
        print_info "アプリケーションを終了中..."
        kill $BACKEND_PID 2>/dev/null || true
        kill $FRONTEND_PID 2>/dev/null || true
        
        # 念のため追加クリーンアップ
        lsof -ti:8000 | xargs kill -9 2>/dev/null || true
        lsof -ti:5173 | xargs kill -9 2>/dev/null || true
        
        print_success "アプリケーションが終了しました"
        exit 0
    }
    
    # Ctrl+Cで終了処理を実行
    trap cleanup SIGINT SIGTERM
    
    # プロセスが終了するまで待機
    wait
}

# スクリプト実行
main "$@" 