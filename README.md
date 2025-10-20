# 🎬 MediaForge Studio

**YouTube動画を自在に加工する教育向けメディア統合ツール**

MediaForge Studioは、YouTube動画のダウンロード、音声抽出、多言語吹き替え、動画・音声連結を統合した、教育コンテンツ制作に最適化されたデスクトップアプリケーションです。

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/UI-PySide6-green.svg)](https://www.qt.io/qt-for-python)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**🚀 現在の開発状況: MVP 85%完成（基本機能実装済み）**

---

## ✨ 主な機能

### 🎥 **1. YouTube動画ダウンロード**
- 単一・複数URLの一括ダウンロード
- 解像度選択（480p/720p/1080p/最高画質）
- ダウンロード履歴・キュー管理
- リアルタイム進捗表示

### 🎵 **2. 音声抽出（MP3変換）**
- 動画から音声のみを抽出
- MP3形式で保存（128/192/320kbps選択可）
- ID3タグ自動設定
- 音声プレビュー機能

### 🗣️ **3. 多言語音声吹き替え** ⭐ NEW
- **処理フロー**: `YouTube音声 → Whisper文字起こし → 翻訳 → TTS音声合成 → MP3出力`
- **多言語対応**: Whisper対応の全言語（日本語、英語、中国語、韓国語など99言語）
- **6段階翻訳フォールバック**:
  - **Groq API** (無料・高速・推奨) ⭐
  - **Gemini API** (Google AI)
  - **DeepL API** (最高品質)
  - **OpenRouter API** (コスパ良)
  - **OpenAI API** (ChatGPT)
  - **Argos Translate** (完全オフライン)
- **複数TTS対応**:
  - **edge_tts** (デフォルト・エンジン不要・自然な日本語) ⭐
  - **VOICEVOX** (キャラクター音声・高品質・要エンジン起動)

### 🎞️ **4. 動画連結**
- 複数動画を1つに統合
- ドラッグ&ドロップで順序変更
- 解像度統一処理
- トランジション効果（オプション）

### 🎼 **5. 音声連結**
- 複数MP3ファイルを統合
- 音量自動正規化
- メタデータ統合

---

## 🚀 クイックスタート

### **必要環境**
- **OS**: Windows 10/11, macOS 11+, Linux
- **Python**: 3.10以上
- **FFmpeg**: 必須（システムにインストール）
- **VOICEVOX Engine**: オプション（高品質日本語TTS使用時）
- **API Keys**: オプション（翻訳APIを使う場合）

### **インストール**

#### **Pythonソースから実行する場合**

```bash
# 1. リポジトリクローン
git clone https://github.com/your-repo/MediaForgeStudio.git
cd MediaForgeStudio

# 2. 仮想環境作成
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 3. FFmpegインストール（必須）
# Windows
choco install ffmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt install ffmpeg

# 4. 依存関係インストール
pip install -r requirements.txt

# 5. 環境変数設定（オプション）
cp .env.template .env
# .envファイルを編集してAPIキーを設定

# 6. アプリケーション起動
python main.py
```

#### **配布版（.EXE）**
現在準備中です。将来的にPyInstallerでビルドしたバイナリを提供予定。

---

## 🎨 スクリーンショット

```
┌──────────────────────────────────────────────┐
│ 🎬 MediaForge Studio           [🔍][−][×]   │
├──────────────────────────────────────────────┤
│ [ダウンロード] [音声抽出] [吹替] [連結]      │
├──────────────────────────────────────────────┤
│                                              │
│  ┌─ YouTube URL入力 ─────────────────────┐  │
│  │ https://youtube.com/watch?v=...       │  │
│  └───────────────────────────────────────┘  │
│                                              │
│  📋 処理キュー                                │
│  ┌──────────────────────────────────────┐  │
│  │ ✅ video1.mp4 - 完了                 │  │
│  │ ⏳ video2.mp4 - 処理中 45%           │  │
│  │ ⏸️ video3.mp4 - 待機中               │  │
│  └──────────────────────────────────────┘  │
│                                              │
│  ■■■■■■■■□□ 78% (1分32秒残り)        │
│                                              │
│  [処理開始] [一時停止] [キャンセル]          │
└──────────────────────────────────────────────┘
```

---

## 📂 プロジェクト構造

```
MediaForgeStudio/
├── app/
│   ├── core/                   # コア処理モジュール
│   │   ├── downloader.py       # YouTube動画DL
│   │   ├── audio_extractor.py  # 音声抽出
│   │   ├── transcriber.py      # Whisper文字起こし
│   │   ├── translator.py       # 翻訳管理
│   │   ├── tts_manager.py      # TTS統合管理
│   │   ├── video_merger.py     # 動画連結
│   │   └── audio_merger.py     # 音声連結
│   │
│   ├── tts/                    # TTS実装
│   │   ├── edge_tts_engine.py
│   │   ├── voicevox_engine.py
│   │   ├── google_tts_engine.py
│   │   └── pyttsx3_engine.py
│   │
│   ├── ui/                     # PySide6 UI
│   │   ├── main_window.py
│   │   ├── tabs/               # 各タブ画面
│   │   ├── widgets/            # カスタムウィジェット
│   │   └── dialogs/            # ダイアログ
│   │
│   ├── models/                 # データモデル
│   ├── utils/                  # ユーティリティ
│   └── resources/              # リソース
│
├── config/                     # 設定ファイル
│   ├── config.yaml
│   └── tts_voices.yaml
│
├── output/                     # 出力先
│   ├── videos/
│   ├── audios/
│   └── dubbed/
│
├── logs/                       # ログ
├── docs/                       # ドキュメント
├── main.py                     # エントリーポイント
├── requirements.txt            # 依存関係
└── README.md
```

---

## 🛠️ 技術スタック

### **コア**
- **Python**: 3.10+
- **UI**: PySide6 (Qt6)
- **デザイン**: QFluentWidgets + qdarktheme

### **メディア処理**
- **yt-dlp**: YouTube動画ダウンロード
- **FFmpeg**: メディアエンコーディング
- **pydub**: 音声操作

### **AI/機械学習**
- **OpenAI Whisper**: 音声認識（13言語）
- **PyTorch**: 機械学習フレームワーク

### **翻訳（6段階フォールバック）**
1. **Groq API**: 高速無料翻訳（推奨）
2. **Gemini API**: Google AI翻訳
3. **DeepL API**: 最高品質翻訳
4. **OpenRouter API**: コスパ良AI翻訳
5. **OpenAI API**: ChatGPT翻訳
6. **Argos Translate**: 完全オフライン翻訳

### **TTS（音声合成）**
- **edge_tts**: Microsoft Edge TTS（デフォルト・推奨）
- **VOICEVOX**: キャラクター音声（要エンジン起動）
- **pyttsx3**: オフラインTTS（フォールバック）

---

## ⚙️ 設定

### **環境変数 (.env)**
```env
# 翻訳APIキー（すべてオプション・設定すると翻訳の選択肢が増えます）
GROQ_API_KEY=your_groq_api_key              # 推奨: 無料で高速
GEMINI_API_KEY=your_gemini_api_key          # Google AI
DEEPL_API_KEY=your_deepl_api_key            # 高品質だが有料
OPENROUTER_API_KEY=your_openrouter_api_key  # コスパ良
OPENAI_API_KEY=your_openai_api_key          # ChatGPT

# VOICEVOX設定（オプション）
VOICEVOX_HOST=localhost
VOICEVOX_PORT=50021

# 処理設定（オプション）
WHISPER_MODEL=base  # tiny/base/small/medium/large
WHISPER_DEVICE=auto  # auto/cuda/cpu/mps
MAX_WORKERS=3
```

**注意**: APIキーを設定しなくても、Argos Translate（オフライン翻訳）とedge_tts（無料TTS）で動作します。

### **config.yaml**
```yaml
app:
  theme: auto  # light/dark/auto
  language: ja

download:
  default_resolution: 720p
  max_concurrent: 3
  
audio:
  default_bitrate: 128k
  
tts:
  default_engine: edge_tts
  edge_voice: ja-JP-NanamiNeural
```

---

## 📖 ドキュメント

詳細なドキュメントは `/docs` フォルダーにあります：

- [要求定義書](docs/01_requirements.md)
- [アーキテクチャ設計書](docs/02_architecture.md)
- [技術仕様書](docs/03_technical_specs.md)
- [UI/UX設計書](docs/04_ui_ux_design.md)
- [API仕様書](docs/05_api_reference.md)
- [開発ロードマップ](docs/06_roadmap.md)
- [セットアップガイド](docs/07_setup_guide.md)
- [Claude Code開発ガイド](docs/CLAUDE.md)

---

## 🔧 ビルド・配布

### **PyInstallerでEXE作成**

```bash
# 依存関係ビルド
pip install pyinstaller

# EXE生成（onefolder形式）
pyinstaller build_exe.spec

# 出力先
dist/MediaForgeStudio/
  ├── MediaForgeStudio.exe
  ├── _internal/
  └── config/
```

### **配布用ZIP作成**

```bash
# dist/MediaForgeStudioフォルダーをZIP圧縮
```

---

## 🐛 トラブルシューティング

### **よくある問題**

**Q: VOICEVOX接続エラー**
```
A: VOICEVOX Engineが起動しているか確認
   http://localhost:50021 にアクセス可能か確認
   エンジンが起動していない場合は自動的に edge_tts にフォールバックします
```

**Q: 翻訳が「すべて失敗」となる**
```
A: 最低1つのAPIキーを .env に設定してください（Groq推奨）
   または、Argos Translateパッケージをインストール:
   pip install argostranslate
```

**Q: yt-dlpダウンロードエラー**
```
A: yt-dlpを最新版に更新
   pip install --upgrade yt-dlp
```

**Q: Whisper GPU認識しない**
```
A: PyTorch CUDA版がインストールされているか確認
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

**Q: FFmpegが見つからない**
```
A: システムにFFmpegをインストールしてください
   Windows: choco install ffmpeg
   macOS: brew install ffmpeg
   Linux: sudo apt install ffmpeg
```

**Q: numba関連エラー**
```
A: numbaのバージョンを固定してください
   pip install numba==0.60.0
```

---

## 🤝 コントリビューション

プルリクエストやIssueを歓迎します！

1. フォーク
2. フィーチャーブランチ作成 (`git checkout -b feature/amazing-feature`)
3. コミット (`git commit -m 'Add amazing feature'`)
4. プッシュ (`git push origin feature/amazing-feature`)
5. プルリクエスト作成

---

## 📝 ライセンス

MIT License - 詳細は [LICENSE](LICENSE) ファイルを参照

---

## 🙏 謝辞

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube動画ダウンロード
- [OpenAI Whisper](https://github.com/openai/whisper) - 音声認識
- [VOICEVOX](https://voicevox.hiroshiba.jp/) - 音声合成エンジン
- [Microsoft Edge TTS](https://github.com/rany2/edge-tts) - 音声合成
- [PySide6](https://www.qt.io/qt-for-python) - UIフレームワーク
- [QFluentWidgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets) - Fluent Designコンポーネント
- [FFmpeg](https://ffmpeg.org/) - メディア処理

---

## 📈 開発状況

### **実装済み（MVP 85%）**
- ✅ YouTube動画ダウンロード（解像度選択、進捗表示）
- ✅ 音声抽出（MP3/WAV変換）
- ✅ Whisper文字起こし（多言語対応）
- ✅ 6段階翻訳フォールバック
- ✅ TTS音声合成（edge_tts、VOICEVOX）
- ✅ 動画・音声連結機能
- ✅ モダンなUI（QFluentWidgets）

### **今後の実装予定**
- ⬜ Google Cloud TTS、pyttsx3エンジン追加
- ⬜ 設定タブ（API キー管理UI）
- ⬜ ダウンロード履歴データベース
- ⬜ ダウンロードキャンセル機能
- ⬜ PyInstallerビルド（配布用EXE）

---

## 📞 サポート

- **Issues**: [GitHub Issues](https://github.com/your-repo/MediaForgeStudio/issues)
- **Discussion**: [GitHub Discussions](https://github.com/your-repo/MediaForgeStudio/discussions)

---

## 🙏 開発者より

このプロジェクトは教育目的で開発されています。YouTube動画の利用規約を遵守し、著作権を尊重してご利用ください。

**MediaForge Studio** - Forging Media for Education 🎓
