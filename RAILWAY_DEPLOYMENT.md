# Railway デプロイガイド

## 概要

このアプリケーションは以下の2つのサービスとしてRailwayにデプロイします：

1. **Backend Service** - FastAPI (Python)
2. **Frontend Service** - React PWA (Node.js/Static)

## 前提条件

- [Railway](https://railway.app/) アカウント
- GitHubアカウント（Railwayと連携済み）
- このリポジトリがGitHubにプッシュ済み

## デプロイ手順

### 1. Railwayプロジェクト作成

1. Railway ダッシュボードで「New Project」をクリック
2. 「Deploy from GitHub repo」を選択
3. このリポジトリを選択

### 2. Backend Service のデプロイ

#### 2.1 サービス設定
1. Railway ダッシュボードで「New Service」→「GitHub Repo」
2. Root Directory を `backend` に設定
3. サービス名を `backend` または `api` に設定

#### 2.2 環境変数設定
Railway の Variables タブで以下を設定：

```
ALLOWED_ORIGINS=*
ENVIRONMENT=production
```

**注意**: 本番環境では `ALLOWED_ORIGINS` をフロントエンドの具体的なURLに変更することを推奨します。

#### 2.3 デプロイ確認
- デプロイ完了後、生成されたURLをメモ（例: `https://backend-production-xxxx.railway.app`）
- `/docs` エンドポイントでAPIドキュメントが表示されることを確認

### 3. Frontend Service のデプロイ

#### 3.1 サービス設定
1. Railway ダッシュボードで「New Service」→「GitHub Repo」
2. Root Directory を `frontend` に設定
3. サービス名を `frontend` に設定

#### 3.2 環境変数設定
Railway の Variables タブで以下を設定：

```
VITE_API_BASE_URL=https://your-backend-service-url.railway.app
```

**注意**: `your-backend-service-url` は手順2.3で取得したBackend ServiceのURLに置き換えてください。

#### 3.3 デプロイ確認
- デプロイ完了後、フロントエンドのURLにアクセス
- アプリケーションが正常に表示されることを確認

### 4. CORS設定の更新（本番環境）

Backend ServiceのCORS設定を厳密にする場合：

1. Backend Service の Variables で `ALLOWED_ORIGINS` を更新：
```
ALLOWED_ORIGINS=https://your-frontend-service-url.railway.app
```

2. サービスを再デプロイ

## 環境変数一覧

### Backend Service

| 変数名 | 必須 | 説明 | 例 |
|--------|------|------|-----|
| `ALLOWED_ORIGINS` | - | CORS許可オリジン | `https://frontend.railway.app` |
| `ENVIRONMENT` | - | 環境設定 | `production` |
| `PORT` | - | ポート番号（Railwayが自動設定） | `8000` |

### Frontend Service

| 変数名 | 必須 | 説明 | 例 |
|--------|------|------|-----|
| `VITE_API_BASE_URL` | ✅ | Backend APIのURL | `https://backend.railway.app` |

## トラブルシューティング

### よくある問題

#### 1. Frontend からBackend APIにアクセスできない
- `VITE_API_BASE_URL` が正しく設定されているか確認
- Backend の `ALLOWED_ORIGINS` にFrontend URLが含まれているか確認
- ブラウザの開発者ツールでネットワークエラーを確認

#### 2. アプリケーションにアクセスできない
- Backend と Frontend の両方が正常にデプロイされているか確認
- Railway のサービス状態を確認

#### 3. FFmpeg関連エラー
- Backend のログで FFmpeg の検出状況を確認
- `/debug/ffmpeg` エンドポイントでFFmpegの状態を確認

#### 4. PWAインストールができない
- HTTPSで配信されているか確認（RailwayではデフォルトでHTTPS）
- `manifest.json` と Service Worker が正しく配信されているか確認

### ログ確認

Railway のダッシュボードで各サービスのログを確認できます：

1. サービスを選択
2. 「Deployments」タブ
3. 最新のデプロイメントをクリック
4. 「View Logs」でログを確認

### 手動デプロイ

コードを更新した場合、Railwayは自動的に再デプロイしますが、手動でも可能です：

1. サービスを選択
2. 「Deployments」タブ
3. 「Deploy」ボタンをクリック

## セキュリティ考慮事項

1. **CORS設定**: 本番環境では具体的なフロントエンドURLを指定
2. **HTTPS**: RailwayではデフォルトでHTTPS配信されます
3. **ファイルアクセス**: アプリケーションは一時ファイルのみ使用し、24時間後に自動削除
4. **公開アクセス**: 認証なしでアクセス可能なため、適切な利用規約の表示を検討

## 料金について

- Railway の無料枠では月500時間の実行時間が利用可能
- 非アクティブ時は自動スリープするため、実際の使用時間のみカウント
- 詳細は [Railway Pricing](https://railway.app/pricing) を参照

## サポート

問題が発生した場合：

1. このドキュメントのトラブルシューティングを確認
2. Railway のログを確認
3. GitHub Issues で報告

---

デプロイ完了後、アプリケーションは以下のURLでアクセス可能になります：
- **Frontend**: `https://your-frontend-service.railway.app`
- **Backend API**: `https://your-backend-service.railway.app`
- **API Documentation**: `https://your-backend-service.railway.app/docs`