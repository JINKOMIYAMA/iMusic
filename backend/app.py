from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Request
from pydantic import BaseModel
import yt_dlp
import os
import uuid
import re
import asyncio
from pathlib import Path
import shutil
import logging
import zipfile
from typing import Optional
import subprocess
import requests
from PIL import Image
from io import BytesIO
from mutagen.mp4 import MP4, MP4Cover
import time
from datetime import datetime
from dotenv import load_dotenv
import glob

# 環境変数を読み込み
load_dotenv()

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_ffmpeg_path():
    """FFmpegのパスを検索"""
    logger.info("FFmpegの検索を開始...")
    
    # 検索パスのリスト（Railway/Nixpacks環境に最適化）
    search_paths = [
        "ffmpeg",  # PATHから検索（最も確実）
        "/usr/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
        "/bin/ffmpeg",
        "/root/.nix-profile/bin/ffmpeg",
        "/nix/var/nix/profiles/default/bin/ffmpeg",
        "/opt/homebrew/bin/ffmpeg",
    ]
    
    # 1. まずPATHから検索
    logger.info("PATHからFFmpegを検索...")
    try:
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            logger.info(f"✅ PATHからFFmpegが見つかりました: {ffmpeg_path}")
            return ffmpeg_path
    except Exception as e:
        logger.info(f"PATHからの検索でエラー: {e}")
    
    # 2. which コマンドでも試す
    logger.info("which コマンドでFFmpegを検索...")
    try:
        result = subprocess.run(["which", "ffmpeg"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            ffmpeg_path = result.stdout.strip()
            if ffmpeg_path and os.path.isfile(ffmpeg_path):
                logger.info(f"✅ which コマンドでFFmpegが見つかりました: {ffmpeg_path}")
                return ffmpeg_path
    except Exception as e:
        logger.info(f"which コマンドでエラー: {e}")
    
    # 3. 標準的なパスを確認
    for path in search_paths:
        if path != "ffmpeg":  # 既にチェック済み
            logger.info(f"検索中: {path}")
            try:
                if os.path.isfile(path) and os.access(path, os.X_OK):
                    logger.info(f"✅ FFmpegが見つかりました: {path}")
                    return path
            except Exception as e:
                logger.info(f"  {path} の検索でエラー: {e}")
    
    # 4. Nixストアでの検索（Railway環境用）
    logger.info("Nixストアでの検索を開始...")
    try:
        # findコマンドを使用してNixストアを検索
        result = subprocess.run(
            ["find", "/nix/store", "-name", "ffmpeg", "-type", "f", "-executable"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            found_paths = result.stdout.strip().split('\n')
            for found_path in found_paths:
                if found_path and os.path.isfile(found_path):
                    logger.info(f"✅ NixストアでFFmpegが見つかりました: {found_path}")
                    return found_path
    except Exception as e:
        logger.info(f"Nixストア検索でエラー: {e}")
    
    # 5. より広範囲なglob検索
    logger.info("glob検索を実行...")
    try:
        for pattern in ["/nix/store/*/bin/ffmpeg", "/nix/store/*/usr/bin/ffmpeg"]:
            matches = glob.glob(pattern)
            if matches:
                for match in matches:
                    if os.path.isfile(match) and os.access(match, os.X_OK):
                        logger.info(f"✅ glob検索でFFmpegが見つかりました: {match}")
                        return match
    except Exception as e:
        logger.info(f"glob検索でエラー: {e}")
    
    # 6. PATHの各ディレクトリを個別に検索
    logger.info("PATHの各ディレクトリを個別に検索...")
    path_dirs = os.environ.get('PATH', '').split(':')
    for path_dir in path_dirs:
        if path_dir:
            ffmpeg_path = os.path.join(path_dir, "ffmpeg")
            try:
                if os.path.isfile(ffmpeg_path) and os.access(ffmpeg_path, os.X_OK):
                    logger.info(f"✅ PATHディレクトリでFFmpegが見つかりました: {ffmpeg_path}")
                    return ffmpeg_path
            except Exception as e:
                pass
    
    # 7. 最後の手段：システム全体での検索
    logger.info("システム全体での検索...")
    try:
        # まずルートディレクトリから検索
        result = subprocess.run(
            ["find", "/", "-name", "ffmpeg", "-type", "f", "-executable", "-not", "-path", "*/proc/*", "-not", "-path", "*/sys/*"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0 and result.stdout.strip():
            found_paths = result.stdout.strip().split('\n')
            for found_path in found_paths:
                if found_path and os.path.isfile(found_path):
                    logger.info(f"✅ システム全体検索でFFmpegが見つかりました: {found_path}")
                    return found_path
    except Exception as e:
        logger.info(f"システム全体検索でエラー: {e}")
    
    # 8. 最終確認：環境変数を調べる
    logger.info("環境変数を調べています...")
    logger.info(f"PATH: {os.environ.get('PATH', '未設定')}")
    logger.info(f"LD_LIBRARY_PATH: {os.environ.get('LD_LIBRARY_PATH', '未設定')}")
    logger.info(f"NIX_PATH: {os.environ.get('NIX_PATH', '未設定')}")
    
    logger.error("❌ FFmpegが見つかりません")
    return None

app = FastAPI(title="YouTube M4A Downloader", version="1.0.0")

# CORS設定 - 本番環境対応
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
if "*" in allowed_origins:
    # 開発環境では全てのオリジンを許可
    cors_origins = ["*"]
else:
    # 本番環境では指定されたオリジンのみ許可
    cors_origins = allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ダウンロードディレクトリの設定（Railway環境では/tmpを使用）
DOWNLOAD_DIR = Path("/tmp/downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# テンプレートの設定
templates = Jinja2Templates(directory="templates")

# 静的ファイル配信の設定（プロダクション環境用）
if Path("../dist").exists():
    app.mount("/assets", StaticFiles(directory="../dist/assets"), name="assets")
    app.mount("/static", StaticFiles(directory="../dist"), name="static")

class DownloadRequest(BaseModel):
    url: str

class DownloadResponse(BaseModel):
    success: bool
    message: str
    file_path: str = ""
    file_name: str = ""

class PreviewRequest(BaseModel):
    url: str

class PreviewResponse(BaseModel):
    success: bool
    message: str
    title: str = ""
    artist: str = ""
    duration: int = 0
    uploader: str = ""
    description: str = ""
    thumbnail: str = ""

class DownloadWithMetadataRequest(BaseModel):
    url: str
    title: str
    artist: str

def sanitize_filename(filename: str) -> str:
    """ファイル名を安全な形式に変換"""
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def parse_title_artist(title: str, uploader: str = None) -> tuple[str, str]:
    """動画タイトルからアーティスト名と曲名を解析（投稿者を優先）"""
    # 投稿者が存在する場合は優先的に使用
    if uploader and uploader.strip():
        # 投稿者をアーティストとして使用し、タイトルから投稿者名を除去
        clean_title = title
        
        # タイトルから投稿者名を除去するパターン
        uploader_patterns = [
            rf'^{re.escape(uploader)}\s*[-–—:：]\s*(.+)$',
            rf'^(.+?)\s*[-–—:：]\s*{re.escape(uploader)}$',
            rf'^{re.escape(uploader)}\s*[「『]\s*(.+?)\s*[」』]$',
            rf'^(.+?)\s*\(\s*{re.escape(uploader)}\s*\)$',
            rf'^(.+?)\s*by\s+{re.escape(uploader)}$',
        ]
        
        for pattern in uploader_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                clean_title = match.group(1).strip()
                break
        
        # 一般的な不要な文字列を除去
        clean_patterns = [
            r'\s*\(Official\s+Video\)\s*',
            r'\s*\(Official\s+Music\s+Video\)\s*',
            r'\s*\(Official\s+Audio\)\s*',
            r'\s*\(Lyrics?\)\s*',
            r'\s*\(HD\)\s*',
            r'\s*\(4K\)\s*',
            r'\s*\[Official\s+Video\]\s*',
            r'\s*\[Official\s+Music\s+Video\]\s*',
            r'\s*\[Official\s+Audio\]\s*',
            r'\s*\[Lyrics?\]\s*',
            r'\s*\[HD\]\s*',
            r'\s*\[4K\]\s*',
        ]
        
        for pattern in clean_patterns:
            clean_title = re.sub(pattern, '', clean_title, flags=re.IGNORECASE)
        
        return clean_title.strip(), uploader.strip()
    
    # 投稿者がない場合は従来のロジックを使用
    patterns = [
        r'^(.+?)\s*[-–—]\s*(.+)$',  # "Artist - Title"
        r'^(.+?)\s*[:|：]\s*(.+)$',  # "Artist: Title"
        r'^(.+?)\s*[「『]\s*(.+?)\s*[」』]$',  # "Artist「Title」"
        r'^(.+?)\s*\(\s*(.+?)\s*\)$',  # "Artist (Title)"
        r'^(.+?)\s*by\s+(.+)$',  # "Title by Artist"
        r'^(.+?)\s*ft\.?\s+(.+)$',  # "Artist ft. Other"
    ]
    
    for pattern in patterns:
        match = re.match(pattern, title, re.IGNORECASE)
        if match:
            part1, part2 = match.groups()
            # より短い方をアーティスト、長い方をタイトルとする傾向
            if len(part1) < len(part2) and not any(word in part1.lower() for word in ['feat', 'ft', 'featuring']):
                return part2.strip(), part1.strip()  # title, artist
            else:
                return part1.strip(), part2.strip()  # artist, title
    
    # パターンにマッチしない場合、全体をタイトルとして使用
    return title.strip(), "Unknown Artist"

def download_and_process_thumbnail(thumbnail_url: str, output_path: Path) -> bool:
    """サムネイル画像をダウンロードして800x800の正方形に加工"""
    try:
        logger.info(f"サムネイル画像をダウンロード中: {thumbnail_url}")
        
        # より高解像度のサムネイルを取得するためのURL調整
        if 'maxresdefault' not in thumbnail_url:
            # YouTubeの場合、最高解像度のサムネイルを試行
            if 'i.ytimg.com' in thumbnail_url:
                high_res_url = thumbnail_url.replace('hqdefault', 'maxresdefault')
                try:
                    response = requests.get(high_res_url, timeout=30)
                    if response.status_code == 200:
                        thumbnail_url = high_res_url
                        logger.info("高解像度サムネイルを使用")
                except:
                    pass  # 失敗した場合は元のURLを使用
        
        response = requests.get(thumbnail_url, timeout=30)
        response.raise_for_status()
        
        # 画像を開く
        img = Image.open(BytesIO(response.content))
        logger.info(f"元画像サイズ: {img.size}")
        
        # RGBモードに変換（透明度を削除）
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 正方形にクロップ（中央部分を使用）
        width, height = img.size
        size = min(width, height)
        left = (width - size) // 2
        top = (height - size) // 2
        right = left + size
        bottom = top + size
        
        img_cropped = img.crop((left, top, right, bottom))
        logger.info(f"クロップ後サイズ: {img_cropped.size}")
        
        # 800x800にリサイズ（高品質リサンプリング）
        img_resized = img_cropped.resize((800, 800), Image.Resampling.LANCZOS)
        
        # 画質を向上させるためのシャープネス調整
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Sharpness(img_resized)
        img_enhanced = enhancer.enhance(1.2)  # シャープネスを20%向上
        
        # 保存
        img_enhanced.save(output_path, 'JPEG', quality=95, optimize=True)
        logger.info(f"✅ サムネイル画像処理完了: {output_path.name}")
        return True
        
    except Exception as e:
        logger.error(f"サムネイル画像処理エラー: {e}")
        return False

def add_metadata_to_m4a(m4a_path: Path, title: str, artist: str, album: str = None, thumbnail_path: Path = None):
    """M4Aファイルにメタデータとジャケット画像を追加"""
    try:
        logger.info(f"メタデータを追加中: {m4a_path.name}")
        logger.info(f"  タイトル: '{title}'")
        logger.info(f"  アーティスト: '{artist}'")
        if album:
            logger.info(f"  アルバム: '{album}'")
        
        # M4Aファイルを開く
        audio = MP4(m4a_path)
        
        # 既存のメタデータをクリア
        audio.clear()
        
        # メタデータを設定
        audio['\xa9nam'] = [title]  # タイトル
        audio['\xa9ART'] = [artist]  # アーティスト
        audio['\xa9day'] = [str(datetime.now().year)]  # 年
        audio['\xa9gen'] = ['Music']  # ジャンル
        
        # ジャケット画像を追加
        if thumbnail_path and thumbnail_path.exists():
            try:
                with open(thumbnail_path, 'rb') as img_file:
                    img_data = img_file.read()
                    if img_data:
                        audio['covr'] = [MP4Cover(img_data, MP4Cover.FORMAT_JPEG)]
                        logger.info(f"✅ ジャケット画像を追加: {thumbnail_path.name} ({len(img_data)} bytes)")
                    else:
                        logger.warning("ジャケット画像ファイルが空です")
            except Exception as img_error:
                logger.warning(f"ジャケット画像の読み込みに失敗: {img_error}")
        else:
            logger.warning("ジャケット画像が見つかりません")
        
        # 保存
        audio.save()
        logger.info(f"✅ メタデータ追加完了: {title} - {artist}")
        return True
        
    except Exception as e:
        logger.error(f"メタデータ追加エラー: {e}")
        return False

def get_ydl_opts(temp_dir: Path, is_playlist: bool = False, use_fallback: bool = False):
    """yt-dlpの設定を取得"""
    # FFmpegのパスを検索
    ffmpeg_path = find_ffmpeg_path()
    
    base_opts = {
        'outtmpl': str(temp_dir / '%(title)s.%(ext)s'),
        'noplaylist': not is_playlist,
        'ignoreerrors': True,
        'no_warnings': False,
        'extract_flat': False,
        'writeinfojson': True,
        'writethumbnail': True,
        'writesubtitles': False,
        'writeautomaticsub': False,
        'socket_timeout': 120,
        'retries': 15,
        'fragment_retries': 15,
        'skip_unavailable_fragments': True,
        'prefer_free_formats': True,
        'youtube_include_dash_manifest': False,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web', 'ios', 'tv_embedded'],
                'skip': ['hls'],
                'formats': ['missing_pot'],
            }
        },
        'geo_bypass': True,
        'geo_bypass_country': 'US',
        'proxy': None,
        'http_chunk_size': 10485760,
        'fragment_timeout': 60,
        'file_access_retries': 10,
        'writesubtitles': False,
        'writeautomaticsub': False,
        'writedescription': False,
        'writeannotations': False,
        'writethumbnail': True,
        'writeinfojson': True,
        # YouTubeボット検出回避のための設定
        'cookiesfrombrowser': None,  # ブラウザからクッキーを取得（利用可能な場合）
        'cookiefile': 'cookies.txt',  # ← ここを追加
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://www.youtube.com/',
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
        },
        # より多くの再試行とフォールバック
        'retries': 20,
        'fragment_retries': 20,
        'file_access_retries': 20,
        'extractor_retries': 20,
        # より多くのクライアントを試行
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web', 'ios', 'tv_embedded', 'mweb', 'web_embedded'],
                'skip': ['hls'],
                'formats': ['missing_pot'],
                'player_skip': ['webpage', 'configs'],
            }
        },
        # より多くのフォーマットを試行
        'format': 'best[height<=1080]/best[height<=720]/best[height<=480]/best[ext=mp4]/best[ext=webm]/best/worst',
    }
    
    if ffmpeg_path:
        # FFmpegが利用可能な場合：音声抽出を行う
        logger.info(f"✅ FFmpegが利用可能です: {ffmpeg_path}")
        base_opts.update({
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
                'preferredquality': '128',
            }],
            'ffmpeg_location': ffmpeg_path,
        })
    else:
        # FFmpegが利用できない場合：直接m4aフォーマットをダウンロード
        logger.warning("⚠️  FFmpegが利用できません。直接m4aフォーマットをダウンロードします。")
        # m4aフォーマットを優先してダウンロード
        base_opts.update({
            'format': 'bestaudio[ext=m4a]/bestaudio[acodec=aac]/bestaudio[acodec=mp4a]/bestaudio[container=m4a]/bestaudio/best',
            'postprocessors': []
        })
    
    return base_opts

