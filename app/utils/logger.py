"""
ロギングユーティリティ

このモジュールは、アプリケーション全体で使用するロガーを提供します。
loguruを使用して、カラフルで読みやすいログ出力を実現します。
"""

import sys
from pathlib import Path
from typing import Optional
from loguru import logger
from datetime import datetime


def setup_logger(
    log_dir: Optional[str] = None,
    log_level: str = "INFO",
    rotation: str = "10 MB",
    retention: str = "7 days",
    compression: str = "zip"
) -> None:
    """
    ロガーを設定する

    Args:
        log_dir: ログディレクトリパス（Noneの場合は"./logs"）
        log_level: ログレベル（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        rotation: ログローテーションサイズ（例: "10 MB", "1 day"）
        retention: ログ保存期間（例: "7 days", "1 week"）
        compression: 圧縮形式（zip, gz, bz2）

    Example:
        >>> setup_logger(log_level="DEBUG")
        >>> logger.info("Logger initialized")
    """
    # デフォルトのハンドラーを削除
    logger.remove()

    # ログディレクトリの設定
    if log_dir is None:
        log_dir = "./logs"

    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # コンソール出力の設定（カラフル）
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        colorize=True
    )

    # ファイル出力の設定（全ログ）
    logger.add(
        log_path / "app_{time:YYYY-MM-DD}.log",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation=rotation,
        retention=retention,
        compression=compression,
        encoding="utf-8"
    )

    # エラーログの設定（ERROR以上のみ）
    logger.add(
        log_path / "error_{time:YYYY-MM-DD}.log",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}\n{exception}",
        rotation=rotation,
        retention=retention,
        compression=compression,
        encoding="utf-8"
    )

    logger.info(f"Logger initialized: level={log_level}, log_dir={log_path}")


def get_logger(name: Optional[str] = None):
    """
    ロガーインスタンスを取得する

    Args:
        name: ロガー名（通常は__name__を指定）

    Returns:
        logger: loguruロガーインスタンス

    Example:
        >>> log = get_logger(__name__)
        >>> log.info("This is a log message")
    """
    if name:
        return logger.bind(name=name)
    return logger


class LoggerContext:
    """
    ログコンテキストマネージャー

    with文を使用して、処理の開始・終了を自動的にログ出力します。

    Example:
        >>> with LoggerContext("Downloading video"):
        ...     # ダウンロード処理
        ...     pass
        [INFO] Starting: Downloading video
        [INFO] Completed: Downloading video (elapsed: 2.34s)
    """

    def __init__(self, task_name: str, log_level: str = "INFO"):
        """
        Args:
            task_name: タスク名
            log_level: ログレベル
        """
        self.task_name = task_name
        self.log_level = log_level
        self.start_time: Optional[datetime] = None

    def __enter__(self):
        """コンテキスト開始"""
        self.start_time = datetime.now()
        logger.log(self.log_level, f"Starting: {self.task_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキスト終了"""
        if self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()

            if exc_type is not None:
                logger.error(
                    f"Failed: {self.task_name} (elapsed: {elapsed:.2f}s) - {exc_val}"
                )
            else:
                logger.log(
                    self.log_level,
                    f"Completed: {self.task_name} (elapsed: {elapsed:.2f}s)"
                )

        # 例外を再発生させる
        return False


def log_function_call(func):
    """
    関数呼び出しをログ出力するデコレータ

    Args:
        func: デコレート対象の関数

    Example:
        >>> @log_function_call
        ... async def download_video(url: str):
        ...     pass
        [DEBUG] Calling: download_video(url='https://...')
        [DEBUG] Returned: download_video -> <result>
    """
    from functools import wraps
    import inspect

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        func_name = func.__name__
        logger.debug(f"Calling: {func_name}(args={args}, kwargs={kwargs})")

        try:
            result = await func(*args, **kwargs)
            logger.debug(f"Returned: {func_name} -> {result}")
            return result
        except Exception as e:
            logger.error(f"Exception in {func_name}: {e}")
            raise

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        func_name = func.__name__
        logger.debug(f"Calling: {func_name}(args={args}, kwargs={kwargs})")

        try:
            result = func(*args, **kwargs)
            logger.debug(f"Returned: {func_name} -> {result}")
            return result
        except Exception as e:
            logger.error(f"Exception in {func_name}: {e}")
            raise

    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


# アプリケーション起動時にロガーをセットアップ
# （main.pyから明示的に呼び出すことも可能）
if __name__ != "__main__":
    # インポート時に自動セットアップ（デフォルト設定）
    try:
        setup_logger()
    except Exception as e:
        print(f"Failed to setup logger: {e}")
