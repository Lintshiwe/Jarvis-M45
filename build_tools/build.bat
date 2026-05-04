@echo off
REM ── JARVIS M45 — Windows Build Script ─────────────────────────
REM Creates a standalone executable at dist\JARVIS-M45.exe
REM
REM Prerequisites:
REM   python -m pip install -r requirements.txt pyinstaller
REM   playwright install
REM
REM Output:
REM   dist\JARVIS-M45.exe

setlocal enabledelayedexpansion
set ROOT=%~dp0..

cd /d "%ROOT%"

echo ╔══════════════════════════════════════════════════════════════╗
echo ║  J.A.R.V.I.S  M45  —  Windows Build                ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM ── check prerequisites ───────────────────────────────────────────
echo [1/5] Checking prerequisites...
python -c "import PyInstaller" >nul 2>&1 || (
    echo   Installing PyInstaller...
    python -m pip install pyinstaller
)

python -c "import google.genai" >nul 2>&1 || (
    echo   google-genai not installed. Installing...
    python -m pip install google-genai
)

python -c "import PyQt6" >nul 2>&1 || (
    echo   PyQt6 not installed. Installing...
    python -m pip install PyQt6
)
echo   All dependencies found
echo.

REM ── clean previous builds ──────────────────────────────────────────
echo [2/5] Cleaning previous builds...
if exist "%ROOT%\build" rmdir /s /q "%ROOT%\build"
if exist "%ROOT%\dist" rmdir /s /q "%ROOT%\dist"
for %%f in ("%ROOT%\*.spec") do (
    if not "%%~nxf"=="jarvios-m45.spec" del "%%f"
)
echo   Cleaned
echo.

REM ── create template configs ────────────────────────────────────────
echo [3/5] Preparing data files...
python -c "import json; from pathlib import Path; cfg=Path(r'%ROOT%/config'); cfg.mkdir(exist_ok=True); api=cfg/'api_keys.json'; api.exists() or api.write_text('{}'); mem=Path(r'%ROOT%/memory'); mem.mkdir(exist_ok=True); mf=mem/'long_term.json'; mf.exists() or mf.write_text(json.dumps({'identity':{},'preferences':{},'projects':{},'relationships':{},'wishes':{},'notes':{}},indent=2)); Path(r'%ROOT%/documents').mkdir(exist_ok=True)"
echo   Data files prepared
echo.

REM ── build with PyInstaller ─────────────────────────────────────────
echo [4/5] Building with PyInstaller...
pyinstaller ^
    --clean ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --name="JARVIS-M45" ^
    --add-data "%ROOT%\core\prompt.txt;core" ^
    --add-data "%ROOT%\face.png;." ^
    --hidden-import google.genai ^
    --hidden-import google.generativeai ^
    --hidden-import google.api_core ^
    --hidden-import google.auth ^
    --hidden-import grpc ^
    --hidden-import sounddevice ^
    --hidden-import _sounddevice ^
    --hidden-import soundfile ^
    --hidden-import playwright ^
    --hidden-import playwright.async_api ^
    --hidden-import playwright._impl ^
    --hidden-import PyQt6 ^
    --hidden-import PyQt6.QtCore ^
    --hidden-import PyQt6.QtGui ^
    --hidden-import PyQt6.QtWidgets ^
    --hidden-import PyQt6.sip ^
    --hidden-import pptx ^
    --hidden-import PIL ^
    --hidden-import PIL.Image ^
    --hidden-import PIL._tkinter_finder ^
    --hidden-import duckduckgo_search ^
    --hidden-import bs4 ^
    --hidden-import requests ^
    --hidden-import urllib3 ^
    --hidden-import pyautogui ^
    --hidden-import pyperclip ^
    --hidden-import numpy ^
    --hidden-import cv2 ^
    --hidden-import mss ^
    --hidden-import psutil ^
    --hidden-import send2trash ^
    --hidden-import youtube_transcript_api ^
    --exclude-module tkinter ^
    --exclude-module unittest ^
    --exclude-module test ^
    --exclude-module pdb ^
    --exclude-module matplotlib ^
    --exclude-module scipy ^
    --exclude-module pandas ^
    --exclude-module IPython ^
    --exclude-module jupyter ^
    "%ROOT%\main.py"
echo   Build complete
echo.

REM ── verify output ──────────────────────────────────────────────────
echo [5/5] Verifying build output...
if exist "%ROOT%\dist\JARVIS-M45.exe" (
    echo   Binary: %ROOT%\dist\JARVIS-M45.exe
    echo.
    echo ╔══════════════════════════════════════════════════════════════╗
    echo ║  Build successful!                                       ║
    echo ║                                                          ║
    echo ║  Run: dist\JARVIS-M45.exe                        ║
    echo ║                                                          ║
    echo ║  Note: First launch prompts for your Gemini API key.     ║
    echo ║  Playwright browsers must be installed on target system. ║
    echo ╚══════════════════════════════════════════════════════════════╝
) else (
    echo   Binary not found - build may have failed.
    exit /b 1
)