@app.get("/")
async def root():
    """ルートエンドポイント - 開発環境ではAPI情報、プロダクション環境では静的ファイルを配信"""
    # distディレクトリが存在する場合（プロダクション環境）
    if Path("../dist").exists():
        return FileResponse("../dist/index.html")
    else:
        return {"message": "YouTube M4A Downloader API", "status": "running"}

@app.options("/download")
async def options_download():
    """CORSプリフライトリクエスト用"""
    return {"message": "OK"}

@app.post("/preview", response_model=PreviewResponse)
async def preview_video(request: PreviewRequest):
    """YouTube動画の情報を取得（メタデータ編集用）"""
    try:
        # プレイリストは受け付けない
        if "list=" in request.url:
            return PreviewResponse(
                success=False,
                message="プレイリストは対応していません。単一動画のURLを入力してください。"
            )
        
        logger.info(f"プレビュー取得開始: {request.url}")
        
        # yt-dlpオプション設定（情報のみ取得）
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extractaudio': False,
            'skip_download': True,  # ダウンロードはスキップ
            'writeinfojson': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'writethumbnail': False,
            # YouTubeボット検出回避のための設定
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'referer': 'https://www.youtube.com/',
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate',
            },
            'retries': 20,
            'fragment_retries': 20,
            'extractor_retries': 20,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web', 'ios', 'tv_embedded', 'mweb', 'web_embedded'],
                    'skip': ['hls'],
                    'formats': ['missing_pot'],
                    'player_skip': ['webpage', 'configs'],
                }
            },
            'cookiefile': 'cookies.txt',  # ← ここを追加
        }
        
        # yt-dlpで動画情報を取得
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=False)
            
            if not info:
                return PreviewResponse(
                    success=False,
                    message="動画情報を取得できませんでした。"
                )
            
            # メタデータを解析
            title = info.get('title', '不明なタイトル')
            uploader = info.get('uploader', '不明なアーティスト')
            duration = info.get('duration', 0)
            description = info.get('description', '')
            thumbnail = info.get('thumbnail', '')
            
            # アーティスト名と曲名を解析
            parsed_title, parsed_artist = parse_title_artist(title, uploader)
            
            logger.info(f"プレビュー取得成功: {parsed_title} by {parsed_artist}")
            
            return PreviewResponse(
                success=True,
                message="動画情報を取得しました",
                title=parsed_title,
                artist=parsed_artist,
                duration=duration,
                uploader=uploader,
                description=description[:200] if description else "",  # 200文字まで
                thumbnail=thumbnail
            )
            
    except Exception as e:
        logger.error(f"プレビュー取得エラー: {str(e)}")
        return PreviewResponse(
            success=False,
            message=f"エラーが発生しました: {str(e)}"
        )

