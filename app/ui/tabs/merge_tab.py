"""
連結タブ

このモジュールは、動画・音声ファイルの連結機能のUIを提供します。
"""

import asyncio
from typing import Optional, List
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
    QListWidget,
    QListWidgetItem
)
from PySide6.QtCore import Qt, QThread, Signal, QObject
from qfluentwidgets import (
    LineEdit,
    PushButton,
    ProgressBar,
    ComboBox,
    BodyLabel,
    StrongBodyLabel,
    PrimaryPushButton,
    FluentIcon,
    SwitchButton
)
from loguru import logger

from app.core.video_merger import VideoMerger
from app.core.audio_merger import AudioMerger


class MergeWorker(QObject):
    """連結処理ワーカー"""
    finished = Signal(str)  # 出力ファイルパス
    error = Signal(str)
    progress = Signal(int)  # 進捗%

    def __init__(self):
        super().__init__()
        self.video_merger = VideoMerger()
        self.audio_merger = AudioMerger()
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    def merge_videos(
        self,
        video_paths: List[str],
        output_name: str,
        method: str
    ):
        """動画連結"""
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            self.progress.emit(50)

            result = self.loop.run_until_complete(
                self.video_merger.merge_videos(
                    video_paths,
                    output_name,
                    method
                )
            )

            self.progress.emit(100)
            self.finished.emit(result.output_path)

        except Exception as e:
            logger.error(f"Video merge failed: {e}")
            self.error.emit(f"動画連結エラー: {str(e)}")

        finally:
            if self.loop:
                self.loop.close()

    def merge_audios(
        self,
        audio_paths: List[str],
        output_name: str,
        format: str,
        bitrate: str
    ):
        """音声連結"""
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            self.progress.emit(50)

            result = self.loop.run_until_complete(
                self.audio_merger.merge_audios(
                    audio_paths,
                    output_name,
                    format,
                    bitrate
                )
            )

            self.progress.emit(100)
            self.finished.emit(result.output_path)

        except Exception as e:
            logger.error(f"Audio merge failed: {e}")
            self.error.emit(f"音声連結エラー: {str(e)}")

        finally:
            if self.loop:
                self.loop.close()


