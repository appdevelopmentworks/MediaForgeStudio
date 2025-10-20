# 🏗️ MediaForge Studio - アーキテクチャ設計書 v1.0

---

## 📐 システムアーキテクチャ概要

MediaForge Studioは、**レイヤードアーキテクチャ**と**モジュラー設計**を採用し、各機能を独立したコンポーネントとして実装します。

### **アーキテクチャ図**

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                    │
│            (PySide6 + QFluentWidgets UI)                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │Download  │ │ Audio    │ │ Dubbing  │ │ Merge    │  │
│  │   Tab    │ │Extract   │ │   Tab    │ │   Tab    │  │
│  │          │ │   Tab    │ │          │ │          │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   Business Logic Layer                   │
│                  (Core Processing Modules)               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │Downloader│ │Audio     │ │Trans-    │ │TTS       │  │
│  │          │ │Extractor │ │criber    │ │Manager   │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │Trans-    │ │Video     │ │Audio     │ │Queue     │  │
│  │lator     │ │Merger    │ │Merger    │ │Manager   │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                    Service Layer                         │
│              (External Services Integration)             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │edge_tts  │ │VOICEVOX  │ │Google    │ │pyttsx3   │  │
│  │Engine    │ │Engine    │ │TTS       │ │Engine    │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                     Data Layer                           │
│         (Models, Database, File Management)              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │SQLite DB │ │File      │ │Config    │ │Log       │  │
│  │          │ │Manager   │ │Manager   │ │Manager   │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                  External Dependencies                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │yt-dlp    │ │FFmpeg    │ │Whisper   │ │PyTorch   │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 設計原則

### **1. 単一責任原則（SRP）**
各モジュールは1つの責任のみを持つ

### **2. 依存性逆転原則（DIP）**
上位モジュールは下位モジュールに依存しない

### **3. モジュラー設計**
各機能は独立したモジュールとして実装し、交換可能

### **4. 非同期処理**
I/O処理は非同期化し、UIブロックを防止

### **5. エラーハンドリング**
すべての外部依存は例外処理を実装

---

## 📦 コンポーネント詳細

### **Presentation Layer (UI層)**

#### **MainWindow**
```python
class MainWindow(FluentWindow):
    """メインウィンドウ - アプリケーションのエントリーポイント"""
    
    def __init__(self):
        - タブナビゲーション管理
        - テーマ切替
        - ウィンドウ状態管理
        
    def setup_ui(self):
        - タブ追加
        - ステータスバー設定
        - シグナル・スロット接続
```

#### **各タブモジュール**

**DownloadTab**
- YouTube URL入力
- 動画情報表示
- ダウンロード設定
- 進捗表示

**AudioExtractTab**
- 音声抽出設定
- ビットレート選択
- プレビュー機能

**DubbingTab**
- TTS エンジン選択
- 話者・感情設定
- 翻訳API選択
- 音声パラメータ調整

**MergeTab**
- ファイルリスト管理
- ドラッグ&ドロップ
- 順序調整
- 結合設定

---

### **Business Logic Layer (ビジネスロジック層)**

#### **YouTubeDownloader**
```python
class YouTubeDownloader:
    """YouTube動画ダウンロード管理"""
    
    async def get_video_info(self, url: str) -> VideoInfo:
        """動画情報取得"""
        
    async def download_video(
        self, 
        url: str, 
        resolution: str,
        progress_callback: Callable
    ) -> DownloadResult:
        """動画ダウンロード実行"""
        
    async def download_batch(
        self, 
        urls: List[str]
    ) -> List[DownloadResult]:
        """バッチダウンロード"""
```

#### **AudioExtractor**
```python
class AudioExtractor:
    """音声抽出・MP3変換"""
    
    async def extract_audio(
        self, 
        video_path: str,
        bitrate: str = "128k"
    ) -> AudioFile:
        """動画から音声抽出"""
        
    def set_id3_tags(
        self, 
        audio_path: str, 
        tags: Dict[str, str]
    ):
        """ID3タグ設定"""
```

