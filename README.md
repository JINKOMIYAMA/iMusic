# YouTube M4A ダウンローダー

YouTubeの動画やプレイリストをM4Aファイルとしてダウンロードできる PWA (Progressive Web App) です。メタデータとジャケット画像が自動で埋め込まれます。

## 🚀 特徴

- YouTube動画・プレイリストの M4A ダウンロード
- メタデータ（タイトル、アーティスト）の自動埋め込み
- ジャケット画像の自動取得・変換（800x800px）
- PWA対応（iPhoneホーム画面追加可能）
- Basic認証によるセキュリティ
- Railway での無料デプロイ

## 📁 プロジェクト構成

```
iMusic m4a/
├── frontend/                 # React + Vite + TypeScript
│   ├── src/
│   │   ├── components/
│   │   │   ├── InstallPWA.tsx   # PWAインストール促進コンポーネント
│   │   │   └── ...
│   │   ├── pages/
│   │   │   └── Index.tsx        # メインページ
│   │   └── App.tsx
│   ├── public/
│   │   ├── manifest.json        # PWA マニフェスト
│   │   └── sw.js               # Service Worker
│   ├── package.json
│   ├── vite.config.ts
│   ├── railway.toml           # Frontend Railway設定
│   └── env.example            # 環境変数例
├── backend/                  # FastAPI + Python
│   ├── app.py                # メインAPIサーバー
│   ├── requirements.txt
│   ├── railway.toml          # Backend Railway設定
│   └── env.example           # 環境変数例
├── .github/workflows/        # GitHub Actions CI/CD
│   ├── deploy-backend.yml
│   └── deploy-frontend.yml
└── README.md
```

## 🛠️ ローカル開発手順

### 1. 必要なソフトウェア

- Python 3.8+
- Node.js 18+
- FFmpeg

### 2. バックエンドの起動

```bash
# 仮想環境作成・有効化
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
cd backend
pip install -r requirements.txt

# 環境変数設定
cp env.example .env
# .env ファイルを編集して認証情報を設定

# サーバー起動
python app.py
```

### 3. フロントエンドの起動

```bash
# 別ターミナルで
cd frontend
npm install

# 開発サーバー起動
npm run dev
```

### 4. アクセス

- フロントエンド: http://localhost:5173
- バックエンドAPI: http://localhost:8000

## 🚀 Railway デプロイ手順

### 1. Railway アカウント作成

1. [Railway](https://railway.app/) でアカウント作成
2. GitHub アカウントと連携

### 2. 新しいプロジェクト作成

1. Railway ダッシュボードで「New Project」
2. 「Deploy from GitHub repo」を選択
3. このリポジトリを選択

### 3. サービスの個別デプロイ

#### Backend サービス

1. Railway で新しいサービスを追加
2. 「Source」を `backend` フォルダに設定
3. 環境変数を設定：
   - `BASIC_AUTH_USERNAME`: 認証ユーザー名
   - `BASIC_AUTH_PASSWORD`: 認証パスワード
   - `PORT`: 8000 (自動設定)

#### Frontend サービス

1. Railway で新しいサービスを追加
2. 「Source」を `frontend` フォルダに設定
3. 環境変数を設定：
   - `VITE_API_BASE_URL`: バックエンドサービスのURL
   - `PORT`: 3000 (自動設定)

### 4. GitHub Secrets 設定

Repository の Settings → Secrets and variables → Actions で以下を設定：

| Secret名 | 説明 | 例 |
|----------|------|-----|
| `RAILWAY_TOKEN` | Railway API トークン | `rltk_xxx...` |
| `BASIC_AUTH_USERNAME` | Basic認証ユーザー名 | `admin` |
| `BASIC_AUTH_PASSWORD` | Basic認証パスワード | `secure_password` |
| `VITE_API_BASE_URL` | バックエンドURL | `https://your-backend.railway.app` |

### 5. Railway Token の取得

```bash
# Railway CLI インストール
curl -fsSL https://railway.app/install.sh | sh

# ログイン
railway login

# トークン表示
railway login --token
```

## 📱 PWA 対応

### iPhone での利用方法

1. Safari でアプリにアクセス
2. 画面下部の「共有」アイコンをタップ
3. 「ホーム画面に追加」を選択
4. ホーム画面のアイコンからアプリを起動

### 必要なアイコン

PWA として正常に動作させるため、以下のアイコンファイルを `frontend/public/` に配置してください：

- `favicon.ico` (32x32)
- `favicon-16x16.png` (16x16)
- `favicon-32x32.png` (32x32)
- `apple-touch-icon.png` (180x180)
- `android-chrome-192x192.png` (192x192)
- `android-chrome-512x512.png` (512x512)
- `icon-512x512.png` (512x512)

## ⚠️ 制限事項・注意点

### Railway 無料枠の制限

- **月間実行時間**: 500時間/月
- **休眠機能**: 非アクティブ時は自動で休眠
- **起動時間**: 休眠からの復帰に数秒かかる場合がある
- **メモリ**: 512MB制限

### 著作権について

- 著作権で保護されたコンテンツのダウンロードは法的な問題を引き起こす可能性があります
- 個人利用の範囲内で使用してください
- 商用利用は避けてください

### 技術的制限

- プレイリストは最大50曲まで
- 大きなファイルのダウンロードには時間がかかります
- 地域制限のある動画はダウンロードできない場合があります

## 🔧 トラブルシューティング

### よくある問題

1. **「動画情報を取得できませんでした」**
   - URL が正しいか確認
   - 動画が公開されているか確認
   - しばらく時間をおいて再試行

2. **認証が求められる**
   - 設定した `BASIC_AUTH_USERNAME` と `BASIC_AUTH_PASSWORD` を入力

3. **PWA がインストールできない**
   - HTTPS で配信されているか確認
   - manifest.json が正しく配置されているか確認

### ログの確認

```bash
# Backend ログ
railway logs --service backend

# Frontend ログ
railway logs --service frontend
```

## 🔄 更新・メンテナンス

### 依存関係の更新

```bash
# Backend
cd backend
pip list --outdated
pip install --upgrade package_name

# Frontend
cd frontend
npm outdated
npm update
```

### Railway での環境変数更新

1. Railway ダッシュボードでサービスを選択
2. 「Variables」タブで環境変数を編集
3. 「Deploy」で再デプロイ

## 📄 ライセンス

このプロジェクトは個人利用を目的としています。商用利用は避けてください。

## 🤝 コントリビューション

1. フォークを作成
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. コミット (`git commit -m 'Add amazing feature'`)
4. プッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを開く

---

**注意**: このアプリはYouTubeの利用規約に従って使用してください。著作権で保護されたコンテンツのダウンロードは法的な問題を引き起こす可能性があります。
# iMusic
