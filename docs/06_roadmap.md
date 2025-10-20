# 🗓️ MediaForge Studio - 開発ロードマップ

---

## 📊 開発スケジュール概要

**総開発期間**: 約10週間  
**開始日**: 2025-01-20  
**予定リリース**: 2025-04-01

---

## 🎯 Phase 1: コア機能実装（Week 1-3）

### **Week 1: プロジェクト基盤**

#### **Day 1-2: セットアップ**
- [x] プロジェクト構造作成
- [x] ドキュメント作成
- [ ] 開発環境セットアップ
- [ ] 依存関係インストール確認

#### **Day 3-5: データモデル実装**
- [ ] `app/models/download_item.py`
  - VideoInfo
  - DownloadResult
  - DownloadHistory
- [ ] `app/models/tts_config.py`
  - TTSParams
  - VoiceConfig
- [ ] `app/models/queue_item.py`
  - QueueItem
  - QueueStatus

#### **Day 6-7: ユーティリティ実装**
- [ ] `app/utils/logger.py`
  - ログ設定
  - ロガー取得
- [ ] `app/utils/file_manager.py`
  - ファイル名サニタイズ
  - ディレクトリ管理
  - 一時ファイル削除
- [ ] `app/utils/config_manager.py`
  - YAML設定読み込み
  - 設定値取得/保存

---

### **Week 2: YouTube動画ダウンロード**

#### **Day 1-3: Downloaderコア実装**
- [ ] `app/core/downloader.py`
  - YouTubeDownloaderクラス
  - get_video_info()
  - download_video()
  - download_batch()
  - 進捗コールバック実装
  - エラーハンドリング

#### **Day 4-5: 音声抽出実装**
- [ ] `app/core/audio_extractor.py`
  - AudioExtractorクラス
  - extract_audio()
  - set_id3_tags()
  - ビットレート変換

#### **Day 6-7: データベース実装**
- [ ] `app/utils/database.py`
  - SQLite接続管理
  - ダウンロード履歴保存
  - 設定保存/読み込み
  - マイグレーション

---

### **Week 3: 基本UI実装**

#### **Day 1-3: MainWindow実装**
- [ ] `app/ui/main_window.py`
  - FluentWindowベース
  - タブナビゲーション
  - ステータスバー
  - テーマ切替

#### **Day 4-5: DownloadTab実装**
- [ ] `app/ui/tabs/download_tab.py`
  - URL入力ウィジェット
  - 動画情報カード
  - プログレスバー
  - ダウンロードボタン
  - 履歴表示

#### **Day 6-7: AudioExtractTab実装**
- [ ] `app/ui/tabs/audio_extract_tab.py`
  - ファイル選択
  - ビットレート選択
  - プレビュー機能
  - 抽出ボタン

**Phase 1 マイルストーン**:
- ✅ YouTube動画ダウンロード機能完成
- ✅ 音声抽出（MP3）機能完成
- ✅ 基本UI動作

---

## 🎤 Phase 2: 音声処理実装（Week 4-6）

### **Week 4: Whisper文字起こし**

#### **Day 1-3: Transcriber実装**
- [ ] `app/core/transcriber.py`
  - WhisperTranscriberクラス
  - モデル読み込み
  - GPU/CPU自動検出
  - transcribe()
  - 言語自動検出
  - セグメント化

#### **Day 4-5: 翻訳システム実装**
- [ ] `app/core/translator.py`
  - TranslationManagerクラス
  - 5段階フォールバック実装
    1. DeepL API
    2. Groq API
    3. Gemini API
    4. OpenAI API
    5. Argos Translate
  - 翻訳キャッシュ

#### **Day 6-7: テスト・デバッグ**
- [ ] 各翻訳APIのテスト
- [ ] エラーハンドリング確認
- [ ] パフォーマンス測定

---

### **Week 5: TTS統合**

#### **Day 1-2: TTSManager実装**
- [ ] `app/core/tts_manager.py`
  - TTSManagerクラス
  - エンジン切替機能
  - synthesize()
  - list_voices()