#### **WhisperTranscriber**
```python
class WhisperTranscriber:
    """Whisper音声認識"""
    
    def __init__(self, model: str = "medium"):
        - モデル読み込み
        - GPU/CPU検出
        
    async def transcribe(
        self, 
        audio_path: str
    ) -> TranscriptionResult:
        """音声認識実行"""
        - 言語自動検出
        - セグメント化
        - タイムスタンプ付与
```

#### **TranslationManager**
```python
class TranslationManager:
    """翻訳管理 - 5段階フォールバック"""
    
    def __init__(self):
        - 翻訳エンジン初期化
        - フォールバック順序設定
        
    async def translate(
        self, 
        text: str,
        source_lang: str,
        target_lang: str = "ja"
    ) -> TranslationResult:
        """翻訳実行"""
        1. DeepL API
        2. Groq API
        3. Gemini API
        4. OpenAI API
        5. Argos Translate
```

#### **TTSManager**
```python
class TTSManager:
    """TTS統合管理"""
    
    def __init__(self):
        - 各TTSエンジン初期化
        - デフォルトエンジン設定
        
    async def synthesize(
        self, 
        text: str,
        engine: str = "edge_tts",
        voice: str = "ja-JP-NanamiNeural",
        params: TTSParams
    ) -> AudioData:
        """音声合成実行"""
        
    def list_available_engines(self) -> List[str]:
        """利用可能エンジン一覧"""
        
    def list_voices(self, engine: str) -> List[Voice]:
        """話者一覧取得"""
```

#### **VideoMerger**
```python
class VideoMerger:
    """動画連結"""
    
    async def merge_videos(
        self, 
        video_files: List[str],
        output_path: str,
        resolution: str = "720p",
        transition: str = "none"
    ) -> MergeResult:
        """動画連結実行"""
        - 解像度統一
        - トランジション追加
        - プログレス通知
```

#### **AudioMerger**
```python
class AudioMerger:
    """音声連結"""
    
    async def merge_audios(
        self, 
        audio_files: List[str],
        output_path: str,
        normalize: bool = True
    ) -> MergeResult:
        """音声連結実行"""
        - 音量正規化
        - メタデータ統合
```

#### **QueueManager**
```python
class QueueManager:
    """処理キュー管理"""
    
    def add_task(self, task: Task):
        """タスク追加"""
        
    def remove_task(self, task_id: str):
        """タスク削除"""
        
    def pause_task(self, task_id: str):
        """タスク一時停止"""
        
    def resume_task(self, task_id: str):
        """タスク再開"""
        
    def get_queue_status(self) -> QueueStatus:
        """キュー状態取得"""
```

---

### **Service Layer (サービス層)**

#### **EdgeTTSEngine**
```python
class EdgeTTSEngine:
    """Microsoft Edge TTS実装"""
    
    async def synthesize(
        self, 
        text: str,
        voice: str,
        rate: float,
        pitch: float
    ) -> bytes:
        """音声合成"""
        
    def list_voices(self) -> List[Voice]:
        """話者一覧"""
```

#### **VoicevoxEngine**
```python
class VoicevoxEngine:
    """VOICEVOX実装"""
    
    def __init__(self, host: str = "localhost", port: int = 50021):
        - 接続確認
        - 話者読み込み
        
    async def synthesize(
        self, 
        text: str,
        speaker_id: int,
        params: VoicevoxParams
    ) -> bytes:
        """音声合成"""
        
    def check_connection(self) -> bool:
        """接続確認"""
```

#### **GoogleTTSEngine**
```python
class GoogleTTSEngine:
    """Google Cloud TTS実装"""
    
    def __init__(self, api_key: str):
        - クライアント初期化
        
    async def synthesize(
        self, 
        text: str,
        voice: str,
        params: GoogleTTSParams
    ) -> bytes:
        """音声合成"""
```

