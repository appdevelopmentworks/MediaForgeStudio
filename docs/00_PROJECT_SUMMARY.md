# 📦 MediaForge Studio - プロジェクトサマリー & Claude Code引き継ぎ情報

---

## ✅ 完了した作業

### **1. プロジェクト構造作成**
```
MediaForgeStudio/
├── app/                    # アプリケーションコード
│   ├── core/              # コア処理モジュール（空）
│   ├── tts/               # TTS実装（空）
│   ├── ui/                # UI実装（空）
│   ├── models/            # データモデル（空）
│   ├── utils/             # ユーティリティ（空）
│   └── resources/         # リソース（空）
├── config/                # 設定ファイル
│   └── config.yaml       ✅ 作成済み
├── output/                # 出力先
│   ├── videos/
│   ├── audios/
│   └── dubbed/
├── logs/                  # ログ
├── docs/                  # ドキュメント ✅ 完全作成
└── main.py               ✅ スケルトン作成
```

### **2. ドキュメント作成（完全）**

#### **メインドキュメント**
- ✅ `README.md` - プロジェクト概要、機能説明、使用方法
- ✅ `requirements.txt` - Python依存関係リスト
- ✅ `config.yaml` - アプリケーション設定
- ✅ `.env.template` - 環境変数テンプレート
- ✅ `.gitignore` - Git除外設定
- ✅ `main.py` - エントリーポイント（スケルトン）

#### **docsフォルダー（Claude Code開発用）**
- ✅ `01_requirements.md` - 詳細要求定義書
- ✅ `02_architecture.md` - アーキテクチャ設計書
- ✅ `06_roadmap.md` - 開発ロードマップ
- ✅ `07_setup_guide.md` - セットアップガイド
- ✅ **`CLAUDE.md`** - **Claude Code開発ガイド（最重要）**

---

## 🎯 プロジェクト概要

### **プロジェクト名**: MediaForge Studio
### **目的**: YouTube動画の加工・吹き替え・統合を行う教育向けツール

### **主要機能（優先度順）**
1. ⭐⭐⭐⭐⭐ YouTube動画ダウンロード
2. ⭐⭐⭐⭐⭐ YouTube音声抽出（MP3）
3. ⭐⭐⭐⭐⭐ 音声吹き替え（Whisper + 翻訳 + TTS）
4. ⭐⭐⭐⭐ 動画連結
5. ⭐⭐⭐⭐ 音声連結
6. ⭐⭐⭐ 見栄えの良いUI

### **技術スタック**
- **UI**: PySide6 + QFluentWidgets + qdarktheme
- **動画処理**: yt-dlp, FFmpeg, moviepy
- **AI/ML**: OpenAI Whisper, PyTorch
- **翻訳**: 5段階フォールバック（DeepL/Groq/Gemini/OpenAI/Argos）
- **TTS**: edge_tts（デフォルト）, VOICEVOX, Google TTS, pyttsx3

---

## 🚀 Claude Code への引き継ぎ事項

### **最初に読むべきドキュメント（必須）**
1. **`docs/CLAUDE.md`** ⭐⭐⭐ - 開発ガイドの全て
2. **`docs/01_requirements.md`** - 機能要求定義
3. **`docs/02_architecture.md`** - アーキテクチャ設計
4. **`docs/06_roadmap.md`** - 開発スケジュール

### **開発の進め方**

#### **Phase 1から順番に実装**
```
Week 1-3: コア機能
  → YouTubeDownloader
  → AudioExtractor
  → 基本UI

Week 4-6: 音声処理
  → Whisper文字起こし
  → 翻訳システム
  → TTS統合

Week 7-8: 連結機能
  → 動画連結
  → 音声連結

Week 9: UI/UX改善
Week 10: 配布準備
```

### **実装順序（推奨）**

#### **1. データモデルから開始**
```python
# app/models/download_item.py
@dataclass
class VideoInfo:
    url: str
    title: str
    duration: int
    # ...
```

#### **2. コア機能実装**
```python
# app/core/downloader.py
class YouTubeDownloader:
    async def get_video_info(self, url: str) -> VideoInfo:
        # yt-dlp使用
        pass
```

#### **3. UI実装**
```python
# app/ui/tabs/download_tab.py
class DownloadTab(QWidget):
    # PySide6 + QFluentWidgets使用
    pass
```

---

## 📝 重要な設計決定事項

