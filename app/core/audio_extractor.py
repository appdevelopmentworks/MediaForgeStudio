"""
音声抽出機能

このモジュールは、動画ファイルから音声を抽出する機能を提供します。
FFmpegを使用してMP3形式で音声を抽出します。
"""

import asyncio
import subprocess
from pathlib import Path
from typing import Optional, Callable
from loguru import logger


class AudioExtractionError(Exception):
    """音声抽出エラー"""
    pass


class FFmpegNotFoundError(AudioExtractionError):
    """FFmpegが見つからない"""
    pass


class AudioExtractor:
    """
    音声抽出クラス

    動画ファイルから音声を抽出し、MP3形式で保存します。

    Attributes:
        output_dir: 出力先ディレクトリ
        default_bitrate: デフォルトビットレート

    Example:
        >>> extractor = AudioExtractor(output_dir="./output/audios")
        >>> result = await extractor.extract_audio(
        ...     video_path="video.mp4",
        ...     output_name="audio.mp3"
        ... )
    """

    def __init__(
        self,
        output_dir: str = "./output/audios",
        default_bitrate: str = "192k"
    ):
        """
        Args:
            output_dir: 音声出力先ディレクトリ
            default_bitrate: デフォルトビットレート（例: 128k, 192k, 320k）
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.default_bitrate = default_bitrate

        # FFmpegの存在確認
        if not self.check_ffmpeg():
            raise FFmpegNotFoundError(
                "FFmpeg not found. Please install FFmpeg and add it to PATH."
            )

        logger.info(
            f"AudioExtractor initialized: "
            f"output_dir={self.output_dir}, bitrate={default_bitrate}"
        )

    def check_ffmpeg(self) -> bool:
        """
        FFmpegがインストールされているか確認

        Returns:
            bool: FFmpegが利用可能な場合True
        """
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=False,  # バイナリモードで実行（エンコーディングエラー回避）
                timeout=5
            )
            if result.returncode == 0:
                logger.debug("FFmpeg found and available")
                return True
            return False

        except FileNotFoundError:
            logger.error("FFmpeg not found in PATH")
            return False

        except subprocess.TimeoutExpired:
            logger.error("FFmpeg check timeout")
            return False

        except Exception as e:
            logger.error(f"Error checking FFmpeg: {e}")
            return False

    async def extract_audio(
        self,
        video_path: str,
        output_name: Optional[str] = None,
        bitrate: Optional[str] = None,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> str:
        """
        動画から音声を抽出

        Args:
            video_path: 動画ファイルパス
            output_name: 出力ファイル名（Noneの場合は動画名.mp3）
            bitrate: ビットレート（Noneの場合はdefault_bitrateを使用）
            progress_callback: 進捗コールバック（0.0-100.0）

        Returns:
            str: 抽出された音声ファイルパス

        Raises:
            AudioExtractionError: 音声抽出に失敗
            FileNotFoundError: 動画ファイルが見つからない

        Example:
            >>> audio_path = await extractor.extract_audio(
            ...     "video.mp4",
            ...     output_name="my_audio.mp3",
            ...     bitrate="320k"
            ... )
        """
        video_path_obj = Path(video_path)

        # 動画ファイルの存在確認
        if not video_path_obj.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # 出力ファイル名の決定
        if output_name is None:
            output_name = f"{video_path_obj.stem}.mp3"

        output_path = self.output_dir / output_name

        # ビットレートの決定
        if bitrate is None:
            bitrate = self.default_bitrate

        logger.info(
            f"Extracting audio: {video_path} -> {output_path} "
            f"(bitrate={bitrate})"
        )

        try:
            # FFmpegコマンドを構築
            command = [
                "ffmpeg",
                "-i", str(video_path_obj),
                "-vn",  # 映像なし
                "-acodec", "libmp3lame",  # MP3エンコーダー
                "-ab", bitrate,  # ビットレート
                "-ar", "44100",  # サンプリングレート
                "-y",  # 上書き許可
                str(output_path)
            ]

            # 非同期でFFmpegを実行
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    command,
                    capture_output=True,
                    text=False,  # バイナリモードで実行（エンコーディングエラー回避）
                    timeout=300  # 5分タイムアウト
                )
            )

            if result.returncode != 0:
                # エラーメッセージを安全にデコード
                try:
                    stderr_msg = result.stderr.decode('utf-8', errors='ignore')
                except:
                    stderr_msg = "Unable to decode error message"

                logger.error(f"FFmpeg error: {stderr_msg}")
                raise AudioExtractionError(
                    f"Failed to extract audio: {stderr_msg}"
                )

            # 出力ファイルの存在確認
            if not output_path.exists():
                raise AudioExtractionError(
                    "Audio extraction completed but file not found"
                )

            file_size = output_path.stat().st_size / (1024 * 1024)  # MB
            logger.info(
                f"Audio extraction completed: {output_path} "
                f"(size={file_size:.2f}MB)"
            )

            # 進捗コールバック（完了）
            if progress_callback:
                progress_callback(100.0)

            return str(output_path)

        except subprocess.TimeoutExpired:
            logger.error("FFmpeg timeout during audio extraction")
            raise AudioExtractionError("Audio extraction timeout")

        except Exception as e:
            logger.error(f"Unexpected error during audio extraction: {e}")
            raise AudioExtractionError(f"Failed to extract audio: {str(e)}")

    async def extract_audio_batch(
        self,
        video_paths: list[str],
        bitrate: Optional[str] = None
    ) -> list[str]:
        """
        複数の動画から音声を一括抽出

        Args:
            video_paths: 動画ファイルパスのリスト
            bitrate: ビットレート

        Returns:
            list[str]: 抽出された音声ファイルパスのリスト

        Example:
            >>> audio_paths = await extractor.extract_audio_batch([
            ...     "video1.mp4",
            ...     "video2.mp4"
            ... ])
        """
        logger.info(f"Starting batch audio extraction: {len(video_paths)} files")

        tasks = [
            self.extract_audio(video_path, bitrate=bitrate)
            for video_path in video_paths
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 例外をログに記録
        audio_paths = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    f"Failed to extract audio from {video_paths[i]}: {result}"
                )
            else:
                audio_paths.append(result)

        logger.info(
            f"Batch audio extraction completed: "
            f"{len(audio_paths)}/{len(video_paths)} successful"
        )

        return audio_paths

    def get_audio_info(self, audio_path: str) -> dict:
        """
        音声ファイルの情報を取得

        Args:
            audio_path: 音声ファイルパス

        Returns:
            dict: 音声情報（duration, bitrate, sample_rate）

        Raises:
            AudioExtractionError: 情報取得に失敗
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
                text=False,  # バイナリモードで実行（エンコーディングエラー回避）
                timeout=10
            )

            if result.returncode != 0:
                raise AudioExtractionError("Failed to get audio info")

            import json
            # stdoutをデコード
            stdout_str = result.stdout.decode('utf-8', errors='ignore')
            info = json.loads(stdout_str)

            # 音声ストリームを検索
            audio_stream = None
            for stream in info.get("streams", []):
                if stream.get("codec_type") == "audio":
                    audio_stream = stream
                    break

            if not audio_stream:
                raise AudioExtractionError("No audio stream found")

            duration = float(info.get("format", {}).get("duration", 0))
            bitrate = int(audio_stream.get("bit_rate", 0))
            sample_rate = int(audio_stream.get("sample_rate", 0))

            logger.debug(
                f"Audio info: duration={duration}s, "
                f"bitrate={bitrate}, sample_rate={sample_rate}"
            )

            return {
                "duration": duration,
                "bitrate": bitrate,
                "sample_rate": sample_rate
            }

        except Exception as e:
            logger.error(f"Error getting audio info: {e}")
            raise AudioExtractionError(f"Failed to get audio info: {str(e)}")
