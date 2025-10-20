"""
Whisper文字起こし機能

このモジュールは、OpenAI Whisperを使用して音声ファイルを文字起こしする機能を提供します。
"""

import asyncio
from pathlib import Path
from typing import Optional, Callable, Literal
from dataclasses import dataclass
from loguru import logger
import warnings

# Whisperの警告を抑制
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)


@dataclass
class TranscriptionResult:
    """
    文字起こし結果

    Attributes:
        text: 文字起こしされたテキスト
        language: 検出された言語コード
        segments: セグメント情報のリスト
        duration: 音声の長さ（秒）
    """
    text: str
    language: str
    segments: list[dict]
    duration: float


class TranscriptionError(Exception):
    """文字起こしエラー"""
    pass


class WhisperNotAvailableError(TranscriptionError):
    """Whisperが利用できない"""
    pass


class WhisperTranscriber:
    """
    Whisper文字起こしクラス

    OpenAI Whisperモデルを使用して音声ファイルを文字起こしします。

    Attributes:
        model_size: 使用するモデルサイズ
        device: 使用するデバイス（cpu/cuda）
        model: ロード済みのWhisperモデル

    Example:
        >>> transcriber = WhisperTranscriber(model_size="base")
        >>> result = await transcriber.transcribe("audio.mp3")
        >>> print(result.text)
    """

    AVAILABLE_MODELS = ["tiny", "base", "small", "medium", "large"]

    def __init__(
        self,
        model_size: Literal["tiny", "base", "small", "medium", "large"] = "base",
        device: Optional[str] = None,
        download_root: Optional[str] = None
    ):
        """
        Args:
            model_size: モデルサイズ（tiny, base, small, medium, large）
            device: 使用デバイス（Noneの場合は自動選択）
            download_root: モデルダウンロード先ディレクトリ
        """
        if model_size not in self.AVAILABLE_MODELS:
            raise ValueError(
                f"Invalid model size: {model_size}. "
                f"Must be one of {self.AVAILABLE_MODELS}"
            )

        self.model_size = model_size
        self.device = device
        self.download_root = download_root
        self.model = None

        logger.info(f"WhisperTranscriber initialized: model={model_size}")

    def _load_model(self):
        """Whisperモデルをロード"""
        if self.model is not None:
            return

        try:
            import whisper

            logger.info(f"Loading Whisper model: {self.model_size}")

            # モデルをロード
            self.model = whisper.load_model(
                self.model_size,
                device=self.device,
                download_root=self.download_root
            )

            logger.info(f"Whisper model loaded: {self.model_size}")

        except ImportError:
            logger.error("Whisper package not installed")
            raise WhisperNotAvailableError(
                "OpenAI Whisper is not installed. "
                "Install it with: pip install openai-whisper"
            )

        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise WhisperNotAvailableError(
                f"Failed to load Whisper model: {str(e)}"
            )

    async def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        task: Literal["transcribe", "translate"] = "transcribe",
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> TranscriptionResult:
        """
        音声ファイルを文字起こし

        Args:
            audio_path: 音声ファイルパス
            language: 言語コード（Noneの場合は自動検出）
            task: タスク（transcribe=文字起こし, translate=英語翻訳）
            progress_callback: 進捗コールバック

        Returns:
            TranscriptionResult: 文字起こし結果

        Raises:
            TranscriptionError: 文字起こしに失敗
            FileNotFoundError: 音声ファイルが見つからない

        Example:
            >>> result = await transcriber.transcribe(
            ...     "audio.mp3",
            ...     language="ja"
            ... )
            >>> print(result.text)
        """
        audio_path_obj = Path(audio_path)

        # ファイル存在確認
        if not audio_path_obj.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(
            f"Starting transcription: {audio_path} "
            f"(language={language}, task={task})"
        )

        try:
            # モデルをロード
            self._load_model()

            # 進捗コールバック
            if progress_callback:
                progress_callback(10.0)

            # 文字起こしオプション
            options = {
                "task": task,
                "verbose": False
            }

            if language:
                options["language"] = language

            # 非同期で文字起こし実行
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.model.transcribe(str(audio_path_obj), **options)
            )

            # 進捗コールバック
            if progress_callback:
                progress_callback(100.0)

            # 結果を整形
            transcription_result = TranscriptionResult(
                text=result["text"].strip(),
                language=result.get("language", language or "unknown"),
                segments=result.get("segments", []),
                duration=result.get("segments", [{}])[-1].get("end", 0.0)
                if result.get("segments") else 0.0
            )

            logger.info(
                f"Transcription completed: "
                f"language={transcription_result.language}, "
                f"length={len(transcription_result.text)} chars"
            )

            return transcription_result

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise TranscriptionError(f"Failed to transcribe audio: {str(e)}")

    async def transcribe_batch(
        self,
        audio_paths: list[str],
        language: Optional[str] = None,
        task: Literal["transcribe", "translate"] = "transcribe"
    ) -> list[TranscriptionResult]:
        """
        複数の音声ファイルを一括文字起こし

        Args:
            audio_paths: 音声ファイルパスのリスト
            language: 言語コード
            task: タスク

        Returns:
            list[TranscriptionResult]: 文字起こし結果のリスト

        Example:
            >>> results = await transcriber.transcribe_batch([
            ...     "audio1.mp3",
            ...     "audio2.mp3"
            ... ])
        """
        logger.info(
            f"Starting batch transcription: {len(audio_paths)} files"
        )

        tasks = [
            self.transcribe(audio_path, language, task)
            for audio_path in audio_paths
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 例外をログに記録
        transcription_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    f"Failed to transcribe {audio_paths[i]}: {result}"
                )
            else:
                transcription_results.append(result)

        logger.info(
            f"Batch transcription completed: "
            f"{len(transcription_results)}/{len(audio_paths)} successful"
        )

        return transcription_results

    def get_available_languages(self) -> list[str]:
        """
        Whisperがサポートする言語のリストを取得

        Returns:
            list[str]: 言語コードのリスト
        """
        try:
            import whisper

            # Whisperがサポートする言語
            languages = list(whisper.tokenizer.LANGUAGES.keys())
            return sorted(languages)

        except Exception as e:
            logger.error(f"Failed to get languages: {e}")
            return []

    def detect_language(self, audio_path: str) -> str:
        """
        音声ファイルの言語を検出

        Args:
            audio_path: 音声ファイルパス

        Returns:
            str: 検出された言語コード

        Raises:
            TranscriptionError: 言語検出に失敗
        """
        try:
            # モデルをロード
            self._load_model()

            import whisper

            # 音声をロード
            audio = whisper.load_audio(audio_path)
            audio = whisper.pad_or_trim(audio)

            # メルスペクトログラムを作成
            mel = whisper.log_mel_spectrogram(audio).to(self.model.device)

            # 言語を検出
            _, probs = self.model.detect_language(mel)
            detected_language = max(probs, key=probs.get)

            logger.info(
                f"Language detected: {detected_language} "
                f"(confidence={probs[detected_language]:.2%})"
            )

            return detected_language

        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            raise TranscriptionError(
                f"Failed to detect language: {str(e)}"
            )

    def unload_model(self):
        """モデルをメモリから解放"""
        if self.model is not None:
            logger.info("Unloading Whisper model")
            del self.model
            self.model = None

            # ガベージコレクション
            import gc
            gc.collect()

            # CUDAメモリをクリア（CUDAが利用可能な場合）
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass

            logger.info("Whisper model unloaded")
