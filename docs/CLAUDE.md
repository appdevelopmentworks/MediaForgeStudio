# 🤖 Claude Code 開発ガイド - MediaForge Studio

このドキュメントは、Claude Codeがこのプロジェクトを開発する際の指針となります。

---

## 📌 プロジェクト概要

**プロジェクト名**: MediaForge Studio  
**目的**: YouTube動画の加工・吹き替え・統合を行う教育向けメディア処理ツール  
**技術スタック**: Python 3.10+, PySide6, QFluentWidgets, yt-dlp, FFmpeg, Whisper

---

## 🎯 開発の基本方針

### **1. コーディング規約**

#### **命名規則**
```python
# クラス: PascalCase
class YouTubeDownloader:
    pass

# 関数・変数: snake_case
def download_video(url: str):
    video_path = "./output/video.mp4"

# 定数: UPPER_SNAKE_CASE
MAX_CONCURRENT_DOWNLOADS = 3

# プライベート: _prefix
def _internal_helper():
    pass
```

#### **型ヒント必須**
```python
from typing import List, Dict, Optional, Callable

async def download_video(
    url: str,
    resolution: str = "720p",
    progress_callback: Optional[Callable[[float], None]] = None
) -> DownloadResult:
    """
    YouTube動画をダウンロード
    
    Args:
        url: YouTube URL
        resolution: 解像度 (480p/720p/1080p)
        progress_callback: 進捗コールバック
        
    Returns:
        DownloadResult: ダウンロード結果
        
    Raises:
        NetworkError: ネットワークエラー
        InvalidURLError: 無効なURL
    """
    pass
```

#### **Docstring必須**
- すべての public メソッドに Docstring を記述
- Google スタイル推奨

### **2. エラーハンドリング**

#### **必ずtry-exceptを使用**
```python
async def download_video(url: str) -> DownloadResult:
    try:
        video_info = await self._fetch_video_info(url)
        video_data = await self._download_video_data(url)
        return DownloadResult(status="success", data=video_data)
        
    except aiohttp.ClientError as e:
        logger.error(f"Network error: {e}")
        raise NetworkError(f"Failed to download: {str(e)}")
        
    except ValueError as e:
        logger.error(f"Invalid URL: {e}")
        raise InvalidURLError(f"Invalid YouTube URL: {url}")
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise DownloadError(f"Unexpected error: {str(e)}")
```

#### **ログ出力必須**
```python
from loguru import logger

logger.info(f"Starting download: {url}")
logger.debug(f"Video info: {video_info}")
logger.warning(f"Slow download speed: {speed} KB/s")
logger.error(f"Download failed: {error}")
```

### **3. 非同期処理**

#### **I/O処理は非同期化**
```python
# ❌ Bad: 同期処理
def download_video(url: str):
    response = requests.get(url)  # UI ブロック

# ✅ Good: 非同期処理
async def download_video(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.read()
```

#### **並行処理**
```python
# 複数タスクの並行実行
tasks = [
    download_video(url1),
    download_video(url2),
    download_video(url3)
]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

---

## 📂 プロジェクト構造の理解

### **ディレクトリ構造**
```
MediaForgeStudio/
├── app/
│   ├── core/           # ビジネスロジック
│   ├── tts/            # TTS実装
│   ├── ui/             # UI実装
│   │   ├── tabs/       # 各タブ画面
│   │   ├── widgets/    # カスタムウィジェット
│   │   └── dialogs/    # ダイアログ
│   ├── models/         # データモデル
│   ├── utils/          # ユーティリティ
│   └── resources/      # リソース
├── config/             # 設定ファイル
├── output/             # 出力先
├── logs/               # ログ
├── docs/               # ドキュメント
├── main.py             # エントリーポイント
└── requirements.txt
```

### **モジュール間の依存関係**
```
UI層 (app/ui/)
  ↓ 依存
Business Logic層 (app/core/)
  ↓ 依存
Service層 (app/tts/)
  ↓ 依存
