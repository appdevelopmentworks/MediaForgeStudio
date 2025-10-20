"""
ダウンロードタブ

このモジュールは、YouTube動画ダウンロード機能のUIを提供します。
"""

import asyncio
from typing import Optional
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame
)
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QPixmap
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
    ImageLabel,
    CheckBox
)
from loguru import logger
import aiohttp

from app.core.downloader import YouTubeDownloader, InvalidURLError, DownloadError
from app.models.download_item import VideoInfo, DownloadResult, DownloadProgress


class DownloadWorker(QObject):
    """
    ダウンロード用ワーカー（非同期処理をQtのシグナル/スロットで扱う）
    """
    finished = Signal(object)  # DownloadResult
    error = Signal(str)
    progress = Signal(object)  # DownloadProgress
    info_fetched = Signal(object)  # VideoInfo

    def __init__(self, downloader: YouTubeDownloader):
        super().__init__()
        self.downloader = downloader

    def fetch_info(self, url: str):
        """動画情報取得"""
        loop = None
        try:
            # 新しいイベントループを作成
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # 動画情報を取得
            video_info = loop.run_until_complete(
                self.downloader.get_video_info(url)
            )

            # シグナルを発行
            self.info_fetched.emit(video_info)
            logger.info(f"Info fetch completed for: {url}")

        except InvalidURLError as e:
            logger.error(f"Invalid URL: {e}")
            self.error.emit(str(e))

        except Exception as e:
            logger.error(f"Failed to fetch info: {e}", exc_info=True)
            self.error.emit(f"エラー: {str(e)}")

        finally:
            # イベントループをクリーンアップ
            self._cleanup_event_loop(loop)

    def download_video(self, url: str, resolution: str, include_audio: bool = True):
        """動画ダウンロード"""
        loop = None
        try:
            # 新しいイベントループを作成
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # 進捗コールバック
            def on_progress(progress: DownloadProgress):
                try:
                    self.progress.emit(progress)
                except RuntimeError as e:
                    # UIが破棄されている場合は無視
                    logger.debug(f"Progress emit failed (UI destroyed?): {e}")
                except Exception as e:
                    logger.warning(f"Progress emit error: {e}")

            # ダウンロード実行
            result = loop.run_until_complete(
                self.downloader.download_video(
                    url, resolution, include_audio, on_progress
                )
            )

            # 結果を発行
            self.finished.emit(result)
            logger.info(f"Download completed for: {url}")

        except Exception as e:
            logger.error(f"Download failed: {e}", exc_info=True)
            self.error.emit(f"ダウンロードエラー: {str(e)}")

        finally:
            # イベントループをクリーンアップ
            self._cleanup_event_loop(loop)

    def _cleanup_event_loop(self, loop: Optional[asyncio.AbstractEventLoop]) -> None:
        """
        イベントループを安全にクリーンアップ

        Args:
            loop: クリーンアップするイベントループ
        """
        if not loop:
            return

        try:
            # まだクローズされていない場合
            if not loop.is_closed():
                # 実行中のタスクを全て取得
                try:
                    pending = asyncio.all_tasks(loop)
                except RuntimeError:
                    # ループが既に停止している場合
                    pending = set()

                # タスクをキャンセル
                for task in pending:
                    task.cancel()

                # キャンセルされたタスクを処理
                if pending:
                    try:
                        loop.run_until_complete(
                            asyncio.gather(*pending, return_exceptions=True)
                        )
                    except Exception as e:
                        logger.debug(f"Error during task cancellation: {e}")

                # ループをクローズ
                try:
                    loop.close()
                    logger.debug("Event loop closed successfully")
                except Exception as e:
                    logger.warning(f"Error closing event loop: {e}")

        except Exception as e:
            logger.warning(f"Error during event loop cleanup: {e}")


