"""
VOICEVOX エンジン

このモジュールは、VOICEVOXを使用した音声合成機能を提供します。
VOICEVOXエンジンが起動している必要があります。
"""

import asyncio
from typing import Optional, List, Dict
from loguru import logger
import aiohttp


class VoicevoxEngine:
    """
    VOICEVOX エンジン

    VOICEVOXエンジンのREST APIを使用して音声合成を行います。

    Attributes:
        base_url: VOICEVOXエンジンのベースURL
        default_speaker: デフォルトの話者ID

    Example:
        >>> engine = VoicevoxEngine(base_url="http://localhost:50021")
        >>> audio_data = await engine.synthesize(
        ...     text="こんにちは、世界",
        ...     speaker=1
        ... )
    """

    def __init__(
        self,
        base_url: str = "http://localhost:50021",
        default_speaker: int = 1,
        timeout: int = 300
    ):
        """
        Args:
            base_url: VOICEVOXエンジンのベースURL
            default_speaker: デフォルトの話者ID
            timeout: タイムアウト時間（秒）
        """
        self.base_url = base_url.rstrip("/")
        self.default_speaker = default_speaker
        self.timeout = timeout
        self._speakers_cache: Optional[List[Dict]] = None
        self._session: Optional[aiohttp.ClientSession] = None

        logger.info(
            f"VoicevoxEngine initialized: "
            f"url={base_url}, speaker={default_speaker}, timeout={timeout}s"
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        """
        セッションを取得（必要に応じて作成）

        Returns:
            aiohttp.ClientSession: HTTPセッション
        """
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self._session

    async def close(self):
        """セッションをクローズ"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def check_connection(self) -> bool:
        """
        VOICEVOXエンジンへの接続を確認

        Returns:
            bool: 接続可能な場合True

        Example:
            >>> is_available = await engine.check_connection()
            >>> if not is_available:
            ...     print("VOICEVOX engine is not running")
        """
        try:
            session = await self._get_session()
            async with session.get(
                f"{self.base_url}/version",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    version = await response.text()
                    logger.info(f"VOICEVOX connection OK: version={version}")
                    return True
                else:
                    logger.warning(
                        f"VOICEVOX returned status {response.status}"
                    )
                    return False

        except aiohttp.ClientError as e:
            logger.warning(f"VOICEVOX connection failed: {e}")
            return False

        except asyncio.TimeoutError:
            logger.warning("VOICEVOX connection timeout")
            return False

        except Exception as e:
            logger.error(f"Unexpected error checking VOICEVOX: {e}")
            return False

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
            voice: 話者名（未使用、speaker IDで指定）
            speed: 話速（0.5-2.0、デフォルト1.0）
            pitch: ピッチ（-0.15-0.15、デフォルト1.0）
            volume: 音量（0.0-2.0、デフォルト1.0）

        Returns:
            bytes: WAV形式の音声データ

        Raises:
            Exception: 音声合成に失敗

        Example:
            >>> audio_data = await engine.synthesize(
            ...     "こんにちは",
            ...     speed=1.2
            ... )
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")

        # 話者IDの決定（voiceが数字文字列の場合はそれを使用）
        if voice and voice.isdigit():
            speaker_id = int(voice)
        else:
            speaker_id = self.default_speaker

        logger.debug(
            f"Synthesizing with VOICEVOX: voice='{voice}', speaker_id={speaker_id}, "
            f"speed={speed}, pitch={pitch}, volume={volume}, text_length={len(text)}"
        )

        try:
            # VOICEVOXエンジンへの接続確認
            if not await self.check_connection():
                raise Exception("VOICEVOX engine is not running")

            # テキストが長い場合は分割処理（500文字以上）
            max_length = 500
            if len(text) > max_length:
                logger.info(
                    f"Text is long ({len(text)} chars), splitting into chunks "
                    f"(max {max_length} chars per chunk)"
                )
                return await self._synthesize_long_text(
                    text, speaker_id, speed, pitch, volume
                )

            # クエリを生成
            query = await self._create_audio_query(text, speaker_id)

            # パラメータを適用
            query["speedScale"] = speed
            query["pitchScale"] = self._convert_pitch(pitch)
            query["volumeScale"] = volume
            query["intonationScale"] = 1.0

            # 音声合成
            audio_data = await self._synthesize_audio(query, speaker_id)

            logger.debug(
                f"VOICEVOX synthesis completed: {len(audio_data)} bytes"
            )

            return audio_data

        except Exception as e:
            error_msg = str(e) if str(e) else repr(e)
            logger.error(f"VOICEVOX synthesis failed: {error_msg}", exc_info=True)
            raise Exception(f"Failed to synthesize with VOICEVOX: {error_msg}")

    async def _synthesize_long_text(
        self,
        text: str,
        speaker_id: int,
        speed: float,
        pitch: float,
        volume: float
    ) -> bytes:
        """
        長文テキストを分割して音声合成

        Args:
            text: 合成するテキスト
            speaker_id: 話者ID
            speed: 話速
            pitch: ピッチ
            volume: 音量

        Returns:
            bytes: 結合された音声データ（WAV）
        """
        import wave
        import io

        # テキストを句読点で分割（最大500文字）
        chunks = self._split_text(text, max_length=500)
        logger.info(f"Split text into {len(chunks)} chunks")

        audio_chunks = []

        for i, chunk in enumerate(chunks):
            logger.debug(f"Processing chunk {i+1}/{len(chunks)}: {len(chunk)} chars")

            # クエリを生成
            query = await self._create_audio_query(chunk, speaker_id)

            # パラメータを適用
            query["speedScale"] = speed
            query["pitchScale"] = self._convert_pitch(pitch)
            query["volumeScale"] = volume
            query["intonationScale"] = 1.0

            # 音声合成
            audio_data = await self._synthesize_audio(query, speaker_id)
            audio_chunks.append(audio_data)

        # 複数のWAVファイルを結合
        combined_audio = self._combine_wav_files(audio_chunks)

        logger.info(
            f"Combined {len(chunks)} audio chunks: {len(combined_audio)} bytes total"
        )

        return combined_audio

    def _split_text(self, text: str, max_length: int = 500) -> List[str]:
        """
        テキストを適切な長さで分割

        Args:
            text: 分割するテキスト
            max_length: 最大文字数

        Returns:
            List[str]: 分割されたテキストのリスト
        """
        chunks = []
        current_chunk = ""

        # 句読点で分割
        sentences = text.replace("。", "。\n").replace(".", ".\n").replace("!", "!\n").replace("?", "?\n").split("\n")

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # 現在のチャンクに追加しても最大長を超えない場合
            if len(current_chunk) + len(sentence) <= max_length:
                current_chunk += sentence
            else:
                # 現在のチャンクを保存
                if current_chunk:
                    chunks.append(current_chunk)

                # 1文が最大長を超える場合は強制的に分割
                if len(sentence) > max_length:
                    for i in range(0, len(sentence), max_length):
                        chunks.append(sentence[i:i+max_length])
                    current_chunk = ""
                else:
                    current_chunk = sentence

        # 残りを追加
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _combine_wav_files(self, wav_files: List[bytes]) -> bytes:
        """
        複数のWAVファイルを結合

        Args:
            wav_files: WAVファイルのバイトデータのリスト

        Returns:
            bytes: 結合されたWAVデータ
        """
        import wave
        import io

        if not wav_files:
            raise ValueError("No WAV files to combine")

        if len(wav_files) == 1:
            return wav_files[0]

        # 最初のWAVファイルのパラメータを取得
        first_wav = wave.open(io.BytesIO(wav_files[0]), 'rb')
        params = first_wav.getparams()
        first_wav.close()

        # 出力用のWAVファイルを作成
        output = io.BytesIO()
        output_wav = wave.open(output, 'wb')
        output_wav.setparams(params)

        # すべてのWAVファイルのオーディオデータを結合
        for wav_data in wav_files:
            wav_file = wave.open(io.BytesIO(wav_data), 'rb')
            output_wav.writeframes(wav_file.readframes(wav_file.getnframes()))
            wav_file.close()

        output_wav.close()

        return output.getvalue()

    async def _create_audio_query(
        self,
        text: str,
        speaker_id: int
    ) -> Dict:
        """
        音声クエリを作成

        Args:
            text: テキスト
            speaker_id: 話者ID

        Returns:
            Dict: 音声クエリ
        """
        logger.debug(
            f"Creating audio query: speaker_id={speaker_id}, "
            f"text_length={len(text)}, text_preview='{text[:100]}...'"
        )

        url = f"{self.base_url}/audio_query"
        params = {
            "text": text,
            "speaker": speaker_id
        }

        session = await self._get_session()
        async with session.post(
            url,
            params=params
        ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(
                        f"VOICEVOX API error: status={response.status}, "
                        f"speaker_id={speaker_id}, text_length={len(text)}, "
                        f"error={error_text}"
                    )
                    raise Exception(
                        f"Failed to create audio query: "
                        f"{response.status} - {error_text}"
                    )

                query = await response.json()
                return query

    async def _synthesize_audio(
        self,
        query: Dict,
        speaker_id: int
    ) -> bytes:
        """
        音声を合成

        Args:
            query: 音声クエリ
            speaker_id: 話者ID

        Returns:
            bytes: 音声データ（WAV）
        """
        url = f"{self.base_url}/synthesis"
        params = {"speaker": speaker_id}

        session = await self._get_session()
        async with session.post(
            url,
            params=params,
            json=query
        ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(
                        f"Failed to synthesize audio: "
                        f"{response.status} - {error_text}"
                    )

                audio_data = await response.read()
                return audio_data

    def _convert_pitch(self, pitch: float) -> float:
        """
        ピッチをVOICEVOX形式に変換

        Args:
            pitch: ピッチ（0.5-2.0）

        Returns:
            float: VOICEVOX形式のピッチ（-0.15-0.15）
        """
        # 1.0を基準に-0.15~0.15の範囲に変換
        # pitch=0.5 -> -0.15, pitch=1.0 -> 0.0, pitch=2.0 -> 0.15
        voicevox_pitch = (pitch - 1.0) * 0.15

        # 範囲制限
        voicevox_pitch = max(-0.15, min(0.15, voicevox_pitch))

        return voicevox_pitch

    async def get_speakers(self) -> List[Dict]:
        """
        利用可能な話者のリストを取得

        Returns:
            List[Dict]: 話者情報のリスト

        Example:
            >>> speakers = await engine.get_speakers()
            >>> for speaker in speakers:
            ...     print(f"{speaker['name']}: {speaker['styles']}")
        """
        # キャッシュがあればそれを返す
        if self._speakers_cache is not None:
            return self._speakers_cache

        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/speakers") as response:
                if response.status != 200:
                    raise Exception(f"Failed to get speakers: {response.status}")

                speakers = await response.json()
                self._speakers_cache = speakers

                logger.debug(f"Retrieved speakers: {len(speakers)} total")
                return speakers

        except asyncio.TimeoutError:
            logger.warning(
                "Failed to get speakers from VOICEVOX (timeout). "
                "This may be a known issue with VOICEVOX 0.24.x. "
                "Synthesis will still work with speaker IDs."
            )
            return []
        except Exception as e:
            error_msg = str(e) if str(e) else repr(e)
            logger.error(f"Failed to get speakers: {error_msg}", exc_info=True)
            return []

    def list_voices(self) -> List[str]:
        """
        利用可能な話者名のリストを取得（同期的）

        Returns:
            List[str]: 話者IDのリスト（文字列）

        Note:
            この関数は同期的なので、話者IDのみを返します。
            詳細な話者情報が必要な場合は get_speakers() を使用してください。
        """
        # デフォルトの話者IDリスト（VOICEVOX 0.14.x時点）
        # 実際のIDはVOICEVOXエンジンに問い合わせる必要があります
        default_speakers = [
            "1",   # 四国めたん（ノーマル）
            "2",   # 四国めたん（あまあま）
            "3",   # 四国めたん（ツンツン）
            "8",   # ずんだもん（ノーマル）
            "10",  # ずんだもん（あまあま）
            "11",  # ずんだもん（ツンツン）
            "13",  # 春日部つむぎ（ノーマル）
            "14",  # 雨晴はう（ノーマル）
            "16",  # 波音リツ（ノーマル）
        ]

        return default_speakers

    def get_default_voice(self) -> str:
        """
        デフォルトの話者IDを取得

        Returns:
            str: デフォルトの話者ID（文字列）
        """
        return str(self.default_speaker)

    def set_default_speaker(self, speaker_id: int) -> None:
        """
        デフォルトの話者IDを設定

        Args:
            speaker_id: 話者ID
        """
        self.default_speaker = speaker_id
        logger.info(f"Default speaker set to: {speaker_id}")

    async def test_synthesis(self) -> bool:
        """
        音声合成のテスト

        Returns:
            bool: 成功した場合True

        Example:
            >>> success = await engine.test_synthesis()
            >>> if success:
            ...     print("VOICEVOX is working!")
        """
        try:
            # 接続確認
            if not await self.check_connection():
                logger.error("VOICEVOX engine is not running")
                return False

            # テスト合成
            test_text = "これはテストです。"
            audio_data = await self.synthesize(test_text)

            if audio_data and len(audio_data) > 0:
                logger.info("VOICEVOX test synthesis successful")
                return True
            else:
                logger.error("VOICEVOX test synthesis returned empty data")
                return False

        except Exception as e:
            logger.error(f"VOICEVOX test synthesis failed: {e}")
            return False

    async def get_speaker_info(self, speaker_id: int) -> Optional[Dict]:
        """
        特定の話者の情報を取得

        Args:
            speaker_id: 話者ID

        Returns:
            Optional[Dict]: 話者情報、見つからない場合はNone
        """
        speakers = await self.get_speakers()

        for speaker in speakers:
            for style in speaker.get("styles", []):
                if style.get("id") == speaker_id:
                    return {
                        "name": speaker.get("name"),
                        "style": style.get("name"),
                        "id": speaker_id
                    }

        return None
