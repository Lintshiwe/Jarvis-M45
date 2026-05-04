import time
import subprocess
import platform
import shutil
import re
from pathlib import Path

try:
    import psutil
    _PSUTIL = True
except ImportError:
    _PSUTIL = False

_SYSTEM = platform.system()

_APP_ALIASES: dict[str, dict[str, str]] = {

    "chrome":             {"Windows": "chrome",                  "Darwin": "Google Chrome",        "Linux": "google-chrome"},
    "google chrome":      {"Windows": "chrome",                  "Darwin": "Google Chrome",        "Linux": "google-chrome"},
    "firefox":            {"Windows": "firefox",                 "Darwin": "Firefox",              "Linux": "firefox"},
    "edge":               {"Windows": "msedge",                  "Darwin": "Microsoft Edge",       "Linux": "microsoft-edge"},
    "brave":              {"Windows": "brave",                   "Darwin": "Brave Browser",        "Linux": "brave-browser"},
    "safari":             {"Windows": "msedge",                  "Darwin": "Safari",               "Linux": "firefox"},
    "opera":              {"Windows": "opera",                   "Darwin": "Opera",                "Linux": "opera"},
    "whatsapp":           {"Windows": "WhatsApp",                "Darwin": "WhatsApp",             "Linux": "whatsapp"},
    "telegram":           {"Windows": "Telegram",                "Darwin": "Telegram",             "Linux": "telegram"},
    "discord":            {"Windows": "Discord",                 "Darwin": "Discord",              "Linux": "discord"},
    "slack":              {"Windows": "Slack",                   "Darwin": "Slack",                "Linux": "slack"},
    "zoom":               {"Windows": "Zoom",                    "Darwin": "zoom.us",              "Linux": "zoom"},
    "teams":              {"Windows": "msteams",                 "Darwin": "Microsoft Teams",      "Linux": "teams"},
    "skype":              {"Windows": "skype",                   "Darwin": "Skype",                "Linux": "skype"},
    "signal":             {"Windows": "signal",                  "Darwin": "Signal",               "Linux": "signal"},
    "spotify":            {"Windows": "Spotify",                 "Darwin": "Spotify",              "Linux": "spotify"},
    "vlc":                {"Windows": "vlc",                     "Darwin": "VLC",                  "Linux": "vlc"},
    "netflix":            {"Windows": "Netflix",                 "Darwin": "Netflix",              "Linux": "firefox"},
    "vscode":             {"Windows": "code",                    "Darwin": "Visual Studio Code",   "Linux": "code"},
    "visual studio code": {"Windows": "code",                    "Darwin": "Visual Studio Code",   "Linux": "code"},
    "code":               {"Windows": "code",                    "Darwin": "Visual Studio Code",   "Linux": "code"},
    "terminal":           {"Windows": "wt",                      "Darwin": "Terminal",             "Linux": "gnome-terminal"},
    "cmd":                {"Windows": "cmd.exe",                 "Darwin": "Terminal",             "Linux": "bash"},
    "powershell":         {"Windows": "powershell.exe",          "Darwin": "Terminal",             "Linux": "bash"},
    "postman":            {"Windows": "Postman",                 "Darwin": "Postman",              "Linux": "postman"},
    "git":                {"Windows": "git-bash",                "Darwin": "Terminal",             "Linux": "bash"},
    "figma":              {"Windows": "Figma",                   "Darwin": "Figma",                "Linux": "figma"},
    "blender":            {"Windows": "blender",                 "Darwin": "Blender",              "Linux": "blender"},
    "word":               {"Windows": "winword",                 "Darwin": "Microsoft Word",       "Linux": "libreoffice --writer"},
    "excel":              {"Windows": "excel",                   "Darwin": "Microsoft Excel",      "Linux": "libreoffice --calc"},
    "powerpoint":         {"Windows": "powerpnt",                "Darwin": "Microsoft PowerPoint", "Linux": "libreoffice --impress"},
    "libreoffice":        {"Windows": "soffice",                 "Darwin": "LibreOffice",          "Linux": "libreoffice"},
    "notepad":            {"Windows": "notepad.exe",             "Darwin": "TextEdit",             "Linux": "gedit"},
    "textedit":           {"Windows": "notepad.exe",             "Darwin": "TextEdit",             "Linux": "gedit"},
    "explorer":           {"Windows": "explorer.exe",            "Darwin": "Finder",               "Linux": "nautilus"},
    "file explorer":      {"Windows": "explorer.exe",            "Darwin": "Finder",               "Linux": "nautilus"},
    "finder":             {"Windows": "explorer.exe",            "Darwin": "Finder",               "Linux": "nautilus"},
    "task manager":       {"Windows": "taskmgr.exe",             "Darwin": "Activity Monitor",     "Linux": "gnome-system-monitor"},
    "settings":           {"Windows": "ms-settings:",            "Darwin": "System Preferences",   "Linux": "gnome-control-center"},
    "calculator":         {"Windows": "calc.exe",                "Darwin": "Calculator",           "Linux": "gnome-calculator"},
    "paint":              {"Windows": "mspaint.exe",             "Darwin": "Preview",              "Linux": "gimp"},
    "instagram":          {"Windows": "Instagram",               "Darwin": "Instagram",            "Linux": "firefox"},
    "tiktok":             {"Windows": "TikTok",                  "Darwin": "TikTok",               "Linux": "firefox"},
    "notion":             {"Windows": "Notion",                  "Darwin": "Notion",               "Linux": "notion"},
    "obsidian":           {"Windows": "Obsidian",                "Darwin": "Obsidian",             "Linux": "obsidian"},
    "capcut":             {"Windows": "CapCut",                  "Darwin": "CapCut",               "Linux": "capcut"},
    "steam":              {"Windows": "steam",                   "Darwin": "Steam",                "Linux": "steam"},
    "epic":               {"Windows": "EpicGamesLauncher",       "Darwin": "Epic Games Launcher",  "Linux": "legendary"},
    "epic games":         {"Windows": "EpicGamesLauncher",       "Darwin": "Epic Games Launcher",  "Linux": "legendary"},
}