@app.post("/download", response_model=DownloadResponse)
async def download_audio(request: DownloadRequest):
    """YouTube動画をM4Aでダウンロード（単一動画のみ）"""
    temp_dir = None
    try:
        url = request.url.strip()
        
        if not url:
            raise HTTPException(status_code=400, detail="URLが指定されていません")
        
        # 単一動画のみ対応
        is_playlist = False
        
        # ダウンロード用の一意なディレクトリを作成
        download_id = str(uuid.uuid4())[:8]
        temp_dir = DOWNLOAD_DIR / download_id
        temp_dir.mkdir(exist_ok=True)
        
        logger.info(f"ダウンロード開始: {url}")
        logger.info(f"一時ディレクトリ: {temp_dir}")
        
        # yt-dlpの設定
        ydl_opts = get_ydl_opts(temp_dir, is_playlist)
        
        # ダウンロード実行
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # まず情報を取得
                logger.info("動画情報を取得中...")
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    raise HTTPException(status_code=404, detail="動画情報を取得できませんでした")
                
                # 単一動画のダウンロード
                logger.info("単一動画をダウンロード中...")
                ydl.download([url])
                
                # M4Aファイルを探す
                m4a_files = list(temp_dir.glob('*.m4a'))
                
                if not m4a_files:
                    # M4Aファイルが見つからない場合、他の音声フォーマットも探す
                    audio_files = list(temp_dir.glob('*.webm')) + list(temp_dir.glob('*.mp4')) + list(temp_dir.glob('*.aac'))
                    if audio_files:
                        # 音声ファイルをm4aに変換（FFmpegなしの場合はそのまま使用）
                        audio_file = audio_files[0]
                        m4a_file = temp_dir / f"{audio_file.stem}.m4a"
                        if audio_file.suffix.lower() in ['.webm', '.mp4', '.aac']:
                            # ファイル名を変更してm4aとして扱う
                            audio_file.rename(m4a_file)
                            logger.info(f"音声ファイルをm4aに変換: {audio_file.name} -> {m4a_file.name}")
                        else:
                            m4a_file = audio_file
                    else:
                        raise HTTPException(status_code=500, detail="音声ファイルの生成に失敗しました")
                else:
                    m4a_file = m4a_files[0]  # 単一動画なので最初のファイル
                
                # 動画情報を取得
                video_title = info.get('title', 'Unknown')
                uploader = info.get('uploader', 'Unknown Artist')
                thumbnail_url = info.get('thumbnail')
                
                logger.info(f"動画情報 - タイトル: '{video_title}', 投稿者: '{uploader}'")
                
                # タイトルとアーティストを解析
                title, artist = parse_title_artist(video_title, uploader)
                logger.info(f"解析結果 - タイトル: '{title}', アーティスト: '{artist}'")
                
                # サムネイル画像を処理
                thumbnail_path = None
                video_id = info.get('id', 'thumb')
                
                # まず既存のサムネイル画像ファイルを探す
                existing_thumbnails = list(temp_dir.glob(f'{video_id}.*')) + list(temp_dir.glob('*.jpg')) + list(temp_dir.glob('*.png')) + list(temp_dir.glob('*.webp'))
                
                if existing_thumbnails:
                    # 既存のサムネイル画像を使用
                    original_thumb = existing_thumbnails[0]
                    thumbnail_path = temp_dir / f"{video_id}_cover.jpg"
                    try:
                        # 既存の画像を800x800に変換
                        from PIL import Image
                        with Image.open(original_thumb) as img:
                            if img.mode != 'RGB':
                                img = img.convert('RGB')
                            
                            # 正方形にクロップ
                            width, height = img.size
                            size = min(width, height)
                            left = (width - size) // 2
                            top = (height - size) // 2
                            right = left + size
                            bottom = top + size
                            
                            img_cropped = img.crop((left, top, right, bottom))
                            img_resized = img_cropped.resize((800, 800), Image.Resampling.LANCZOS)
                            
                            # 保存
                            img_resized.save(thumbnail_path, 'JPEG', quality=95, optimize=True)
                            logger.info(f"✅ 既存サムネイルから800x800ジャケット画像を作成: {thumbnail_path.name}")
                    except Exception as e:
                        logger.warning(f"既存サムネイルの処理に失敗: {e}")
                        thumbnail_path = None
                
                # 既存のサムネイルがない場合、URLからダウンロードして処理
                if not thumbnail_path and thumbnail_url:
                    thumbnail_path = temp_dir / f"{video_id}_cover.jpg"
                    if download_and_process_thumbnail(thumbnail_url, thumbnail_path):
                        logger.info(f"✅ URLからジャケット画像処理完了: {thumbnail_path.name}")
                    else:
                        thumbnail_path = None
                
                # メタデータを追加
                add_metadata_to_m4a(m4a_file, title, artist, None, thumbnail_path)
                
                # ファイル名を変更
                safe_artist = sanitize_filename(artist)
                safe_title = sanitize_filename(title)
                new_filename = f"{safe_artist}-{safe_title}.m4a"
                new_filepath = temp_dir / new_filename
                
                # ファイル名を変更
                m4a_file.rename(new_filepath)
                logger.info(f"ファイル名変更: {new_filename}")
                
                # ファイルをダウンロードディレクトリに移動
                final_path = DOWNLOAD_DIR / new_filename
                shutil.move(str(new_filepath), str(final_path))
                logger.info(f"ファイル移動: {new_filename} -> downloads/")
                
                # 一時ディレクトリを削除
                shutil.rmtree(temp_dir)
                temp_dir = None
                
                return DownloadResponse(
                    success=True,
                    message=f"ダウンロード完了: {title} - {artist}",
                    file_path=str(final_path),
                    file_name=new_filename
                )
                
            except Exception as e:
                logger.error(f"ダウンロードエラー: {e}")
                raise HTTPException(status_code=500, detail=f"ダウンロードエラー: {str(e)}")
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
        raise HTTPException(status_code=500, detail=f"予期しないエラー: {str(e)}")
    finally:
        # 一時ディレクトリのクリーンアップ
        if temp_dir and temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"一時ディレクトリを削除: {temp_dir}")
            except Exception as e:
                logger.warning(f"一時ディレクトリの削除に失敗: {e}")

