# MediaForge Studio - ビルドガイド

このガイドでは、MediaForge Studioの実行ファイル（.exe）を作成する手順を説明します。

## 前提条件

- Python 3.9以上がインストールされていること
- すべての依存パッケージがインストールされていること
- FFmpegがシステムにインストールされていること

## ビルド手順

### 方法1: バッチスクリプトを使用（推奨）

プロジェクトには3つのビルド用バッチファイルが用意されています。用途に応じて選択してください。

#### 📄 `build.bat` - 標準ビルド（推奨）

最も一般的なビルド方法です。仮想環境のチェックやビルド結果の確認を含む、最も堅牢なスクリプトです。

**用途**: 通常のビルド作業

**実行内容**:
1. 仮想環境の自動検出と有効化
2. 古いビルドファイルのクリーンアップ
3. `MediaForgeStudio.spec`を使用したビルド
4. ビルド成功/失敗のチェックと詳細なメッセージ表示
5. 追加で必要な手順の案内（FFmpegコピー、.env設定など）

**使い方**:
```bash
build.bat
```

**推奨する場合**:
- 初めてビルドする
- 安定したビルドプロセスが必要
- ビルド後の手順を確認したい

---

#### 📄 `build_simple.bat` - 最小構成ビルド

最小限のコマンドで素早くビルドします。`.spec`ファイルを使わず、必要最低限の設定のみでビルドします。

**用途**: クイックテスト、軽量ビルド

**実行内容**:
1. 古いビルドファイルのクリーンアップ
2. PyInstallerに直接コマンドラインオプションを指定してビルド
   - アイコン設定
   - ウィンドウモード
   - onedirモード
3. シンプルな完了メッセージ

**使い方**:
```bash
build_simple.bat
```

**推奨する場合**:
- 開発中の動作確認
- 軽量で素早いビルドが必要
- カスタムビルドオプションを試したい

**注意**:
- 隠しインポートが含まれないため、一部のモジュールが欠落する可能性があります
- 本番配布には`build.bat`または`build_with_ffmpeg.bat`を推奨

---

#### 📄 `build_with_ffmpeg.bat` - 完全パッケージビルド

FFmpegバイナリと.env.exampleを自動的にコピーし、配布準備まで完了させるスクリプトです。

**用途**: 配布用パッケージの作成