def _normalize(raw: str) -> str:
    key = raw.lower().strip()

    if key in _APP_ALIASES:
        return _APP_ALIASES[key].get(_SYSTEM, raw)

    for alias_key, os_map in _APP_ALIASES.items():
        if alias_key in key or key in alias_key:
            return os_map.get(_SYSTEM, raw)

    return raw  

def _launch_windows(app_name: str) -> bool:

    if shutil.which(app_name) or shutil.which(app_name.split(".")[0]):
        try:
            subprocess.Popen(
                app_name,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(1.5)
            return True
        except Exception as e:
            print(f"[open_app] subprocess failed: {e}")

    if ":" in app_name:
        try:
            subprocess.Popen(f"start {app_name}", shell=True)
            time.sleep(1.0)
            return True
        except Exception:
            pass

    try:
        import pyautogui
        pyautogui.PAUSE = 0.1
        pyautogui.press("win")
        time.sleep(0.7)
        pyautogui.write(app_name, interval=0.05)
        time.sleep(0.9)
        pyautogui.press("enter")
        time.sleep(2.5)
        return True
    except Exception as e:
        print(f"[open_app] Start Menu search failed: {e}")

    return False


def _launch_macos(app_name: str) -> bool:

    try:
        result = subprocess.run(
            ["open", "-a", app_name],
            capture_output=True, timeout=8
        )
        if result.returncode == 0:
            time.sleep(1.0)
            return True
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["open", "-a", f"{app_name}.app"],
            capture_output=True, timeout=8
        )
        if result.returncode == 0:
            time.sleep(1.0)
            return True
    except Exception:
        pass

    binary = shutil.which(app_name) or shutil.which(app_name.lower())
    if binary:
        try:
            subprocess.Popen(
                [binary],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(1.0)
            return True
        except Exception:
            pass

    try:
        import pyautogui
        pyautogui.hotkey("command", "space")
        time.sleep(0.6)
        pyautogui.write(app_name, interval=0.05)
        time.sleep(0.8)
        pyautogui.press("enter")
        time.sleep(1.5)
        return True
    except Exception as e:
        print(f"[open_app] Spotlight failed: {e}")

    return False


def _verify_app_running(name: str) -> bool:
    """Check if an app is actually running by looking at process list."""
    try:
        import psutil
        import os as _os
        my_pid = _os.getpid()
        name_lower = name.lower().replace(" ", "-").replace(" ", "")

        # Skip checking against these (our own test/debug processes)
        skip_terms = ("python", "bash", "timeout", "sh", "zsh", "fish", "gnome-terminal",
                      "kitty", "alacritty", "konsole", "xfce4-terminal", "terminator")

        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['pid'] == my_pid:
                    continue
                pname = (proc.info['name'] or "").lower()

                # Skip shell/terminal/script processes
                if any(t in pname for t in skip_terms):
                    continue

                # Check process name for direct match (most reliable)
                if name_lower in pname:
                    return True

                # Check command line for the app binary
                cmd = " ".join(proc.info['cmdline'] or []).lower()
                # Only match if the binary name appears as a distinct word in cmdline
                # (not as a substring of a python script path etc)
                cmd_parts = cmd.split()
                for part in cmd_parts:
                    part = part.split("/")[-1]  # get just the binary name
                    if name_lower in part:
                        return True

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except ImportError:
        pass
    return False


def _launch_and_verify(cmd: list[str], app_name: str, wait: float = 2.0) -> bool:
    """Launch an app and verify it's running after a short wait."""
    try:
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(wait)
        return _verify_app_running(app_name)
    except Exception:
        return False


def _launch_linux(app_name: str) -> bool:

    # 1. Binary in $PATH
    binary = (
        shutil.which(app_name) or
        shutil.which(app_name.lower()) or
        shutil.which(app_name.lower().replace(" ", "-")) or
        shutil.which(app_name.lower().replace(" ", "_"))
    )
    if binary:
        try:
            subprocess.Popen(
                [binary],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(1.0)
            return True
        except Exception:
            pass

    # 2. Snap packages (check /snap/bin and /var/lib/snapd/snap)
    name_lower = app_name.lower().replace(" ", "-")
    snap_bin = f"/snap/bin/{name_lower}"
    if shutil.which("snap") and (Path(snap_bin).exists() if Path else True):
        try:
            result = subprocess.run(
                [snap_bin] if Path(snap_bin).exists() else ["snap", "run", name_lower],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10
            )
            if Path(snap_bin).exists():
                subprocess.Popen([snap_bin], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(1.0)
                return True
        except Exception:
            pass

    # 3. Flatpak packages
    if shutil.which("flatpak"):
        for flatpak_id in [
            app_name.lower(),
            app_name.lower().replace(" ", "."),
            f"com.{app_name.lower().replace(' ', '.')}",
            f"org.{app_name.lower().replace(' ', '.')}",
        ]:
            try:
                result = subprocess.run(
                    ["flatpak", "run", flatpak_id],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5
                )
                if result.returncode == 0:
                    time.sleep(0.5)
                    return True
            except Exception:
                pass
            try:
                result = subprocess.run(
                    ["flatpak", "run", f"{flatpak_id}.desktop"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5
                )
                if result.returncode == 0:
                    time.sleep(0.5)
                    return True
            except Exception:
                pass

    # 4. Search .desktop files for matching app
    desktop_dirs = [
        Path.home() / ".local" / "share" / "applications",
        Path("/usr/share/applications"),
        Path("/var/lib/flatpak/exports/share/applications"),
        Path.home() / ".local" / "share" / "flatpak" / "exports" / "share" / "applications",
    ]
    for ddir in desktop_dirs:
        if not ddir.exists():
            continue
        for df in ddir.glob("*.desktop"):
            try:
                content = df.read_text(errors="ignore").lower()
                if name_lower not in content and name_lower.replace("-", "") not in content:
                    continue
                # Parse Exec= line
                for line in content.splitlines():
                    if line.lower().startswith("exec="):
                        exe = line[5:].strip()
                        # Remove desktop file field codes
                        exe = re.sub(r'%[fFuUdDnNickvm]', '', exe).strip()
                        if exe:
                            subprocess.Popen(
                                exe.split() if " " in exe else [exe],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL
                            )
                            time.sleep(1.0)
                            return True
            except Exception:
                continue

    # 5. xdg-open (handles URLs and file associations)
    try:
        result = subprocess.run(
            ["xdg-open", app_name],
            capture_output=True, timeout=5
        )
        if result.returncode == 0:
            time.sleep(0.5)
            return True
    except Exception:
        pass

    # 6. gtk-launch (GNOME/GTK app launcher)
    for desktop_name in [
        app_name.lower(),
        name_lower,
        name_lower.replace(" ", ""),
    ]:
        try:
            result = subprocess.run(
                ["gtk-launch", desktop_name],
                capture_output=True, timeout=5
            )
            if result.returncode == 0:
                time.sleep(0.5)
                return True
        except Exception:
            pass

    # 7. GUI fallback via Super/Activities key and typing (GNOME/KDE/XFCE)
    try:
        import pyautogui
        pyautogui.PAUSE = 0.08
        pyautogui.press("super")
        time.sleep(0.6)
        pyautogui.write(app_name, interval=0.04)
        time.sleep(0.8)
        pyautogui.press("enter")
        time.sleep(2.0)
        return True
    except Exception:
        pass

    # 8. Web service fallback: open known web services via browser
    _WEB_SERVICES = {
        "instagram": "https://instagram.com",
        "tiktok": "https://tiktok.com",
        "netflix": "https://netflix.com",
        "twitter": "https://twitter.com",
        "x": "https://x.com",
        "facebook": "https://facebook.com",
        "reddit": "https://reddit.com",
        "linkedin": "https://linkedin.com",
        "pinterest": "https://pinterest.com",
        "snapchat": "https://snapchat.com",
        "youtube": "https://youtube.com",
        "twitch": "https://twitch.tv",
        "gmail": "https://mail.google.com",
        "outlook": "https://outlook.live.com",
        "calendar": "https://calendar.google.com",
        "maps": "https://maps.google.com",
        "translate": "https://translate.google.com",
        "drive": "https://drive.google.com",
        "docs": "https://docs.google.com",
        "sheets": "https://sheets.google.com",
        "slides": "https://slides.google.com",
        "photos": "https://photos.google.com",
        "chatgpt": "https://chat.openai.com",
        "claude": "https://claude.ai",
        "gemini": "https://gemini.google.com",
        "copilot": "https://copilot.microsoft.com",
        "perplexity": "https://perplexity.ai",
        "deepseek": "https://chat.deepseek.com",
        "github": "https://github.com",
        "gitlab": "https://gitlab.com",
        "stackoverflow": "https://stackoverflow.com",
        "wikipedia": "https://wikipedia.org",
        "amazon": "https://amazon.com",
        "ebay": "https://ebay.com",
        "spotify": "https://open.spotify.com",
        "soundcloud": "https://soundcloud.com",
        "canva": "https://canva.com",
        "figma": "https://figma.com",
        "notion": "https://notion.so",
        "trello": "https://trello.com",
        "slack": "https://slack.com",
        "discord": "https://discord.com/app",
        "telegram": "https://web.telegram.org",
        "whatsapp": "https://web.whatsapp.com",
        "web.whatsapp": "https://web.whatsapp.com",
        "messenger": "https://messenger.com",
        "zoom": "https://zoom.us",
        "teams": "https://teams.microsoft.com",
        "meet": "https://meet.google.com",
        "gimp": "https://www.photopea.com",
        "photoshop": "https://www.photopea.com",
    }
    web_key = name_lower.replace(" ", "").replace("-", "")
    for svc, url in _WEB_SERVICES.items():
        if svc in web_key or web_key in svc:
            try:
                subprocess.Popen(
                    ["xdg-open", url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                time.sleep(1.5)
                return True
            except Exception:
                pass

    return False


_OS_LAUNCHERS = {
    "Windows": _launch_windows,
    "Darwin":  _launch_macos,
    "Linux":   _launch_linux,
}

def open_app(
    parameters=None,
    response=None,
    player=None,
    session_memory=None,
) -> str:
    app_name = (parameters or {}).get("app_name", "").strip()

    if not app_name:
        return "No application name provided."

    launcher = _OS_LAUNCHERS.get(_SYSTEM)
    if launcher is None:
        return f"Unsupported operating system: {_SYSTEM}"

    normalized = _normalize(app_name)
    print(f"[open_app] Launching: '{app_name}' → '{normalized}' ({_SYSTEM})")

    if player:
        player.write_log(f"[open_app] {app_name}")

    try:
        launched = launcher(normalized)
        if not launched and normalized.lower() != app_name.lower():
            launched = launcher(app_name)

        if launched:
            # Verify the app actually started
            time.sleep(0.5)
            if _verify_app_running(normalized) or _verify_app_running(app_name):
                return f"Opened {app_name}."
            else:
                return (
                    f"I attempted to open {app_name}, but I cannot confirm it launched. "
                    f"It may not be installed, or it may need a moment to start. "
                    f"Please check manually, sir."
                )
        else:
            return (
                f"I couldn't find or launch {app_name}, sir. "
                f"It might not be installed on this system. "
                f"You can install it or try a different name."
            )
    except Exception as e:
        print(f"[open_app] Error: {e}")
        return f"Failed to open {app_name}: {e}"