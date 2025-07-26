import { useState } from "react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Progress } from "../components/ui/progress";
import { Download, Music, AlertCircle, Info, Sparkles, Play } from "lucide-react";
import { toast } from "../hooks/use-toast";
import { Alert, AlertDescription } from "../components/ui/alert";

// 動的にAPIベースURLを決定
const getApiBaseUrl = () => {
  // 開発環境では/apiプロキシを使用、本番環境では環境変数を使用
  if (import.meta.env.DEV) {
    return "/api";
  }
  return import.meta.env.VITE_API_BASE_URL || "";
};

const API_BASE_URL = getApiBaseUrl();

interface DownloadResponse {
  success: boolean;
  message: string;
  file_path: string;
  file_name: string;
}

interface PreviewResponse {
  success: boolean;
  message: string;
  title: string;
  artist: string;
  duration: number;
  uploader: string;
  description: string;
  thumbnail: string;
}

interface VideoMetadata {
  title: string;
  artist: string;
  duration: number;
  uploader: string;
  description: string;
  thumbnail: string;
}

const Index = () => {
  const [url, setUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [error, setError] = useState<string>("");
  
  // メタデータ編集機能用のstate
  const [showMetadataEdit, setShowMetadataEdit] = useState(false);
  const [metadata, setMetadata] = useState<VideoMetadata | null>(null);
  const [editedTitle, setEditedTitle] = useState("");
  const [editedArtist, setEditedArtist] = useState("");

  const handlePreview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;

    // バリデーション
    if (!url.includes("youtube.com") && !url.includes("youtu.be")) {
      setError("有効なYouTubeのURLを入力してください");
      return;
    }
    
    // プレイリストは受け付けない
    if (url.includes("list=")) {
      setError("プレイリストは対応していません。単一動画のURLを入力してください");
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE_URL}/preview`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: PreviewResponse = await response.json();
      
      if (data.success) {
        const videoMetadata = {
          title: data.title,
          artist: data.artist,
          duration: data.duration,
          uploader: data.uploader,
          description: data.description,
          thumbnail: data.thumbnail,
        };
        
        setMetadata(videoMetadata);
        setEditedTitle(data.title);
        setEditedArtist(data.artist);
        setShowMetadataEdit(true);
        
        toast({
          title: "取得完了",
          description: "動画情報を取得しました",
        });
      } else {
        setError(data.message || "プレビュー取得に失敗しました");
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "エラーが発生しました";
      setError(errorMessage);
      toast({
        title: "エラー",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!metadata || !editedTitle || !editedArtist) {
      toast({
        title: "エラー",
        description: "タイトルとアーティスト名を入力してください",
        variant: "destructive",
      });
      return;
    }

    setIsDownloading(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE_URL}/download-with-metadata`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          url, 
          title: editedTitle, 
          artist: editedArtist 
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        const data = await response.json();
        setError(data.message || "ダウンロードに失敗しました");
      } else {
        // ファイルダウンロード成功
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.download = `${editedArtist}-${editedTitle}.m4a`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(downloadUrl);
        document.body.removeChild(a);

        toast({
          title: "完了",
          description: "ダウンロードが完了しました",
        });
        
        // リセット
        setUrl("");
        setShowMetadataEdit(false);
        setMetadata(null);
        setEditedTitle("");
        setEditedArtist("");
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "エラーが発生しました";
      setError(errorMessage);
      toast({
        title: "エラー",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsDownloading(false);
    }
  };

  const handleReset = () => {
    setUrl("");
    setShowMetadataEdit(false);
    setMetadata(null);
    setEditedTitle("");
    setEditedArtist("");
    setError("");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-red-950/20 to-black relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-10 left-10 w-72 h-72 bg-red-600 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-10 right-10 w-96 h-96 bg-red-800 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-red-700 rounded-full blur-3xl animate-pulse delay-500"></div>
      </div>

      {/* Grid Pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,0,0,0.1)_1px,transparent_1px),linear-gradient(90deg,rgba(255,0,0,0.1)_1px,transparent_1px)] bg-[size:50px_50px] opacity-20"></div>

      {/* Header */}
      <header className="relative p-8 text-center">
        <div className="absolute top-6 right-6">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => window.location.href = '/about'}
            className="text-gray-400 hover:text-red-400 hover:bg-red-950/20 transition-all duration-300"
          >
            <Info className="w-4 h-4" />
          </Button>
        </div>
        
        <div className="flex justify-center mb-6">
          <div className="relative">
            <Music size={60} className="text-red-600 drop-shadow-2xl animate-pulse" />
            <div className="absolute -inset-2 bg-red-600/20 rounded-full blur-xl animate-pulse"></div>
          </div>
        </div>
        
        <h1 className="text-6xl font-bold bg-gradient-to-r from-white via-red-200 to-white bg-clip-text text-transparent tracking-wider drop-shadow-lg">
          iMusic
        </h1>
        
        <div className="flex justify-center mt-4">
          <div className="flex items-center gap-2 bg-red-950/30 px-4 py-2 rounded-full border border-red-800/50">
            <Sparkles className="w-4 h-4 text-red-400" />
            <span className="text-red-200 text-sm font-medium">M4A High Quality</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center px-4 relative z-10">
        <div className="w-full max-w-md space-y-8">
          
          {/* Error Display */}
          {error && (
            <Alert className="bg-red-900/30 border-red-600/50 text-red-200 shadow-lg shadow-red-900/20">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* URL Input */}
          <Card className="bg-black/60 border-red-800/50 shadow-2xl shadow-red-950/30 backdrop-blur-sm">
            <CardContent className="p-8">
              <form onSubmit={handlePreview} className="space-y-6">
                <div className="relative">
                  <Input
                    type="url"
                    placeholder="YouTube URL"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    disabled={isLoading || isDownloading}
                    className="bg-black/80 border-red-700/50 text-white placeholder:text-gray-400 h-14 text-center text-lg rounded-lg focus:border-red-500 focus:ring-2 focus:ring-red-500/20 transition-all duration-300"
                  />
                  <div className="absolute inset-0 bg-gradient-to-r from-red-600/10 to-transparent rounded-lg pointer-events-none"></div>
                </div>
                
                <div className="flex gap-3">
                  <Button 
                    type="submit" 
                    className="flex-1 bg-gradient-to-r from-red-600 to-red-700 hover:from-red-500 hover:to-red-600 text-white h-14 font-semibold rounded-lg shadow-lg shadow-red-900/30 transition-all duration-300 hover:shadow-red-900/50 hover:scale-105"
                    disabled={!url || isLoading || isDownloading}
                  >
                    {isLoading ? (
                      <div className="flex items-center gap-2">
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        処理中...
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <Play className="w-5 h-5" />
                        プレビュー
                      </div>
                    )}
                  </Button>
                  {showMetadataEdit && (
                    <Button 
                      type="button"
                      variant="outline"
                      onClick={handleReset}
                      className="border-red-600/50 text-red-200 hover:bg-red-950/20 hover:border-red-500 h-14 px-6 rounded-lg transition-all duration-300"
                    >
                      リセット
                    </Button>
                  )}
                </div>
              </form>
            </CardContent>
          </Card>

          {/* Loading */}
          {isLoading && (
            <Card className="bg-black/60 border-red-800/50 shadow-2xl shadow-red-950/30 backdrop-blur-sm">
              <CardContent className="p-8">
                <div className="text-center space-y-4">
                  <div className="text-red-200 font-medium">動画情報を取得中...</div>
                  <div className="relative">
                    <Progress value={undefined} className="h-2 bg-red-950/50" />
                    <div className="absolute inset-0 bg-gradient-to-r from-red-600/50 to-red-800/50 rounded-full animate-pulse"></div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Metadata Edit */}
          {showMetadataEdit && (
            <Card className="bg-black/60 border-red-800/50 shadow-2xl shadow-red-950/30 backdrop-blur-sm">
              <CardContent className="p-8">
                
                {/* Artwork */}
                {metadata?.thumbnail && (
                  <div className="flex justify-center mb-8">
                    <div className="relative">
                      <img
                        src={metadata.thumbnail}
                        alt="アートワーク"
                        className="w-32 h-32 object-cover rounded-xl border-2 border-red-700/50 shadow-lg shadow-red-900/30"
                        onError={(e) => {
                          const target = e.target as HTMLImageElement;
                          target.style.display = 'none';
                        }}
                      />
                      <div className="absolute -inset-1 bg-gradient-to-r from-red-600/30 to-red-800/30 rounded-xl blur-sm -z-10"></div>
                    </div>
                  </div>
                )}

                {/* Metadata Fields */}
                <div className="space-y-6 mb-8">
                  <div>
                    <Label className="text-red-200 text-sm uppercase tracking-wide font-medium">タイトル</Label>
                    <Input
                      value={editedTitle}
                      onChange={(e) => setEditedTitle(e.target.value)}
                      className="bg-black/80 border-red-700/50 text-white mt-2 h-12 rounded-lg focus:border-red-500 focus:ring-2 focus:ring-red-500/20 transition-all duration-300"
                    />
                  </div>
                  <div>
                    <Label className="text-red-200 text-sm uppercase tracking-wide font-medium">アーティスト</Label>
                    <Input
                      value={editedArtist}
                      onChange={(e) => setEditedArtist(e.target.value)}
                      className="bg-black/80 border-red-700/50 text-white mt-2 h-12 rounded-lg focus:border-red-500 focus:ring-2 focus:ring-red-500/20 transition-all duration-300"
                    />
                  </div>
                </div>

                {/* Download Button */}
                <Button 
                  onClick={handleDownload}
                  className="w-full bg-gradient-to-r from-red-600 to-red-700 hover:from-red-500 hover:to-red-600 text-white h-14 font-semibold rounded-lg shadow-lg shadow-red-900/30 transition-all duration-300 hover:shadow-red-900/50 hover:scale-105"
                  disabled={isDownloading}
                >
                  {isDownloading ? (
                    <div className="flex items-center gap-2">
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      ダウンロード中...
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <Download className="w-5 h-5" />
                      ダウンロード
                    </div>
                  )}
                </Button>
              </CardContent>
            </Card>
          )}

        </div>
      </main>
    </div>
  );
};

export default Index;
