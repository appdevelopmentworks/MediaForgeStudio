@echo off
REM MediaForge Studio - Build Script
REM Character Encoding: Shift_JIS (CP932)

echo ========================================
echo MediaForge Studio - Build Script
echo ========================================
echo.

REM Check if virtual environment exists
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Clean up old build files
echo Cleaning up old build files...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build with PyInstaller
echo.
echo Building executable with PyInstaller...
echo.
pyinstaller MediaForgeStudio.spec

REM Check build result
if exist dist\MediaForgeStudio\MediaForgeStudio.exe (
    echo.
    echo ========================================
    echo Build successful!
    echo ========================================
    echo.
    echo Executable location: dist\MediaForgeStudio\MediaForgeStudio.exe
    echo.
    echo Additional steps required:
    echo 1. Copy FFmpeg binaries to dist\MediaForgeStudio\
    echo 2. Create .env file in dist\MediaForgeStudio\ with your API keys
    echo 3. Test the executable before distribution
    echo.
) else (
    echo.
    echo ========================================
    echo Build failed!
    echo ========================================
    echo.
    echo Please check the error messages above.
)

pause
