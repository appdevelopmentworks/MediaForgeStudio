"""
ファイル管理ユーティリティ

このモジュールは、ファイル名のサニタイズ、一時ファイル管理、
ディレクトリ操作などのユーティリティ機能を提供します。
"""

import os
import re
import shutil
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from loguru import logger


class FileManager:
    """
    ファイル管理クラス

    ファイル名のサニタイズ、一時ファイル管理、ディレクトリ操作を提供します。

    Example:
        >>> fm = FileManager()
        >>> safe_name = fm.sanitize_filename("video: test/file.mp4")
        >>> print(safe_name)
        'video test file.mp4'
    """

    # ファイル名に使用できない文字
    INVALID_CHARS = r'[<>:"/\\|?*\x00-\x1f]'

    # 予約されたファイル名（Windows）
    RESERVED_NAMES = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }

    def __init__(self):
        """FileManagerを初期化"""
        logger.debug("FileManager initialized")

    def sanitize_filename(
        self,
        filename: str,
        max_length: int = 255,
        replacement: str = "_"
    ) -> str:
        """
        ファイル名を安全な形式にサニタイズ

        Args:
            filename: サニタイズするファイル名
            max_length: 最大文字数（デフォルト: 255）
            replacement: 無効な文字の置換文字（デフォルト: "_"）

        Returns:
            str: サニタイズされたファイル名

        Example:
            >>> fm.sanitize_filename("video: test/file.mp4")
            'video_ test_file.mp4'
        """
        if not filename:
            return "unnamed"

        # パスの分離（拡張子を保持）
        name, ext = os.path.splitext(filename)

        # 無効な文字を置換
        name = re.sub(self.INVALID_CHARS, replacement, name)

        # 連続する置換文字を1つにまとめる
        name = re.sub(f"{re.escape(replacement)}+", replacement, name)

        # 前後の空白・ドット・置換文字を削除
        name = name.strip(f" .{replacement}")

        # 空の場合はデフォルト名
        if not name:
            name = "unnamed"

        # Windowsの予約語チェック
        if name.upper() in self.RESERVED_NAMES:
            name = f"{name}_file"

        # 長さ制限（拡張子を含めて）
        max_name_length = max_length - len(ext)
        if len(name) > max_name_length:
            name = name[:max_name_length]

        result = f"{name}{ext}"

        logger.debug(f"Sanitized filename: '{filename}' -> '{result}'")

        return result

    def sanitize_path(self, path: str, max_length: int = 255) -> str:
        """
        パス全体をサニタイズ

        Args:
            path: サニタイズするパス
            max_length: ファイル名部分の最大文字数

        Returns:
            str: サニタイズされたパス

        Example:
            >>> fm.sanitize_path("/output/video: test.mp4")
            '/output/video_ test.mp4'
        """
        path_obj = Path(path)

        # ディレクトリ部分とファイル名を分離
        directory = path_obj.parent
        filename = path_obj.name

        # ファイル名をサニタイズ
        safe_filename = self.sanitize_filename(filename, max_length)

        # パスを再構築
        safe_path = directory / safe_filename

        return str(safe_path)

    def ensure_directory(self, directory: str) -> Path:
        """
        ディレクトリが存在することを確認（存在しない場合は作成）

        Args:
            directory: ディレクトリパス

        Returns:
            Path: ディレクトリパス

        Example:
            >>> fm.ensure_directory("./output/videos")
            Path('./output/videos')
        """
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Directory ensured: {dir_path}")

        return dir_path

    def get_unique_filename(self, filepath: str) -> str:
        """
        重複しないファイル名を取得（既存の場合は番号を追加）

        Args:
            filepath: ファイルパス

        Returns:
            str: 重複しないファイルパス

        Example:
            >>> # video.mp4が存在する場合
            >>> fm.get_unique_filename("./video.mp4")
            './video_1.mp4'
        """
        path = Path(filepath)

        if not path.exists():
            return str(path)

        # ファイル名と拡張子を分離
        name = path.stem
        ext = path.suffix
        directory = path.parent

        # 重複しない番号を探す
        counter = 1
        while True:
            new_name = f"{name}_{counter}{ext}"
            new_path = directory / new_name

            if not new_path.exists():
                logger.debug(f"Unique filename: '{filepath}' -> '{new_path}'")
                return str(new_path)

            counter += 1

            # 無限ループ防止
            if counter > 9999:
                raise RuntimeError(f"Too many duplicate files: {filepath}")

    def get_file_size(self, filepath: str) -> int:
        """
        ファイルサイズを取得（バイト単位）

        Args:
            filepath: ファイルパス

        Returns:
            int: ファイルサイズ（バイト）

        Raises:
            FileNotFoundError: ファイルが存在しない
        """
        path = Path(filepath)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        return path.stat().st_size

    def get_file_size_human(self, filepath: str) -> str:
        """
        ファイルサイズを人間が読みやすい形式で取得

        Args:
            filepath: ファイルパス

        Returns:
            str: ファイルサイズ（例: "1.5 MB"）

        Example:
            >>> fm.get_file_size_human("video.mp4")
            '125.3 MB'
        """
        size_bytes = self.get_file_size(filepath)

        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0

        return f"{size_bytes:.1f} PB"

    def delete_file(self, filepath: str, ignore_errors: bool = True) -> bool:
        """
        ファイルを削除

        Args:
            filepath: ファイルパス
            ignore_errors: エラーを無視するか（デフォルト: True）

        Returns:
            bool: 削除に成功した場合True

        Example:
            >>> fm.delete_file("temp.txt")
            True
        """
        try:
            path = Path(filepath)

            if not path.exists():
                logger.debug(f"File not found, skipping: {filepath}")
                return True

            path.unlink()
            logger.info(f"File deleted: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete file: {filepath} - {e}")

            if not ignore_errors:
                raise

            return False

    def delete_directory(
        self,
        directory: str,
        ignore_errors: bool = True
    ) -> bool:
        """
        ディレクトリを削除（中身も含めて）

        Args:
            directory: ディレクトリパス
            ignore_errors: エラーを無視するか（デフォルト: True）

        Returns:
            bool: 削除に成功した場合True

        Example:
            >>> fm.delete_directory("./temp")
            True
        """
        try:
            path = Path(directory)

            if not path.exists():
                logger.debug(f"Directory not found, skipping: {directory}")
                return True

            shutil.rmtree(path, ignore_errors=ignore_errors)
            logger.info(f"Directory deleted: {directory}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete directory: {directory} - {e}")

            if not ignore_errors:
                raise

            return False

    def clean_old_files(
        self,
        directory: str,
        days: int = 7,
        pattern: str = "*"
    ) -> List[str]:
        """
        指定日数より古いファイルを削除

        Args:
            directory: ディレクトリパス
            days: 保持日数（これより古いファイルを削除）
            pattern: ファイルパターン（例: "*.log"）

        Returns:
            List[str]: 削除したファイルのリスト

        Example:
            >>> # 7日より古いログファイルを削除
            >>> fm.clean_old_files("./logs", days=7, pattern="*.log")
            ['./logs/old.log', './logs/old2.log']
        """
        deleted_files = []

        try:
            dir_path = Path(directory)

            if not dir_path.exists():
                logger.warning(f"Directory not found: {directory}")
                return deleted_files

            # 現在時刻
            now = datetime.now()

            # パターンにマッチするファイルを検索
            for file_path in dir_path.glob(pattern):
                if not file_path.is_file():
                    continue

                # ファイルの更新時刻
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)

                # 経過日数
                age = (now - mtime).days

                # 古いファイルを削除
                if age > days:
                    if self.delete_file(str(file_path)):
                        deleted_files.append(str(file_path))

            if deleted_files:
                logger.info(
                    f"Cleaned {len(deleted_files)} old files from {directory}"
                )

        except Exception as e:
            logger.error(f"Failed to clean old files: {e}")

        return deleted_files

    def move_file(
        self,
        source: str,
        destination: str,
        overwrite: bool = False
    ) -> bool:
        """
        ファイルを移動

        Args:
            source: 移動元ファイルパス
            destination: 移動先ファイルパス
            overwrite: 上書きを許可するか（デフォルト: False）

        Returns:
            bool: 移動に成功した場合True

        Example:
            >>> fm.move_file("temp.txt", "archive/temp.txt")
            True
        """
        try:
            src_path = Path(source)
            dst_path = Path(destination)

            if not src_path.exists():
                raise FileNotFoundError(f"Source file not found: {source}")

            # 移動先ディレクトリを作成
            dst_path.parent.mkdir(parents=True, exist_ok=True)

            # 上書きチェック
            if dst_path.exists() and not overwrite:
                dst_path = Path(self.get_unique_filename(str(dst_path)))

            # 移動
            shutil.move(str(src_path), str(dst_path))
            logger.info(f"File moved: {source} -> {dst_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to move file: {e}")
            return False

    def copy_file(
        self,
        source: str,
        destination: str,
        overwrite: bool = False
    ) -> bool:
        """
        ファイルをコピー

        Args:
            source: コピー元ファイルパス
            destination: コピー先ファイルパス
            overwrite: 上書きを許可するか（デフォルト: False）

        Returns:
            bool: コピーに成功した場合True

        Example:
            >>> fm.copy_file("video.mp4", "backup/video.mp4")
            True
        """
        try:
            src_path = Path(source)
            dst_path = Path(destination)

            if not src_path.exists():
                raise FileNotFoundError(f"Source file not found: {source}")

            # コピー先ディレクトリを作成
            dst_path.parent.mkdir(parents=True, exist_ok=True)

            # 上書きチェック
            if dst_path.exists() and not overwrite:
                dst_path = Path(self.get_unique_filename(str(dst_path)))

            # コピー
            shutil.copy2(str(src_path), str(dst_path))
            logger.info(f"File copied: {source} -> {dst_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to copy file: {e}")
            return False
