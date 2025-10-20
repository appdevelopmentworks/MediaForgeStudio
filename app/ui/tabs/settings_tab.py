"""
設定タブ

このモジュールは、アプリケーション設定とAPIキー管理のUIを提供します。
"""

import os
from typing import Dict
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QScrollArea
)
from PySide6.QtCore import Qt
from qfluentwidgets import (
    LineEdit,
    PasswordLineEdit,
    PushButton,
    CardWidget,
    BodyLabel,
    StrongBodyLabel,
    PrimaryPushButton,
    FluentIcon,
    InfoBar,
    InfoBarPosition,
    ComboBox,
    SwitchButton
)
from loguru import logger


class SettingsTab(QWidget):
    """
    設定タブ

    アプリケーション設定とAPIキー管理のUIを提供します。

    Features:
        - APIキー設定（翻訳API、Google TTS）
        - VOICEVOX設定
        - Whisper設定
        - テーマ設定
    """

    def __init__(self, parent=None):
        """
        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)

        self.env_file = Path(".env")
        self.api_keys: Dict[str, str] = {}

        self.setup_ui()
        self.load_settings()

        logger.info("SettingsTab initialized")

    def setup_ui(self) -> None:
        """UIをセットアップ"""
        # メインレイアウト
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # タイトル
        title_label = StrongBodyLabel("設定")
        title_label.setStyleSheet("font-size: 24px;")
        main_layout.addWidget(title_label)

        # スクロールエリア
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        # スクロールコンテンツ
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)

        # 翻訳API設定カード
        translation_card = self._create_translation_api_card()
        scroll_layout.addWidget(translation_card)

        # TTS設定カード
        tts_card = self._create_tts_settings_card()
        scroll_layout.addWidget(tts_card)

        # Whisper設定カード
        whisper_card = self._create_whisper_settings_card()
        scroll_layout.addWidget(whisper_card)

        # アプリ設定カード
        app_card = self._create_app_settings_card()
        scroll_layout.addWidget(app_card)

        # 保存ボタン
        save_button = PrimaryPushButton(FluentIcon.SAVE, "設定を保存")
        save_button.clicked.connect(self.save_settings)
        scroll_layout.addWidget(save_button)

        scroll_layout.addStretch()

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

    def _create_translation_api_card(self) -> CardWidget:
        """翻訳API設定カード"""
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # タイトル
        title = StrongBodyLabel("翻訳API設定")
        title.setStyleSheet("font-size: 18px;")
        layout.addWidget(title)

        # 説明
        desc = BodyLabel(
            "翻訳APIキーを設定すると、翻訳の選択肢が増えます。\n"
            "すべてオプションです（最低1つ設定推奨）。"
        )
        desc.setStyleSheet("color: gray;")
        layout.addWidget(desc)

        # フォーム
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # Groq API Key
        self.groq_key_input = PasswordLineEdit()
        self.groq_key_input.setPlaceholderText("Groq APIキー（無料・高速・推奨）")
        form_layout.addRow("Groq API:", self.groq_key_input)

        # Gemini API Key
        self.gemini_key_input = PasswordLineEdit()
        self.gemini_key_input.setPlaceholderText("Gemini APIキー")
        form_layout.addRow("Gemini API:", self.gemini_key_input)

        # DeepL API Key
        self.deepl_key_input = PasswordLineEdit()
        self.deepl_key_input.setPlaceholderText("DeepL APIキー（高品質）")
        form_layout.addRow("DeepL API:", self.deepl_key_input)

        # OpenRouter API Key
        self.openrouter_key_input = PasswordLineEdit()
        self.openrouter_key_input.setPlaceholderText("OpenRouter APIキー")
        form_layout.addRow("OpenRouter API:", self.openrouter_key_input)

        # OpenAI API Key
        self.openai_key_input = PasswordLineEdit()
        self.openai_key_input.setPlaceholderText("OpenAI APIキー")
        form_layout.addRow("OpenAI API:", self.openai_key_input)

        layout.addLayout(form_layout)

        return card

    def _create_tts_settings_card(self) -> CardWidget:
        """TTS設定カード"""
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # タイトル
        title = StrongBodyLabel("TTS（音声合成）設定")
        title.setStyleSheet("font-size: 18px;")
        layout.addWidget(title)

        # 説明
        desc = BodyLabel(
            "VOICEVOXとGoogle Cloud TTSの設定（どちらもオプション）。"
        )
        desc.setStyleSheet("color: gray;")
        layout.addWidget(desc)

        # フォーム
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # VOICEVOX Host
        self.voicevox_host_input = LineEdit()
        self.voicevox_host_input.setText("localhost")
        self.voicevox_host_input.setPlaceholderText("localhost")
        form_layout.addRow("VOICEVOX Host:", self.voicevox_host_input)

        # VOICEVOX Port
        self.voicevox_port_input = LineEdit()
        self.voicevox_port_input.setText("50021")
        self.voicevox_port_input.setPlaceholderText("50021")
        form_layout.addRow("VOICEVOX Port:", self.voicevox_port_input)

        # Google Cloud API Key
        self.google_tts_key_input = PasswordLineEdit()
        self.google_tts_key_input.setPlaceholderText(
            "Google Cloud TTS APIキー（オプション）"
        )
        form_layout.addRow("Google TTS API:", self.google_tts_key_input)

        layout.addLayout(form_layout)

        return card

    def _create_whisper_settings_card(self) -> CardWidget:
        """Whisper設定カード"""
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # タイトル
        title = StrongBodyLabel("Whisper文字起こし設定")
        title.setStyleSheet("font-size: 18px;")
        layout.addWidget(title)

        # フォーム
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # Whisperモデルサイズ
        self.whisper_model_combo = ComboBox()
        self.whisper_model_combo.addItems([
            "tiny（最速・低精度）",
            "base（高速・標準精度）",
            "small（標準速度・高精度）",
            "medium（低速・高精度）",
            "large（最低速・最高精度）"
        ])
        self.whisper_model_combo.setCurrentIndex(1)  # base
        form_layout.addRow("モデルサイズ:", self.whisper_model_combo)

        # デバイス選択
        self.whisper_device_combo = ComboBox()
        self.whisper_device_combo.addItems([
            "auto（自動選択）",
            "cuda（NVIDIA GPU）",
            "cpu（CPU）",
            "mps（Apple Silicon）"
        ])
        self.whisper_device_combo.setCurrentIndex(0)  # auto
        form_layout.addRow("デバイス:", self.whisper_device_combo)

        layout.addLayout(form_layout)

        return card

    def _create_app_settings_card(self) -> CardWidget:
        """アプリ設定カード"""
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # タイトル
        title = StrongBodyLabel("アプリケーション設定")
        title.setStyleSheet("font-size: 18px;")
        layout.addWidget(title)

        # フォーム
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # 最大並列ダウンロード数
        self.max_workers_combo = ComboBox()
        self.max_workers_combo.addItems(["1", "2", "3", "4", "5"])
        self.max_workers_combo.setCurrentIndex(2)  # 3
        form_layout.addRow("並列ダウンロード数:", self.max_workers_combo)

        layout.addLayout(form_layout)

        return card

    def load_settings(self) -> None:
        """設定を.envファイルから読み込み"""
        try:
            if not self.env_file.exists():
                logger.info(".env file not found, using defaults")
                return

            # .envファイルを読み込み
            from dotenv import dotenv_values
            env_values = dotenv_values(self.env_file)

            # APIキーを読み込み
            self.groq_key_input.setText(env_values.get("GROQ_API_KEY", ""))
            self.gemini_key_input.setText(env_values.get("GEMINI_API_KEY", ""))
            self.deepl_key_input.setText(env_values.get("DEEPL_API_KEY", ""))
            self.openrouter_key_input.setText(
                env_values.get("OPENROUTER_API_KEY", "")
            )
            self.openai_key_input.setText(env_values.get("OPENAI_API_KEY", ""))

            # VOICEVOX設定
            self.voicevox_host_input.setText(
                env_values.get("VOICEVOX_HOST", "localhost")
            )
            self.voicevox_port_input.setText(
                env_values.get("VOICEVOX_PORT", "50021")
            )

            # Google TTS
            self.google_tts_key_input.setText(
                env_values.get("GOOGLE_CLOUD_API_KEY", "")
            )

            # Whisper設定
            whisper_model = env_values.get("WHISPER_MODEL", "base")
            model_map = {
                "tiny": 0, "base": 1, "small": 2, "medium": 3, "large": 4
            }
            self.whisper_model_combo.setCurrentIndex(
                model_map.get(whisper_model, 1)
            )

            whisper_device = env_values.get("WHISPER_DEVICE", "auto")
            device_map = {"auto": 0, "cuda": 1, "cpu": 2, "mps": 3}
            self.whisper_device_combo.setCurrentIndex(
                device_map.get(whisper_device, 0)
            )

            # 並列ダウンロード数
            max_workers = env_values.get("MAX_WORKERS", "3")
            try:
                workers_index = int(max_workers) - 1
                if 0 <= workers_index < 5:
                    self.max_workers_combo.setCurrentIndex(workers_index)
            except ValueError:
                pass

            logger.info("Settings loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load settings: {e}")

    def save_settings(self) -> None:
        """設定を.envファイルに保存"""
        try:
            # .env.templateを読み込んでベースにする
            template_file = Path(".env.template")
            env_content = []

            if template_file.exists():
                with open(template_file, 'r', encoding='utf-8') as f:
                    env_content = f.readlines()

            # 新しい設定値
            new_values = {
                "GROQ_API_KEY": self.groq_key_input.text().strip(),
                "GEMINI_API_KEY": self.gemini_key_input.text().strip(),
                "DEEPL_API_KEY": self.deepl_key_input.text().strip(),
                "OPENROUTER_API_KEY": self.openrouter_key_input.text().strip(),
                "OPENAI_API_KEY": self.openai_key_input.text().strip(),
                "VOICEVOX_HOST": self.voicevox_host_input.text().strip(),
                "VOICEVOX_PORT": self.voicevox_port_input.text().strip(),
                "GOOGLE_CLOUD_API_KEY": self.google_tts_key_input.text().strip(),
                "WHISPER_MODEL": ["tiny", "base", "small", "medium", "large"][
                    self.whisper_model_combo.currentIndex()
                ],
                "WHISPER_DEVICE": ["auto", "cuda", "cpu", "mps"][
                    self.whisper_device_combo.currentIndex()
                ],
                "MAX_WORKERS": str(self.max_workers_combo.currentIndex() + 1)
            }

            # .envファイルに書き込み
            with open(self.env_file, 'w', encoding='utf-8') as f:
                # テンプレートのコメント行を保持
                for line in env_content:
                    if line.startswith("#") or line.strip() == "":
                        f.write(line)

                # 新しい値を書き込み
                f.write("\n# API Keys\n")
                for key, value in new_values.items():
                    if value:  # 空でない値のみ書き込み
                        f.write(f"{key}={value}\n")

            logger.info("Settings saved successfully")

            # 成功メッセージ
            InfoBar.success(
                title="保存完了",
                content="設定を保存しました。再起動後に反映されます。",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )

            # 環境変数を再読み込み
            from dotenv import load_dotenv
            load_dotenv(override=True)

        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

            # エラーメッセージ
            InfoBar.error(
                title="保存失敗",
                content=f"設定の保存に失敗しました: {str(e)}",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
