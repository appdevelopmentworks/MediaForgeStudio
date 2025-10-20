"""
メインウィンドウ

このモジュールは、アプリケーションのメインウィンドウを提供します。
QFluentWidgetsを使用してモダンなUIを実現します。
"""

import sys
from typing import Optional
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from qfluentwidgets import (
    FluentWindow,
    NavigationItemPosition,
    FluentIcon,
    Theme,
    setTheme,
    isDarkTheme,
    MessageBox,
    InfoBar,
    InfoBarPosition
)
from loguru import logger


class MainWindow(FluentWindow):
    """
    メインウィンドウ

    アプリケーションのメインウィンドウで、タブナビゲーションと
    各機能タブを管理します。

    Attributes:
        app_name: アプリケーション名
        version: バージョン番号
    """

    def __init__(self):
        """メインウィンドウを初期化"""
        super().__init__()

        self.app_name = "MediaForge Studio"
        self.version = "0.1.0"

        # ウィンドウ設定
        self.setup_window()

        # UI初期化
        self.setup_ui()

        # テーマ設定
        self.setup_theme()

        logger.info(f"{self.app_name} v{self.version} initialized")

    def setup_window(self) -> None:
        """ウィンドウの基本設定"""
        # ウィンドウタイトル
        self.setWindowTitle(f"{self.app_name} v{self.version}")

        # ウィンドウサイズ
        self.resize(1200, 800)

        # 最小サイズ
        self.setMinimumSize(800, 600)

        # ウィンドウを中央に配置
        self.center_window()

        logger.debug("Window setup completed")

    def setup_ui(self) -> None:
        """UIコンポーネントを初期化"""
        try:
            # ナビゲーションインターフェイスを作成
            self.create_navigation_interface()

            logger.info("UI setup completed")

        except Exception as e:
            logger.error(f"Failed to setup UI: {e}")
            raise

    def create_navigation_interface(self) -> None:
        """ナビゲーションインターフェイスを作成"""
        # ホームタブ（プレースホルダー）
        placeholder = QWidget()
        placeholder.setObjectName("homeTab")
        placeholder_layout = QVBoxLayout(placeholder)
        from PySide6.QtWidgets import QLabel
        label = QLabel("MediaForge Studio\n\nPhase 1: ダウンロード機能実装完了\n\n左側のメニューから「ダウンロード」を選択してください")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 18px; color: gray;")
        placeholder_layout.addWidget(label)

        self.addSubInterface(
            placeholder,
            FluentIcon.HOME,
            "ホーム",
            NavigationItemPosition.TOP
        )

        # ダウンロードタブ
        from app.ui.tabs.download_tab import DownloadTab
        self.download_tab = DownloadTab(self)
        self.download_tab.setObjectName("downloadTab")
        self.addSubInterface(
            self.download_tab,
            FluentIcon.DOWNLOAD,
            "ダウンロード",
            NavigationItemPosition.TOP
        )

        # 吹き替えタブ
        from app.ui.tabs.dubbing_tab import DubbingTab
        self.dubbing_tab = DubbingTab(self)
        self.dubbing_tab.setObjectName("dubbingTab")
        self.addSubInterface(
            self.dubbing_tab,
            FluentIcon.MICROPHONE,
            "吹き替え",
            NavigationItemPosition.TOP
        )

        # 連結タブ
        from app.ui.tabs.merge_tab import MergeTab
        self.merge_tab = MergeTab(self)
        self.merge_tab.setObjectName("mergeTab")
        self.addSubInterface(
            self.merge_tab,
            FluentIcon.CONNECT,
            "連結",
            NavigationItemPosition.TOP
        )

        # 設定タブ（将来実装）
        # from app.ui.tabs.settings_tab import SettingsTab
        # self.settings_tab = SettingsTab(self)
        # self.addSubInterface(
        #     self.settings_tab,
        #     FluentIcon.SETTING,
        #     "設定",
        #     NavigationItemPosition.BOTTOM
        # )

        logger.debug("Navigation interface created")

    def setup_theme(self) -> None:
        """テーマを設定"""
        try:
            # システムテーマを自動検出
            if isDarkTheme():
                setTheme(Theme.DARK)
                logger.info("Theme set to DARK")
            else:
                setTheme(Theme.LIGHT)
                logger.info("Theme set to LIGHT")

        except Exception as e:
            logger.warning(f"Failed to setup theme: {e}")
            setTheme(Theme.AUTO)

    def center_window(self) -> None:
        """ウィンドウを画面中央に配置"""
        try:
            screen = QApplication.primaryScreen()
            if screen:
                screen_geometry = screen.availableGeometry()
                window_geometry = self.frameGeometry()
                center_point = screen_geometry.center()
                window_geometry.moveCenter(center_point)
                self.move(window_geometry.topLeft())

                logger.debug("Window centered on screen")

        except Exception as e:
            logger.warning(f"Failed to center window: {e}")

    def show_success_message(
        self,
        title: str,
        message: str,
        duration: int = 3000
    ) -> None:
        """
        成功メッセージを表示

        Args:
            title: タイトル
            message: メッセージ本文
            duration: 表示時間（ミリ秒）
        """
        InfoBar.success(
            title=title,
            content=message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=duration,
            parent=self
        )
        logger.info(f"Success message: {title} - {message}")

    def show_error_message(
        self,
        title: str,
        message: str,
        duration: int = 5000
    ) -> None:
        """
        エラーメッセージを表示

        Args:
            title: タイトル
            message: メッセージ本文
            duration: 表示時間（ミリ秒）
        """
        InfoBar.error(
            title=title,
            content=message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=duration,
            parent=self
        )
        logger.error(f"Error message: {title} - {message}")

    def show_warning_message(
        self,
        title: str,
        message: str,
        duration: int = 4000
    ) -> None:
        """
        警告メッセージを表示

        Args:
            title: タイトル
            message: メッセージ本文
            duration: 表示時間（ミリ秒）
        """
        InfoBar.warning(
            title=title,
            content=message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=duration,
            parent=self
        )
        logger.warning(f"Warning message: {title} - {message}")

    def show_info_message(
        self,
        title: str,
        message: str,
        duration: int = 3000
    ) -> None:
        """
        情報メッセージを表示

        Args:
            title: タイトル
            message: メッセージ本文
            duration: 表示時間（ミリ秒）
        """
        InfoBar.info(
            title=title,
            content=message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=duration,
            parent=self
        )
        logger.info(f"Info message: {title} - {message}")

    def show_confirmation_dialog(
        self,
        title: str,
        message: str
    ) -> bool:
        """
        確認ダイアログを表示

        Args:
            title: タイトル
            message: メッセージ本文

        Returns:
            bool: ユーザーがOKを選択した場合True
        """
        dialog = MessageBox(title, message, self)
        return dialog.exec() == MessageBox.Accepted

    def closeEvent(self, event) -> None:
        """
        ウィンドウクローズイベント

        Args:
            event: クローズイベント
        """
        logger.info("Main window closing")

        # TODO: 実行中のダウンロードがある場合は確認ダイアログを表示

        event.accept()


def create_application() -> QApplication:
    """
    Qtアプリケーションを作成

    Returns:
        QApplication: Qtアプリケーションインスタンス
    """
    # 高DPI対応
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    app.setApplicationName("MediaForge Studio")
    app.setApplicationVersion("0.1.0")

    logger.info("Qt application created")

    return app


def main() -> int:
    """
    アプリケーションのエントリーポイント

    Returns:
        int: 終了コード
    """
    try:
        # ロガー初期化
        from app.utils.logger import setup_logger
        setup_logger(log_level="DEBUG")

        logger.info("Starting MediaForge Studio")

        # アプリケーション作成
        app = create_application()

        # メインウィンドウ作成
        window = MainWindow()
        window.show()

        # イベントループ開始
        exit_code = app.exec()

        logger.info(f"Application exited with code {exit_code}")
        return exit_code

    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
