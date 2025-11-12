@echo off
chcp 932 >nul
REM ============================================================================
REM MediaForge Studio - Nuitka ビルドスクリプト
REM ============================================================================
REM
REM 使い方:
REM   build_nuitka.bat [オプション]
REM
REM オプション:
REM   clean    - ビルド前に既存の成果物を削除
REM   onefile  - 単一EXEファイルとしてビルド
REM   debug    - デバッグモード（コンソール表示）
REM
REM 例:
REM   build_nuitka.bat
REM   build_nuitka.bat clean
REM   build_nuitka.bat onefile
REM
REM 注意:
REM   - Nuitkaは初回ビルド時にC++コンパイラ（MSVC）が必要です
REM   - Visual Studio Build Tools 2019以降をインストール推奨
REM   - ビルド時間: 10～30分程度
REM ============================================================================

echo.
echo ========================================
echo   MediaForge Studio ビルドツール
echo   Nuitka版（高速実行・最適化）
echo ========================================
echo.

REM ----------------------------------------------------------------------------
REM 環境チェック
REM ----------------------------------------------------------------------------

echo [1/7] 環境をチェックしています...

REM Python インストールチェック
python --version >nul 2>&1
if errorlevel 1 (
    echo [エラー] Pythonがインストールされていません
    echo https://www.python.org/ からPython 3.10以上をインストールしてください
    pause
    exit /b 1
)

echo   - Python: OK

REM Nuitka インストールチェック
python -c "import nuitka" >nul 2>&1
if errorlevel 1 (
    echo [警告] Nuitkaがインストールされていません
    echo インストールを開始します...
    pip install nuitka ordered-set zstandard
    if errorlevel 1 (
        echo [エラー] Nuitkaのインストールに失敗しました
        pause
        exit /b 1
    )
)

echo   - Nuitka: OK

REM アイコンファイルチェック
if not exist "Appimg.ico" (
    echo [警告] Appimg.icoが見つかりません
    echo アイコンなしでビルドを続行します...
    set ICON_PARAM=
) else (
    echo   - アイコン: OK
    set ICON_PARAM=--windows-icon-from-ico=Appimg.ico
)

echo.

REM ----------------------------------------------------------------------------
REM C++コンパイラチェック
REM ----------------------------------------------------------------------------

echo [2/7] C++コンパイラをチェックしています...

where cl.exe >nul 2>&1
if errorlevel 1 (
    echo [警告] MSVC（Visual Studio C++コンパイラ）が見つかりません
    echo.
    echo Nuitkaはネイティブコンパイルのため、C++コンパイラが必要です。
    echo.
    echo インストール方法:
    echo   1. Visual Studio Community 2019以降をインストール
    echo      https://visualstudio.microsoft.com/ja/downloads/
    echo   2. または、Build Tools for Visual Studio をインストール
    echo      https://visualstudio.microsoft.com/ja/downloads/#build-tools-for-visual-studio-2022
    echo   3. インストール時に「C++によるデスクトップ開発」を選択
    echo.
    echo それでも続行しますか？（Nuitkaが自動でMinGWをダウンロードする可能性があります）
    echo.
    choice /c YN /m "続行しますか？ (Y/N)"
    if errorlevel 2 exit /b 1
    echo.
    echo   - コンパイラ: MinGW自動ダウンロード予定
) else (
    echo   - MSVC: OK
)

echo.

REM ----------------------------------------------------------------------------
REM クリーンアップ（オプション）
REM ----------------------------------------------------------------------------

if "%1"=="clean" (
    echo [3/7] 既存のビルド成果物を削除しています...

    if exist "MediaForgeStudio.build" (
        echo   - ビルドキャッシュ削除中...
        rmdir /s /q MediaForgeStudio.build
    )

    if exist "MediaForgeStudio.dist" (
        echo   - 成果物フォルダ削除中...
        rmdir /s /q MediaForgeStudio.dist
    )

    if exist "MediaForgeStudio.exe" (
        echo   - 旧EXEファイル削除中...
        del /q MediaForgeStudio.exe
    )

    echo   完了
    echo.
) else (
    echo [3/7] クリーンアップをスキップ（cleanオプションなし）
    echo.
)

