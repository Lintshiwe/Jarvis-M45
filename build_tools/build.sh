#!/usr/bin/env bash
set -euo pipefail

# ── JARVIS M45 — Linux Build Script ─────────────────────────
# Creates a standalone executable at dist/JARVIS-M45
#
# Prerequisites:
#   python3 -m pip install -r requirements.txt pyinstaller
#   playwright install
#
# Output:
#   dist/JARVIS-M45 (binary)

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  J.A.R.V.I.S  JARVIS M45  —  Linux Build                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ── check prerequisites ───────────────────────────────────────────
echo "[1/5] Checking prerequisites..."
python3 -c "import PyInstaller" 2>/dev/null || {
    echo "  Installing PyInstaller..."
    python3 -m pip install pyinstaller
}

python3 -c "import google.genai" 2>/dev/null || {
    echo "  ❌ google-genai not installed. Run: pip install -r requirements.txt"
    exit 1
}

python3 -c "import PyQt6" 2>/dev/null || {
    echo "  ❌ PyQt6 not installed. Run: pip install -r requirements.txt"
    exit 1
}

echo "  ✅ All dependencies found"
echo ""

# ── clean previous builds ──────────────────────────────────────────
echo "[2/5] Cleaning previous builds..."
rm -rf "$ROOT/build" "$ROOT/dist"
find "$ROOT" -name "*.spec" -not -path "*/build_tools/*" -delete 2>/dev/null || true
echo "  ✅ Cleaned"
echo ""

# ── create template configs ────────────────────────────────────────
echo "[3/5] Preparing data files..."
python3 -c "
import json
from pathlib import Path

# Ensure config dir exists
cfg = Path('$ROOT/config')
cfg.mkdir(exist_ok=True)

# Empty API keys (user fills in at first run)
api = cfg / 'api_keys.json'
if not api.exists():
    api.write_text('{}')

# Empty memory template
mem_dir = Path('$ROOT/memory')
mem_dir.mkdir(exist_ok=True)
mem_file = mem_dir / 'long_term.json'
if not mem_file.exists():
    mem_file.write_text(json.dumps({
        'identity': {}, 'preferences': {}, 'projects': {},
        'relationships': {}, 'wishes': {}, 'notes': {},
    }, indent=2))

docs = Path('$ROOT/documents')
docs.mkdir(exist_ok=True)
"
echo "  ✅ Data files prepared"
echo ""

# ── build with PyInstaller ─────────────────────────────────────────
echo "[4/5] Building with PyInstaller..."
pyinstaller \
    --clean \
    --noconfirm \
    --onefile \
    --windowed \
    --name="JARVIS-M45" \
    --add-data "$ROOT/core/prompt.txt:core" \
    --add-data "$ROOT/face.png:." \
    --hidden-import google.genai \
    --hidden-import google.generativeai \
    --hidden-import google.api_core \
    --hidden-import google.auth \
    --hidden-import grpc \
    --hidden-import sounddevice \
    --hidden-import _sounddevice \
    --hidden-import soundfile \
    --hidden-import playwright \
    --hidden-import playwright.async_api \
    --hidden-import playwright._impl \
    --hidden-import PyQt6 \
    --hidden-import PyQt6.QtCore \
    --hidden-import PyQt6.QtGui \
    --hidden-import PyQt6.QtWidgets \
    --hidden-import PyQt6.sip \
    --hidden-import pptx \
    --hidden-import PIL \
    --hidden-import PIL.Image \
    --hidden-import PIL._tkinter_finder \
    --hidden-import duckduckgo_search \
    --hidden-import bs4 \
    --hidden-import requests \
    --hidden-import urllib3 \
    --hidden-import pyautogui \
    --hidden-import pyperclip \
    --hidden-import numpy \
    --hidden-import cv2 \
    --hidden-import mss \
    --hidden-import psutil \
    --hidden-import send2trash \
    --hidden-import youtube_transcript_api \
    --exclude-module tkinter \
    --exclude-module unittest \
    --exclude-module test \
    --exclude-module pdb \
    --exclude-module matplotlib \
    --exclude-module scipy \
    --exclude-module pandas \
    --exclude-module IPython \
    --exclude-module jupyter \
    "$ROOT/main.py" 2>&1
echo "  ✅ Build complete"
echo ""

# ── verify output ──────────────────────────────────────────────────
echo "[5/5] Verifying build output..."
BINARY="$ROOT/dist/JARVIS-M45"
if [ -f "$BINARY" ]; then
    SIZE=$(du -h "$BINARY" | cut -f1)
    echo "  ✅ Binary: $BINARY"
    echo "  📦 Size:   $SIZE"
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║  ✅ Build successful!                                      ║"
    echo "║                                                             ║"
    echo "║  Run:  dist/JARVIS-M45                              ║"
    echo "║                                                             ║"
    echo "║  Note: The first launch will prompt for your Gemini API key.║"
    echo "║  Playwright browsers must be installed on the target system.║"
    echo "╚══════════════════════════════════════════════════════════════╝"
else
    echo "  ❌ Binary not found. Build may have failed."
    exit 1
fi
