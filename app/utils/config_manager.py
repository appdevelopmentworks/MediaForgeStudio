"""
設定管理ユーティリティ

このモジュールは、config.yamlファイルの読み書きと設定値の管理を提供します。
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
from loguru import logger
import yaml


class ConfigManager:
    """
    設定管理クラス

    config.yamlファイルの読み書きと設定値の取得・更新を管理します。

    Attributes:
        config_path: 設定ファイルのパス
        config: 読み込まれた設定データ

    Example:
        >>> config = ConfigManager()
        >>> theme = config.get("app.theme")
        >>> print(theme)
        'auto'
    """

    def __init__(self, config_path: str = "./config/config.yaml"):
        """
        Args:
            config_path: 設定ファイルのパス（デフォルト: "./config/config.yaml"）
        """
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}

        # 設定ファイルを読み込み
        self.load()

        logger.info(f"ConfigManager initialized: {self.config_path}")

    def load(self) -> bool:
        """
        設定ファイルを読み込み

        Returns:
            bool: 読み込みに成功した場合True

        Example:
            >>> config.load()
            True
        """
        try:
            if not self.config_path.exists():
                logger.warning(
                    f"Config file not found: {self.config_path}, "
                    f"using default settings"
                )
                self.config = self._get_default_config()
                return False

            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f) or {}

            logger.info(f"Config loaded: {self.config_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.config = self._get_default_config()
            return False

    def save(self) -> bool:
        """
        設定ファイルに保存

        Returns:
            bool: 保存に成功した場合True

        Example:
            >>> config.set("app.theme", "dark")
            >>> config.save()
            True
        """
        try:
            # ディレクトリを作成
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # YAMLファイルに書き込み
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(
                    self.config,
                    f,
                    allow_unicode=True,
                    default_flow_style=False,
                    sort_keys=False
                )

            logger.info(f"Config saved: {self.config_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        設定値を取得（ドット記法をサポート）

        Args:
            key: 設定キー（例: "app.theme", "download.max_concurrent"）
            default: デフォルト値

        Returns:
            Any: 設定値（存在しない場合はdefault）

        Example:
            >>> config.get("app.theme")
            'auto'
            >>> config.get("app.unknown", "default_value")
            'default_value'
        """
        try:
            keys = key.split(".")
            value = self.config

            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    logger.debug(f"Config key not found: {key}, using default")
                    return default

            return value

        except Exception as e:
            logger.warning(f"Error getting config value: {key} - {e}")
            return default

    def set(self, key: str, value: Any) -> bool:
        """
        設定値を更新（ドット記法をサポート）

        Args:
            key: 設定キー（例: "app.theme"）
            value: 設定値

        Returns:
            bool: 更新に成功した場合True

        Example:
            >>> config.set("app.theme", "dark")
            True
        """
        try:
            keys = key.split(".")
            target = self.config

            # 最後のキー以外をたどる
            for k in keys[:-1]:
                if k not in target or not isinstance(target[k], dict):
                    target[k] = {}
                target = target[k]

            # 最後のキーに値を設定
            target[keys[-1]] = value

            logger.debug(f"Config updated: {key} = {value}")
            return True

        except Exception as e:
            logger.error(f"Failed to set config value: {key} - {e}")
            return False

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        設定セクション全体を取得

        Args:
            section: セクション名（例: "app", "download"）

        Returns:
            Dict[str, Any]: セクションの設定

        Example:
            >>> config.get_section("app")
            {'theme': 'auto', 'language': 'ja', ...}
        """
        return self.get(section, {})

    def update_section(self, section: str, values: Dict[str, Any]) -> bool:
        """
        設定セクション全体を更新

        Args:
            section: セクション名
            values: 更新する値の辞書

        Returns:
            bool: 更新に成功した場合True

        Example:
            >>> config.update_section("app", {"theme": "dark", "language": "en"})
            True
        """
        try:
            if section not in self.config:
                self.config[section] = {}

            if isinstance(self.config[section], dict):
                self.config[section].update(values)
                logger.info(f"Config section updated: {section}")
                return True
            else:
                logger.error(f"Config section is not a dict: {section}")
                return False

        except Exception as e:
            logger.error(f"Failed to update section: {section} - {e}")
            return False

    def reset_to_default(self) -> bool:
        """
        設定をデフォルトに戻す

        Returns:
            bool: リセットに成功した場合True

        Example:
            >>> config.reset_to_default()
            True
        """
        try:
            self.config = self._get_default_config()
            logger.info("Config reset to default")
            return True

        except Exception as e:
            logger.error(f"Failed to reset config: {e}")
            return False

    def _get_default_config(self) -> Dict[str, Any]:
        """
        デフォルト設定を取得

        Returns:
            Dict[str, Any]: デフォルト設定
        """
        return {
            "app": {
                "theme": "auto",
                "language": "ja",
                "log_level": "INFO"
            },
            "window": {
                "width": 1200,
                "height": 800,
                "min_width": 800,
                "min_height": 600
            },
            "download": {
                "default_resolution": "720p",
                "max_concurrent": 3,
                "output_dir": "./output/videos",
                "retry_count": 3
            },
            "audio": {
                "default_bitrate": "128k",
                "output_dir": "./output/audios",
                "format": "mp3"
            },
            "dubbing": {
                "output_dir": "./output/dubbed"
            },
            "tts": {
                "default_engine": "edge_tts"
            },
            "translation": {
                "default_api": "argos",
                "target_language": "ja"
            },
            "whisper": {
                "model": "base",
                "device": "auto",
                "language": "auto"
            },
            "processing": {
                "max_workers": 3,
                "temp_dir": "./temp"
            }
        }

    # 便利なヘルパーメソッド

    def get_app_config(self) -> Dict[str, Any]:
        """アプリケーション設定を取得"""
        return self.get_section("app")

    def get_download_config(self) -> Dict[str, Any]:
        """ダウンロード設定を取得"""
        return self.get_section("download")

    def get_tts_config(self) -> Dict[str, Any]:
        """TTS設定を取得"""
        return self.get_section("tts")

    def get_whisper_config(self) -> Dict[str, Any]:
        """Whisper設定を取得"""
        return self.get_section("whisper")

    def get_translation_config(self) -> Dict[str, Any]:
        """翻訳設定を取得"""
        return self.get_section("translation")

    def get_output_dir(self, type: str = "videos") -> str:
        """
        出力ディレクトリを取得

        Args:
            type: タイプ（videos/audios/dubbed）

        Returns:
            str: 出力ディレクトリパス
        """
        dir_map = {
            "videos": "download.output_dir",
            "audios": "audio.output_dir",
            "dubbed": "dubbing.output_dir"
        }

        key = dir_map.get(type, "download.output_dir")
        return self.get(key, f"./output/{type}")

    def get_max_workers(self) -> int:
        """並列処理数を取得"""
        return self.get("processing.max_workers", 3)

    def get_theme(self) -> str:
        """テーマを取得"""
        return self.get("app.theme", "auto")

    def set_theme(self, theme: str) -> bool:
        """テーマを設定"""
        if theme in ["light", "dark", "auto"]:
            return self.set("app.theme", theme)
        else:
            logger.warning(f"Invalid theme: {theme}")
            return False

    def get_default_resolution(self) -> str:
        """デフォルト解像度を取得"""
        return self.get("download.default_resolution", "720p")

    def get_default_tts_engine(self) -> str:
        """デフォルトTTSエンジンを取得"""
        return self.get("tts.default_engine", "edge_tts")


# シングルトンインスタンス
_config_instance: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """
    ConfigManagerのシングルトンインスタンスを取得

    Returns:
        ConfigManager: 設定管理インスタンス

    Example:
        >>> from app.utils.config_manager import get_config
        >>> config = get_config()
        >>> theme = config.get("app.theme")
    """
    global _config_instance

    if _config_instance is None:
        _config_instance = ConfigManager()

    return _config_instance
