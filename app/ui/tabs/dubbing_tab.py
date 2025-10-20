"""
吹き替えタブ

このモジュールは、YouTube動画の音声吹き替え機能のUIを提供します。
音声抽出 → 文字起こし → 翻訳 → TTS合成 の一連の処理を行います。
"""

import asyncio
from typing import Optional
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog
)
from PySide6.QtCore import Qt, QThread, Signal, QObject, Slot
from qfluentwidgets import (
    LineEdit,
    PushButton,
    ProgressBar,
    CardWidget,
    ComboBox,
    BodyLabel,
    StrongBodyLabel,
    PrimaryPushButton,
    FluentIcon,
    TextEdit
)
from loguru import logger

from app.core.audio_extractor import AudioExtractor
from app.core.transcriber import WhisperTranscriber
from app.core.translator import TranslationManager
from app.core.tts_manager import TTSManager, TTSConfig


class DubbingWorker(QObject):
    """吹き替え処理ワーカー"""
    finished = Signal(str)  # 出力ファイルパス
    error = Signal(str)
    progress = Signal(int, str)  # 進捗%, ステータスメッセージ

    def __init__(self):
        super().__init__()
        self.audio_extractor = AudioExtractor()
        self.transcriber = WhisperTranscriber(model_size="base")
        self.translator = TranslationManager()
        self.tts_manager = TTSManager()
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    def process_dubbing(
        self,
        video_path: str,
        target_lang: str,
        tts_engine: str,
        voice: Optional[str]
    ):
        """吹き替え処理"""
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            # 1. 音声抽出
            self.progress.emit(10, "音声を抽出中...")
            audio_path = self.loop.run_until_complete(
                self.audio_extractor.extract_audio(video_path)
            )
            logger.info(f"Audio extracted: {audio_path}")

            # 2. 文字起こし
            self.progress.emit(30, "音声を文字起こし中...")
            transcription = self.loop.run_until_complete(
                self.transcriber.transcribe(audio_path)
            )
            logger.info(f"Transcription completed: {len(transcription.text)} chars")

            # 3. 翻訳
            self.progress.emit(60, "テキストを翻訳中...")
            translation = self.loop.run_until_complete(
                self.translator.translate(
                    transcription.text,
                    source_lang=transcription.language,
                    target_lang=target_lang
                )
            )
            logger.info(f"Translation completed: {translation.engine}")

            # 4. TTS合成
            self.progress.emit(80, "音声を合成中...")
            config = TTSConfig(voice=voice)
            tts_result = self.loop.run_until_complete(
                self.tts_manager.synthesize(
                    text=translation.translated_text,
                    engine=tts_engine,
                    config=config,
                    output_name=f"dubbed_{Path(video_path).stem}.mp3"
                )
            )
            logger.info(f"TTS synthesis completed: {tts_result.audio_path}")

            self.progress.emit(100, "完了！")
            self.finished.emit(tts_result.audio_path)

        except Exception as e:
            logger.error(f"Dubbing failed: {e}")
            self.error.emit(f"吹き替え処理エラー: {str(e)}")

        finally:
            if self.loop:
                self.loop.close()