#### **Day 3: edge_tts実装**
- [ ] `app/tts/edge_tts_engine.py`
  - EdgeTTSEngineクラス
  - 話者一覧取得
  - 音声合成
  - パラメータ調整

#### **Day 4: VOICEVOX実装**
- [ ] `app/tts/voicevox_engine.py`
  - VoicevoxEngineクラス
  - 接続確認
  - 話者一覧取得
  - 音声合成
  - 感情対応

#### **Day 5: Google TTS実装**
- [ ] `app/tts/google_tts_engine.py`
  - GoogleTTSEngineクラス
  - APIキー管理
  - 音声合成

#### **Day 6: pyttsx3実装**
- [ ] `app/tts/pyttsx3_engine.py`
  - Pyttsx3Engineクラス
  - オフライン音声合成
  - システム音声使用

#### **Day 7: 統合テスト**
- [ ] 全TTSエンジンのテスト
- [ ] フォールバック動作確認

---

### **Week 6: 吹き替えUI実装**

#### **Day 1-3: DubbingTab実装**
- [ ] `app/ui/tabs/dubbing_tab.py`
  - URL/ファイル入力
  - TTS エンジン選択UI
  - 話者選択
  - パラメータスライダー
  - 翻訳API選択
  - 処理開始ボタン

#### **Day 4-5: TTS設定ウィジェット**
- [ ] `app/ui/widgets/tts_selector.py`
  - TTSエンジン切替
  - 話者ドロップダウン
  - パラメータスライダー
  - プレビュー機能

#### **Day 6-7: 統合・テスト**
- [ ] 吹き替え処理の統合テスト
- [ ] エラーケーステスト
- [ ] パフォーマンス最適化

**Phase 2 マイルストーン**:
- ✅ Whisper文字起こし機能完成
- ✅ 5段階翻訳システム完成
- ✅ 複数TTS対応完成
- ✅ 吹き替え機能完成

---

## 🔗 Phase 3: 連結機能実装（Week 7-8）

### **Week 7: 動画・音声連結**

#### **Day 1-3: VideoMerger実装**
- [ ] `app/core/video_merger.py`
  - VideoMergerクラス
  - merge_videos()
  - 解像度統一処理
  - トランジション効果（オプション）
  - プログレス通知

#### **Day 4-5: AudioMerger実装**
- [ ] `app/core/audio_merger.py`
  - AudioMergerクラス
  - merge_audios()
  - 音量正規化
  - メタデータ統合

#### **Day 6-7: テスト**
- [ ] 動画連結テスト
- [ ] 音声連結テスト
- [ ] 大量ファイルテスト

---

### **Week 8: 連結UI実装**

#### **Day 1-3: MergeTab実装**
- [ ] `app/ui/tabs/merge_tab.py`
  - ファイルリスト表示
  - ドラッグ&ドロップ
  - 順序変更ボタン
  - 設定UI
  - 連結ボタン

#### **Day 4-5: ファイルリストウィジェット**
- [ ] `app/ui/widgets/file_list_widget.py`
  - サムネイル表示
  - 順序変更機能
  - ファイル削除
  - 情報表示

#### **Day 6-7: キュー管理実装**
- [ ] `app/core/queue_manager.py`
  - QueueManagerクラス
  - タスク追加/削除
  - 優先度変更
  - 一時停止/再開
- [ ] `app/ui/widgets/queue_widget.py`
  - キュー表示ウィジェット
  - 操作ボタン

**Phase 3 マイルストーン**:
- ✅ 動画連結機能完成
- ✅ 音声連結機能完成
- ✅ ドラッグ&ドロップUI完成
- ✅ キュー管理機能完成

---

## 🎨 Phase 4: UI/UX改善（Week 9）

### **Week 9: デザイン・アニメーション**

#### **Day 1-2: テーマ実装**
- [ ] ダークモード実装
- [ ] ライトモード実装
- [ ] OS設定自動追従
- [ ] カラーパレット調整

#### **Day 3-4: アニメーション追加**
- [ ] ページ遷移アニメーション
- [ ] プログレスアニメーション
- [ ] ボタンホバーエフェクト
- [ ] カード展開アニメーション

