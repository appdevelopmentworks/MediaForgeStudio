"""
翻訳システム（6段階フォールバック）

このモジュールは、複数の翻訳APIを使用して、高い可用性を実現する翻訳システムを提供します。
Groq → Gemini → DeepL → OpenRouter → OpenAI → Argos Translate の順でフォールバックします。

OpenRouterは openai/gpt-oss-120b モデルを使用し、コストパフォーマンスに優れた翻訳を提供します。
"""

import asyncio
import os
from typing import Optional, Literal
from dataclasses import dataclass
from loguru import logger
import aiohttp


@dataclass
class TranslationResult:
    """
    翻訳結果

    Attributes:
        translated_text: 翻訳されたテキスト
        source_language: 元の言語
        target_language: 翻訳先の言語
        engine: 使用した翻訳エンジン
    """
    translated_text: str
    source_language: str
    target_language: str
    engine: str


class TranslationError(Exception):
    """翻訳エラー"""
    pass


class TranslationManager:
    """
    翻訳統合管理クラス

    複数の翻訳エンジンを使用し、フォールバック機能を提供します。

    Attributes:
        target_language: デフォルトの翻訳先言語
        api_keys: 各APIのキー

    Example:
        >>> translator = TranslationManager(target_language="ja")
        >>> result = await translator.translate("Hello, world!", source_lang="en")
        >>> print(result.translated_text)
    """

    def __init__(
        self,
        target_language: str = "ja",
        deepl_api_key: Optional[str] = None,
        openrouter_api_key: Optional[str] = None,
        groq_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None
    ):
        """
        Args:
            target_language: デフォルトの翻訳先言語
            deepl_api_key: DeepL APIキー
            openrouter_api_key: OpenRouter APIキー
            groq_api_key: Groq APIキー
            gemini_api_key: Gemini APIキー
            openai_api_key: OpenAI APIキー
        """
        self.target_language = target_language

        # APIキーの設定（環境変数からも取得）
        self.api_keys = {
            "deepl": deepl_api_key or os.getenv("DEEPL_API_KEY"),
            "openrouter": openrouter_api_key or os.getenv("OPENROUTER_API_KEY"),
            "groq": groq_api_key or os.getenv("GROQ_API_KEY"),
            "gemini": gemini_api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
            "openai": openai_api_key or os.getenv("OPENAI_API_KEY")
        }

        # デバッグ: APIキーの状態をログ出力
        for engine, key in self.api_keys.items():
            if key:
                logger.debug(f"{engine}: {key[:10]}... (loaded)")
            else:
                logger.debug(f"{engine}: not configured")

        # 利用可能なエンジンをログ出力
        available_engines = [
            engine for engine, key in self.api_keys.items() if key
        ]
        logger.info(
            f"TranslationManager initialized: "
            f"target={target_language}, "
            f"available_engines={available_engines}"
        )

    async def translate(
        self,
        text: str,
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None
    ) -> TranslationResult:
        """
        テキストを翻訳（フォールバック機能付き）

        Args:
            text: 翻訳するテキスト
            source_lang: 元の言語（Noneの場合は自動検出）
            target_lang: 翻訳先の言語（Noneの場合はデフォルト言語）

        Returns:
            TranslationResult: 翻訳結果

        Raises:
            TranslationError: すべてのエンジンで翻訳に失敗

        Example:
            >>> result = await translator.translate("Hello", "en", "ja")
            >>> print(result.translated_text)
            'こんにちは'
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")

        if target_lang is None:
            target_lang = self.target_language

        logger.info(
            f"Translating text: '{text[:50]}...' "
            f"({source_lang} -> {target_lang})"
        )

        # 翻訳エンジンを順番に試す
        engines = [
            ("Groq", self._translate_groq),
            ("Gemini", self._translate_gemini),
            ("DeepL", self._translate_deepl),
            ("OpenRouter", self._translate_openrouter),
            ("OpenAI", self._translate_openai),
            ("Argos", self._translate_argos)
        ]

        last_error = None

        for engine_name, translate_func in engines:
            try:
                logger.debug(f"Trying {engine_name}...")

                result = await translate_func(text, source_lang, target_lang)

                logger.info(f"Translation successful using {engine_name}")
                return result

            except Exception as e:
                logger.warning(f"{engine_name} translation failed: {e}")
                last_error = e
                continue

        # すべてのエンジンで失敗
        logger.error("All translation engines failed")
        raise TranslationError(
            f"Translation failed with all engines. Last error: {last_error}"
        )

    async def _translate_deepl(
        self,
        text: str,
        source_lang: Optional[str],
        target_lang: str
    ) -> TranslationResult:
        """DeepL APIで翻訳"""
        api_key = self.api_keys.get("deepl")
        if not api_key:
            raise TranslationError("DeepL API key not configured")

        url = "https://api-free.deepl.com/v2/translate"

        params = {
            "auth_key": api_key,
            "text": text,
            "target_lang": target_lang.upper()
        }

        if source_lang:
            params["source_lang"] = source_lang.upper()

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=params, timeout=30) as response:
                if response.status != 200:
                    raise TranslationError(
                        f"DeepL API error: {response.status}"
                    )

                data = await response.json()
                translation = data["translations"][0]

                return TranslationResult(
                    translated_text=translation["text"],
                    source_language=translation.get(
                        "detected_source_language", source_lang or "auto"
                    ).lower(),
                    target_language=target_lang,
                    engine="DeepL"
                )

    async def _translate_openrouter(
        self,
        text: str,
        source_lang: Optional[str],
        target_lang: str
    ) -> TranslationResult:
        """OpenRouter APIで翻訳（openai/gpt-oss-120bモデル使用）"""
        api_key = self.api_keys.get("openrouter")
        if not api_key:
            raise TranslationError("OpenRouter API key not configured")

        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/MediaForgeStudio",  # 任意のリファラー
            "X-Title": "MediaForgeStudio"  # 任意のアプリ名
        }

        lang_names = {
            "en": "English",
            "ja": "Japanese",
            "zh": "Chinese",
            "ko": "Korean",
            "fr": "French",
            "de": "German",
            "es": "Spanish",
            "it": "Italian",
            "ru": "Russian"
        }

        target_lang_name = lang_names.get(target_lang, target_lang)

        prompt = f"Translate the following text to {target_lang_name}. Only output the translation, nothing else:\n\n{text}"

        payload = {
            "model": "openai/gpt-oss-120b",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 4096
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, headers=headers, json=payload, timeout=60
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"OpenRouter API error: {response.status}, {error_text}")
                    raise TranslationError(f"OpenRouter API error: {response.status}")

                data = await response.json()
                translated_text = data["choices"][0]["message"]["content"].strip()

                return TranslationResult(
                    translated_text=translated_text,
                    source_language=source_lang or "auto",
                    target_language=target_lang,
                    engine="OpenRouter"
                )

    async def _translate_groq(
        self,
        text: str,
        source_lang: Optional[str],
        target_lang: str
    ) -> TranslationResult:
        """Groq APIで翻訳"""
        api_key = self.api_keys.get("groq")
        if not api_key:
            raise TranslationError("Groq API key not configured")

        url = "https://api.groq.com/openai/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        lang_names = {
            "en": "English",
            "ja": "Japanese",
            "zh": "Chinese",
            "ko": "Korean"
        }

        target_lang_name = lang_names.get(target_lang, target_lang)

        prompt = f"Translate the following text to {target_lang_name}. Only output the translation, nothing else:\n\n{text}"

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 4096
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, headers=headers, json=payload, timeout=30
            ) as response:
                if response.status != 200:
                    raise TranslationError(f"Groq API error: {response.status}")

                data = await response.json()
                translated_text = data["choices"][0]["message"]["content"].strip()

                return TranslationResult(
                    translated_text=translated_text,
                    source_language=source_lang or "auto",
                    target_language=target_lang,
                    engine="Groq"
                )

    async def _translate_gemini(
        self,
        text: str,
        source_lang: Optional[str],
        target_lang: str
    ) -> TranslationResult:
        """Gemini APIで翻訳"""
        api_key = self.api_keys.get("gemini")
        if not api_key:
            raise TranslationError("Gemini API key not configured")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"

        lang_names = {
            "en": "English",
            "ja": "Japanese",
            "zh": "Chinese",
            "ko": "Korean"
        }

        target_lang_name = lang_names.get(target_lang, target_lang)

        prompt = f"Translate the following text to {target_lang_name}. Only output the translation:\n\n{text}"

        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=30) as response:
                if response.status != 200:
                    raise TranslationError(
                        f"Gemini API error: {response.status}"
                    )

                data = await response.json()
                translated_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()

                return TranslationResult(
                    translated_text=translated_text,
                    source_language=source_lang or "auto",
                    target_language=target_lang,
                    engine="Gemini"
                )

    async def _translate_openai(
        self,
        text: str,
        source_lang: Optional[str],
        target_lang: str
    ) -> TranslationResult:
        """OpenAI APIで翻訳"""
        api_key = self.api_keys.get("openai")
        if not api_key:
            raise TranslationError("OpenAI API key not configured")

        url = "https://api.openai.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        lang_names = {
            "en": "English",
            "ja": "Japanese",
            "zh": "Chinese",
            "ko": "Korean"
        }

        target_lang_name = lang_names.get(target_lang, target_lang)

        prompt = f"Translate the following text to {target_lang_name}. Only output the translation:\n\n{text}"

        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, headers=headers, json=payload, timeout=30
            ) as response:
                if response.status != 200:
                    raise TranslationError(
                        f"OpenAI API error: {response.status}"
                    )

                data = await response.json()
                translated_text = data["choices"][0]["message"]["content"].strip()

                return TranslationResult(
                    translated_text=translated_text,
                    source_language=source_lang or "auto",
                    target_language=target_lang,
                    engine="OpenAI"
                )

    async def _translate_argos(
        self,
        text: str,
        source_lang: Optional[str],
        target_lang: str
    ) -> TranslationResult:
        """Argos Translateで翻訳（オフライン）"""
        try:
            from argostranslate import package, translate

            # パッケージが未インストールの場合はインストール
            package.update_package_index()
            available_packages = package.get_available_packages()

            # 必要な言語パッケージを検索
            if source_lang is None:
                source_lang = "en"

            installed_languages = translate.get_installed_languages()
            from_lang = None
            to_lang = None

            for lang in installed_languages:
                if lang.code == source_lang:
                    from_lang = lang
                if lang.code == target_lang:
                    to_lang = lang

            if not from_lang or not to_lang:
                # パッケージをインストール
                for pkg in available_packages:
                    if pkg.from_code == source_lang and pkg.to_code == target_lang:
                        package.install_from_path(pkg.download())
                        break

                # 再度取得
                installed_languages = translate.get_installed_languages()
                for lang in installed_languages:
                    if lang.code == source_lang:
                        from_lang = lang
                    if lang.code == target_lang:
                        to_lang = lang

            if not from_lang or not to_lang:
                raise TranslationError(
                    f"Language pair not available: {source_lang} -> {target_lang}"
                )

            # 翻訳実行
            translation = from_lang.get_translation(to_lang)
            translated_text = translation.translate(text)

            return TranslationResult(
                translated_text=translated_text,
                source_language=source_lang,
                target_language=target_lang,
                engine="Argos Translate"
            )

        except ImportError:
            raise TranslationError(
                "Argos Translate not installed. "
                "Install it with: pip install argostranslate"
            )

        except Exception as e:
            raise TranslationError(f"Argos translation failed: {str(e)}")