### **1. TTS優先順位**
```
1. edge_tts（デフォルト）
   - エンジン不要
   - 無料
   - 自然な日本語

2. VOICEVOX（オプション）
   - エンジン起動必要
   - 高品質キャラクター音声

3. Google Cloud TTS（オプション）
   - APIキー必要
   - 最高品質

4. pyttsx3（フォールバック）
   - オフライン
   - OS標準音声
```

### **2. 翻訳システム - 5段階フォールバック**
```
1. DeepL API → 2. Groq API → 3. Gemini API → 4. OpenAI API → 5. Argos Translate
```

### **3. 音声吹き替えの処理フロー**
```
YouTube音声
  ↓
Whisper文字起こし
  ↓
翻訳（5段階フォールバック）
  ↓
TTS音声合成
  ↓
MP3出力（動画との結合なし）
```

### **4. UI設計**
- シングルウィンドウ、タブ切り替え
- Fluent Design
- ダーク/ライトモード自動切替
- ドラッグ&ドロップ対応

---

## 🔧 開発環境セットアップ手順

### **1. 仮想環境作成**
```bash
cd C:\Users\hartm\Desktop\MediaForgeStudio
python -m venv venv
venv\Scripts\activate  # Windows
```

### **2. 依存関係インストール**
```bash
pip install -r requirements.txt
```

### **3. FFmpegインストール**
```bash
choco install ffmpeg  # Windows
```

### **4. 環境変数設定**
```bash
cp .env.template .env
# .envを編集してAPIキーを設定（オプション）
```

### **5. 動作確認**
```bash
python main.py
# メッセージボックスが表示されれば成功
```

---

## 💡 開発のヒント

### **コーディング規約**
- 型ヒント必須
- Docstring必須（Google Style）
- エラーハンドリング必須（try-except）
- ログ出力必須（loguru使用）
- 非同期処理（asyncio）

### **命名規則**
- クラス: `PascalCase`
- 関数/変数: `snake_case`
- 定数: `UPPER_SNAKE_CASE`
- プライベート: `_prefix`

### **ディレクトリ配置**
```
app/core/       → ビジネスロジック
app/tts/        → TTS実装
app/ui/         → UI実装
app/models/     → データモデル
app/utils/      → ユーティリティ
```

---

## 🐛 注意事項

### **1. PyVDTClaudeとの違い**
- **動画との結合なし**: 音声ファイルのみ出力（時間短縮）
- **複数TTS対応**: edge_tts優先、VOICEVOX optional
- **連結機能あり**: 動画連結、音声連結機能を追加
- **UI**: PySide6 + QFluentWidgets（PyVDTClaudeはGradio）

### **2. 外部依存**
- **FFmpeg**: EXE同梱
- **VOICEVOX Engine**: ユーザー手動インストール（オプション）
- **APIキー**: すべてオプション（オフライン動作可能）

### **3. 配布形態**
- Phase 1: PyInstaller onefolder
- Phase 2: Nuitka（将来）

---

## ✅ 次のステップ（Claude Codeへの指示）

### **最初に実装すべきもの**

1. **データモデル** (`app/models/`)
   - `download_item.py`
   - `tts_config.py`
   - `queue_item.py`

2. **ユーティリティ** (`app/utils/`)
   - `logger.py`
   - `file_manager.py`
   - `config_manager.py`

3. **YouTubeDownloader** (`app/core/downloader.py`)
   - `get_video_info()`
   - `download_video()`
   - `download_batch()`

4. **基本UI** (`app/ui/`)
   - `main_window.py`
   - `tabs/download_tab.py`

### **実装時の確認事項**
- [ ] `docs/CLAUDE.md` を読んだか
- [ ] 型ヒントを記述したか
- [ ] Docstringを記述したか
- [ ] エラーハンドリングを実装したか
- [ ] ログ出力を追加したか
- [ ] 非同期処理を適切に使用したか

---

## 📞 質問・相談

実装中に不明点があれば:
1. `docs/CLAUDE.md` を参照
2. `docs/02_architecture.md` でアーキテクチャ確認
3. ユーザーに質問

---

## 🎉 完了状況

```
[████████░░░░░░░░░░░░] 40% - プロジェクト準備完了

✅ プロジェクト構造作成
✅ ドキュメント完全作成
✅ 設定ファイル作成
✅ メインファイルスケルトン作成
⬜ 実装開始（Claude Codeへ引き継ぎ）
```

---

**MediaForge Studio プロジェクトの準備が完了しました！**

**次は Claude Code で実装を進めてください。**

---

**作成日**: 2025-01-20  
**準備完了**: 2025-01-20  
**引き継ぎ先**: Claude Code  
**開発開始予定**: すぐに開始可能
