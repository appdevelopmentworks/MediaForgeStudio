"""
音声連結機能

このモジュールは、複数の音声ファイルを連結する機能を提供します。
FFmpegを使用して高速かつ高品質な音声連結を実現します。
"""

import asyncio
import subprocess
from pathlib import Path
from typing import List, Optional, Callable
from dataclasses import dataclass
from loguru import logger


@dataclass
class AudioMergeResult:
    """
    音声連結結果

    Attributes:
        output_path: 出力ファイルパス
        audio_count: 連結した音声数
        duration: 総再生時間（秒）
        filesize: ファイルサイズ（バイト）
    """
    output_path: str
    audio_count: int
    duration: Optional[float] = None
    filesize: Optional[int] = None


class AudioMergeError(Exception):
    """音声連結エラー"""
    pass


class AudioMerger:
    """
    音声連結クラス

    複数の音声ファイルを1つに連結します。

    Attributes:
        output_dir: 出力先ディレクトリ
        temp_dir: 一時ファイルディレクトリ

    Example:
        >>> merger = AudioMerger()
        >>> result = await merger.merge_audios(
        ...     audio_paths=["audio1.mp3", "audio2.mp3"],
        ...     output_name="merged.mp3"
        ... )
    """

    def __init__(
        self,
        output_dir: str = "./output/merged",
        temp_dir: str = "./temp"
    ):
        """
        Args:
            output_dir: 出力先ディレクトリ
            temp_dir: 一時ファイルディレクトリ
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"AudioMerger initialized: "
            f"output_dir={self.output_dir}"
        )

    async def merge_audios(
        self,
        audio_paths: List[str],
        output_name: str,
        format: str = "mp3",
        bitrate: str = "192k",
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> AudioMergeResult:
        """
        複数の音声を連結

        Args:
            audio_paths: 音声ファイルパスのリスト
            output_name: 出力ファイル名
            format: 出力フォーマット（mp3, wav, aac）
            bitrate: ビットレート（例: 128k, 192k, 320k）
            progress_callback: 進捗コールバック

        Returns:
            AudioMergeResult: 連結結果

        Raises:
            AudioMergeError: 連結に失敗

        Example:
            >>> result = await merger.merge_audios(
            ...     ["audio1.mp3", "audio2.mp3"],
            ...     "output.mp3"
            ... )
        """
        if not audio_paths:
            raise ValueError("Audio paths cannot be empty")

        if len(audio_paths) < 2:
            raise ValueError("At least 2 audios are required for merging")

        # 全ファイルの存在確認
        for path in audio_paths:
            if not Path(path).exists():
                raise FileNotFoundError(f"Audio file not found: {path}")

        output_path = self.output_dir / output_name

        logger.info(
            f"Merging {len(audio_paths)} audios -> {output_path} "
            f"(format={format}, bitrate={bitrate})"
        )

        try:
            # ファイルリストを作成
            filelist_path = self.temp_dir / "audio_filelist.txt"

            with open(filelist_path, "w", encoding="utf-8") as f:
                for audio_path in audio_paths:
                    abs_path = Path(audio_path).resolve()
                    f.write(f"file '{abs_path}'\n")

            logger.debug(f"Created audio filelist: {filelist_path}")

            # FFmpegコマンド
            command = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", str(filelist_path),
                "-c:a", self._get_audio_codec(format),
                "-b:a", bitrate,
                "-y",
                str(output_path)
            ]

            # 実行
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=600
                )
            )

            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise AudioMergeError(f"FFmpeg failed: {result.stderr}")

            # ファイルリストを削除
            filelist_path.unlink()

            # 進捗コールバック
            if progress_callback:
                progress_callback(100.0)

            # 結果を返す
            merge_result = AudioMergeResult(
                output_path=str(output_path),
                audio_count=len(audio_paths),
                filesize=output_path.stat().st_size if output_path.exists() else None
            )

            logger.info(
                f"Audio merge completed: {merge_result.output_path} "
                f"({merge_result.audio_count} audios)"
            )

            return merge_result

        except Exception as e:
            logger.error(f"Audio merge failed: {e}")
            raise AudioMergeError(f"Failed to merge audios: {str(e)}")

    async def mix_audios(
        self,
        audio_paths: List[str],
        output_name: str,
        format: str = "mp3",
        bitrate: str = "192k",
        volumes: Optional[List[float]] = None
    ) -> AudioMergeResult:
        """
        複数の音声をミックス（同時再生）

        Args:
            audio_paths: 音声ファイルパスのリスト
            output_name: 出力ファイル名
            format: 出力フォーマット
            bitrate: ビットレート
            volumes: 各音声の音量（0.0-1.0、Noneの場合は均等）

        Returns:
            AudioMergeResult: ミックス結果

        Raises:
            AudioMergeError: ミックスに失敗

        Example:
            >>> result = await merger.mix_audios(
            ...     ["voice.mp3", "bgm.mp3"],
            ...     "mixed.mp3",
            ...     volumes=[1.0, 0.3]  # BGMを小さく
            ... )
        """
        if not audio_paths:
            raise ValueError("Audio paths cannot be empty")

        # 全ファイルの存在確認
        for path in audio_paths:
            if not Path(path).exists():
                raise FileNotFoundError(f"Audio file not found: {path}")

        output_path = self.output_dir / output_name

        # 音量の設定
        if volumes is None:
            volumes = [1.0 / len(audio_paths)] * len(audio_paths)
        elif len(volumes) != len(audio_paths):
            raise ValueError("volumes length must match audio_paths length")

        logger.info(
            f"Mixing {len(audio_paths)} audios -> {output_path} "
            f"(volumes={volumes})"
        )

        try:
            # 入力ファイル指定
            inputs = []
            for path in audio_paths:
                inputs.extend(["-i", str(Path(path).resolve())])

            # amix filterを構築
            filter_inputs = ""
            for i, vol in enumerate(volumes):
                filter_inputs += f"[{i}:a]volume={vol}[a{i}];"

            # amixで全ての音声をミックス
            amix_inputs = "".join([f"[a{i}]" for i in range(len(audio_paths))])
            filter_complex = filter_inputs + f"{amix_inputs}amix=inputs={len(audio_paths)}:duration=longest[out]"

            # FFmpegコマンド
            command = [
                "ffmpeg",
                *inputs,
                "-filter_complex", filter_complex,
                "-map", "[out]",
                "-c:a", self._get_audio_codec(format),
                "-b:a", bitrate,
                "-y",
                str(output_path)
            ]

            # 実行
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=600
                )
            )

            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise AudioMergeError(f"FFmpeg failed: {result.stderr}")

            # 結果を返す
            merge_result = AudioMergeResult(
                output_path=str(output_path),
                audio_count=len(audio_paths),
                filesize=output_path.stat().st_size if output_path.exists() else None
            )

            logger.info(
                f"Audio mix completed: {merge_result.output_path}"
            )

            return merge_result

        except Exception as e:
            logger.error(f"Audio mix failed: {e}")
            raise AudioMergeError(f"Failed to mix audios: {str(e)}")

    async def adjust_audio_speed(
        self,
        audio_path: str,
        output_name: str,
        speed: float = 1.0
    ) -> str:
        """
        音声の再生速度を調整

        Args:
            audio_path: 音声ファイルパス
            output_name: 出力ファイル名
            speed: 再生速度（0.5-2.0、1.0=通常速度）

        Returns:
            str: 出力ファイルパス

        Raises:
            AudioMergeError: 速度調整に失敗

        Example:
            >>> output = await merger.adjust_audio_speed(
            ...     "audio.mp3",
            ...     "fast.mp3",
            ...     speed=1.5
            ... )
        """
        audio_path_obj = Path(audio_path)

        if not audio_path_obj.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        if speed <= 0 or speed > 2.0:
            raise ValueError("Speed must be between 0 and 2.0")

        output_path = self.output_dir / output_name

        logger.info(
            f"Adjusting audio speed: {audio_path} -> {output_path} "
            f"(speed={speed})"
        )

        try:
            # asetrate + atempo filter
            command = [
                "ffmpeg",
                "-i", str(audio_path_obj),
                "-filter:a", f"atempo={speed}",
                "-y",
                str(output_path)
            ]

            # 実行
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
            )

            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise AudioMergeError(f"Failed to adjust speed: {result.stderr}")

            logger.info(f"Audio speed adjusted: {output_path}")

            return str(output_path)

        except Exception as e:
            logger.error(f"Failed to adjust audio speed: {e}")
            raise AudioMergeError(f"Failed to adjust speed: {str(e)}")

    def _get_audio_codec(self, format: str) -> str:
        """
        フォーマットに応じたオーディオコーデックを返す

        Args:
            format: フォーマット（mp3, wav, aac）

        Returns:
            str: FFmpegコーデック名
        """
        codec_map = {
            "mp3": "libmp3lame",
            "wav": "pcm_s16le",
            "aac": "aac",
            "m4a": "aac",
            "ogg": "libvorbis"
        }

        return codec_map.get(format.lower(), "libmp3lame")

    def get_audio_info(self, audio_path: str) -> dict:
        """
        音声情報を取得

        Args:
            audio_path: 音声ファイルパス

        Returns:
            dict: 音声情報

        Raises:
            AudioMergeError: 情報取得に失敗
        """
        try:
            command = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                audio_path
            ]

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                raise AudioMergeError("Failed to get audio info")

            import json
            info = json.loads(result.stdout)

            return info

        except Exception as e:
            logger.error(f"Error getting audio info: {e}")
            raise AudioMergeError(f"Failed to get audio info: {str(e)}")