@app.post("/download-with-metadata", response_model=DownloadResponse)
async def download_audio_with_metadata(request: DownloadWithMetadataRequest):
    """YouTube動画をM4Aでダウンロード（編集されたメタデータ付き）"""
    temp_dir = None
    success = False  # 成功フラグ
    
    try:
        url = request.url.strip()
        title = request.title.strip()
        artist = request.artist.strip()
        
        if not url:
            raise HTTPException(status_code=400, detail="URLが指定されていません")
        
        if not title:
            raise HTTPException(status_code=400, detail="タイトルが指定されていません")
        
        if not artist:
            raise HTTPException(status_code=400, detail="アーティスト名が指定されていません")
        
        # 単一動画のみ対応
        is_playlist = False
        
        # ダウンロード用の一意なディレクトリを作成
        download_id = str(uuid.uuid4())[:8]
        temp_dir = DOWNLOAD_DIR / download_id
        temp_dir.mkdir(exist_ok=True)
        
        logger.info(f"メタデータ付きダウンロード開始: {url}")
        logger.info(f"タイトル: '{title}', アーティスト: '{artist}'")
        logger.info(f"一時ディレクトリ: {temp_dir}")
        
        # yt-dlpの設定
        ydl_opts = get_ydl_opts(temp_dir, is_playlist)
        
        # ダウンロード実行
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # まず情報を取得
                logger.info("動画情報を取得中...")
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    raise HTTPException(status_code=404, detail="動画情報を取得できませんでした")
                
                # 単一動画のダウンロード
                logger.info("単一動画をダウンロード中...")
                ydl.download([url])
                
                # M4Aファイルを探す
                m4a_files = list(temp_dir.glob('*.m4a'))
                
                if not m4a_files:
                    # M4Aファイルが見つからない場合、他の音声フォーマットも探す
                    audio_files = list(temp_dir.glob('*.webm')) + list(temp_dir.glob('*.mp4')) + list(temp_dir.glob('*.aac'))
                    if audio_files:
                        # 音声ファイルをm4aに変換（FFmpegなしの場合はそのまま使用）
                        audio_file = audio_files[0]
                        m4a_file = temp_dir / f"{audio_file.stem}.m4a"
                        if audio_file.suffix.lower() in ['.webm', '.mp4', '.aac']:
                            # ファイル名を変更してm4aとして扱う
                            audio_file.rename(m4a_file)
                            logger.info(f"音声ファイルをm4aに変換: {audio_file.name} -> {m4a_file.name}")
                        else:
                            m4a_file = audio_file
                    else:
                        raise HTTPException(status_code=500, detail="音声ファイルの生成に失敗しました")
                else:
                    m4a_file = m4a_files[0]  # 単一動画なので最初のファイル
                
                # 動画情報を取得
                thumbnail_url = info.get('thumbnail')
                video_id = info.get('id', 'thumb')
                
                # サムネイル画像を処理
                thumbnail_path = None
                
                # まず既存のサムネイル画像ファイルを探す
                existing_thumbnails = list(temp_dir.glob(f'{video_id}.*')) + list(temp_dir.glob('*.jpg')) + list(temp_dir.glob('*.png')) + list(temp_dir.glob('*.webp'))
                
                if existing_thumbnails:
                    # 既存のサムネイル画像を使用
                    original_thumb = existing_thumbnails[0]
                    thumbnail_path = temp_dir / f"{video_id}_cover.jpg"
                    try:
                        # 既存の画像を800x800に変換
                        from PIL import Image
                        with Image.open(original_thumb) as img:
                            if img.mode != 'RGB':
                                img = img.convert('RGB')
                            
                            # 正方形にクロップ
                            width, height = img.size
                            size = min(width, height)
                            left = (width - size) // 2
                            top = (height - size) // 2
                            right = left + size
                            bottom = top + size
                            
                            img_cropped = img.crop((left, top, right, bottom))
                            img_resized = img_cropped.resize((800, 800), Image.Resampling.LANCZOS)
                            
                            # 保存
                            img_resized.save(thumbnail_path, 'JPEG', quality=95, optimize=True)
                            logger.info(f"✅ 既存サムネイルから800x800ジャケット画像を作成: {thumbnail_path.name}")
                    except Exception as e:
                        logger.warning(f"既存サムネイルの処理に失敗: {e}")
                        thumbnail_path = None
                
                # 既存のサムネイルがない場合、URLからダウンロードして処理
                if not thumbnail_path and thumbnail_url:
                    thumbnail_path = temp_dir / f"{video_id}_cover.jpg"
                    if download_and_process_thumbnail(thumbnail_url, thumbnail_path):
                        logger.info(f"✅ URLからジャケット画像処理完了: {thumbnail_path.name}")
                    else:
                        logger.warning("サムネイル画像の処理に失敗")
                        thumbnail_path = None
                
                # M4Aファイルにメタデータを追加（編集されたメタデータを使用）
                try:
                    if add_metadata_to_m4a(m4a_file, title, artist, None, thumbnail_path):
                        logger.info("✅ メタデータの追加が完了しました")
                    else:
                        logger.warning("メタデータの追加に失敗しました（処理は続行）")
                except Exception as e:
                    logger.warning(f"メタデータ追加中にエラーが発生: {e} （処理は続行）")
                
                # ファイル名を生成（編集されたメタデータを使用）
                filename = f"{sanitize_filename(artist)}-{sanitize_filename(title)}.m4a"
                
                logger.info(f"ダウンロード完了: {filename}")
                
                # 成功フラグを設定
                success = True
                
                # ファイルをレスポンスとして返し、バックグラウンドで一時ディレクトリを削除
                def cleanup_temp_dir():
                    try:
                        if temp_dir and temp_dir.exists():
                            shutil.rmtree(temp_dir)
                            logger.info(f"一時ディレクトリを削除: {temp_dir}")
                    except Exception as e:
                        logger.warning(f"一時ディレクトリの削除に失敗: {e}")
                
                # ファイルレスポンスを返す（バックグラウンドタスクで削除）
                background_tasks = BackgroundTasks()
                background_tasks.add_task(cleanup_temp_dir)
                
                return FileResponse(
                    m4a_file,
                    media_type="audio/m4a",
                    filename=filename,
                    headers={"Content-Disposition": f"attachment; filename={filename}"},
                    background=background_tasks
                )
                
            except Exception as e:
                logger.error(f"ダウンロード処理エラー: {str(e)}")
                return DownloadResponse(
                    success=False,
                    message=f"ダウンロードエラー: {str(e)}"
                )

    except Exception as e:
        logger.error(f"ダウンロードエラー: {str(e)}")
        return DownloadResponse(
            success=False,
            message=f"エラーが発生しました: {str(e)}"
        )
    
    finally:
        # 成功した場合はバックグラウンドタスクで削除されるため、エラー時のみ削除
        if not success and temp_dir and temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"一時ディレクトリを削除（エラー時）: {temp_dir}")
            except Exception as e:
                logger.warning(f"一時ディレクトリの削除に失敗: {e}")