#### **Pyttsx3Engine**
```python
class Pyttsx3Engine:
    """オフラインTTS実装"""
    
    def __init__(self):
        - エンジン初期化
        - システム音声取得
        
    def synthesize(
        self, 
        text: str
    ) -> bytes:
        """音声合成"""
```

---

### **Data Layer (データ層)**

#### **Database Manager**
```python
class DatabaseManager:
    """SQLite データベース管理"""
    
    def __init__(self, db_path: str):
        - DB接続
        - テーブル作成
        
    def save_download_history(self, item: DownloadItem):
        """ダウンロード履歴保存"""
        
    def get_download_history(
        self, 
        limit: int = 100
    ) -> List[DownloadItem]:
        """履歴取得"""
        
    def save_settings(self, settings: Dict):
        """設定保存"""
        
    def load_settings(self) -> Dict:
        """設定読み込み"""
```

#### **File Manager**
```python
class FileManager:
    """ファイル管理"""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """ファイル名サニタイズ"""
        
    @staticmethod
    def ensure_directory(path: str):
        """ディレクトリ作成"""
        
    @staticmethod
    def get_file_size(path: str) -> int:
        """ファイルサイズ取得"""
        
    @staticmethod
    def cleanup_temp_files(pattern: str):
        """一時ファイル削除"""
```

#### **Config Manager**
```python
class ConfigManager:
    """設定管理"""
    
    def __init__(self, config_path: str):
        - YAML設定読み込み
        
    def get(self, key: str, default: Any = None) -> Any:
        """設定値取得"""
        
    def set(self, key: str, value: Any):
        """設定値設定"""
        
    def save(self):
        """設定保存"""
```

#### **Logger**
```python
class Logger:
    """ログ管理"""
    
    @staticmethod
    def setup(log_dir: str = "./logs"):
        """ログ設定"""
        - ファイルハンドラ設定
        - コンソールハンドラ設定
        - ローテーション設定
        
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """ロガー取得"""
```

---

## 🔄 データフロー

### **YouTube動画ダウンロード**
```
UI (DownloadTab)
  │
  ├─ URL入力
  │
  ▼
QueueManager
  │
  ├─ タスク追加
  │
  ▼
YouTubeDownloader
  │
  ├─ get_video_info() → yt-dlp
  ├─ download_video() → yt-dlp
  │
  ▼
FileManager
  │
  ├─ ファイル保存 (output/videos/)
  │
  ▼
DatabaseManager
  │
  ├─ 履歴保存
  │
  ▼
UI (更新)
```

### **音声吹き替え**
```
UI (DubbingTab)
  │
  ├─ URL or ファイル選択
  ├─ TTS設定
  ├─ 翻訳API選択
  │
  ▼
AudioExtractor
  │
  ├─ extract_audio() → FFmpeg
  │
  ▼
WhisperTranscriber
  │
  ├─ transcribe() → Whisper
  │
  ▼
TranslationManager
  │
  ├─ translate() → 5段階フォールバック
  │    ├─ DeepL API
  │    ├─ Groq API
  │    ├─ Gemini API
  │    ├─ OpenAI API
  │    └─ Argos Translate
  │
  ▼
TTSManager
  │
  ├─ synthesize()
  │    ├─ EdgeTTSEngine
  │    ├─ VoicevoxEngine
  │    ├─ GoogleTTSEngine
  │    └─ Pyttsx3Engine
  │
  ▼
FileManager
  │
  ├─ MP3保存 (output/dubbed/)
  │
  ▼
UI (更新)
```

### **動画連結**
```
UI (MergeTab)
  │
  ├─ ファイル追加
  ├─ 順序調整
  ├─ 解像度設定
  │
  ▼
VideoMerger
  │
  ├─ merge_videos() → FFmpeg
  │    ├─ 解像度統一
  │    ├─ トランジション追加
  │    └─ エンコーディング
  │
  ▼
FileManager
  │
  ├─ MP4保存 (output/videos/)
  │
  ▼
UI (更新)
```

