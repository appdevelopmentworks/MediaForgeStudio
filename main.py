#!/usr/bin/env python3
"""
MediaForge Studio - Main Entry Point
YouTube動画加工・吹き替え・統合ツール
"""

import sys
import asyncio
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from qfluentwidgets import setTheme, Theme, setThemeColor

# Import modules
from app.ui.main_window import MainWindow
from app.utils.logger import setup_logger


def setup_application():
    """アプリケーション初期化"""
    # High DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    app = QApplication(sys.argv)
    app.setApplicationName("MediaForge Studio")
    app.setOrganizationName("MediaForge")
    app.setApplicationVersion("1.0.0")
    
    return app


def setup_theme(app: QApplication):
    """テーマ設定"""
    # TODO: config.yamlから読み込み
    theme_mode = "auto"  # light / dark / auto
    
    if theme_mode == "dark":
        setTheme(Theme.DARK)
    elif theme_mode == "light":
        setTheme(Theme.LIGHT)
    else:  # auto
        setTheme(Theme.AUTO)
    
    # Primary color
    setThemeColor("#0078D4")  # Microsoft Blue


def setup_logging():
    """ログ設定"""
    # Use the logger setup from app.utils.logger
    setup_logger(log_level="DEBUG")
    logger.info("MediaForge Studio starting...")


def create_directories():
    """必要なディレクトリを作成"""
    directories = [
        "./output/videos",
        "./output/audios",
        "./output/dubbed",
        "./temp",
        "./logs",
        "./data",
        "./models"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    logger.info("Directories created successfully")


def main():
    """メイン実行関数"""
    try:
        # Load .env file first (ensure it's loaded before anything else)
        load_dotenv(override=True)

        # Setup
        setup_logging()
        create_directories()
        
        # Create application
        app = setup_application()
        setup_theme(app)
        
        logger.info("Application initialized")

        # Create and show main window
        window = MainWindow()
        window.show()

        logger.info("Main window displayed")

        # Start event loop
        exit_code = app.exec()
        logger.info(f"Application exited with code {exit_code}")

        return exit_code
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
        
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
