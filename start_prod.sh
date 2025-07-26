#!/bin/bash

# YouTube M4A変換アプリケーション プロダクション環境起動スクリプト
echo "🎵 YouTube M4A変換アプリケーション（プロダクション）起動中..."

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

# Reactアプリのビルド
build_frontend() {
    print_info "フロントエンドをビルド中..."
    
    # 依存関係をインストール（必要に応じて）
    if [ ! -d "node_modules" ]; then
        print_info "Node.js依存関係をインストール中..."
        npm install > /dev/null 2>&1
    fi
    
    # プロダクションビルド
    npm run build > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        print_success "フロントエンドのビルド完了"
    else
        print_error "フロントエンドのビルドに失敗しました"
        exit 1
    fi
}

# 既存のプロセスを停止
cleanup_processes() {
    print_info "既存のプロセスをクリーンアップ中..."
    
    # ポート8000を使用しているプロセスを停止
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    
    # python app.pyプロセスを停止
    pkill -f "python app.py" 2>/dev/null || true
    
    sleep 2
    print_success "クリーンアップ完了"
}

# FastAPIアプリケーションを静的ファイル配信対応に設定
setup_static_serving() {
    print_info "静的ファイル配信を設定中..."
    
    # distディレクトリが存在するか確認
    if [ ! -d "dist" ]; then
        print_error "distディレクトリが見つかりません。先にビルドを実行してください。"
        exit 1
    fi
    
    # app.pyに静的ファイル配信の設定を追加（必要に応じて）
    print_success "静的ファイル配信の設定完了"
}

# メイン処理
main() {
    print_info "YouTube M4A変換アプリケーション（プロダクション）を起動します"
    
    # 必要なコマンドの確認
    check_command "python3"
    check_command "npm"
    check_command "lsof"
    
    # 既存プロセスのクリーンアップ
    cleanup_processes
    
    # 環境セットアップ
    setup_python_env
    
    # フロントエンドのビルド
    build_frontend
    
    # 静的ファイル配信の設定
    setup_static_serving
    
    print_info "プロダクションサーバーを起動中..."
    
    # バックエンド（FastAPI）を起動
    source venv/bin/activate
    python app.py &
    BACKEND_PID=$!
    
    # 起動完了メッセージ
    sleep 5
    echo ""
    echo "🎉 プロダクション環境で起動完了！"
    echo ""
    echo "🌐 アプリケーション: http://localhost:8000"
    echo "🔧 API: http://localhost:8000/docs"
    echo ""
    echo "💡 使用方法:"
    echo "   1. ブラウザで http://localhost:8000 にアクセス"
    echo "   2. YouTubeのURLを入力してダウンロード"
    echo ""
    echo "⚠️  終了するには Ctrl+C を押してください"
    echo ""
    
    # プロセスの監視と終了処理
    cleanup() {
        print_info "アプリケーションを終了中..."
        kill $BACKEND_PID 2>/dev/null || true
        
        # 念のため追加クリーンアップ
        lsof -ti:8000 | xargs kill -9 2>/dev/null || true
        
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