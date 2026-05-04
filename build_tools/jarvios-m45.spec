# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for JARVIS M45
Cross-platform: Windows, macOS, Linux

Build:
    pyinstaller --clean build_tools/jarvios-m45.spec
    # or use the build scripts:
    #   Linux:   bash build_tools/build.sh
    #   Windows: build_tools\build.bat
    #   macOS:   bash build_tools/build.command
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ── hidden imports ──────────────────────────────────────────────────
hiddenimports = [
    "google.genai", "google.generativeai", "google.api_core",
    "google.auth", "grpc",
    "sounddevice", "_sounddevice", "soundfile",
    "playwright", "playwright.async_api", "playwright._impl",
    "PyQt6", "PyQt6.QtCore", "PyQt6.QtGui", "PyQt6.QtWidgets", "PyQt6.sip",
    "pptx", "PIL", "PIL.Image", "PIL._tkinter_finder",
    "duckduckgo_search", "bs4", "requests", "urllib3",
    "pyautogui", "pyperclip", "numpy", "cv2", "mss", "psutil",
    "send2trash", "youtube_transcript_api",
]

excluded = [
    "tkinter", "test", "unittest", "pdb",
    "distutils", "setuptools", "pip", "wheel",
    "IPython", "jupyter", "notebook",
    "matplotlib", "scipy", "pandas",
]

# ── data files ──────────────────────────────────────────────────────
datas = [
    (str(ROOT / "core" / "prompt.txt"), "core"),
    (str(ROOT / "face.png"), "."),
]

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excluded,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="JARVIS-M45",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / "face.png") if (ROOT / "face.png").exists() else None,
)

if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="JARVIS-M45.app",
        icon=str(ROOT / "face.png") if (ROOT / "face.png").exists() else None,
        bundle_identifier="com.jarvios.m45",
        info_plist={
            "NSPrincipalClass": "NSApplication",
            "NSHighResolutionCapable": True,
            "CFBundleName": "JARVIS M45",
            "CFBundleDisplayName": "JARVIS",
            "CFBundleShortVersionString": "2.0.0",
            "CFBundleVersion": "2.0.0",
            "CFBundleExecutable": "JARVIS-M45",
            "NSMicrophoneUsageDescription": "JARVIS needs microphone access for voice commands.",
            "NSCameraUsageDescription": "JARVIS needs camera access for screen/vision features.",
        },
    )