class DownloadTab(QWidget):
    """
    ダウンロードタブ

    YouTube動画のダウンロード機能を提供するUIタブです。

    Features:
        - URL入力
        - 動画情報プレビュー
        - 解像度選択
        - ダウンロード進捗表示
    """

    def __init__(self, parent=None):
        """
        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)

        self.downloader = YouTubeDownloader()
        self.current_video_info: Optional[VideoInfo] = None
        self.worker_thread: Optional[QThread] = None
        self.worker: Optional[DownloadWorker] = None

        self.setup_ui()

        logger.info("DownloadTab initialized")

    def setup_ui(self) -> None:
        """UIをセットアップ"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # タイトル
        title_label = StrongBodyLabel("YouTube動画ダウンロード")
        title_label.setStyleSheet("font-size: 24px;")
        layout.addWidget(title_label)

        # URL入力セクション
        layout.addWidget(self.create_url_input_section())

        # 動画情報カード
        self.info_card = self.create_info_card()
        self.info_card.hide()
        layout.addWidget(self.info_card)

        # ダウンロード設定セクション
        layout.addWidget(self.create_download_settings_section())

        # 進捗バー
        self.progress_bar = ProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # 進捗ラベル
        self.progress_label = BodyLabel("")
        self.progress_label.hide()
        layout.addWidget(self.progress_label)

        # ダウンロードボタン
        self.download_btn = PrimaryPushButton(FluentIcon.DOWNLOAD, "ダウンロード開始")
        self.download_btn.clicked.connect(self.on_download_clicked)
        self.download_btn.setEnabled(False)
        layout.addWidget(self.download_btn)

        # ストレッチ
        layout.addStretch()

        logger.debug("DownloadTab UI setup completed")

    def create_url_input_section(self) -> QWidget:
        """URL入力セクションを作成"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # URL入力
        self.url_input = LineEdit()
        self.url_input.setPlaceholderText("YouTube URLを入力してください...")
        self.url_input.setClearButtonEnabled(True)
        layout.addWidget(self.url_input, stretch=1)

        # 情報取得ボタン
        self.fetch_btn = PushButton(FluentIcon.SEARCH, "動画情報取得")
        self.fetch_btn.clicked.connect(self.on_fetch_info_clicked)
        layout.addWidget(self.fetch_btn)

        return widget

    def create_info_card(self) -> CardWidget:
        """動画情報カードを作成"""
        card = CardWidget()
        card_layout = QHBoxLayout(card)

        # サムネイル
        self.thumbnail_label = ImageLabel()
        self.thumbnail_label.setFixedSize(240, 135)
        self.thumbnail_label.setScaledContents(True)
        card_layout.addWidget(self.thumbnail_label)

        # 動画情報
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)

        self.title_label = StrongBodyLabel("")
        self.title_label.setWordWrap(True)
        info_layout.addWidget(self.title_label)

        self.duration_label = BodyLabel("")
        info_layout.addWidget(self.duration_label)

        self.uploader_label = BodyLabel("")
        info_layout.addWidget(self.uploader_label)

        self.filesize_label = BodyLabel("")
        info_layout.addWidget(self.filesize_label)

        info_layout.addStretch()

        card_layout.addLayout(info_layout, stretch=1)

        return card

    def create_download_settings_section(self) -> QWidget:
        """ダウンロード設定セクションを作成"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # 解像度選択
        resolution_label = BodyLabel("解像度:")
        layout.addWidget(resolution_label)

        self.resolution_combo = ComboBox()
        self.resolution_combo.addItems(["480p", "720p", "1080p", "best"])
        self.resolution_combo.setCurrentIndex(1)  # 720p
        layout.addWidget(self.resolution_combo)

        # スペーサー
        layout.addSpacing(30)

        # 音声あり/なしチェックボックス
        self.audio_checkbox = CheckBox("音声を含める")
        self.audio_checkbox.setChecked(True)  # デフォルトは音声あり
        self.audio_checkbox.setToolTip(
            "チェックを外すと音声なしの動画がダウンロードされます"
        )
        layout.addWidget(self.audio_checkbox)

        layout.addStretch()

        return widget

    def on_fetch_info_clicked(self) -> None:
        """動画情報取得ボタンクリック"""
        url = self.url_input.text().strip()

        if not url:
            self.show_error("URLを入力してください")
            return

        if not self.is_valid_youtube_url(url):
            self.show_error("有効なYouTube URLを入力してください")
            return

        logger.info(f"Fetching video info: {url}")

        # UIを無効化
        self.fetch_btn.setEnabled(False)
        self.fetch_btn.setText("取得中...")

        # ワーカースレッドで情報取得
        self.start_worker_thread()
        self.worker.fetch_info(url)

    def on_download_clicked(self) -> None:
        """ダウンロードボタンクリック"""
        if not self.current_video_info:
            self.show_error("先に動画情報を取得してください")
            return

        url = self.current_video_info.url
        resolution = self.resolution_combo.currentText()
        include_audio = self.audio_checkbox.isChecked()

        logger.info(
            f"Starting download: {url} "
            f"({resolution}, audio={include_audio})"
        )

        # UIを更新
        self.download_btn.setEnabled(False)
        self.download_btn.setText("ダウンロード中...")
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.progress_label.show()

        # ワーカースレッドでダウンロード
        self.start_worker_thread()
        self.worker.download_video(url, resolution, include_audio)

    def start_worker_thread(self) -> None:
        """ワーカースレッドを開始"""
        # 既存のスレッドをクリーンアップ
        self._cleanup_worker_thread()

        # 新しいワーカーとスレッドを作成
        self.worker_thread = QThread()
        self.worker = DownloadWorker(self.downloader)
        self.worker.moveToThread(self.worker_thread)

        # シグナル接続
        self.worker.info_fetched.connect(self.on_info_fetched)
        self.worker.progress.connect(self.on_progress_updated)
        self.worker.finished.connect(self.on_download_finished)
        self.worker.error.connect(self.on_error)

        # スレッド終了時のクリーンアップ
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.finished.connect(self.worker.deleteLater)

        # スレッド開始
        self.worker_thread.start()
        logger.debug("Worker thread started")

    def _cleanup_worker_thread(self) -> None:
        """ワーカースレッドをクリーンアップ"""
        if self.worker_thread and self.worker_thread.isRunning():
            logger.debug("Cleaning up existing worker thread")
            self.worker_thread.quit()
            if not self.worker_thread.wait(3000):  # 3秒待機
                logger.warning("Worker thread did not quit in time")
                self.worker_thread.terminate()
                self.worker_thread.wait()

    def on_info_fetched(self, video_info: VideoInfo) -> None:
        """動画情報取得完了"""
        self.current_video_info = video_info

        # 情報カードを更新
        self.title_label.setText(video_info.title)
        self.duration_label.setText(f"長さ: {video_info.duration_str}")

        if video_info.uploader:
            self.uploader_label.setText(f"投稿者: {video_info.uploader}")

        if video_info.filesize_mb:
            self.filesize_label.setText(f"サイズ: 約{video_info.filesize_mb} MB")

        # サムネイルをダウンロード
        if video_info.thumbnail_url:
            self.load_thumbnail(video_info.thumbnail_url)

        # カードを表示
        self.info_card.show()

        # ダウンロードボタンを有効化
        self.download_btn.setEnabled(True)

        # 取得ボタンを再有効化
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("動画情報取得")

        logger.info(f"Video info displayed: {video_info.title}")

    def on_progress_updated(self, progress: DownloadProgress) -> None:
        """ダウンロード進捗更新"""
        self.progress_bar.setValue(int(progress.percent))

        status_text = (
            f"ダウンロード中: {progress.percent:.1f}% | "
            f"速度: {progress.speed_mbps:.2f} MB/s | "
            f"残り時間: {progress.eta_str}"
        )
        self.progress_label.setText(status_text)

    def on_download_finished(self, result: DownloadResult) -> None:
        """ダウンロード完了"""
        if result.is_success:
            # 成功メッセージ
            message = f"ダウンロード完了: {result.title}"
            if result.audio_path:
                message += f"\n音声ファイル: {Path(result.audio_path).name}"

            self.show_success(message)
            self.progress_bar.setValue(100)
            logger.info(f"Download completed: video={result.video_path}, audio={result.audio_path}")
        else:
            self.show_error(f"ダウンロード失敗: {result.error_message}")
            self.progress_bar.setValue(0)

        # UIを再有効化
        self.download_btn.setEnabled(True)
        self.download_btn.setText("ダウンロード開始")

    def on_error(self, error_message: str) -> None:
        """エラー発生"""
        self.show_error(error_message)

        # UIを再有効化
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("動画情報取得")
        self.download_btn.setEnabled(False)

    def load_thumbnail(self, url: str) -> None:
        """サムネイルをロード"""
        try:
            import urllib.request
            data = urllib.request.urlopen(url).read()

            pixmap = QPixmap()
            pixmap.loadFromData(data)

            self.thumbnail_label.setPixmap(pixmap)
            logger.debug(f"Thumbnail loaded: {url}")

        except Exception as e:
            logger.warning(f"Failed to load thumbnail: {e}")

    def is_valid_youtube_url(self, url: str) -> bool:
        """YouTube URLの簡易バリデーション"""
        return (
            "youtube.com/watch?" in url or
            "youtu.be/" in url or
            "youtube.com/shorts/" in url
        )

    def show_success(self, message: str) -> None:
        """成功メッセージ表示"""
        if hasattr(self.parent(), 'show_success_message'):
            self.parent().show_success_message("成功", message)

    def show_error(self, message: str) -> None:
        """エラーメッセージ表示"""
        if hasattr(self.parent(), 'show_error_message'):
            self.parent().show_error_message("エラー", message)
        logger.error(message)
