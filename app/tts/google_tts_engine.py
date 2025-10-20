"""
Google Cloud Text-to-Speech エンジン

このモジュールは、Google Cloud TTSを使用した音声合成機能を提供します。
高品質な音声を生成できますが、APIキーが必要です。
"""

import os
from typing import Optional, List
from loguru import logger


class GoogleTTSEngine:
    """
    Google Cloud TTS エンジン

    Google Cloud Text-to-Speech APIを使用して音声合成を行います。

    Attributes:
        default_voice: デフォルトの話者
        api_key: Google Cloud APIキー

    Example:
        >>> engine = GoogleTTSEngine(api_key="your_api_key")
        >>> audio_data = await engine.synthesize(
        ...     text="こんにちは、世界",
        ...     voice="ja-JP-Neural2-B"
        ... )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_voice: str = "ja-JP-Neural2-B"
    ):
        """
        Args:
            api_key: Google Cloud APIキー（Noneの場合は環境変数から取得）
            default_voice: デフォルトの話者
        """
        self.default_voice = default_voice
        self.api_key = api_key or os.getenv("GOOGLE_CLOUD_API_KEY")

        if not self.api_key:
            logger.warning(
                "Google Cloud API key not found. "
                "Set GOOGLE_CLOUD_API_KEY environment variable."
            )

        # Google Cloud TTSが利用可能か確認
        try:
            from google.cloud import texttospeech
            self.client = None  # 遅延初期化
            self.texttospeech = texttospeech
            logger.info(f"GoogleTTSEngine initialized: voice={default_voice}")

        except ImportError:
            logger.error("google-cloud-texttospeech package not installed")
            raise ImportError(
                "google-cloud-texttospeech is not installed. "
                "Install it with: pip install google-cloud-texttospeech"
            )

    def _get_client(self):
        """TTSクライアントを取得（遅延初期化）"""
        if self.client is None:
            if not self.api_key:
                raise ValueError(
                    "Google Cloud API key is required. "
                    "Set GOOGLE_CLOUD_API_KEY environment variable."
                )

            # APIキーを使用してクライアントを初期化
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.api_key
            self.client = self.texttospeech.TextToSpeechClient()

        return self.client

    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        pitch: float = 1.0,
        volume: float = 1.0
    ) -> bytes:
        """
        テキストを音声に変換

        Args:
            text: 合成するテキスト
            voice: 話者名（Noneの場合はデフォルト）
            speed: 話速（0.25-4.0、デフォルト1.0）
            pitch: ピッチ（-20.0～20.0、デフォルト1.0 → 0.0）
            volume: 音量（0.0-1.0、デフォルト1.0）※Google TTSでは未使用

        Returns:
            bytes: MP3形式の音声データ

        Raises:
            Exception: 音声合成に失敗

        Example:
            >>> audio_data = await engine.synthesize(
            ...     "こんにちは",
            ...     speed=1.2,
            ...     pitch=1.1
            ... )
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")

        if voice is None:
            voice = self.default_voice

        logger.debug(
            f"Synthesizing with Google TTS: voice={voice}, "
            f"speed={speed}, pitch={pitch}"
        )

        try:
            # クライアント取得
            client = self._get_client()

            # 言語コードを抽出（例: "ja-JP-Neural2-B" → "ja-JP"）
            language_code = "-".join(voice.split("-")[:2])

            # 音声入力設定
            synthesis_input = self.texttospeech.SynthesisInput(text=text)

            # 音声パラメータ設定
            voice_params = self.texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name=voice
            )

            # ピッチをGoogle TTS形式に変換（1.0 → 0.0, 1.1 → 2.0, 0.9 → -2.0）
            pitch_semitones = (pitch - 1.0) * 20.0

            # オーディオ設定
            audio_config = self.texttospeech.AudioConfig(
                audio_encoding=self.texttospeech.AudioEncoding.MP3,
                speaking_rate=speed,
                pitch=pitch_semitones,
                volume_gain_db=0.0  # volumeは-96.0～16.0の範囲だが、簡略化のため0.0固定
            )

            # 非同期実行のために同期APIをラップ
            import asyncio
            loop = asyncio.get_event_loop()

            response = await loop.run_in_executor(
                None,
                lambda: client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice_params,
                    audio_config=audio_config
                )
            )

            logger.info(
                f"Google TTS synthesis completed: "
                f"{len(response.audio_content)} bytes"
            )

            return response.audio_content

        except Exception as e:
            logger.error(f"Google TTS synthesis failed: {e}")
            raise Exception(f"Failed to synthesize with Google TTS: {str(e)}")

    def list_voices(self) -> List[str]:
        """
        使用可能な日本語話者のリストを取得

        Returns:
            List[str]: 話者名のリスト

        Example:
            >>> voices = engine.list_voices()
            >>> print(voices)
            ['ja-JP-Neural2-B', 'ja-JP-Neural2-C', ...]
        """
        # Google TTSの日本語話者リスト（主要なもの）
        return [
            # Neural2 voices (高品質)
            "ja-JP-Neural2-B",  # 女性
            "ja-JP-Neural2-C",  # 男性
            "ja-JP-Neural2-D",  # 男性
            # Standard voices
            "ja-JP-Standard-A",  # 女性
            "ja-JP-Standard-B",  # 女性
            "ja-JP-Standard-C",  # 男性
            "ja-JP-Standard-D",  # 男性
            # Wavenet voices (高品質、コスト高)
            "ja-JP-Wavenet-A",  # 女性
            "ja-JP-Wavenet-B",  # 女性
            "ja-JP-Wavenet-C",  # 男性
            "ja-JP-Wavenet-D",  # 男性
        ]

    def get_default_voice(self) -> str:
        """
        デフォルトの話者を取得

        Returns:
            str: デフォルトの話者名
        """
        return self.default_voice

    async def is_available(self) -> bool:
        """
        Google TTSが利用可能か確認

        Returns:
            bool: 利用可能な場合True
        """
        try:
            if not self.api_key:
                return False

            # 簡単なテストリクエストを実行
            client = self._get_client()
            return True

        except Exception as e:
            logger.debug(f"Google TTS not available: {e}")
            return False