#### **Day 5: アイコン・画像**
- [ ] アイコンセット作成
- [ ] サムネイル表示改善
- [ ] スプラッシュスクリーン

#### **Day 6-7: 設定ダイアログ**
- [ ] `app/ui/dialogs/settings_dialog.py`
  - API キー設定
  - 一般設定
  - テーマ設定
  - 詳細設定

**Phase 4 マイルストーン**:
- ✅ モダンなUI完成
- ✅ アニメーション実装
- ✅ テーマ切替完成
- ✅ 設定画面完成

---

## 📦 Phase 5: 配布準備（Week 10）

### **Week 10: ビルド・テスト**

#### **Day 1-2: PyInstallerセットアップ**
- [ ] `build_exe.spec` 作成
- [ ] FFmpeg同梱設定
- [ ] アイコン設定
- [ ] onefolder形式ビルド

#### **Day 3-4: 総合テスト**
- [ ] 全機能の動作確認
- [ ] エラーケーステスト
- [ ] パフォーマンステスト
- [ ] 長時間動画テスト

#### **Day 5: ドキュメント整備**
- [ ] README.md更新
- [ ] ユーザーガイド作成
- [ ] トラブルシューティングガイド
- [ ] CHANGELOG.md作成

#### **Day 6: 配布パッケージ作成**
- [ ] EXEビルド
- [ ] ZIP圧縮
- [ ] インストーラー作成（オプション）
- [ ] バージョン情報埋め込み

#### **Day 7: リリース準備**
- [ ] GitHub Release作成
- [ ] リリースノート作成
- [ ] ダウンロードリンク準備

**Phase 5 マイルストーン**:
- ✅ 配布用EXE完成
- ✅ ドキュメント完成
- ✅ v1.0.0リリース

---

## 🚀 今後の計画（Post v1.0）

### **v1.1 計画**
- [ ] 字幕ファイル生成機能
- [ ] 動画トランジション効果拡充
- [ ] バッチ処理UI改善
- [ ] 処理履歴エクスポート

### **v1.2 計画**
- [ ] 動画編集機能（トリミング等）
- [ ] 音声エフェクト追加
- [ ] プラグインシステム
- [ ] 多言語UI対応

### **v2.0 計画（Nuitka移行）**
- [ ] Nuitkaビルド
- [ ] 実行速度向上
- [ ] ファイルサイズ削減
- [ ] 配布形式改善

---

## 📊 進捗管理

### **チェックリスト**

#### **Phase 1: コア機能** (0/21)
- [ ] データモデル実装
- [ ] YouTubeDownloader実装
- [ ] AudioExtractor実装
- [ ] データベース実装
- [ ] Logger実装
- [ ] ConfigManager実装
- [ ] MainWindow実装
- [ ] DownloadTab実装
- [ ] AudioExtractTab実装
- ...

#### **Phase 2: 音声処理** (0/15)
- [ ] WhisperTranscriber実装
- [ ] TranslationManager実装
- [ ] TTSManager実装
- [ ] EdgeTTSEngine実装
- [ ] VoicevoxEngine実装
- ...

#### **Phase 3: 連結機能** (0/10)
- [ ] VideoMerger実装
- [ ] AudioMerger実装
- [ ] QueueManager実装
- [ ] MergeTab実装
- ...

#### **Phase 4: UI/UX** (0/8)
- [ ] テーマ実装
- [ ] アニメーション実装
- [ ] 設定ダイアログ実装
- ...

#### **Phase 5: 配布** (0/7)
- [ ] PyInstallerセットアップ
- [ ] 総合テスト
- [ ] ドキュメント整備
- ...

---

## 📞 サポート・相談

開発中に質問や相談がある場合:
- **ドキュメント**: `docs/CLAUDE.md`
- **Issues**: GitHub Issues
- **Discussion**: GitHub Discussions

---

**一緒に素晴らしいアプリを作りましょう！** 🎉

---

**作成日**: 2025-01-20  
**最終更新**: 2025-01-20
