"""
TTS統合管理システム

このモジュールは、複数のTTSエンジンを統合管理する機能を提供します。
edge_tts（デフォルト）、VOICEVOX、Google TTS、pyttsx3をサポートします。
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, List, Literal
from dataclasses import dataclass
from loguru import logger


@dataclass
class TTSConfig:
    """
    TTS設定

    Attributes:
        engine: 使用するエンジン
        voice: 話者名
        speed: 話速（0.5-2.0）
        pitch: ピッチ（0.5-2.0）
        volume: 音量（0.0-1.0）
    """
    engine: str = "edge_tts"
    voice: Optional[str] = None
    speed: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0


@dataclass
class TTSResult:
    """
    TTS結果

    Attributes:
        audio_path: 生成された音声ファイルパス
        text: 合成したテキスト
        engine: 使用したエンジン
        duration: 音声の長さ（秒）
    """
    audio_path: str
    text: str
    engine: str
    duration: Optional[float] = None


class TTSError(Exception):
    """TTS合成エラー"""
    pass


class TTSManager:
    """
    TTS統合管理クラス

    複数のTTSエンジンを管理し、テキストから音声を合成します。

    Attributes:
        output_dir: 音声出力先ディレクトリ
        default_engine: デフォルトのエンジン
        engines: ロード済みのエンジン

    Example:
        >>> tts_manager = TTSManager()
        >>> result = await tts_manager.synthesize(
        ...     text="こんにちは、世界",
        ...     engine="edge_tts"
        ... )
        >>> print(result.audio_path)
    """

    AVAILABLE_ENGINES = ["edge_tts", "voicevox", "google_tts", "pyttsx3"]

    def __init__(
        self,
        output_dir: str = "./output/tts",
        default_engine: str = "edge_tts"
    ):
        """
        Args:
            output_dir: 音声出力先ディレクトリ
            default_engine: デフォルトのエンジン
        """
        if default_engine not in self.AVAILABLE_ENGINES:
            logger.warning(
                f"Unknown engine: {default_engine}, "
                f"using edge_tts instead"
            )
            default_engine = "edge_tts"

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.default_engine = default_engine
        self.engines: Dict[str, any] = {}

        logger.info(
            f"TTSManager initialized: "
            f"default_engine={default_engine}"
        )

    def _get_engine(self, engine_name: str):
        """エンジンインスタンスを取得（遅延ロード）"""
        if engine_name in self.engines:
            return self.engines[engine_name]

        logger.info(f"Loading TTS engine: {engine_name}")

        try:
            if engine_name == "edge_tts":
                from app.tts.edge_tts_engine import EdgeTTSEngine
                self.engines[engine_name] = EdgeTTSEngine()

            elif engine_name == "voicevox":
                from app.tts.voicevox_engine import VoicevoxEngine
                self.engines[engine_name] = VoicevoxEngine()

            elif engine_name == "google_tts":
                from app.tts.google_tts_engine import GoogleTTSEngine
                self.engines[engine_name] = GoogleTTSEngine()

            elif engine_name == "pyttsx3":
                from app.tts.pyttsx3_engine import Pyttsx3Engine
                self.engines[engine_name] = Pyttsx3Engine()

            else:
                raise TTSError(f"Unknown engine: {engine_name}")

            logger.info(f"TTS engine loaded: {engine_name}")
            return self.engines[engine_name]

        except ImportError as e:
            logger.error(f"Failed to import engine {engine_name}: {e}")
            raise TTSError(
                f"Engine {engine_name} not available. "
                f"Please install required dependencies."
            )

        except Exception as e:
            logger.error(f"Failed to load engine {engine_name}: {e}")
            raise TTSError(f"Failed to load engine: {str(e)}")

    async def synthesize(
        self,
        text: str,
        engine: Optional[str] = None,
        config: Optional[TTSConfig] = None,
        output_name: Optional[str] = None
    ) -> TTSResult:
        """
        テキストを音声に変換

        Args:
            text: 合成するテキスト
            engine: 使用するエンジン（Noneの場合はデフォルト）
            config: TTS設定
            output_name: 出力ファイル名

        Returns:
            TTSResult: TTS結果

        Raises:
            TTSError: 音声合成に失敗

        Example:
            >>> config = TTSConfig(voice="ja-JP-NanamiNeural", speed=1.2)
            >>> result = await tts_manager.synthesize(
            ...     "こんにちは",
            ...     config=config
            ... )
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")

        if engine is None:
            engine = self.default_engine

        if config is None:
            config = TTSConfig(engine=engine)

        if output_name is None:
            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
            output_name = f"tts_{text_hash}.mp3"

        output_path = self.output_dir / output_name

        logger.info(
            f"Synthesizing TTS: engine={engine}, "
            f"text='{text[:50]}...'"
        )

        try:
            # エンジンを取得
            tts_engine = self._get_engine(engine)

            # 音声合成
            audio_data = await tts_engine.synthesize(
                text=text,
                voice=config.voice,
                speed=config.speed,
                pitch=config.pitch,
                volume=config.volume
            )

            # ファイルに保存
            output_path.write_bytes(audio_data)

            logger.info(
                f"TTS synthesis completed: {output_path} "
                f"(size={len(audio_data) / 1024:.2f}KB)"
            )

            return TTSResult(
                audio_path=str(output_path),
                text=text,
                engine=engine
            )

        except Exception as e:
            error_msg = str(e) if str(e) else repr(e)
            logger.error(f"TTS synthesis failed: {error_msg}", exc_info=True)
            raise TTSError(f"Failed to synthesize: {error_msg}")

    async def synthesize_batch(
        self,
        texts: List[str],
        engine: Optional[str] = None,
        config: Optional[TTSConfig] = None
    ) -> List[TTSResult]:
        """
        複数のテキストを一括音声合成

        Args:
            texts: テキストのリスト
            engine: 使用するエンジン
            config: TTS設定

        Returns:
            List[TTSResult]: TTS結果のリスト

        Example:
            >>> results = await tts_manager.synthesize_batch([
            ...     "こんにちは",
            ...     "さようなら"
            ... ])
        """
        logger.info(f"Starting batch TTS synthesis: {len(texts)} texts")

        tasks = [
            self.synthesize(text, engine, config)
            for text in texts
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 例外をログに記録
        tts_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    f"Failed to synthesize text {i}: {result}"
                )
            else:
                tts_results.append(result)

        logger.info(
            f"Batch TTS synthesis completed: "
            f"{len(tts_results)}/{len(texts)} successful"
        )

        return tts_results

    def list_voices(self, engine: Optional[str] = None) -> List[str]:
        """
        使用可能な話者のリストを取得

        Args:
            engine: エンジン名（Noneの場合はデフォルト）

        Returns:
            List[str]: 話者名のリスト

        Example:
            >>> voices = tts_manager.list_voices("edge_tts")
            >>> print(voices)
            ['ja-JP-NanamiNeural', 'ja-JP-KeitaNeural', ...]
        """
        if engine is None:
            engine = self.default_engine

        try:
            tts_engine = self._get_engine(engine)
            voices = tts_engine.list_voices()

            logger.debug(f"Available voices for {engine}: {len(voices)}")
            return voices

        except Exception as e:
            logger.error(f"Failed to list voices: {e}")
            return []

    def get_default_voice(self, engine: Optional[str] = None) -> str:
        """
        デフォルトの話者を取得

        Args:
            engine: エンジン名

        Returns:
            str: デフォルトの話者名
        """
        if engine is None:
            engine = self.default_engine

        try:
            tts_engine = self._get_engine(engine)
            return tts_engine.get_default_voice()

        except Exception as e:
            logger.error(f"Failed to get default voice: {e}")
            return ""

    def is_engine_available(self, engine: str) -> bool:
        """
        エンジンが利用可能か確認

        Args:
            engine: エンジン名

        Returns:
            bool: 利用可能な場合True
        """
        try:
            self._get_engine(engine)
            return True

        except Exception:
            return False

    def get_available_engines(self) -> List[str]:
        """
        利用可能なエンジンのリストを取得

        Returns:
            List[str]: 利用可能なエンジン名のリスト
        """
        available = []

        for engine in self.AVAILABLE_ENGINES:
            if self.is_engine_available(engine):
                available.append(engine)

        logger.info(f"Available TTS engines: {available}")
        return available