@app.get("/download/{file_name}")
async def get_file(file_name: str):
    """ダウンロードしたファイルを取得"""
    file_path = DOWNLOAD_DIR / file_name
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="ファイルが見つかりません")
    
    # M4Aファイルとして返す
    return FileResponse(
        path=str(file_path),
        filename=file_name,
        media_type='audio/m4a'
    )

@app.delete("/cleanup")
async def cleanup_old_files():
    """古いファイルを削除"""
    try:
        # 24時間以上古いファイルを削除
        cutoff_time = time.time() - (24 * 60 * 60)
        deleted_count = 0
        
        for file_path in DOWNLOAD_DIR.glob('*'):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    deleted_count += 1
                    logger.info(f"古いファイルを削除: {file_path.name}")
                except Exception as e:
                    logger.warning(f"ファイル削除に失敗: {file_path.name} - {e}")
        
        return {"message": f"{deleted_count}個の古いファイルを削除しました"}
        
    except Exception as e:
        logger.error(f"クリーンアップエラー: {e}")
        raise HTTPException(status_code=500, detail=f"クリーンアップエラー: {str(e)}")

@app.get("/debug/ffmpeg")
async def debug_ffmpeg():
    """FFmpegの状態をデバッグするエンドポイント"""
    debug_info = {
        "ffmpeg_path": None,
        "ffmpeg_version": None,
        "path_env": os.environ.get('PATH', ''),
        "nix_path": os.environ.get('NIX_PATH', ''),
        "ld_library_path": os.environ.get('LD_LIBRARY_PATH', ''),
        "search_results": [],
        "error": None
    }
    
    try:
        # FFmpegのパスを検索
        ffmpeg_path = find_ffmpeg_path()
        debug_info["ffmpeg_path"] = ffmpeg_path
        
        if ffmpeg_path:
            # FFmpegのバージョンを取得
            try:
                result = subprocess.run([ffmpeg_path, "-version"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    debug_info["ffmpeg_version"] = result.stdout.split('\n')[0]
            except Exception as e:
                debug_info["error"] = f"FFmpeg version check failed: {e}"
        
        # 各種検索結果を記録
        search_locations = [
            "/usr/bin/ffmpeg",
            "/usr/local/bin/ffmpeg", 
            "/bin/ffmpeg",
            "/root/.nix-profile/bin/ffmpeg",
            "/nix/var/nix/profiles/default/bin/ffmpeg",
        ]
        
        for location in search_locations:
            exists = os.path.exists(location)
            executable = os.access(location, os.X_OK) if exists else False
            debug_info["search_results"].append({
                "path": location,
                "exists": exists,
                "executable": executable
            })
        
        # Nixストアでの検索結果
        try:
            result = subprocess.run(
                ["find", "/nix/store", "-name", "ffmpeg", "-type", "f", "-executable"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0 and result.stdout.strip():
                nix_paths = result.stdout.strip().split('\n')
                debug_info["nix_store_paths"] = nix_paths[:10]  # 最初の10個のみ
        except Exception as e:
            debug_info["nix_store_error"] = str(e)
        
        # PATHの各ディレクトリを確認
        path_dirs = os.environ.get('PATH', '').split(':')
        debug_info["path_dirs"] = path_dirs
        
    except Exception as e:
        debug_info["error"] = str(e)
    
    return debug_info

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 