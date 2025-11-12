@echo off
chcp 932 >nul
REM ============================================================================
REM MediaForge Studio - PyInstaller ビルドスクリプト
REM ============================================================================
REM
REM 使い方:
REM   build_pyinstaller.bat [オプション]
REM
REM オプション:
REM   clean    - ビルド前に既存の成果物を削除
REM   onefile  - 単一EXEファイルとしてビルド（起動が遅い）
REM   debug    - デバッグモード（コンソール表示）
REM
REM 例:
REM   build_pyinstaller.bat
REM   build_pyinstaller.bat clean
REM   build_pyinstaller.bat onefile
REM ============================================================================

echo.
echo ========================================
echo   MediaForge Studio ビルドツール
echo   PyInstaller版
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

REM PyInstaller インストールチェック
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [警告] PyInstallerがインストールされていません
    echo インストールを開始します...
    pip install pyinstaller
    if errorlevel 1 (
        echo [エラー] PyInstallerのインストールに失敗しました
        pause
        exit /b 1
    )
)

echo   - PyInstaller: OK

REM アイコンファイルチェック
if not exist "Appimg.ico" (
    echo [警告] Appimg.icoが見つかりません
    echo アイコンなしでビルドを続行します...
    set ICON_PARAM=
) else (
    echo   - アイコン: OK
    set ICON_PARAM=--icon=Appimg.ico
)

REM .specファイルチェック
if not exist "MediaForgeStudio.spec" (
    echo [エラー] MediaForgeStudio.specが見つかりません
    pause
    exit /b 1
)

echo   - .spec: OK
echo.

REM ----------------------------------------------------------------------------
REM クリーンアップ（オプション）
REM ----------------------------------------------------------------------------

if "%1"=="clean" (
    echo [2/7] 既存のビルド成果物を削除しています...

    if exist "build" (
        echo   - buildフォルダ削除中...
        rmdir /s /q build
    )

    if exist "dist" (
        echo   - distフォルダ削除中...
        rmdir /s /q dist
    )

    if exist "*.spec~" (
        echo   - 一時ファイル削除中...
        del /q *.spec~
    )

    echo   完了
    echo.
) else (
    echo [2/7] クリーンアップをスキップ（cleanオプションなし）
    echo.
)

REM ----------------------------------------------------------------------------
REM ビルドモード選択
REM ----------------------------------------------------------------------------

echo [3/7] ビルドモードを確認しています...

set BUILD_MODE=spec
set EXTRA_PARAMS=

if "%1"=="onefile" (
    echo   モード: 単一EXEファイル（起動遅め）
    set BUILD_MODE=onefile
    set EXTRA_PARAMS=--onefile
) else if "%2"=="onefile" (
    echo   モード: 単一EXEファイル（起動遅め）
    set BUILD_MODE=onefile
    set EXTRA_PARAMS=--onefile
) else (
    echo   モード: フォルダ形式（推奨・起動速い）
    set BUILD_MODE=spec
)

if "%1"=="debug" (
    echo   デバッグ: 有効（コンソール表示）
    set EXTRA_PARAMS=%EXTRA_PARAMS% --console
) else if "%2"=="debug" (
    echo   デバッグ: 有効（コンソール表示）
    set EXTRA_PARAMS=%EXTRA_PARAMS% --console
)

echo.

REM ----------------------------------------------------------------------------
REM 依存関係チェック
REM ----------------------------------------------------------------------------

echo [4/7] 依存関係をチェックしています...
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

echo [5/7] 外部ツールをチェックしています...

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

echo [6/7] ビルドを開始します...
echo.
echo ----------------------------------------
echo   ビルド設定サマリー
echo ----------------------------------------
echo   プロジェクト: MediaForge Studio
echo   ビルド方法: %BUILD_MODE%
echo   アイコン: Appimg.ico
echo   出力先: dist\MediaForgeStudio\
echo ----------------------------------------
echo.

if "%BUILD_MODE%"=="onefile" (
    echo PyInstallerを実行中（単一EXEモード）...
    pyinstaller --clean %EXTRA_PARAMS% %ICON_PARAM% --name=MediaForgeStudio main.py
) else (
    echo PyInstallerを実行中（.specファイル使用）...
    pyinstaller --clean MediaForgeStudio.spec
)

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

echo [7/7] ビルド後処理を実行しています...

REM FFmpegを出力フォルダにコピー（存在する場合）
where ffmpeg >nul 2>&1
if not errorlevel 1 (
    echo   - FFmpegをコピー中...

    for /f "delims=" %%i in ('where ffmpeg') do set FFMPEG_PATH=%%i
    for /f "delims=" %%i in ('where ffprobe') do set FFPROBE_PATH=%%i

    if exist "dist\MediaForgeStudio\" (
        copy /y "%FFMPEG_PATH%" "dist\MediaForgeStudio\" >nul 2>&1
        copy /y "%FFPROBE_PATH%" "dist\MediaForgeStudio\" >nul 2>&1
        echo     完了
    )
)

REM .envファイルをコピー（存在する場合）
if exist ".env.example" (
    echo   - .env.exampleをコピー中...
    if exist "dist\MediaForgeStudio\" (
        copy /y ".env.example" "dist\MediaForgeStudio\.env.example" >nul 2>&1
        echo     完了
    )
)

REM READMEをコピー（存在する場合）
if exist "README.md" (
    echo   - README.mdをコピー中...
    if exist "dist\MediaForgeStudio\" (
        copy /y "README.md" "dist\MediaForgeStudio\README.md" >nul 2>&1
        echo     完了
    )
)

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
echo ============================================
echo.

pause
