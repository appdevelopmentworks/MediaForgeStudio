@echo off
echo ========================================
echo MediaForge Studio - Build with FFmpeg
echo ========================================
echo.

REM Clean old builds
echo Cleaning old build files...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build with PyInstaller
echo.
echo Building executable...
pyinstaller MediaForgeStudio.spec

REM Check if build succeeded
if not exist dist\MediaForgeStudio\MediaForgeStudio.exe (
    echo.
    echo Build failed! Please check errors above.
    pause
    exit /b 1
)

REM Copy FFmpeg binaries
echo.
echo Copying FFmpeg binaries...
copy C:\ffmpeg\bin\ffmpeg.exe dist\MediaForgeStudio\
copy C:\ffmpeg\bin\ffprobe.exe dist\MediaForgeStudio\

REM Copy .env.example
echo.
echo Copying .env.example...
copy .env.example dist\MediaForgeStudio\

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Executable: dist\MediaForgeStudio\MediaForgeStudio.exe
echo.
echo Next steps:
echo 1. Copy .env.example to .env and add your API keys
echo 2. Test the executable
echo.

pause
