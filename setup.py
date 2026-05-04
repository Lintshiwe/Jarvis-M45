"""Cross-platform setup script for JARVIS M45"""
import platform
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OS = platform.system()  # "Windows" | "Darwin" | "Linux"


def run(cmd: list[str], desc: str = "") -> bool:
    """Run a command, return True on success."""
    print(f"\n  {desc or ' '.join(cmd)}", flush=True)
    try:
        subprocess.run(cmd, check=True, cwd=str(BASE_DIR))
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ⚠️  Warning (non-fatal): {e}", flush=True)
        return False
    except FileNotFoundError:
        print(f"  ⚠️  Command not found: {cmd[0]}", flush=True)
        return False


def pip_install(pkg: str) -> bool:
    return run([sys.executable, "-m", "pip", "install", pkg],
               desc=f"pip install {pkg}")


def install_core():
    """Install core Python dependencies."""
    print("\n📦 Installing core Python dependencies...", flush=True)
    return run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
               desc="pip install -r requirements.txt")


def install_platform_deps():
    """Install platform-specific Python packages."""
    print(f"\n💻 Detected OS: {OS}", flush=True)

    if OS == "Windows":
        print("  Installing Windows-specific packages...", flush=True)
        win_deps = [
            "pygetwindow>=0.0.9",
            "pywinauto>=0.6.8",
            "win10toast>=0.9",
            "comtypes>=1.4.0",
            "pycaw>=20240210",
        ]
        for dep in win_deps:
            pip_install(dep)

    elif OS == "Darwin":
        print("  Installing macOS-specific packages...", flush=True)
        pip_install("pyobjc-framework-Cocoa>=10.0")

    elif OS == "Linux":
        print("  Linux detected — most features use system utilities.", flush=True)
        print("  If some features fail, install:", flush=True)
        print("    • wmctrl / xdotool          — window management", flush=True)
        print("    • gnome-screenshot-tool      — screen capture", flush=True)
        print("    • pactl (pulseaudio-utils)   — volume control", flush=True)
        print("    • brightnessctl              — brightness control", flush=True)
        print("    • gnome-control-center       — settings navigation", flush=True)

    else:
        print(f"  Unknown OS '{OS}' — skipping platform packages.", flush=True)


def install_playwright():
    """Install Playwright browser binaries."""
    print("\n🌐 Installing Playwright browser binaries...", flush=True)
    return run([sys.executable, "-m", "playwright", "install"],
               desc="playwright install")


def create_directories():
    """Ensure required directories exist."""
    dirs = [
        BASE_DIR / "config",
        BASE_DIR / "memory",
        BASE_DIR / "documents",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    # Ensure default config file exists (empty, user fills in API key)
    api_file = BASE_DIR / "config" / "api_keys.json"
    if not api_file.exists():
        api_file.write_text("{}\n", encoding="utf-8")
        print(f"  Created: {api_file}", flush=True)

    # Ensure default memory file
    mem_file = BASE_DIR / "memory" / "long_term.json"
    if not mem_file.exists():
        import json
        default_mem = {
            "identity": {},
            "preferences": {},
            "projects": {},
            "relationships": {},
            "wishes": {},
            "notes": {},
        }
        mem_file.write_text(json.dumps(default_mem, indent=2), encoding="utf-8")
        print(f"  Created: {mem_file}", flush=True)


def main():
    print("=" * 60, flush=True)
    print("  J.A.R.V.I.S — M45   Setup", flush=True)
    print("=" * 60, flush=True)

    create_directories()

    if not install_core():
        print("\n❌ Core dependency installation failed.", flush=True)
        print("   Try: pip install -r requirements.txt", flush=True)
        sys.exit(1)

    install_platform_deps()

    if not install_playwright():
        print("\n⚠️  Playwright browser install failed.", flush=True)
        print("   Run: playwright install", flush=True)

    print("\n" + "=" * 60, flush=True)
    print("✅ Setup complete!", flush=True)
    print(f"   Run: {sys.executable} main.py", flush=True)
    print("   On first launch, enter your Gemini API key in the setup overlay.", flush=True)
    print("=" * 60, flush=True)


if __name__ == "__main__":
    main()