REM ----------------------------------------------------------------------------
REM ビルドモード選択
REM ----------------------------------------------------------------------------

echo [4/7] ビルドモードを確認しています...

set BUILD_MODE=standalone
set EXTRA_PARAMS=

if "%1"=="onefile" (
    echo   モード: 単一EXEファイル（推奨）
    set BUILD_MODE=onefile
    set EXTRA_PARAMS=--onefile
) else if "%2"=="onefile" (
    echo   モード: 単一EXEファイル（推奨）
    set BUILD_MODE=onefile
    set EXTRA_PARAMS=--onefile
) else (
    echo   モード: スタンドアロン（フォルダ形式）
    set BUILD_MODE=standalone
    set EXTRA_PARAMS=--standalone
)

if "%1"=="debug" (
    echo   デバッグ: 有効（コンソール表示）
    set EXTRA_PARAMS=%EXTRA_PARAMS% --windows-console-mode=attach
) else if "%2"=="debug" (
    echo   デバッグ: 有効（コンソール表示）
    set EXTRA_PARAMS=%EXTRA_PARAMS% --windows-console-mode=attach
) else (
    set EXTRA_PARAMS=%EXTRA_PARAMS% --windows-console-mode=disable
)

echo.

REM ----------------------------------------------------------------------------
REM 依存関係チェック
REM ----------------------------------------------------------------------------

echo [5/7] 依存関係をチェックしています...
echo   必要なパッケージの存在確認中...

python -c "import PySide6" >nul 2>&1
if errorlevel 1 (
    echo [エラー] PySide6がインストールされていません
    echo pip install -r requirements.txt を実行してください
    pause
    exit /b 1
)

echo   - PySide6: OK

python -c "import qfluentwidgets" >nul 2>&1
if errorlevel 1 (
    echo [エラー] qfluentwidgetsがインストールされていません
    echo pip install -r requirements.txt を実行してください
    pause
    exit /b 1
)

echo   - qfluentwidgets: OK
echo   依存関係チェック完了
echo.

REM ----------------------------------------------------------------------------
REM FFmpegチェック（警告のみ）
REM ----------------------------------------------------------------------------

echo [6/7] 外部ツールをチェックしています...

where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo [警告] FFmpegが見つかりません
    echo アプリは動作しますが、動画・音声処理が使えません
    echo インストール推奨: choco install ffmpeg
) else (
    echo   - FFmpeg: OK
)

echo.

REM ----------------------------------------------------------------------------
REM ビルド実行
REM ----------------------------------------------------------------------------

echo [7/7] ビルドを開始します...
echo.
echo ----------------------------------------
echo   ビルド設定サマリー
echo ----------------------------------------
echo   プロジェクト: MediaForge Studio
echo   ビルド方法: Nuitka %BUILD_MODE%
echo   アイコン: Appimg.ico
echo   最適化: 有効
echo   想定ビルド時間: 10～30分
echo ----------------------------------------
echo.
echo ビルド中... しばらくお待ちください
echo （初回は特に時間がかかります）
echo.

python -m nuitka ^
    --mingw64 ^
    %EXTRA_PARAMS% ^
    --enable-plugin=pyside6 ^
    --enable-plugin=numpy ^
    --disable-console ^
    --windows-company-name="MediaForge" ^
    --windows-product-name="MediaForge Studio" ^
    --windows-file-version=1.0.0.0 ^
    --windows-product-version=1.0.0.0 ^
    --windows-file-description="YouTube Video Processing and Dubbing Tool" ^
    %ICON_PARAM% ^
    --assume-yes-for-downloads ^
    --output-dir=nuitka_build ^
    --include-data-dir=app=app ^
    --nofollow-import-to=pytest ^
    --nofollow-import-to=unittest ^
    --nofollow-import-to=test ^
    --nofollow-import-to=tkinter ^
    --nofollow-import-to=matplotlib ^
    main.py

if errorlevel 1 (
    echo.
    echo [エラー] ビルドに失敗しました
    echo ログを確認してください
    pause
    exit /b 1
)

