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

# 環境変数を読み込み
load_dotenv()

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="YouTube M4A Downloader", version="1.0.0")

# CORS設定（ローカル開発用）- より寛容な設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開発環境では全てのオリジンを許可
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ダウンロードディレクトリの設定
DOWNLOAD_DIR = Path("downloads")
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
    """ファイル名に使用できない文字を除去"""
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
        img_enhanced = enhancer.enhance(1.2)  # 少しシャープネスを向上
        
        # JPEG形式で高品質保存
        img_enhanced.save(output_path, 'JPEG', quality=95, optimize=True)
        logger.info(f"✅ ジャケット画像を作成: {output_path} (800x800, 高品質)")
        
        # 保存されたファイルのサイズを確認
        file_size = output_path.stat().st_size
        logger.info(f"保存されたジャケット画像サイズ: {file_size} bytes")
        
        return True
        
    except Exception as e:
        logger.error(f"ジャケット画像の処理に失敗: {e}")
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
        
        # 保存後の確認
        try:
            verify_audio = MP4(m4a_path)
            saved_title = verify_audio.get('\xa9nam', [''])[0]
            saved_artist = verify_audio.get('\xa9ART', [''])[0]
            has_cover = 'covr' in verify_audio
            logger.info(f"保存確認 - タイトル: '{saved_title}', アーティスト: '{saved_artist}', ジャケット: {has_cover}")
        except Exception as verify_error:
            logger.warning(f"メタデータ保存確認に失敗: {verify_error}")
        
    except Exception as e:
        logger.error(f"メタデータの追加に失敗: {m4a_path.name} - {e}")
        # エラーが発生してもファイル自体は保持

def get_ydl_opts(temp_dir: Path, is_playlist: bool = False, use_fallback: bool = False):
    """yt-dlpの設定を取得"""
    base_opts = {
        'outtmpl': str(temp_dir / '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
            'preferredquality': '128',
        }],
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
        # より多くのフォーマットを試行
        'format': 'best[height<=1080]/best[height<=720]/best[height<=480]/best[ext=mp4]/best[ext=webm]/best/worst',
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web', 'ios', 'tv_embedded'],  # 複数のクライアントを試行
                'skip': ['hls'],  # HLSをスキップして安定性向上
                'formats': ['missing_pot'],
            }
        },
        # 地域制限の回避を試行
        'geo_bypass': True,
        'geo_bypass_country': 'US',
        # プロキシ設定（必要に応じて）
        'proxy': None,
        # より多くの再試行オプション
        'http_chunk_size': 10485760,  # 10MB chunks
        'fragment_timeout': 60,
        'file_access_retries': 10,
        # より多くのメタデータを取得
        'writesubtitles': False,
        'writeautomaticsub': False,
        'writedescription': False,
        'writeannotations': False,
        # サムネイルの品質を向上
        'writethumbnail': True,
        'writeinfojson': True,
    }
    
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
    """OPTIONSリクエストを処理"""
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
                    raise HTTPException(status_code=500, detail="M4Aファイルの生成に失敗しました")
                
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
                    raise HTTPException(status_code=500, detail="M4Aファイルの生成に失敗しました")
                
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
    """古いファイルをクリーンアップ"""
    try:
        current_time = time.time()
        deleted_count = 0
        
        for file_path in DOWNLOAD_DIR.iterdir():
            if file_path.is_file():
                # 1時間以上古いファイルを削除
                if current_time - file_path.stat().st_mtime > 3600:
                    file_path.unlink()
                    deleted_count += 1
        
        return {"message": f"{deleted_count}個のファイルを削除しました"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"クリーンアップエラー: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 