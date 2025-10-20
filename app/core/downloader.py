"""
YouTube動画ダウンローダー

このモジュールは、yt-dlpを使用してYouTube動画をダウンロードする機能を提供します。
"""

import asyncio
from pathlib import Path
from typing import Optional, Callable, List
import yt_dlp
from loguru import logger

from app.models.download_item import (
    VideoInfo,
    DownloadResult,
    DownloadProgress,
    DownloadStatus
)


class DownloadError(Exception):
    """ダウンロードエラー"""
    pass


class InvalidURLError(DownloadError):
    """無効なURL"""
    pass


class NetworkError(DownloadError):
    """ネットワークエラー"""
    pass


class YouTubeDownloader:
    """
    YouTube動画ダウンローダー

    yt-dlpを使用してYouTube動画のダウンロードと情報取得を行います。

    Attributes:
        output_dir: ダウンロード先ディレクトリ
        max_concurrent: 最大同時ダウンロード数

    Example:
        >>> downloader = YouTubeDownloader(output_dir="./output/videos")
        >>> video_info = await downloader.get_video_info("https://youtube.com/watch?v=...")
        >>> result = await downloader.download_video(video_info.url, resolution="720p")
    """

    def __init__(
        self,
        output_dir: str = "./output/videos",
        max_concurrent: int = 3
    ):
        """
        Args:
            output_dir: ダウンロード先ディレクトリ
            max_concurrent: 最大同時ダウンロード数
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)

        logger.info(
            f"YouTubeDownloader initialized: "
            f"output_dir={self.output_dir}, max_concurrent={max_concurrent}"
        )

    async def get_video_info(self, url: str) -> VideoInfo:
        """
        YouTube動画情報を取得

        Args:
            url: YouTube動画URL

        Returns:
            VideoInfo: 動画情報

        Raises:
            InvalidURLError: 無効なURL
            NetworkError: ネットワークエラー

        Example:
            >>> info = await downloader.get_video_info("https://youtube.com/watch?v=...")
            >>> print(info.title)
            'Example Video Title'
        """
        try:
            logger.info(f"Fetching video info: {url}")

            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'extract_flat': False
            }

            # yt-dlpを非同期で実行
            loop = asyncio.get_event_loop()
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await loop.run_in_executor(
                    None,
                    lambda: ydl.extract_info(url, download=False)
                )

            if info is None:
                raise InvalidURLError(f"Failed to extract video info: {url}")

            # VideoInfoオブジェクトを作成
            video_info = VideoInfo(
                url=url,
                title=info.get('title', 'Unknown'),
                duration=info.get('duration', 0),
                resolution=f"{info.get('height', 0)}p",
                thumbnail_url=info.get('thumbnail'),
                uploader=info.get('uploader'),
                upload_date=info.get('upload_date'),
                view_count=info.get('view_count'),
                filesize=info.get('filesize') or info.get('filesize_approx')
            )

            logger.info(
                f"Video info fetched: title='{video_info.title}', "
                f"duration={video_info.duration_str}, "
                f"resolution={video_info.resolution}"
            )

            return video_info

        except yt_dlp.utils.DownloadError as e:
            logger.error(f"Failed to fetch video info: {e}")
            raise InvalidURLError(f"Invalid YouTube URL or video unavailable: {url}")

        except Exception as e:
            logger.error(f"Unexpected error while fetching video info: {e}")
            raise NetworkError(f"Network error: {str(e)}")

    async def download_video(
        self,
        url: str,
        resolution: str = "720p",
        include_audio: bool = True,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None
    ) -> DownloadResult:
        """
        YouTube動画をダウンロード

        Args:
            url: YouTube動画URL
            resolution: 解像度（480p, 720p, 1080p, best）
            include_audio: 音声を含めるかどうか（デフォルト: True）
            progress_callback: 進捗コールバック

        Returns:
            DownloadResult: ダウンロード結果

        Raises:
            DownloadError: ダウンロード失敗

        Example:
            >>> def on_progress(progress: DownloadProgress):
            ...     print(f"Progress: {progress.percent:.1f}%")
            >>> result = await downloader.download_video(
            ...     "https://youtube.com/watch?v=...",
            ...     resolution="720p",
            ...     include_audio=True,
            ...     progress_callback=on_progress
            ... )
        """
        async with self._semaphore:
            try:
                from datetime import datetime
                start_time = datetime.now()

                logger.info(
                    f"Starting download: {url} "
                    f"(resolution={resolution}, audio={include_audio})"
                )

                # 進捗フック
                def progress_hook(d):
                    if progress_callback is None:
                        return

                    try:
                        status_map = {
                            'downloading': DownloadStatus.DOWNLOADING,
                            'finished': DownloadStatus.COMPLETED,
                            'error': DownloadStatus.FAILED
                        }

                        status = status_map.get(
                            d.get('status'),
                            DownloadStatus.DOWNLOADING
                        )

                        downloaded = d.get('downloaded_bytes', 0)
                        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                        speed = d.get('speed', 0.0) or 0.0
                        eta = d.get('eta')

                        percent = 0.0
                        if total > 0:
                            percent = (downloaded / total) * 100.0

                        progress = DownloadProgress(
                            url=url,
                            percent=percent,
                            downloaded_bytes=downloaded,
                            total_bytes=total,
                            speed=speed,
                            eta=eta,
                            status=status
                        )

                        progress_callback(progress)

                    except Exception as e:
                        logger.warning(f"Error in progress hook: {e}")

                # yt-dlpオプション
                ydl_opts = {
                    'format': self._get_format_selector(resolution, include_audio),
                    'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
                    'progress_hooks': [progress_hook],
                    'quiet': True,
                    'no_warnings': True,
                    'ignoreerrors': False,
                    'merge_output_format': 'mp4',
                }

                # ダウンロード実行
                loop = asyncio.get_event_loop()
                ydl = yt_dlp.YoutubeDL(ydl_opts)

                info = await loop.run_in_executor(
                    None,
                    lambda: ydl.extract_info(url, download=True)
                )

                if info is None:
                    raise DownloadError("Failed to download video")

                # 保存されたファイルパスを取得（yt-dlpが使用する実際のファイル名）
                title = info.get('title', 'video')
                video_filename = ydl.prepare_filename(info)
                video_path = Path(video_filename)

                # 音声ありの場合、音声ファイルを別途抽出
                audio_path = None
                if include_audio:
                    logger.info("Extracting audio file separately...")
                    audio_path = await self._extract_audio(video_path)

                    # AAC変換は時間がかかりすぎてアプリがクラッシュするためスキップ
                    # 動画内の音声がOpusでも、音声ファイル（WAV）は抽出されている
                    # ユーザーは動画内の音声またはWAVファイルのどちらでも使用可能
                    logger.info("Audio extraction completed. Video may contain Opus audio (not all players support it).")

                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                logger.info(
                    f"Download completed: '{title}' "
                    f"(duration={duration:.2f}s, video={video_path}, audio={audio_path})"
                )

                return DownloadResult(
                    status=DownloadStatus.COMPLETED,
                    video_path=str(video_path),
                    audio_path=audio_path,
                    title=title,
                    download_time=end_time,
                    duration_seconds=duration
                )

            except yt_dlp.utils.DownloadError as e:
                logger.error(f"Download failed: {e}")
                return DownloadResult(
                    status=DownloadStatus.FAILED,
                    error_message=str(e)
                )

            except Exception as e:
                logger.error(f"Unexpected error during download: {e}")
                return DownloadResult(
                    status=DownloadStatus.FAILED,
                    error_message=f"Unexpected error: {str(e)}"
                )

    async def download_batch(
        self,
        urls: List[str],
        resolution: str = "720p",
        progress_callback: Optional[Callable[[str, DownloadProgress], None]] = None
    ) -> List[DownloadResult]:
        """
        複数の動画を並行ダウンロード

        Args:
            urls: YouTube動画URLのリスト
            resolution: 解像度
            progress_callback: 進捗コールバック（url, progressを受け取る）

        Returns:
            List[DownloadResult]: ダウンロード結果のリスト

        Example:
            >>> urls = [
            ...     "https://youtube.com/watch?v=...",
            ...     "https://youtube.com/watch?v=..."
            ... ]
            >>> results = await downloader.download_batch(urls)
            >>> for result in results:
            ...     print(f"{result.title}: {result.status}")
        """
        logger.info(f"Starting batch download: {len(urls)} videos")

        async def download_with_callback(url: str) -> DownloadResult:
            def on_progress(progress: DownloadProgress):
                if progress_callback:
                    progress_callback(url, progress)

            return await self.download_video(
                url,
                resolution,
                on_progress
            )

        tasks = [download_with_callback(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 例外をDownloadResultに変換
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Download failed for {urls[i]}: {result}")
                processed_results.append(
                    DownloadResult(
                        status=DownloadStatus.FAILED,
                        error_message=str(result)
                    )
                )
            else:
                processed_results.append(result)

        success_count = sum(1 for r in processed_results if r.is_success)
        logger.info(
            f"Batch download completed: "
            f"{success_count}/{len(urls)} successful"
        )

        return processed_results

    async def _extract_audio(self, video_path: Path) -> Optional[str]:
        """
        動画から音声を抽出してWAVファイルとして保存

        Args:
            video_path: 動画ファイルのパス

        Returns:
            Optional[str]: 抽出された音声ファイルのパス、失敗時はNone
        """
        import subprocess

        try:
            # 音声ファイルのパス（動画と同じ場所、拡張子を.wavに変更）
            audio_path = video_path.parent / f"{video_path.stem}_audio.wav"

            # FFmpegコマンド: 音声のみを抽出
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-vn',           # 映像ストリームを無視
                '-acodec', 'pcm_s16le',  # WAV形式（16bit PCM）
                '-ar', '44100',  # サンプリングレート 44.1kHz
                '-ac', '2',      # ステレオ
                '-y',            # 上書き確認をスキップ
                str(audio_path)
            ]

            # 非同期でFFmpegを実行
            loop = asyncio.get_event_loop()
            process = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=False,  # バイナリモードで実行（エンコーディングエラー回避）
                    timeout=180  # 3分タイムアウト
                )
            )

            if process.returncode == 0:
                logger.info(f"Audio extracted: {audio_path}")
                return str(audio_path)
            else:
                # stderrはバイナリなので、エラー時だけデコードを試みる
                try:
                    stderr_msg = process.stderr.decode('utf-8', errors='ignore')
                except:
                    stderr_msg = "Unable to decode error message"
                logger.warning(f"Audio extraction failed: {stderr_msg}")
                return None

        except subprocess.TimeoutExpired:
            logger.error("Audio extraction timed out")
            return None
        except Exception as e:
            logger.error(f"Audio extraction failed: {e}")
            return None

    async def _convert_audio_to_aac(self, video_path: Path) -> None:
        """
        動画の音声をAACに変換（Opus→AAC）

        Args:
            video_path: 変換する動画ファイルのパス
        """
        import subprocess

        try:
            # 一時ファイル名
            temp_path = video_path.parent / f"{video_path.stem}_temp{video_path.suffix}"

            # FFmpegコマンド: 動画コピー、音声をAACに変換
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-c:v', 'copy',  # 動画ストリームはコピー
                '-c:a', 'aac',   # 音声をAACに変換
                '-b:a', '192k',  # ビットレート
                '-y',            # 上書き確認をスキップ
                str(temp_path)
            ]

            # 非同期でFFmpegを実行
            loop = asyncio.get_event_loop()
            process = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=False,  # バイナリモードで実行（エンコーディングエラー回避）
                    timeout=300  # 5分タイムアウト
                )
            )

            if process.returncode == 0:
                # 成功: 元ファイルを削除して一時ファイルをリネーム
                video_path.unlink()
                temp_path.rename(video_path)
                logger.info(f"Audio converted to AAC: {video_path}")
            else:
                # stderrはバイナリなので、エラー時だけデコードを試みる
                try:
                    stderr_msg = process.stderr.decode('utf-8', errors='ignore')
                except:
                    stderr_msg = "Unable to decode error message"
                logger.warning(f"FFmpeg conversion failed: {stderr_msg}")
                # 変換失敗でも元のファイルは残す
                if temp_path.exists():
                    temp_path.unlink()

        except subprocess.TimeoutExpired:
            logger.error("FFmpeg conversion timed out")
            if temp_path.exists():
                temp_path.unlink()
        except Exception as e:
            logger.error(f"Audio conversion failed: {e}")
            if temp_path.exists():
                temp_path.unlink()

    def _get_format_selector(self, resolution: str, include_audio: bool = True) -> str:
        """
        解像度に応じたフォーマット選択文字列を返す

        Args:
            resolution: 解像度（480p, 720p, 1080p, best）
            include_audio: 音声を含めるかどうか

        Returns:
            str: yt-dlpフォーマット選択文字列
        """
        if include_audio:
            # 音声あり - 参考アプリと同じフォールバック付き形式
            resolution_map = {
                '480p': 'bestvideo[height<=480]+bestaudio/best[height<=480]/best',
                '720p': 'bestvideo[height<=720]+bestaudio/best[height<=720]/best',
                '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
                'best': 'bestvideo+bestaudio/best'
            }
        else:
            # 音声なし（映像のみ）
            resolution_map = {
                '480p': 'bestvideo[height<=480]/best[height<=480]',
                '720p': 'bestvideo[height<=720]/best[height<=720]',
                '1080p': 'bestvideo[height<=1080]/best[height<=1080]',
                'best': 'bestvideo/best'
            }

        format_str = resolution_map.get(resolution, resolution_map['720p'])
        logger.debug(
            f"Format selector for {resolution} "
            f"(audio={include_audio}): {format_str}"
        )

        return format_str

    async def cancel_download(self, url: str) -> bool:
        """
        ダウンロードをキャンセル（将来的な実装）

        Args:
            url: キャンセルする動画のURL

        Returns:
            bool: キャンセルに成功した場合True
        """
        # TODO: ダウンロードキャンセル機能の実装
        logger.warning("Download cancellation not implemented yet")
        return False