class MergeTab(QWidget):
    """
    連結タブ

    動画・音声ファイルの連結機能を提供するUIタブです。

    Features:
        - 動画/音声の切り替え
        - 複数ファイル選択
        - ファイル順序変更
        - 連結実行
    """

    def __init__(self, parent=None):
        """
        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)

        self.worker_thread: Optional[QThread] = None
        self.worker: Optional[MergeWorker] = None
        self.file_paths: List[str] = []

        self.setup_ui()

        logger.info("MergeTab initialized")

    def setup_ui(self) -> None:
        """UIをセットアップ"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # タイトル
        title_label = StrongBodyLabel("ファイル連結")
        title_label.setStyleSheet("font-size: 24px;")
        layout.addWidget(title_label)

        # モード切替
        layout.addWidget(self.create_mode_section())

        # ファイルリスト
        list_label = StrongBodyLabel("連結するファイル")
        layout.addWidget(list_label)

        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(200)
        layout.addWidget(self.file_list)

        # ファイル操作ボタン
        layout.addWidget(self.create_file_controls())

        # 出力設定
        layout.addWidget(self.create_output_settings())

        # プログレスバー
        self.progress_bar = ProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # 実行ボタン
        self.execute_btn = PrimaryPushButton(FluentIcon.SYNC, "連結開始")
        self.execute_btn.clicked.connect(self.on_execute_clicked)
        self.execute_btn.setEnabled(False)
        layout.addWidget(self.execute_btn)

        # ストレッチ
        layout.addStretch()

        logger.debug("MergeTab UI setup completed")

    def create_mode_section(self) -> QWidget:
        """モード切替セクションを作成"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        mode_label = BodyLabel("連結モード:")
        layout.addWidget(mode_label)

        self.mode_combo = ComboBox()
        self.mode_combo.addItems(["動画連結", "音声連結"])
        self.mode_combo.setCurrentIndex(0)
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        layout.addWidget(self.mode_combo)

        layout.addStretch()

        return widget

    def create_file_controls(self) -> QWidget:
        """ファイル操作ボタンを作成"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # ファイル追加
        self.add_btn = PushButton(FluentIcon.ADD, "ファイル追加")
        self.add_btn.clicked.connect(self.on_add_files_clicked)
        layout.addWidget(self.add_btn)

        # 選択削除
        self.remove_btn = PushButton(FluentIcon.DELETE, "選択削除")
        self.remove_btn.clicked.connect(self.on_remove_clicked)
        layout.addWidget(self.remove_btn)

        # 上に移動
        self.up_btn = PushButton(FluentIcon.UP, "上へ")
        self.up_btn.clicked.connect(self.on_move_up_clicked)
        layout.addWidget(self.up_btn)

        # 下に移動
        self.down_btn = PushButton(FluentIcon.DOWN, "下へ")
        self.down_btn.clicked.connect(self.on_move_down_clicked)
        layout.addWidget(self.down_btn)

        # クリア
        self.clear_btn = PushButton(FluentIcon.CANCEL, "全クリア")
        self.clear_btn.clicked.connect(self.on_clear_clicked)
        layout.addWidget(self.clear_btn)

        layout.addStretch()

        return widget

    def create_output_settings(self) -> QWidget:
        """出力設定セクションを作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 出力ファイル名
        name_layout = QHBoxLayout()
        name_label = BodyLabel("出力ファイル名:")
        name_layout.addWidget(name_label)

        self.output_name_input = LineEdit()
        self.output_name_input.setPlaceholderText("merged")
        name_layout.addWidget(self.output_name_input)

        layout.addLayout(name_layout)

        # 動画連結設定
        self.video_settings = QWidget()
        video_layout = QHBoxLayout(self.video_settings)
        video_layout.setContentsMargins(0, 0, 0, 0)

        method_label = BodyLabel("連結方法:")
        video_layout.addWidget(method_label)

        self.method_combo = ComboBox()
        self.method_combo.addItems(["高速 (concat)", "高品質 (filter)"])
        self.method_combo.setCurrentIndex(0)
        video_layout.addWidget(self.method_combo)
        video_layout.addStretch()

        layout.addWidget(self.video_settings)

        # 音声連結設定
        self.audio_settings = QWidget()
        audio_layout = QHBoxLayout(self.audio_settings)
        audio_layout.setContentsMargins(0, 0, 0, 0)

        format_label = BodyLabel("出力形式:")
        audio_layout.addWidget(format_label)

        self.format_combo = ComboBox()
        self.format_combo.addItems(["MP3", "WAV", "AAC"])
        self.format_combo.setCurrentIndex(0)
        audio_layout.addWidget(self.format_combo)

        bitrate_label = BodyLabel("ビットレート:")
        audio_layout.addWidget(bitrate_label)

        self.bitrate_combo = ComboBox()
        self.bitrate_combo.addItems(["128k", "192k", "256k", "320k"])
        self.bitrate_combo.setCurrentIndex(1)
        audio_layout.addWidget(self.bitrate_combo)
        audio_layout.addStretch()

        layout.addWidget(self.audio_settings)
        self.audio_settings.hide()

        return widget

    def on_mode_changed(self, mode: str) -> None:
        """モード変更"""
        if mode == "動画連結":
            self.video_settings.show()
            self.audio_settings.hide()
        else:
            self.video_settings.hide()
            self.audio_settings.show()

        # リストをクリア
        self.file_list.clear()
        self.file_paths.clear()
        self.execute_btn.setEnabled(False)

    def on_add_files_clicked(self) -> None:
        """ファイル追加ボタンクリック"""
        mode = self.mode_combo.currentText()

        if mode == "動画連結":
            file_filter = "動画ファイル (*.mp4 *.avi *.mkv *.mov);;すべてのファイル (*)"
        else:
            file_filter = "音声ファイル (*.mp3 *.wav *.aac *.m4a);;すべてのファイル (*)"

        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "ファイルを選択",
            "",
            file_filter
        )

        if file_paths:
            for path in file_paths:
                self.file_paths.append(path)
                self.file_list.addItem(Path(path).name)

            self.update_execute_button()
            logger.info(f"Added {len(file_paths)} files")

    def on_remove_clicked(self) -> None:
        """選択削除ボタンクリック"""
        current_row = self.file_list.currentRow()
        if current_row >= 0:
            self.file_list.takeItem(current_row)
            self.file_paths.pop(current_row)
            self.update_execute_button()

    def on_move_up_clicked(self) -> None:
        """上へ移動ボタンクリック"""
        current_row = self.file_list.currentRow()
        if current_row > 0:
            # リストを入れ替え
            self.file_paths[current_row], self.file_paths[current_row - 1] = \
                self.file_paths[current_row - 1], self.file_paths[current_row]

            # UIを更新
            item = self.file_list.takeItem(current_row)
            self.file_list.insertItem(current_row - 1, item)
            self.file_list.setCurrentRow(current_row - 1)

    def on_move_down_clicked(self) -> None:
        """下へ移動ボタンクリック"""
        current_row = self.file_list.currentRow()
        if 0 <= current_row < len(self.file_paths) - 1:
            # リストを入れ替え
            self.file_paths[current_row], self.file_paths[current_row + 1] = \
                self.file_paths[current_row + 1], self.file_paths[current_row]

            # UIを更新
            item = self.file_list.takeItem(current_row)
            self.file_list.insertItem(current_row + 1, item)
            self.file_list.setCurrentRow(current_row + 1)

    def on_clear_clicked(self) -> None:
        """全クリアボタンクリック"""
        self.file_list.clear()
        self.file_paths.clear()
        self.execute_btn.setEnabled(False)

    def update_execute_button(self) -> None:
        """実行ボタンの有効/無効を更新"""
        self.execute_btn.setEnabled(len(self.file_paths) >= 2)

    def on_execute_clicked(self) -> None:
        """連結開始ボタンクリック"""
        if len(self.file_paths) < 2:
            self.show_error("2つ以上のファイルを選択してください")
            return

        mode = self.mode_combo.currentText()
        output_name = self.output_name_input.text().strip()

        if not output_name:
            output_name = "merged"

        if mode == "動画連結":
            if not output_name.endswith(".mp4"):
                output_name += ".mp4"

            method = "concat" if "高速" in self.method_combo.currentText() else "filter"

            logger.info(
                f"Starting video merge: {len(self.file_paths)} files, "
                f"method={method}"
            )

            # UIを更新
            self.execute_btn.setEnabled(False)
            self.execute_btn.setText("連結中...")
            self.progress_bar.setValue(0)
            self.progress_bar.show()

            # ワーカースレッドで実行
            self.start_worker_thread()
            self.worker.merge_videos(self.file_paths, output_name, method)

        else:  # 音声連結
            format = self.format_combo.currentText().lower()
            if not output_name.endswith(f".{format}"):
                output_name += f".{format}"

            bitrate = self.bitrate_combo.currentText()

            logger.info(
                f"Starting audio merge: {len(self.file_paths)} files, "
                f"format={format}, bitrate={bitrate}"
            )

            # UIを更新
            self.execute_btn.setEnabled(False)
            self.execute_btn.setText("連結中...")
            self.progress_bar.setValue(0)
            self.progress_bar.show()

            # ワーカースレッドで実行
            self.start_worker_thread()
            self.worker.merge_audios(self.file_paths, output_name, format, bitrate)

    def start_worker_thread(self) -> None:
        """ワーカースレッドを開始"""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait()

        self.worker_thread = QThread()
        self.worker = MergeWorker()
        self.worker.moveToThread(self.worker_thread)

        # シグナル接続
        self.worker.progress.connect(self.on_progress_updated)
        self.worker.finished.connect(self.on_merge_finished)
        self.worker.error.connect(self.on_error)

        self.worker_thread.start()

    def on_progress_updated(self, percent: int) -> None:
        """進捗更新"""
        self.progress_bar.setValue(percent)

    def on_merge_finished(self, output_path: str) -> None:
        """連結完了"""
        self.execute_btn.setEnabled(True)
        self.execute_btn.setText("連結開始")
        self.progress_bar.setValue(100)

        self.show_success(f"ファイルの連結が完了しました\n出力: {output_path}")

        logger.info(f"Merge completed: {output_path}")

    def on_error(self, error_message: str) -> None:
        """エラー発生"""
        self.execute_btn.setEnabled(True)
        self.execute_btn.setText("連結開始")
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