class DubbingTab(QWidget):
    """
    吹き替えタブ

    YouTube動画の音声吹き替え機能を提供するUIタブです。

    Features:
        - 動画ファイル選択
        - 翻訳先言語選択
        - TTSエンジン・話者選択
        - 吹き替え音声生成
    """

    def __init__(self, parent=None):
        """
        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)

        self.worker_thread: Optional[QThread] = None
        self.worker: Optional[DubbingWorker] = None
        self.selected_video_path: Optional[str] = None

        self.setup_ui()

        logger.info("DubbingTab initialized")

    def setup_ui(self) -> None:
        """UIをセットアップ"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # タイトル
        title_label = StrongBodyLabel("音声吹き替え")
        title_label.setStyleSheet("font-size: 24px;")
        layout.addWidget(title_label)

        # 説明
        desc_label = BodyLabel(
            "動画ファイルから音声を抽出し、文字起こし → 翻訳 → TTS合成で吹き替え音声を生成します"
        )
        layout.addWidget(desc_label)

        # 動画ファイル選択
        layout.addWidget(self.create_file_section())

        # 吹き替え設定
        layout.addWidget(self.create_settings_section())

        # プログレスバー
        self.progress_bar = ProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # ステータスラベル
        self.status_label = BodyLabel("")
        self.status_label.hide()
        layout.addWidget(self.status_label)

        # 実行ボタン
        self.execute_btn = PrimaryPushButton(FluentIcon.PLAY, "吹き替え開始")
        self.execute_btn.clicked.connect(self.on_execute_clicked)
        self.execute_btn.setEnabled(False)
        layout.addWidget(self.execute_btn)

        # 結果表示エリア
        result_label = StrongBodyLabel("処理結果")
        layout.addWidget(result_label)

        self.result_text = TextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText("処理結果がここに表示されます...")
        layout.addWidget(self.result_text)

        # ストレッチ
        layout.addStretch()

        logger.debug("DubbingTab UI setup completed")

    def create_file_section(self) -> QWidget:
        """ファイル選択セクションを作成"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # ファイルパス表示
        self.file_path_input = LineEdit()
        self.file_path_input.setPlaceholderText("動画ファイルを選択してください...")
        self.file_path_input.setReadOnly(True)
        layout.addWidget(self.file_path_input, stretch=1)

        # ファイル選択ボタン
        self.browse_btn = PushButton(FluentIcon.FOLDER, "参照")
        self.browse_btn.clicked.connect(self.on_browse_clicked)
        layout.addWidget(self.browse_btn)

        return widget

    def create_settings_section(self) -> QWidget:
        """吹き替え設定セクションを作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 翻訳先言語
        lang_layout = QHBoxLayout()
        lang_label = BodyLabel("翻訳先言語:")
        lang_layout.addWidget(lang_label)

        self.lang_combo = ComboBox()
        self.lang_combo.addItems(["日本語 (ja)", "英語 (en)", "中国語 (zh)", "韓国語 (ko)"])
        self.lang_combo.setCurrentIndex(0)
        lang_layout.addWidget(self.lang_combo)
        lang_layout.addStretch()

        layout.addLayout(lang_layout)

        # TTSエンジン
        tts_layout = QHBoxLayout()
        tts_label = BodyLabel("TTSエンジン:")
        tts_layout.addWidget(tts_label)

        self.tts_combo = ComboBox()
        self.tts_combo.addItems(["Edge TTS", "VOICEVOX"])
        self.tts_combo.setCurrentIndex(0)  # Edge TTSをデフォルトに
        self.tts_combo.currentTextChanged.connect(self.on_tts_engine_changed)
        tts_layout.addWidget(self.tts_combo)

        # VOICEVOX警告ラベル
        self.voicevox_warning = BodyLabel("")
        self.voicevox_warning.setStyleSheet("color: orange;")
        self.voicevox_warning.hide()
        tts_layout.addWidget(self.voicevox_warning)
        tts_layout.addStretch()

        layout.addLayout(tts_layout)

        # 話者選択
        voice_layout = QHBoxLayout()
        voice_label = BodyLabel("話者:")
        voice_layout.addWidget(voice_label)

        self.voice_combo = ComboBox()
        self.update_voice_list()
        voice_layout.addWidget(self.voice_combo)
        voice_layout.addStretch()

        layout.addLayout(voice_layout)

        return widget

    def on_browse_clicked(self) -> None:
        """ファイル参照ボタンクリック"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "動画ファイルを選択",
            "",
            "動画ファイル (*.mp4 *.avi *.mkv *.mov);;すべてのファイル (*)"
        )

        if file_path:
            self.selected_video_path = file_path
            self.file_path_input.setText(file_path)
            self.execute_btn.setEnabled(True)
            logger.info(f"Video file selected: {file_path}")

    def on_tts_engine_changed(self, engine_name: str) -> None:
        """TTSエンジン変更"""
        if engine_name == "VOICEVOX":
            self.voicevox_warning.setText(
                "⚠️ VOICEVOX ENGINEが起動していない、または動作が遅い場合があります。"
                "Edge TTSの使用をお勧めします。"
            )
            self.voicevox_warning.show()
        else:
            self.voicevox_warning.hide()

        self.update_voice_list()

    def update_voice_list(self) -> None:
        """話者リストを更新"""
        self.voice_combo.clear()

        engine_name = self.tts_combo.currentText()

        if engine_name == "Edge TTS":
            voices = [
                "ja-JP-NanamiNeural (女性)",
                "ja-JP-KeitaNeural (男性)",
                "ja-JP-AoiNeural (女性)",
                "ja-JP-DaichiNeural (男性)",
                "ja-JP-MayuNeural (女性)",
                "ja-JP-NaokiNeural (男性)",
                "ja-JP-ShioriNeural (女性)"
            ]
            self.voice_combo.addItems(voices)
        else:  # VOICEVOX
            # VOICEVOXの話者を動的に取得
            self.voice_combo.addItem("読み込み中...")
            self.voice_combo.setEnabled(False)
            # 非同期で話者リストを取得
            self._load_voicevox_speakers()

    def on_execute_clicked(self) -> None:
        """吹き替え開始ボタンクリック"""
        if not self.selected_video_path:
            self.show_error("動画ファイルを選択してください")
            return

        # 設定を取得
        lang_text = self.lang_combo.currentText()
        target_lang = lang_text.split("(")[1].rstrip(")")

        tts_engine = "edge_tts" if self.tts_combo.currentText() == "Edge TTS" else "voicevox"

        voice_text = self.voice_combo.currentText()

        # VOICEVOX話者が読み込み中かチェック
        if tts_engine == "voicevox" and (voice_text == "読み込み中..." or not self.voice_combo.isEnabled()):
            self.show_error("VOICEVOX話者の読み込みが完了していません。しばらくお待ちください。")
            return

        if tts_engine == "edge_tts":
            voice = voice_text.split(" ")[0]
        else:
            voice = voice_text.split(" ")[0]

        logger.info(
            f"Starting dubbing: video={self.selected_video_path}, "
            f"lang={target_lang}, tts={tts_engine}, voice={voice}, "
            f"voice_text={voice_text}"
        )

        # UIを更新
        self.execute_btn.setEnabled(False)
        self.execute_btn.setText("処理中...")
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.status_label.show()
        self.result_text.clear()

        # ワーカースレッドで実行
        self.start_worker_thread()
        self.worker.process_dubbing(
            self.selected_video_path,
            target_lang,
            tts_engine,
            voice
        )

    def start_worker_thread(self) -> None:
        """ワーカースレッドを開始"""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait()

        self.worker_thread = QThread()
        self.worker = DubbingWorker()
        self.worker.moveToThread(self.worker_thread)

        # シグナル接続
        self.worker.progress.connect(self.on_progress_updated)
        self.worker.finished.connect(self.on_dubbing_finished)
        self.worker.error.connect(self.on_error)

        self.worker_thread.start()

    def on_progress_updated(self, percent: int, message: str) -> None:
        """進捗更新"""
        self.progress_bar.setValue(percent)
        self.status_label.setText(message)

    def on_dubbing_finished(self, output_path: str) -> None:
        """吹き替え完了"""
        self.result_text.setPlainText(
            f"✅ 吹き替え音声が生成されました！\n\n"
            f"出力ファイル:\n{output_path}\n\n"
            f"この音声ファイルを動画に合成する場合は、\n"
            f"動画編集ソフトをご使用ください。"
        )

        self.execute_btn.setEnabled(True)
        self.execute_btn.setText("吹き替え開始")

        self.show_success("吹き替え音声の生成が完了しました")

        logger.info(f"Dubbing completed: {output_path}")

    def on_error(self, error_message: str) -> None:
        """エラー発生"""
        self.result_text.setPlainText(f"❌ エラー:\n{error_message}")

        self.execute_btn.setEnabled(True)
        self.execute_btn.setText("吹き替え開始")
        self.progress_bar.setValue(0)

        self.show_error(error_message)

    def show_success(self, message: str) -> None:
        """成功メッセージ表示"""
        if hasattr(self.parent(), 'show_success_message'):
            self.parent().show_success_message("成功", message)

    def show_error(self, message: str) -> None:
        """エラーメッセージ表示"""
        if hasattr(self.parent(), 'show_error_message'):
            self.parent().show_error_message("エラー", message)
        logger.error(message)

    def _load_voicevox_speakers(self) -> None:
        """VOICEVOXの話者リストを非同期で取得"""
        import threading

        def fetch_speakers():
            # まずデフォルトリストをすぐに表示
            default_voices = [
                "1 - 四国めたん (ノーマル)",
                "2 - 四国めたん (あまあま)",
                "3 - 四国めたん (ツンツン)",
                "8 - ずんだもん (ノーマル)",
                "10 - ずんだもん (あまあま)",
                "11 - ずんだもん (ツンツン)",
                "13 - 春日部つむぎ (ノーマル)",
                "14 - 雨晴はう (ノーマル)",
                "16 - 波音リツ (ノーマル)"
            ]

            from PySide6.QtCore import QMetaObject, Qt
            self._voicevox_speakers_loaded = default_voices
            QMetaObject.invokeMethod(
                self,
                "_update_voicevox_voices",
                Qt.ConnectionType.QueuedConnection
            )

            logger.info(f"Loaded {len(default_voices)} default VOICEVOX speakers")

            # バックグラウンドで実際の話者リストを取得（タイムアウト付き）
            try:
                from app.tts.voicevox_engine import VoicevoxEngine
                import asyncio

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    # VOICEVOXエンジンを初期化（タイムアウト30秒）
                    engine = VoicevoxEngine(timeout=30)

                    # 話者リストを取得（タイムアウト付き）
                    async def fetch_with_timeout():
                        try:
                            speakers = await asyncio.wait_for(
                                engine.get_speakers(),
                                timeout=15.0  # 15秒でタイムアウト
                            )
                            return speakers
                        except asyncio.TimeoutError:
                            logger.warning("話者リスト取得がタイムアウトしました（デフォルトを使用）")
                            return []

                    speakers = loop.run_until_complete(fetch_with_timeout())

                    if speakers and len(speakers) > 0:
                        # 成功した場合のみUIを更新
                        voices = []
                        for speaker in speakers:
                            speaker_name = speaker.get("name", "Unknown")
                            for style in speaker.get("styles", []):
                                style_name = style.get("name", "")
                                style_id = style.get("id")
                                if style_name:
                                    voices.append(f"{style_id} - {speaker_name} ({style_name})")
                                else:
                                    voices.append(f"{style_id} - {speaker_name}")

                        self._voicevox_speakers_loaded = voices
                        QMetaObject.invokeMethod(
                            self,
                            "_update_voicevox_voices",
                            Qt.ConnectionType.QueuedConnection
                        )

                        logger.info(f"Updated with {len(voices)} actual VOICEVOX speakers")

                    # セッションをクローズ
                    loop.run_until_complete(engine.close())

                finally:
                    if loop and not loop.is_closed():
                        loop.close()

            except Exception as e:
                logger.warning(f"Could not fetch actual speakers (using defaults): {e}")

        # バックグラウンドスレッドで実行
        thread = threading.Thread(target=fetch_speakers, daemon=True)
        thread.start()

    @Slot()
    def _update_voicevox_voices(self) -> None:
        """VOICEVOX話者リストをUIに反映（メインスレッドで実行）"""
        # インスタンス変数から話者リストを取得
        voices = getattr(self, '_voicevox_speakers_loaded', [])

        if not voices:
            # フォールバック
            voices = [
                "1 - 四国めたん (ノーマル)",
                "8 - ずんだもん (ノーマル)",
                "13 - 春日部つむぎ (ノーマル)",
                "14 - 雨晴はう (ノーマル)",
                "16 - 波音リツ (ノーマル)"
            ]

        self.voice_combo.clear()
        self.voice_combo.addItems(voices)
        self.voice_combo.setEnabled(True)
        logger.debug(f"Updated voice combo with {len(voices)} voices")
