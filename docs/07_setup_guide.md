# 🚀 MediaForge Studio - セットアップガイド

このガイドでは、MediaForge Studioの開発環境をセットアップする手順を説明します。

---

## 📋 必要な環境

### **必須**
- **Python**: 3.10以上
- **FFmpeg**: メディア処理用
- **Git**: バージョン管理

### **オプション**
- **VOICEVOX Engine**: 高品質TTS使用時
- **CUDA**: GPU高速化（Windows）
- **MPS**: GPU高速化（Mac）

---

## 🔧 セットアップ手順

### **1. リポジトリクローン**

```bash
# GitHubからクローン（公開時）
git clone https://github.com/your-repo/MediaForgeStudio.git
cd MediaForgeStudio

# またはローカルフォルダから
cd /path/to/MediaForgeStudio
```

### **2. Pythonバージョン確認**

```bash
python --version
# Python 3.10.x 以上であることを確認
```

### **3. 仮想環境作成**

#### **Windows**
```bash
python -m venv venv
venv\Scripts\activate
```

#### **macOS / Linux**
```bash
python3 -m venv venv
source venv/bin/activate
```

### **4. 依存関係インストール**

```bash
# 基本パッケージ
pip install --upgrade pip
pip install -r requirements.txt

# PyTorch（GPU対応版 - オプション）
# CUDA 11.8の場合
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Mac (Apple Silicon)の場合
# pip install torch torchvision torchaudio
```

### **5. FFmpegインストール**

#### **Windows**
```bash
# Chocolateyを使用
choco install ffmpeg

# または https://ffmpeg.org/download.html からダウンロード
# ffmpeg.exeをPATHに追加
```

#### **macOS**
```bash
brew install ffmpeg
```

#### **Linux (Ubuntu/Debian)**
```bash
sudo apt update
sudo apt install ffmpeg
```

**確認**:
```bash
ffmpeg -version
```

### **6. 環境変数設定**

```bash
# .env.template を .env にコピー
cp .env.template .env

# .env ファイルを編集してAPIキーを設定（オプション）
# エディタで開く
nano .env  # または code .env
```

**.env 例**:
```env
# 翻訳API（オプション）
DEEPL_API_KEY=your_deepl_api_key_here
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# VOICEVOX設定
VOICEVOX_HOST=localhost
VOICEVOX_PORT=50021
```

### **7. VOICEVOX Engineインストール（オプション）**

高品質なキャラクター音声を使用する場合のみ必要です。

1. [VOICEVOX公式サイト](https://voicevox.hiroshiba.jp/)からダウンロード
2. インストールして起動
3. `http://localhost:50021` で接続確認

**確認**:
```bash
curl http://localhost:50021/version
```

### **8. 動作確認**

```bash
# アプリケーション起動
python main.py
```

メッセージボックスが表示されれば成功です！

---

## 🧪 開発環境セットアップ（オプション）

### **開発用ツールのインストール**

```bash
# コード品質チェック
pip install black flake8 mypy

# テストフレームワーク
pip install pytest pytest-asyncio pytest-qt

# 型チェック
pip install types-PyYAML types-requests
```

### **VS Code設定（推奨）**

`.vscode/settings.json` を作成:
```json
{
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "100"],
  "editor.formatOnSave": true,
  "python.analysis.typeCheckingMode": "basic"
}
```

---

## 🐛 トラブルシューティング

### **問題1: ModuleNotFoundError**

```bash
# 仮想環境が有効化されているか確認
which python  # macOS/Linux
where python  # Windows

# 依存関係を再インストール
pip install --force-reinstall -r requirements.txt
```

### **問題2: FFmpegが見つからない**

```bash
# PATHに追加されているか確認
ffmpeg -version

# Windows: 環境変数PATHにffmpeg.exeのパスを追加
# macOS/Linux: ~/.bashrc または ~/.zshrc に追加
export PATH="/path/to/ffmpeg:$PATH"
```

### **問題3: PyTorch CUDA認識しない**

```bash
# CUDAバージョン確認
nvidia-smi

# 対応するPyTorchをインストール
# https://pytorch.org/get-started/locally/ で確認
```

### **問題4: VOICEVOX接続エラー**

```bash
# VOICEVOX Engineが起動しているか確認
curl http://localhost:50021/version

# ポートが使用中の場合
netstat -ano | findstr :50021  # Windows
lsof -i :50021                 # macOS/Linux
```

### **問題5: Permission denied (macOS/Linux)**

```bash
# 実行権限を付与
chmod +x main.py
```

---

## 📁 ディレクトリ構造確認

セットアップ後、以下の構造になっていることを確認:

```
MediaForgeStudio/
├── venv/                   # 仮想環境（作成済み）
├── app/                    # アプリケーションコード
├── config/                 # 設定ファイル
├── output/                 # 出力先（自動作成）
│   ├── videos/
│   ├── audios/
│   └── dubbed/
├── logs/                   # ログ（自動作成）
├── temp/                   # 一時ファイル（自動作成）
├── data/                   # データベース（自動作成）
├── docs/                   # ドキュメント
├── .env                    # 環境変数（作成済み）
├── main.py
└── requirements.txt
```

---

## 🚀 次のステップ

1. **ドキュメントを読む**:
   - `README.md`: プロジェクト概要
   - `docs/01_requirements.md`: 要求定義
   - `docs/02_architecture.md`: アーキテクチャ
   - `docs/CLAUDE.md`: Claude Code開発ガイド

2. **開発開始**:
   - `app/core/downloader.py` から実装開始
   - `docs/CLAUDE.md` の実装ガイドに従う

3. **テスト実行**:
   ```bash
   pytest tests/
   ```

---

## 📞 サポート

問題が解決しない場合:
- [GitHub Issues](https://github.com/your-repo/MediaForgeStudio/issues)
- [ドキュメント](./docs/)

---

**セットアップ完了！開発を楽しんでください！** 🎉
