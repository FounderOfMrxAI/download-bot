@echo off
setlocal
cd /d "%~dp0"
title Download Bot - Building EXE

echo [1/3] Installing required packages...
py -m pip install --upgrade pip >nul 2>&1
py -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto fail

if not exist "ffmpeg\ffmpeg.exe" (
    echo [2/3] Downloading ffmpeg ^(one time, ~100 MB^)...
    powershell -NoProfile -ExecutionPolicy Bypass -File "tools\get_ffmpeg.ps1"
    if errorlevel 1 goto fail
) else (
    echo [2/3] ffmpeg already present.
)

echo [3/3] Building DownloadBot.exe...
py -m PyInstaller --noconfirm --clean --onefile --noconsole ^
    --name DownloadBot ^
    --icon icon.ico ^
    --collect-all customtkinter ^
    --collect-all yt_dlp ^
    --add-binary "ffmpeg\ffmpeg.exe;." ^
    --add-data "icon.ico;." ^
    indirme_botu.py
if errorlevel 1 goto fail

echo.
echo Done: dist\DownloadBot.exe
pause
exit /b 0

:fail
echo.
echo Something went wrong. Check the messages above.
pause
exit /b 1