echo.
echo   ビルド完了！
echo.

REM ----------------------------------------------------------------------------
REM ビルド後処理
REM ----------------------------------------------------------------------------

echo ビルド後処理を実行しています...

REM 出力フォルダを確認
if "%BUILD_MODE%"=="onefile" (
    set OUTPUT_DIR=nuitka_build
    set OUTPUT_EXE=main.exe
) else (
    set OUTPUT_DIR=nuitka_build\main.dist
    set OUTPUT_EXE=main.exe
)

REM EXEファイル名を変更
if exist "%OUTPUT_DIR%\%OUTPUT_EXE%" (
    echo   - EXEファイル名を変更中...
    move /y "%OUTPUT_DIR%\%OUTPUT_EXE%" "%OUTPUT_DIR%\MediaForgeStudio.exe" >nul 2>&1
    echo     完了
)

REM FFmpegをコピー（存在する場合）
where ffmpeg >nul 2>&1
if not errorlevel 1 (
    echo   - FFmpegをコピー中...

    for /f "delims=" %%i in ('where ffmpeg') do set FFMPEG_PATH=%%i
    for /f "delims=" %%i in ('where ffprobe') do set FFPROBE_PATH=%%i

    if exist "%OUTPUT_DIR%\" (
        copy /y "%FFMPEG_PATH%" "%OUTPUT_DIR%\" >nul 2>&1
        copy /y "%FFPROBE_PATH%" "%OUTPUT_DIR%\" >nul 2>&1
        echo     完了
    )
)

REM .envファイルをコピー
if exist ".env.example" (
    echo   - .env.exampleをコピー中...
    if exist "%OUTPUT_DIR%\" (
        copy /y ".env.example" "%OUTPUT_DIR%\.env.example" >nul 2>&1
        echo     完了
    )
)

REM READMEをコピー
if exist "README.md" (
    echo   - README.mdをコピー中...
    if exist "%OUTPUT_DIR%\" (
        copy /y "README.md" "%OUTPUT_DIR%\README.md" >nul 2>&1
        echo     完了
    )
)

REM 出力フォルダを dist に移動（統一のため）
if exist "dist" rmdir /s /q dist
mkdir dist
echo   - 成果物をdistフォルダに移動中...
if "%BUILD_MODE%"=="onefile" (
    mkdir dist\MediaForgeStudio
    move /y "%OUTPUT_DIR%\MediaForgeStudio.exe" "dist\MediaForgeStudio\" >nul 2>&1
    if exist "%OUTPUT_DIR%\ffmpeg.exe" copy /y "%OUTPUT_DIR%\ffmpeg.exe" "dist\MediaForgeStudio\" >nul 2>&1
    if exist "%OUTPUT_DIR%\ffprobe.exe" copy /y "%OUTPUT_DIR%\ffprobe.exe" "dist\MediaForgeStudio\" >nul 2>&1
    if exist "%OUTPUT_DIR%\.env.example" copy /y "%OUTPUT_DIR%\.env.example" "dist\MediaForgeStudio\" >nul 2>&1
    if exist "%OUTPUT_DIR%\README.md" copy /y "%OUTPUT_DIR%\README.md" "dist\MediaForgeStudio\" >nul 2>&1
) else (
    move /y "%OUTPUT_DIR%" "dist\MediaForgeStudio" >nul 2>&1
)
echo     完了

echo.
echo ============================================
echo   ビルド成功！
echo ============================================
echo.
echo 出力場所:
echo   dist\MediaForgeStudio\MediaForgeStudio.exe
echo.
echo 実行方法:
echo   1. dist\MediaForgeStudio\ フォルダごと移動
echo   2. MediaForgeStudio.exe をダブルクリック
echo.
echo 配布方法:
echo   dist\MediaForgeStudio\ フォルダをZIP圧縮
echo.
echo Nuitkaの利点:
echo   - 起動速度が高速
echo   - パフォーマンスが最適化
echo   - ファイルサイズが小さい
echo.
echo ============================================
echo.

pause
