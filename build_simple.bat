@echo off
echo Building MediaForge Studio...
echo.

REM Clean old builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Simple PyInstaller command
pyinstaller --name MediaForgeStudio --icon=arisa004.ico --windowed --onedir main.py

echo.
echo Done! Check dist\MediaForgeStudio\ folder
pause
