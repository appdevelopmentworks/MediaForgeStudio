# -*- mode: python ; coding: utf-8 -*-

"""
MediaForge Studio - PyInstaller Spec File
"""

import sys
from pathlib import Path

# プロジェクトルート
project_root = Path('.').resolve()

# データファイル（必要なリソースファイルを含める）
datas = [
    ('.env', '.'),  # .envファイル（存在する場合）
]

# 隠しインポート（動的にインポートされるモジュール）
hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'qfluentwidgets',
    'loguru',
    'dotenv',
    'yt_dlp',
    'whisper',
    'groq',
    'google.generativeai',
    'openai',
    'deepl',
    'argostranslate',
    'edge_tts',
    'pyttsx3',
    'google.cloud.texttospeech',
    'requests',
    'aiohttp',
    'asyncio',
    'subprocess',
    'pathlib',
    'yaml',
    'torch',
    'torchaudio',
    'numpy',
    'numba',
    # Whisperの依存関係
    'tiktoken',
    'regex',
    'tqdm',
    'more_itertools',
    # PySide6の追加モジュール
    'PySide6.QtSvg',
    'PySide6.QtNetwork',
    # QFluentWidgetsの内部モジュール
    'qfluentwidgets.components',
    'qfluentwidgets.common',
    'qfluentwidgets.window',
]

# 除外するモジュール（ビルドサイズ削減）
excludes = [
    'matplotlib',
    'PIL',
    'tkinter',
    'test',
    'unittest',
    'pytest',
]

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MediaForgeStudio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUIアプリなのでコンソールを非表示
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='arisa004.ico',  # アプリアイコン
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MediaForgeStudio',
)
