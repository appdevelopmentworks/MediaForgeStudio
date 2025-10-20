"""
Microsoft Edge TTS エンジン

このモジュールは、Microsoft Edge TTSを使用した音声合成機能を提供します。
無料で利用でき、自然な日本語音声を生成できます。
"""

import asyncio
from typing import Optional, List
from loguru import logger


class EdgeTTSEngine:
    """
    Microsoft Edge TTS エンジン

    edge-ttsを使用して音声合成を行います。

    Attributes:
        default_voice: デフォルトの話者

    Example:
        >>> engine = EdgeTTSEngine()
        >>> audio_data = await engine.synthesize(
        ...     text="こんにちは、世界",
        ...     voice="ja-JP-NanamiNeural"
        ... )
    """

    def __init__(self, default_voice: str = "ja-JP-NanamiNeural"):
        """
        Args:
            default_voice: デフォルトの話者
        """
        self.default_voice = default_voice

        # edge-ttsが利用可能か確認
        try:
            import edge_tts
            self.edge_tts = edge_tts
            logger.info(f"EdgeTTSEngine initialized: voice={default_voice}")

        except ImportError:
            logger.error("edge-tts package not installed")
            raise ImportError(
                "edge-tts is not installed. "
                "Install it with: pip install edge-tts"
            )

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
            speed: 話速（0.5-2.0、デフォルト1.0）
            pitch: ピッチ（0.5-2.0、デフォルト1.0）
            volume: 音量（0.0-1.0、デフォルト1.0）

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
            f"Synthesizing with Edge TTS: voice={voice}, "
            f"speed={speed}, pitch={pitch}, volume={volume}"
        )

        try:
            # パラメータを Edge TTS 形式に変換
            rate = self._convert_speed(speed)
            pitch_str = self._convert_pitch(pitch)
            volume_str = self._convert_volume(volume)

            # Communicateオブジェクトを作成
            communicate = self.edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=rate,
                pitch=pitch_str,
                volume=volume_str
            )

            # 音声データを取得
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]

            if not audio_data:
                raise Exception("No audio data received from Edge TTS")

            logger.debug(
                f"Edge TTS synthesis completed: {len(audio_data)} bytes"
            )

            return audio_data

        except Exception as e:
            logger.error(f"Edge TTS synthesis failed: {e}")
            raise Exception(f"Failed to synthesize with Edge TTS: {str(e)}")

    def _convert_speed(self, speed: float) -> str:
        """
        話速をEdge TTS形式に変換

        Args:
            speed: 話速（0.5-2.0）

        Returns:
            str: Edge TTS形式の話速（例: "+20%", "-30%"）
        """
        # speedを1.0基準のパーセンテージに変換
        percent = int((speed - 1.0) * 100)

        # -50% ~ +100% の範囲に制限
        percent = max(-50, min(100, percent))

        return f"{percent:+d}%"

    def _convert_pitch(self, pitch: float) -> str:
        """
        ピッチをEdge TTS形式に変換

        Args:
            pitch: ピッチ（0.5-2.0）

        Returns:
            str: Edge TTS形式のピッチ（例: "+5Hz", "-10Hz"）
        """
        # pitchを周波数変化に変換（簡易的な変換）
        # 1.0 = 0Hz, 2.0 = +50Hz, 0.5 = -50Hz
        hz = int((pitch - 1.0) * 50)

        # -50Hz ~ +50Hz の範囲に制限
        hz = max(-50, min(50, hz))

        return f"{hz:+d}Hz"

    def _convert_volume(self, volume: float) -> str:
        """
        音量をEdge TTS形式に変換

        Args:
            volume: 音量（0.0-1.0）

        Returns:
            str: Edge TTS形式の音量（例: "+0%", "-20%"）
        """
        # volumeを1.0基準のパーセンテージに変換
        percent = int((volume - 1.0) * 100)

        # -100% ~ +0% の範囲に制限（Edge TTSは音量増加をサポートしない）
        percent = max(-100, min(0, percent))

        return f"{percent:+d}%"

    def list_voices(self) -> List[str]:
        """
        利用可能な日本語話者のリストを取得

        Returns:
            List[str]: 話者名のリスト

        Example:
            >>> voices = engine.list_voices()
            >>> print(voices)
            ['ja-JP-NanamiNeural', 'ja-JP-KeitaNeural', ...]
        """
        # 日本語話者のリスト（2024年時点）
        voices = [
            "ja-JP-NanamiNeural",      # 女性、明るい
            "ja-JP-KeitaNeural",       # 男性、落ち着いた
            "ja-JP-AoiNeural",         # 女性、若い
            "ja-JP-DaichiNeural",      # 男性、若い
            "ja-JP-MayuNeural",        # 女性、柔らかい
            "ja-JP-NaokiNeural",       # 男性、力強い
            "ja-JP-ShioriNeural",      # 女性、優しい
        ]

        logger.debug(f"Available voices: {len(voices)}")
        return voices

    async def get_all_voices(self) -> List[dict]:
        """
        すべての利用可能な話者情報を取得（全言語）

        Returns:
            List[dict]: 話者情報のリスト

        Example:
            >>> voices = await engine.get_all_voices()
            >>> for voice in voices:
            ...     print(f"{voice['Name']}: {voice['Locale']}")
        """
        try:
            voices = await self.edge_tts.list_voices()
            logger.debug(f"Retrieved all voices: {len(voices)} total")
            return voices

        except Exception as e:
            logger.error(f"Failed to get all voices: {e}")
            return []

    async def get_voices_by_language(self, language_code: str) -> List[dict]:
        """
        特定の言語の話者情報を取得

        Args:
            language_code: 言語コード（例: "ja-JP", "en-US"）

        Returns:
            List[dict]: 話者情報のリスト

        Example:
            >>> voices = await engine.get_voices_by_language("ja-JP")
        """
        try:
            all_voices = await self.get_all_voices()
            filtered_voices = [
                voice for voice in all_voices
                if voice.get("Locale", "").startswith(language_code)
            ]

            logger.debug(
                f"Voices for {language_code}: {len(filtered_voices)}"
            )
            return filtered_voices

        except Exception as e:
            logger.error(f"Failed to get voices by language: {e}")
            return []

    def get_default_voice(self) -> str:
        """
        デフォルトの話者を取得

        Returns:
            str: デフォルトの話者名
        """
        return self.default_voice

    def set_default_voice(self, voice: str) -> None:
        """
        デフォルトの話者を設定

        Args:
            voice: 話者名
        """
        self.default_voice = voice
        logger.info(f"Default voice set to: {voice}")

    async def test_synthesis(self) -> bool:
        """
        音声合成のテスト

        Returns:
            bool: 成功した場合True

        Example:
            >>> success = await engine.test_synthesis()
            >>> if success:
            ...     print("Edge TTS is working!")
        """
        try:
            test_text = "これはテストです。"
            audio_data = await self.synthesize(test_text)

            if audio_data and len(audio_data) > 0:
                logger.info("Edge TTS test synthesis successful")
                return True
            else:
                logger.error("Edge TTS test synthesis returned empty data")
                return False

        except Exception as e:
            logger.error(f"Edge TTS test synthesis failed: {e}")
            return False
