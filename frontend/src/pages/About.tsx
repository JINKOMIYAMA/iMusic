
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertTriangle, Info, Music, ArrowLeft, Download, Settings, Globe, Sparkles, Shield, Clock } from "lucide-react";

const About = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-red-950/20 to-black relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-20 left-20 w-64 h-64 bg-red-600 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-20 right-20 w-80 h-80 bg-red-800 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/3 right-1/3 w-72 h-72 bg-red-700 rounded-full blur-3xl animate-pulse delay-500"></div>
      </div>

      {/* Grid Pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,0,0,0.1)_1px,transparent_1px),linear-gradient(90deg,rgba(255,0,0,0.1)_1px,transparent_1px)] bg-[size:50px_50px] opacity-20"></div>

      {/* Header */}
      <header className="relative p-8 border-b border-red-800/50 backdrop-blur-sm">
        <div className="flex items-center gap-6">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => window.location.href = '/'}
            className="text-gray-400 hover:text-red-400 hover:bg-red-950/20 transition-all duration-300"
          >
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div className="flex items-center gap-3">
            <div className="relative">
              <Music className="w-8 h-8 text-red-600 drop-shadow-lg" />
              <div className="absolute -inset-1 bg-red-600/20 rounded-full blur-md animate-pulse"></div>
            </div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-white via-red-200 to-white bg-clip-text text-transparent">
              iMusic
            </h1>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="relative z-10 p-8">
        <div className="max-w-4xl mx-auto space-y-8">
          
          {/* About */}
          <Card className="bg-black/60 border-red-800/50 shadow-2xl shadow-red-950/30 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-3">
                <div className="relative">
                  <Info className="w-6 h-6 text-red-400" />
                  <div className="absolute -inset-1 bg-red-400/20 rounded-full blur-sm animate-pulse"></div>
                </div>
                About iMusic
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6 text-gray-300">
              <p className="text-lg leading-relaxed">
                iMusicは、YouTubeの動画を<span className="text-red-400 font-semibold">M4A（高品質オーディオ）</span>形式でダウンロードできるWebアプリケーションです。
                メタデータとジャケット画像を自動的に追加し、音楽ライブラリにそのまま保存できます。
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex items-center gap-3 bg-red-950/20 p-4 rounded-lg border border-red-800/30">
                  <Download className="w-5 h-5 text-red-400" />
                  <div>
                    <p className="font-medium text-red-200">M4A形式</p>
                    <p className="text-sm text-gray-400">高品質オーディオ</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 bg-red-950/20 p-4 rounded-lg border border-red-800/30">
                  <Settings className="w-5 h-5 text-red-400" />
                  <div>
                    <p className="font-medium text-red-200">メタデータ編集</p>
                    <p className="text-sm text-gray-400">タイトル・アーティスト</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 bg-red-950/20 p-4 rounded-lg border border-red-800/30">
                  <Globe className="w-5 h-5 text-red-400" />
                  <div>
                    <p className="font-medium text-red-200">ジャケット画像</p>
                    <p className="text-sm text-gray-400">自動取得・埋め込み</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* How to Use */}
          <Card className="bg-black/60 border-red-800/50 shadow-2xl shadow-red-950/30 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-3">
                <div className="relative">
                  <Sparkles className="w-6 h-6 text-red-400" />
                  <div className="absolute -inset-1 bg-red-400/20 rounded-full blur-sm animate-pulse"></div>
                </div>
                使い方
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6 text-gray-300">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="flex gap-4">
                    <div className="w-10 h-10 bg-gradient-to-r from-red-600 to-red-700 text-white rounded-full flex items-center justify-center text-sm font-bold shadow-lg shadow-red-900/30">1</div>
                    <div>
                      <p className="font-semibold text-red-200">YouTube URLを入力</p>
                      <p className="text-sm text-gray-400">単一動画のURLを入力してください</p>
                    </div>
                  </div>
                  <div className="flex gap-4">
                    <div className="w-10 h-10 bg-gradient-to-r from-red-600 to-red-700 text-white rounded-full flex items-center justify-center text-sm font-bold shadow-lg shadow-red-900/30">2</div>
                    <div>
                      <p className="font-semibold text-red-200">プレビューを確認</p>
                      <p className="text-sm text-gray-400">動画情報とジャケット画像を確認</p>
                    </div>
                  </div>
                </div>
                <div className="space-y-4">
                  <div className="flex gap-4">
                    <div className="w-10 h-10 bg-gradient-to-r from-red-600 to-red-700 text-white rounded-full flex items-center justify-center text-sm font-bold shadow-lg shadow-red-900/30">3</div>
                    <div>
                      <p className="font-semibold text-red-200">メタデータを編集</p>
                      <p className="text-sm text-gray-400">タイトルとアーティスト名を調整</p>
                    </div>
                  </div>
                  <div className="flex gap-4">
                    <div className="w-10 h-10 bg-gradient-to-r from-red-600 to-red-700 text-white rounded-full flex items-center justify-center text-sm font-bold shadow-lg shadow-red-900/30">4</div>
                    <div>
                      <p className="font-semibold text-red-200">ダウンロード</p>
                      <p className="text-sm text-gray-400">M4Aファイルをダウンロード</p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Technical Details */}
          <Card className="bg-black/60 border-red-800/50 shadow-2xl shadow-red-950/30 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-3">
                <div className="relative">
                  <Settings className="w-6 h-6 text-red-400" />
                  <div className="absolute -inset-1 bg-red-400/20 rounded-full blur-sm animate-pulse"></div>
                </div>
                技術的な詳細
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-gray-300">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="p-4 bg-red-950/20 rounded-lg border border-red-800/30">
                    <h4 className="font-semibold text-red-200 mb-2">対応フォーマット</h4>
                    <p className="text-sm text-gray-400">M4A（AAC）- 高品質オーディオ</p>
                  </div>
                  <div className="p-4 bg-red-950/20 rounded-lg border border-red-800/30">
                    <h4 className="font-semibold text-red-200 mb-2">メタデータ</h4>
                    <p className="text-sm text-gray-400">タイトル、アーティスト名、ジャケット画像を自動追加</p>
                  </div>
                </div>
                <div className="space-y-4">
                  <div className="p-4 bg-red-950/20 rounded-lg border border-red-800/30">
                    <h4 className="font-semibold text-red-200 mb-2">対応サイト</h4>
                    <p className="text-sm text-gray-400">YouTube（単一動画のみ）</p>
                  </div>
                  <div className="p-4 bg-red-950/20 rounded-lg border border-red-800/30">
                    <h4 className="font-semibold text-red-200 mb-2">ローカル実行</h4>
                    <p className="text-sm text-gray-400">バックエンドサーバー（http://localhost:8000）が必要</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* PWA Installation */}
          <Card className="bg-black/60 border-red-800/50 shadow-2xl shadow-red-950/30 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-3">
                <div className="relative">
                  <Globe className="w-6 h-6 text-red-400" />
                  <div className="absolute -inset-1 bg-red-400/20 rounded-full blur-sm animate-pulse"></div>
                </div>
                iPhone/iPadでの利用
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6 text-gray-300">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-4 bg-red-950/20 rounded-lg border border-red-800/30">
                  <h4 className="font-semibold text-red-200 mb-2">ホーム画面に追加</h4>
                  <p className="text-sm text-gray-400">
                    Safariで「共有」→「ホーム画面に追加」でアプリのように使用できます
                  </p>
                </div>
                <div className="p-4 bg-red-950/20 rounded-lg border border-red-800/30">
                  <h4 className="font-semibold text-red-200 mb-2">ファイルの保存</h4>
                  <p className="text-sm text-gray-400">
                    ダウンロード後、共有ボタンから「ファイル」アプリに保存してください
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Warning */}
          <Card className="bg-red-900/30 border-red-600/50 shadow-2xl shadow-red-950/30 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-red-200 flex items-center gap-3">
                <div className="relative">
                  <AlertTriangle className="w-6 h-6 text-red-400" />
                  <div className="absolute -inset-1 bg-red-400/20 rounded-full blur-sm animate-pulse"></div>
                </div>
                重要な注意事項
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6 text-red-100">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="p-4 bg-red-900/40 rounded-lg border border-red-700/50">
                    <h4 className="font-semibold text-red-200 mb-2 flex items-center gap-2">
                      <Shield className="w-4 h-4" />
                      著作権について
                    </h4>
                    <p className="text-sm text-red-100">
                      著作権で保護されたコンテンツのダウンロードは、個人利用の範囲内で行ってください。
                      商用利用や再配布は法的な問題を引き起こす可能性があります。
                    </p>
                  </div>
                  <div className="p-4 bg-red-900/40 rounded-lg border border-red-700/50">
                    <h4 className="font-semibold text-red-200 mb-2 flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4" />
                      利用責任
                    </h4>
                    <p className="text-sm text-red-100">
                      本ツールの使用により生じた問題について、開発者は一切の責任を負いません。
                      ユーザー自身の責任において利用してください。
                    </p>
                  </div>
                </div>
                <div className="space-y-4">
                  <div className="p-4 bg-red-900/40 rounded-lg border border-red-700/50">
                    <h4 className="font-semibold text-red-200 mb-2 flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      サービスの制限
                    </h4>
                    <p className="text-sm text-red-100">
                      YouTubeの仕様変更により、一時的にサービスが利用できなくなる可能性があります。
                    </p>
                  </div>
                  <div className="p-4 bg-red-900/40 rounded-lg border border-red-700/50">
                    <h4 className="font-semibold text-red-200 mb-2">品質保証</h4>
                    <p className="text-sm text-red-100">
                      ダウンロードされるファイルの品質は、元の動画の品質に依存します。
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

        </div>
      </main>
    </div>
  );
};

export default About;
