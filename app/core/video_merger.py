"""
動画連結機能

このモジュールは、複数の動画ファイルを連結する機能を提供します。
FFmpegを使用して高速かつ高品質な動画連結を実現します。
"""

import asyncio
import subprocess
from pathlib import Path
from typing import List, Optional, Callable
from dataclasses import dataclass
from loguru import logger


@dataclass
class MergeResult:
    """
    連結結果

    Attributes:
        output_path: 出力ファイルパス
        video_count: 連結した動画数
        duration: 総再生時間（秒）
        filesize: ファイルサイズ（バイト）
    """
    output_path: str
    video_count: int
    duration: Optional[float] = None
    filesize: Optional[int] = None


class VideoMergeError(Exception):
    """動画連結エラー"""
    pass


class VideoMerger:
    """
    動画連結クラス

    複数の動画ファイルを1つに連結します。

    Attributes:
        output_dir: 出力先ディレクトリ
        temp_dir: 一時ファイルディレクトリ

    Example:
        >>> merger = VideoMerger()
        >>> result = await merger.merge_videos(
        ...     video_paths=["video1.mp4", "video2.mp4"],
        ...     output_name="merged.mp4"
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
            f"VideoMerger initialized: "
            f"output_dir={self.output_dir}"
        )

    async def merge_videos(
        self,
        video_paths: List[str],
        output_name: str,
        method: str = "concat",
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> MergeResult:
        """
        複数の動画を連結

        Args:
            video_paths: 動画ファイルパスのリスト
            output_name: 出力ファイル名
            method: 連結方法（concat: 高速, filter: 高品質）
            progress_callback: 進捗コールバック

        Returns:
            MergeResult: 連結結果

        Raises:
            VideoMergeError: 連結に失敗

        Example:
            >>> result = await merger.merge_videos(
            ...     ["video1.mp4", "video2.mp4"],
            ...     "output.mp4"
            ... )
        """
        if not video_paths:
            raise ValueError("Video paths cannot be empty")

        if len(video_paths) < 2:
            raise ValueError("At least 2 videos are required for merging")

        # 全ファイルの存在確認
        for path in video_paths:
            if not Path(path).exists():
                raise FileNotFoundError(f"Video file not found: {path}")

        output_path = self.output_dir / output_name

        logger.info(
            f"Merging {len(video_paths)} videos -> {output_path} "
            f"(method={method})"
        )

        try:
            if method == "concat":
                # concat demuxer（高速、再エンコードなし）
                result = await self._merge_concat(
                    video_paths, output_path, progress_callback
                )
            elif method == "filter":
                # concat filter（高品質、再エンコードあり）
                result = await self._merge_filter(
                    video_paths, output_path, progress_callback
                )
            else:
                raise ValueError(f"Unknown merge method: {method}")

            logger.info(
                f"Video merge completed: {result.output_path} "
                f"({result.video_count} videos)"
            )

            return result

        except Exception as e:
            logger.error(f"Video merge failed: {e}")
            raise VideoMergeError(f"Failed to merge videos: {str(e)}")

    async def _merge_concat(
        self,
        video_paths: List[str],
        output_path: Path,
        progress_callback: Optional[Callable[[float], None]]
    ) -> MergeResult:
        """
        concat demuxerで連結（高速）

        Args:
            video_paths: 動画パスリスト
            output_path: 出力パス
            progress_callback: 進捗コールバック

        Returns:
            MergeResult: 連結結果
        """
        # ファイルリストを作成
        filelist_path = self.temp_dir / "filelist.txt"

        with open(filelist_path, "w", encoding="utf-8") as f:
            for video_path in video_paths:
                # FFmpegのconcat demuxer用フォーマット
                abs_path = Path(video_path).resolve()
                f.write(f"file '{abs_path}'\n")

        logger.debug(f"Created filelist: {filelist_path}")

        # FFmpegコマンド
        command = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", str(filelist_path),
            "-c", "copy",  # ストリームコピー（再エンコードなし）
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
            raise VideoMergeError(f"FFmpeg failed: {result.stderr}")

        # ファイルリストを削除
        filelist_path.unlink()

        # 結果を返す
        if progress_callback:
            progress_callback(100.0)

        return MergeResult(
            output_path=str(output_path),
            video_count=len(video_paths),
            filesize=output_path.stat().st_size if output_path.exists() else None
        )

    async def _merge_filter(
        self,
        video_paths: List[str],
        output_path: Path,
        progress_callback: Optional[Callable[[float], None]]
    ) -> MergeResult:
        """
        concat filterで連結（高品質、再エンコードあり）

        Args:
            video_paths: 動画パスリスト
            output_path: 出力パス
            progress_callback: 進捗コールバック

        Returns:
            MergeResult: 連結結果
        """
        # 入力ファイル指定
        inputs = []
        for path in video_paths:
            inputs.extend(["-i", str(Path(path).resolve())])

        # concat filter構築
        n = len(video_paths)
        filter_complex = "".join([f"[{i}:v][{i}:a]" for i in range(n)])
        filter_complex += f"concat=n={n}:v=1:a=1[outv][outa]"

        # FFmpegコマンド
        command = [
            "ffmpeg",
            *inputs,
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-map", "[outa]",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "192k",
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
                timeout=1800  # 30分タイムアウト
            )
        )

        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            raise VideoMergeError(f"FFmpeg failed: {result.stderr}")

        # 結果を返す
        if progress_callback:
            progress_callback(100.0)

        return MergeResult(
            output_path=str(output_path),
            video_count=len(video_paths),
            filesize=output_path.stat().st_size if output_path.exists() else None
        )

    async def add_audio_to_video(
        self,
        video_path: str,
        audio_path: str,
        output_name: str,
        replace_audio: bool = True
    ) -> str:
        """
        動画に音声を追加または置き換え

        Args:
            video_path: 動画ファイルパス
            audio_path: 音声ファイルパス
            output_name: 出力ファイル名
            replace_audio: 既存音声を置き換えるか（False=ミックス）

        Returns:
            str: 出力ファイルパス

        Raises:
            VideoMergeError: 音声追加に失敗

        Example:
            >>> output = await merger.add_audio_to_video(
            ...     "video.mp4",
            ...     "audio.mp3",
            ...     "dubbed.mp4"
            ... )
        """
        video_path_obj = Path(video_path)
        audio_path_obj = Path(audio_path)

        if not video_path_obj.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        if not audio_path_obj.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        output_path = self.output_dir / output_name

        logger.info(
            f"Adding audio to video: {video_path} + {audio_path} "
            f"-> {output_path} (replace={replace_audio})"
        )

        try:
            if replace_audio:
                # 既存音声を置き換え
                command = [
                    "ffmpeg",
                    "-i", str(video_path_obj),
                    "-i", str(audio_path_obj),
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    "-shortest",
                    "-y",
                    str(output_path)
                ]
            else:
                # 既存音声とミックス
                command = [
                    "ffmpeg",
                    "-i", str(video_path_obj),
                    "-i", str(audio_path_obj),
                    "-filter_complex", "[0:a][1:a]amerge=inputs=2[a]",
                    "-map", "0:v",
                    "-map", "[a]",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-shortest",
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
                raise VideoMergeError(f"Failed to add audio: {result.stderr}")

            logger.info(f"Audio added successfully: {output_path}")

            return str(output_path)

        except Exception as e:
            logger.error(f"Failed to add audio to video: {e}")
            raise VideoMergeError(f"Failed to add audio: {str(e)}")

    def get_video_info(self, video_path: str) -> dict:
        """
        動画情報を取得

        Args:
            video_path: 動画ファイルパス

        Returns:
            dict: 動画情報

        Raises:
            VideoMergeError: 情報取得に失敗
        """
        try:
            command = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                video_path
            ]

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                raise VideoMergeError("Failed to get video info")

            import json
            info = json.loads(result.stdout)

            return info

        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            raise VideoMergeError(f"Failed to get video info: {str(e)}")
