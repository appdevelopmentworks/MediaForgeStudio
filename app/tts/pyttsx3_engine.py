"""
pyttsx3 オフライン TTS エンジン

このモジュールは、pyttsx3を使用したオフライン音声合成機能を提供します。
インターネット接続不要で、システムのTTSエンジンを使用します。
"""

import asyncio
import io
from typing import Optional, List
from pathlib import Path
from loguru import logger


class Pyttsx3Engine:
    """
    pyttsx3 オフライン TTS エンジン

    pyttsx3を使用してシステムのTTSエンジンで音声合成を行います。
    インターネット接続不要ですが、音質は他のエンジンより劣ります。

    Attributes:
        engine: pyttsx3エンジンインスタンス
        default_voice_index: デフォルトの話者インデックス

    Example:
        >>> engine = Pyttsx3Engine()
        >>> audio_data = await engine.synthesize(
        ...     text="こんにちは、世界"
        ... )
    """

    def __init__(self, default_voice_index: int = 0):
        """
        Args:
            default_voice_index: デフォルトの話者インデックス（0から始まる）
        """
        self.default_voice_index = default_voice_index
        self.engine = None

        # pyttsx3が利用可能か確認
        try:
            import pyttsx3
            self.pyttsx3 = pyttsx3
            logger.info(
                f"Pyttsx3Engine initialized: "
                f"voice_index={default_voice_index}"
            )

        except ImportError:
            logger.error("pyttsx3 package not installed")
            raise ImportError(
                "pyttsx3 is not installed. "
                "Install it with: pip install pyttsx3"
            )

    def _get_engine(self):
        """pyttsx3エンジンを取得（遅延初期化）"""
        if self.engine is None:
            self.engine = self.pyttsx3.init()

            # 利用可能な音声をログ出力
            voices = self.engine.getProperty('voices')
            logger.debug(f"Available pyttsx3 voices: {len(voices)}")
            for i, voice in enumerate(voices):
                logger.debug(f"  [{i}] {voice.name} ({voice.languages})")

        return self.engine

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
            voice: 話者インデックス（文字列、例: "0", "1"）
            speed: 話速（0.5-2.0、デフォルト1.0）
            pitch: ピッチ（pyttsx3では未サポート）
            volume: 音量（0.0-1.0、デフォルト1.0）

        Returns:
            bytes: WAV形式の音声データ

        Raises:
            Exception: 音声合成に失敗

        Example:
            >>> audio_data = await engine.synthesize(
            ...     "こんにちは",
            ...     speed=1.2,
            ...     volume=0.8
            ... )
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")

        logger.debug(
            f"Synthesizing with pyttsx3: voice={voice}, "
            f"speed={speed}, volume={volume}"
        )

        try:
            # 非同期実行用のラッパー
            loop = asyncio.get_event_loop()
            audio_data = await loop.run_in_executor(
                None,
                self._synthesize_sync,
                text,
                voice,
                speed,
                volume
            )

            logger.info(
                f"pyttsx3 synthesis completed: {len(audio_data)} bytes"
            )

            return audio_data

        except Exception as e:
            logger.error(f"pyttsx3 synthesis failed: {e}")
            raise Exception(f"Failed to synthesize with pyttsx3: {str(e)}")

    def _synthesize_sync(
        self,
        text: str,
        voice: Optional[str],
        speed: float,
        volume: float
    ) -> bytes:
        """
        同期的に音声合成を実行

        Args:
            text: 合成するテキスト
            voice: 話者インデックス（文字列）
            speed: 話速
            volume: 音量

        Returns:
            bytes: WAV形式の音声データ
        """
        import tempfile

        engine = self._get_engine()

        # 音声設定
        voices = engine.getProperty('voices')

        # 話者を設定
        if voice is not None:
            try:
                voice_index = int(voice)
                if 0 <= voice_index < len(voices):
                    engine.setProperty('voice', voices[voice_index].id)
                else:
                    logger.warning(
                        f"Invalid voice index: {voice_index}, "
                        f"using default"
                    )
            except ValueError:
                logger.warning(f"Invalid voice format: {voice}, using default")
        else:
            # デフォルトの話者を設定
            if self.default_voice_index < len(voices):
                engine.setProperty(
                    'voice',
                    voices[self.default_voice_index].id
                )

        # 話速を設定（pyttsx3は words per minute で設定）
        # デフォルトは200 WPM程度
        rate = engine.getProperty('rate')
        engine.setProperty('rate', int(rate * speed))

        # 音量を設定（0.0-1.0）
        engine.setProperty('volume', volume)

        # 一時ファイルに保存
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # 音声合成してファイルに保存
            engine.save_to_file(text, tmp_path)
            engine.runAndWait()

            # ファイルから読み込み
            with open(tmp_path, 'rb') as f:
                audio_data = f.read()

            return audio_data

        finally:
            # 一時ファイルを削除
            Path(tmp_path).unlink(missing_ok=True)

    def list_voices(self) -> List[str]:
        """
        使用可能な話者のリストを取得

        Returns:
            List[str]: 話者のインデックス番号と名前のリスト

        Example:
            >>> voices = engine.list_voices()
            >>> print(voices)
            ['0: Microsoft Zira', '1: Microsoft David', ...]
        """
        try:
            engine = self._get_engine()
            voices = engine.getProperty('voices')

            voice_list = []
            for i, voice in enumerate(voices):
                voice_list.append(f"{i}: {voice.name}")

            return voice_list

        except Exception as e:
            logger.error(f"Failed to list voices: {e}")
            return []

    def get_default_voice(self) -> str:
        """
        デフォルトの話者を取得

        Returns:
            str: デフォルトの話者インデックス（文字列）
        """
        return str(self.default_voice_index)

    async def is_available(self) -> bool:
        """
        pyttsx3が利用可能か確認

        Returns:
            bool: 利用可能な場合True
        """
        try:
            engine = self._get_engine()
            voices = engine.getProperty('voices')
            return len(voices) > 0

        except Exception as e:
            logger.debug(f"pyttsx3 not available: {e}")
            return False