Data層 (app/models/, app/utils/)
```

**重要**: 上位層は下位層に依存できるが、逆は禁止

---

## 🛠️ 実装ガイドライン

### **Phase 1: コア機能実装（最優先）**

#### **1.1 YouTubeDownloader**
```python
# app/core/downloader.py

from typing import Optional, Callable
from loguru import logger
import yt_dlp

class YouTubeDownloader:
    """YouTube動画ダウンロード管理"""
    
    def __init__(self, output_dir: str = "./output/videos"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    async def get_video_info(self, url: str) -> VideoInfo:
        """
        YouTube動画情報を取得
        
        Args:
            url: YouTube URL
            
        Returns:
            VideoInfo: 動画情報
            
        Raises:
            InvalidURLError: 無効なURL
        """
        try:
            logger.info(f"Fetching video info: {url}")
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await asyncio.get_event_loop().run_in_executor(
                    None, ydl.extract_info, url, False
                )
            
            video_info = VideoInfo(
                url=url,
                title=info['title'],
                duration=info['duration'],
                resolution=f"{info.get('height', 0)}p",
                thumbnail_url=info.get('thumbnail')
            )
            
            logger.info(f"Video info fetched: {video_info.title}")
            return video_info
            
        except Exception as e:
            logger.error(f"Failed to fetch video info: {e}")
            raise InvalidURLError(f"Invalid YouTube URL: {url}")
    
    async def download_video(
        self,
        url: str,
        resolution: str = "720p",
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> DownloadResult:
        """
        YouTube動画をダウンロード
        
        Args:
            url: YouTube URL
            resolution: 解像度
            progress_callback: 進捗コールバック (0.0-100.0)
            
        Returns:
            DownloadResult: ダウンロード結果
        """
        try:
            logger.info(f"Starting download: {url} ({resolution})")
            
            def progress_hook(d):
                if progress_callback and d['status'] == 'downloading':
                    if d.get('total_bytes'):
                        percent = d['downloaded_bytes'] / d['total_bytes'] * 100
                        progress_callback(percent)
            
            ydl_opts = {
                'format': self._get_format_selector(resolution),
                'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
                'progress_hooks': [progress_hook]
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await asyncio.get_event_loop().run_in_executor(
                    None, ydl.extract_info, url
                )
            
            video_path = self.output_dir / f"{info['title']}.{info['ext']}"
            
            logger.info(f"Download completed: {video_path}")
            
            return DownloadResult(
                status="success",
                video_path=str(video_path),
                title=info['title']
            )
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            raise DownloadError(f"Failed to download: {str(e)}")
    
    def _get_format_selector(self, resolution: str) -> str:
        """解像度に応じたフォーマット選択"""
        resolution_map = {
            '480p': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
            '720p': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
        }
        return resolution_map.get(resolution, 'bestvideo+bestaudio/best')
```

#### **1.2 データモデル**
```python
# app/models/download_item.py

from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class VideoInfo:
    """動画情報"""
    url: str
    title: str
    duration: int  # 秒
    resolution: str
    thumbnail_url: Optional[str] = None
    
    @property
    def duration_str(self) -> str:
        """HH:MM:SS形式の長さ"""
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

@dataclass
class DownloadResult:
    """ダウンロード結果"""
    status: str  # success, error
    video_path: Optional[str] = None
    title: Optional[str] = None
    error_message: Optional[str] = None
    download_time: Optional[datetime] = None
```

#### **1.3 UI実装（DownloadTab）**
```python
# app/ui/tabs/download_tab.py

from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import (
    LineEdit, PushButton, ProgressBar, 
    CardWidget, ImageLabel
)
from loguru import logger

class DownloadTab(QWidget):
    """ダウンロードタブ"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.downloader = YouTubeDownloader()
        self.setup_ui()
        
    def setup_ui(self):
        """UI初期化"""
        layout = QVBoxLayout(self)
        
        # URL入力
        self.url_input = LineEdit()
        self.url_input.setPlaceholderText("YouTube URLを入力...")
        layout.addWidget(self.url_input)
        
        # ボタン
        self.fetch_btn = PushButton("動画情報取得")
        self.fetch_btn.clicked.connect(self.on_fetch_info)
        layout.addWidget(self.fetch_btn)
        
        # 動画情報カード
        self.info_card = CardWidget()
        self.thumbnail = ImageLabel()
        self.title_label = QLabel()
        # ... カードレイアウト設定
        layout.addWidget(self.info_card)
        
        # プログレスバー
        self.progress_bar = ProgressBar()
        layout.addWidget(self.progress_bar)
        
        # ダウンロードボタン
        self.download_btn = PushButton("ダウンロード開始")
        self.download_btn.clicked.connect(self.on_download)
        layout.addWidget(self.download_btn)
    
    def on_fetch_info(self):
        """動画情報取得ボタン"""
        url = self.url_input.text().strip()
        if not url:
            # エラーダイアログ表示
            return
        
        # 非同期実行
        asyncio.create_task(self._fetch_info_async(url))
    
    async def _fetch_info_async(self, url: str):
        """動画情報取得（非同期）"""
        try:
            video_info = await self.downloader.get_video_info(url)
            
            # UI更新（メインスレッドで実行）
            self.title_label.setText(video_info.title)
            # ... サムネイル表示等
            
        except Exception as e:
            logger.error(f"Failed to fetch info: {e}")
            # エラーダイアログ表示
    
    def on_download(self):
        """ダウンロードボタン"""
        url = self.url_input.text().strip()
        resolution = self.resolution_combo.currentText()
        
        asyncio.create_task(self._download_async(url, resolution))
    
    async def _download_async(self, url: str, resolution: str):
        """ダウンロード実行（非同期）"""
        try:
            def update_progress(percent: float):
                self.progress_bar.setValue(int(percent))
            
            result = await self.downloader.download_video(
                url, 
                resolution, 
                update_progress
            )
            
            if result.status == "success":
                # 成功ダイアログ表示
                logger.info(f"Download success: {result.video_path}")
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            # エラーダイアログ表示
```

---

### **Phase 2: TTS統合**

#### **2.1 TTSManager**
```python
# app/core/tts_manager.py

from typing import Dict, List, Optional
from app.tts.edge_tts_engine import EdgeTTSEngine
from app.tts.voicevox_engine import VoicevoxEngine

class TTSManager:
    """TTS統合管理"""
    
    def __init__(self):
        self.engines = {
            'edge_tts': EdgeTTSEngine(),
            'voicevox': VoicevoxEngine()
        }
        self.default_engine = 'edge_tts'
        
    async def synthesize(
        self,
        text: str,
        engine: str = None,
        voice: str = None,
        params: Optional[Dict] = None
    ) -> bytes:
        """
        音声合成
        
        Args:
            text: 合成するテキスト
            engine: TTSエンジン名
            voice: 話者名
            params: パラメータ
            
        Returns:
            bytes: 音声データ
        """
        if engine is None:
            engine = self.default_engine
        
        if engine not in self.engines:
            raise ValueError(f"Unknown engine: {engine}")
        
        tts_engine = self.engines[engine]
        
        try:
            audio_data = await tts_engine.synthesize(text, voice, params)
            return audio_data
            
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            raise TTSError(f"Failed to synthesize: {str(e)}")
    
    def list_voices(self, engine: str) -> List[str]:
        """話者一覧取得"""
        if engine not in self.engines:
            return []
        
        return self.engines[engine].list_voices()
```

#### **2.2 EdgeTTSEngine**
```python
# app/tts/edge_tts_engine.py

import edge_tts
from typing import Optional, Dict

class EdgeTTSEngine:
    """Microsoft Edge TTS実装"""
    
    def __init__(self):
        self.default_voice = "ja-JP-NanamiNeural"
        
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        params: Optional[Dict] = None
    ) -> bytes:
        """
        音声合成
        
        Args:
            text: テキスト
            voice: 話者名
            params: パラメータ (rate, pitch, volume)
            
        Returns:
            bytes: 音声データ
        """
        if voice is None:
            voice = self.default_voice
        
        if params is None:
            params = {}
        
        rate = params.get('rate', 1.0)
        pitch = params.get('pitch', 1.0)
        volume = params.get('volume', 1.0)
        
        # edge_tts形式に変換
        rate_str = f"{int((rate - 1.0) * 100):+d}%"
        pitch_str = f"{int((pitch - 1.0) * 100):+d}Hz"
        volume_str = f"{int((volume - 1.0) * 100):+d}%"
        
        communicate = edge_tts.Communicate(
            text,
            voice,
            rate=rate_str,
            pitch=pitch_str,
            volume=volume_str
        )
        
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        return audio_data
    
    def list_voices(self) -> List[str]:
        """日本語話者一覧"""
        return [
            "ja-JP-NanamiNeural",
            "ja-JP-KeitaNeural",
            "ja-JP-ShioriNeural",
            "ja-JP-AoiNeural",
            "ja-JP-DaichiNeural",
            "ja-JP-MayuNeural",
            "ja-JP-NaokiNeural"
        ]
```

---

## 🐛 デバッグ・トラブルシューティング

### **ログの確認**
```bash
# リアルタイムログ監視
tail -f logs/app_2025-01-20.log

# エラーログのみ
tail -f logs/error_2025-01-20.log
```

### **よくあるエラー**

#### **1. VOICEVOX接続エラー**
```python
# app/tts/voicevox_engine.py

async def check_connection(self) -> bool:
    """VOICEVOX接続確認"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/version") as response:
                if response.status == 200:
                    logger.info("VOICEVOX connection OK")
                    return True
    except aiohttp.ClientError:
        logger.warning("VOICEVOX not available, using fallback")
        return False
```

#### **2. FFmpeg not found**
```python
# app/utils/ffmpeg_checker.py

def check_ffmpeg() -> bool:
    """FFmpeg存在確認"""
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        logger.error("FFmpeg not found")
        return False
```

---

## 📝 コミットメッセージ規約

```
<type>: <subject>

<body>

<footer>
```

### **Type**
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント
- `style`: コード整形
- `refactor`: リファクタリング
- `test`: テスト追加
- `chore`: ビルド・設定変更

### **例**
```
feat: YouTube動画ダウンロード機能を追加

- YouTubeDownloaderクラス実装
- DownloadTabUI作成
- 進捗表示機能追加

Closes #1
```

---

## ✅ チェックリスト

### **実装前**
- [ ] 要求定義書を読んだ
- [ ] アーキテクチャ設計書を理解した
- [ ] 該当モジュールの依存関係を確認した

### **実装中**
- [ ] 型ヒントを記述した
- [ ] Docstringを記述した
- [ ] エラーハンドリングを実装した
- [ ] ログ出力を追加した
- [ ] 非同期処理を適切に使用した

### **実装後**
- [ ] ユニットテストを作成した
- [ ] ログで動作確認した
- [ ] エラーケースをテストした
- [ ] ドキュメントを更新した

---

## 🚀 開発の進め方

### **1. 最初に読むべきドキュメント**
1. `README.md` - プロジェクト概要
2. `docs/01_requirements.md` - 要求定義
3. `docs/02_architecture.md` - アーキテクチャ
4. このドキュメント (`docs/CLAUDE.md`)

### **2. 実装順序（推奨）**
1. **Phase 1**: コア機能
   - YouTubeDownloader
   - AudioExtractor
   - データモデル
   - 基本UI

2. **Phase 2**: 音声処理
   - WhisperTranscriber
   - TranslationManager
   - TTSManager
   - 各TTSEngine

3. **Phase 3**: 連結機能
   - VideoMerger
   - AudioMerger

4. **Phase 4**: UI/UX改善
   - アニメーション
   - テーマ切替
   - キュー管理

5. **Phase 5**: 配布準備
   - PyInstallerビルド
   - テスト・バグ修正

### **3. 質問・相談**
- 不明点があれば docs/を参照
- 技術的な判断が必要な場合はユーザーに確認

---

**頑張って開発を進めてください！**

---

**作成日**: 2025-01-20  
**最終更新**: 2025-01-20