---

## 🔌 外部依存関係

### **必須依存**
- **yt-dlp**: YouTube動画ダウンロード
- **FFmpeg**: メディアエンコーディング
- **Whisper**: 音声認識
- **PyTorch**: 機械学習フレームワーク

### **オプション依存**
- **VOICEVOX Engine**: 高品質TTS（手動インストール）
- **DeepL API**: 最高品質翻訳
- **Groq API**: 高速翻訳
- **Google Gemini API**: AI翻訳
- **OpenAI API**: GPT翻訳
- **Google Cloud TTS**: 最高品質TTS

---

## 🛡️ エラーハンドリング戦略

### **階層別エラーハンドリング**

```python
# UI層: ユーザーフレンドリーなエラーメッセージ
try:
    result = await downloader.download_video(url)
except NetworkError as e:
    show_error_dialog("ネットワークエラー", "接続を確認してください")
except InvalidURLError as e:
    show_error_dialog("無効なURL", "正しいYouTube URLを入力してください")

# ビジネスロジック層: 詳細なエラーログ
try:
    video_info = ydl.extract_info(url)
except yt_dlp.DownloadError as e:
    logger.error(f"Download failed: {url}, Error: {e}")
    raise DownloadError(f"Failed to download: {str(e)}")

# サービス層: リトライ機能
@retry(max_attempts=3, delay=[5, 10, 30])
async def fetch_with_retry(url: str):
    try:
        response = await http_client.get(url)
        return response
    except aiohttp.ClientError as e:
        logger.warning(f"Retry attempt failed: {e}")
        raise
```

---

## 🚀 パフォーマンス最適化

### **非同期処理**
```python
# 複数タスクの並行実行
tasks = [
    download_video(url1),
    download_video(url2),
    download_video(url3)
]
results = await asyncio.gather(*tasks)
```

### **キャッシュ戦略**
```python
# 翻訳結果のキャッシュ
@lru_cache(maxsize=1000)
def translate_cached(text: str, target_lang: str) -> str:
    return translator.translate(text, target_lang)
```

### **GPU活用**
```python
# Whisper GPU使用
device = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model("medium", device=device)
```

---

## 🔐 セキュリティ考慮事項

### **APIキー管理**
- 環境変数 (.env) で管理
- 平文保存禁止
- 設定UIで入力時にマスク表示

### **ファイルパス検証**
```python
def validate_file_path(path: str) -> bool:
    """パストラバーサル攻撃を防止"""
    real_path = os.path.realpath(path)
    return real_path.startswith(ALLOWED_DIRECTORY)
```

### **入力サニタイズ**
```python
def sanitize_filename(filename: str) -> str:
    """危険な文字を除去"""
    return re.sub(r'[<>:"/\\|?*]', '_', filename)
```

---

## 📊 モニタリング・ロギング

### **ログレベル**
- **DEBUG**: 開発時の詳細情報
- **INFO**: 通常の処理フロー
- **WARNING**: 警告（処理は継続）
- **ERROR**: エラー（処理失敗）
- **CRITICAL**: 致命的エラー

### **ログ出力先**
```
./logs/
  ├── app_{date}.log          # アプリケーションログ
  ├── download_{date}.log     # ダウンロードログ
  ├── error_{date}.log        # エラーログ
  └── performance_{date}.log  # パフォーマンスログ
```

---

## 🧪 テスト戦略

### **ユニットテスト**
- 各モジュールの単体テスト
- pytest使用

### **統合テスト**
- コンポーネント間の連携テスト

### **E2Eテスト**
- UI操作の自動テスト
- pytest-qt使用

---

**作成日**: 2025-01-20  
**最終更新**: 2025-01-20  
**バージョン**: 1.0