**実行内容**:
1. 古いビルドファイルのクリーンアップ
2. `MediaForgeStudio.spec`を使用したビルド
3. ビルド成功のチェック
4. **FFmpegバイナリの自動コピー** (`C:\ffmpeg\bin\`から)
5. **.env.exampleの自動コピー**
6. 次のステップの案内

**使い方**:
```bash
build_with_ffmpeg.bat
```

**推奨する場合**:
- 配布用パッケージを作成する
- FFmpegを含めた完全なパッケージが必要
- ワンクリックでビルド完了させたい

**前提条件**:
- FFmpegが`C:\ffmpeg\bin\`にインストールされている必要があります
- `.env.example`ファイルが存在する必要があります

**カスタマイズ**:
FFmpegのパスが異なる場合は、バッチファイルの28-29行目を編集してください：
```batch
copy C:\ffmpeg\bin\ffmpeg.exe dist\MediaForgeStudio\
copy C:\ffmpeg\bin\ffprobe.exe dist\MediaForgeStudio\
```

---

### どのバッチファイルを使うべき？

| シチュエーション | 推奨バッチファイル |
|-----------------|-------------------|
| 初めてビルドする | `build.bat` |
| 開発中の動作確認 | `build_simple.bat` |
| 配布パッケージ作成 | `build_with_ffmpeg.bat` |
| 標準的なビルド | `build.bat` |
| FFmpegを手動でコピーしたい | `build.bat` |
| FFmpegを自動でコピーしたい | `build_with_ffmpeg.bat` |

### 方法2: 手動コマンド

より細かい制御が必要な場合は、以下のコマンドを手動で実行します。

#### 1. PyInstallerのインストール（まだの場合）

```bash
pip install pyinstaller
```

#### 2. 古いビルドファイルの削除

```bash
rmdir /s /q build
rmdir /s /q dist
```

#### 3. .specファイルを使用してビルド

```bash
pyinstaller MediaForgeStudio.spec
```

#### 4. または、コマンドラインオプションで直接ビルド

```bash
pyinstaller --name MediaForgeStudio ^
    --icon=arisa004.ico ^
    --windowed ^
    --onedir ^
    --add-data ".env;." ^
    --hidden-import PySide6.QtCore ^
    --hidden-import PySide6.QtGui ^
    --hidden-import PySide6.QtWidgets ^
    --hidden-import qfluentwidgets ^
    --hidden-import whisper ^
    --hidden-import torch ^
    --hidden-import groq ^
    --hidden-import edge_tts ^
    main.py
```

## ビルド後の設定

ビルドが成功すると、`dist/MediaForgeStudio/` フォルダに実行ファイルが作成されます。

### 必須の追加ファイル

実行ファイルを動作させるために、以下のファイルを `dist/MediaForgeStudio/` にコピーしてください：

#### 1. FFmpeg バイナリ（必須）

以下のファイルを `dist/MediaForgeStudio/` にコピー：
- `ffmpeg.exe`
- `ffprobe.exe`

**入手先**: https://github.com/BtbN/FFmpeg-Builds/releases

#### 2. .env ファイル（APIキーを使用する場合）

```bash
# dist/MediaForgeStudio/.env

# Translation APIs
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
DEEPL_API_KEY=your_deepl_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Google Cloud TTS (Optional)
GOOGLE_CLOUD_API_KEY=your_google_cloud_api_key_here

# VOICEVOX (Optional)
VOICEVOX_HOST=127.0.0.1
VOICEVOX_PORT=50021
```

**注意**: .envファイルには機密情報が含まれるため、配布版では含めないでください。ユーザーに自分のAPIキーを設定してもらうようにしましょう。

#### 3. config.yaml（オプション）

デフォルト設定をカスタマイズする場合：

```yaml
# dist/MediaForgeStudio/config/config.yaml
app:
  theme: auto
  language: ja
  log_level: INFO

download:
  default_resolution: 720p
  max_concurrent: 3
  output_dir: ./output/videos

# ... その他の設定
```

## ディレクトリ構成

ビルド後のディレクトリ構成は以下のようになります：

```
dist/
└── MediaForgeStudio/
    ├── MediaForgeStudio.exe  # メイン実行ファイル
    ├── ffmpeg.exe            # FFmpeg (手動でコピー)
    ├── ffprobe.exe           # FFprobe (手動でコピー)
    ├── .env                  # 環境変数 (手動で作成)
    ├── _internal/            # PyInstallerが作成した依存ファイル
    ├── config/               # 設定ファイル（自動生成）
    ├── output/               # 出力ディレクトリ（自動生成）
    ├── temp/                 # 一時ファイル（自動生成）
    └── logs/                 # ログファイル（自動生成）
```

## 実行とテスト

### 1. 基本動作確認

```bash
cd dist\MediaForgeStudio
MediaForgeStudio.exe
```

### 2. 確認項目

- [ ] アプリケーションが正常に起動する
- [ ] UIが正しく表示される
- [ ] YouTube動画のダウンロードが動作する
- [ ] 音声抽出が動作する
- [ ] Whisper文字起こしが動作する
- [ ] 翻訳機能が動作する（APIキー設定済みの場合）
- [ ] TTS音声合成が動作する
- [ ] 動画・音声連結が動作する

## トラブルシューティング

### エラー: "FFmpeg not found"

**原因**: FFmpegがシステムパスに含まれていない

**解決策**:
1. `ffmpeg.exe`と`ffprobe.exe`を`dist/MediaForgeStudio/`にコピー
2. または、システムのPATH環境変数にFFmpegのパスを追加

### エラー: "Module not found"

**原因**: 隠しインポートが不足している

**解決策**:
1. `MediaForgeStudio.spec`の`hiddenimports`リストに該当モジュールを追加
2. 再ビルド

### ビルドサイズが大きすぎる

**原因**: PyTorch、Whisperなどの大きなライブラリを含んでいる

**解決策**:
- `--onefile`オプションは使用しない（起動が遅くなる）
- 不要なモジュールを`excludes`リストに追加
- UPX圧縮を有効化（既に有効）

### 起動が遅い

**原因**: `--onefile`モードで一時ファイルを展開している

**解決策**:
- `--onedir`モード（デフォルト）を使用
- ビルドサイズは大きくなるが、起動は高速

## 配布前のチェックリスト

- [ ] すべての機能が正常に動作することを確認
- [ ] FFmpegバイナリが含まれている
- [ ] .envファイルのサンプル（.env.example）を作成
- [ ] README.mdを同梱（使用方法を記載）
- [ ] ライセンスファイルを同梱
- [ ] 配布用のZIPファイルを作成

## 配布方法

### ZIP配布

```bash
# dist/MediaForgeStudio フォルダをZIP圧縮
# MediaForgeStudio_v1.0.0.zip
```

含めるファイル：
- `MediaForgeStudio.exe`
- `_internal/` フォルダ
- `ffmpeg.exe`, `ffprobe.exe`
- `.env.example` （APIキーのサンプル）
- `README.md` （使い方）
- `LICENSE.txt`

### インストーラー作成（上級）

Inno SetupやNSISを使用してインストーラーを作成することも可能です。

## パフォーマンス最適化

### ビルドサイズの削減

1. **仮想環境を使用**
   ```bash
   python -m venv venv_build
   venv_build\Scripts\activate
   pip install -r requirements.txt
   pip install pyinstaller
   pyinstaller MediaForgeStudio.spec
   ```

2. **不要なモジュールを除外**
   - `MediaForgeStudio.spec`の`excludes`リストを編集

3. **UPX圧縮を使用**
   - 既に有効化されています（`upx=True`）
   - UPXをダウンロード: https://upx.github.io/

### 起動時間の短縮

1. **遅延インポート**
   - 必要になるまでモジュールをインポートしない
   - 大きなライブラリ（Whisper、PyTorch）は初回使用時にロード

2. **--onedir モードを使用**（推奨）
   - すでにデフォルトで有効

## よくある質問

### Q: ビルドにどれくらい時間がかかりますか？

A: 環境によりますが、通常5〜15分程度です。初回ビルドは特に時間がかかります。

### Q: ビルドしたファイルのサイズは？

A: Whisper、PyTorchを含むため、約1.5〜2GB程度になります。

### Q: 他のPCでも動作しますか？

A: はい。ただし、以下の条件を満たす必要があります：
- Windows 10/11 (64-bit)
- 十分なメモリ（推奨8GB以上）
- インターネット接続（YouTube、API使用時）

### Q: ウイルス対策ソフトが警告を出します

A: PyInstallerでビルドしたファイルは誤検知される場合があります。
- コード署名証明書で署名する
- VirusTotalで確認する
- ソースコードを公開して信頼性を高める

## サポート

問題が発生した場合：
1. `logs/`フォルダのログファイルを確認
2. GitHubのIssuesに報告
3. ドキュメントを参照

---

**ビルド成功を祈っています！** 🚀
