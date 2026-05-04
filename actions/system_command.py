# system_command.py — Jarvis system shell & diagnostics (cross‑platform)
import json
import os
import platform
import re
import subprocess
import sys
import time
from pathlib import Path

_OS = platform.system()  # "Windows" | "Darwin" | "Linux"

# ── safety ──────────────────────────────────────────────────────────
_FORBIDDEN_COMMANDS = [
    "rm -rf /", "rm -rf /*", "rm -rf ~", "rm -rf .",
    "mkfs.", "dd if=", ":(){ :|:& };:",
    "chmod 777 /", "chmod -R 777 /",
    "shutdown", "reboot", "poweroff", "halt",
]

_DANGEROUS_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"rm\s+-rf\s+~",
    r"mkfs\.\w+\s+/dev",
    r"dd\s+if=",
    r">\s*/dev/(?!null|zero|random|urandom)",
    r"chmod\s+.*777\s+/",
    r":\(\)\s*\{",
]


def _get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


_BASE = _get_base_dir()


def _get_api_key() -> str:
    path = _BASE / "config" / "api_keys.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["gemini_api_key"]


def _is_safe_command(command: str) -> tuple[bool, str]:
    cmd_lower = command.lower().strip()
    for forbidden in _FORBIDDEN_COMMANDS:
        if forbidden in cmd_lower:
            return False, f"Forbidden: contains dangerous pattern '{forbidden}'"
    for pattern in _DANGEROUS_PATTERNS:
        if re.search(pattern, cmd_lower):
            return False, f"Forbidden: matches dangerous pattern '{pattern}'"
    return True, ""


def _get_shell_executable() -> str | None:
    """Return the best available shell for the current OS."""
    if _OS == "Windows":
        for exe in ["powershell.exe", "pwsh.exe", "cmd.exe"]:
            if shutil_which(exe):
                return exe
        return None
    else:
        for exe in ["/bin/bash", "/bin/zsh", "/bin/sh"]:
            if os.path.exists(exe):
                return exe
        return "/bin/sh"


def _shutil_which(name: str) -> str | None:
    """Safe shutil.which."""
    try:
        from shutil import which
        return which(name)
    except Exception:
        for p in os.environ.get("PATH", "").split(os.pathsep):
            full = os.path.join(p, name)
            if os.path.isfile(full) and os.access(full, os.X_OK):
                return full
    return None


shutil_which = _shutil_which

# ── diagnostic commands per OS ──────────────────────────────────────
_DIAGNOSTICS = {
    "disk": {
        "Linux":   "df -h && echo '---' && lsblk -o NAME,SIZE,TYPE,MOUNTPOINT 2>/dev/null",
        "Darwin":  "df -h && echo '---' && diskutil list 2>/dev/null",
        "Windows": "Get-PSDrive -PSProvider FileSystem | Format-Table Name,Used,Free,Root -AutoSize; Write-Host '---'; Get-Disk | Format-Table Number,Size,PartitionStyle -AutoSize",
    },
    "memory": {
        "Linux":   "free -h && echo '---' && vmstat -s | head -20",
        "Darwin":  "vm_stat && echo '---' && sysctl hw.memsize && echo '---' && top -l 1 -s 0 | grep PhysMem",
        "Windows": "Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize,FreePhysicalMemory; Write-Host '---'; Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 10 Name,WorkingSet64 | Format-Table -AutoSize",
    },
    "system": {
        "Linux":   "uname -a && echo '---' && cat /etc/os-release 2>/dev/null && echo '---' && uptime",
        "Darwin":  "uname -a && echo '---' && sw_vers && echo '---' && uptime",
        "Windows": "Get-ComputerInfo | Select-Object WindowsVersion,OsName,CsProcessors,CsTotalPhysicalMemory | Format-List; Write-Host '---'; Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer,Model,TotalPhysicalMemory | Format-List",
    },
    "cpu": {
        "Linux":   "lscpu | head -20 && echo '---' && uptime",
        "Darwin":  "sysctl -n machdep.cpu.brand_string && echo '---' && sysctl hw.ncpu && echo '---' && uptime",
        "Windows": "Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,MaxClockSpeed | Format-List; Write-Host '---'; Get-Counter '\\Processor(_Total)\\% Processor Time' | Select-Object -ExpandProperty CounterSamples | Select-Object CookedValue | Format-List",
    },
    "network": {
        "Linux":   "ip addr show && echo '---' && ip route && echo '---' && ss -tuln 2>/dev/null | head -20",
        "Darwin":  "ifconfig && echo '---' && netstat -rn && echo '---' && lsof -iTCP -sTCP:LISTEN -P -n 2>/dev/null | head -20",
        "Windows": "Get-NetIPAddress -AddressFamily IPv4 | Format-Table InterfaceAlias,IPAddress -AutoSize; Write-Host '---'; Get-NetRoute | Format-Table DestinationPrefix,NextHop -AutoSize; Write-Host '---'; Get-NetTCPConnection -State Listen | Format-Table LocalAddress,LocalPort -AutoSize",
    },
    "processes": {
        "Linux":   "ps aux --sort=-%mem | head -20",
        "Darwin":  "ps aux --sort=-%mem | head -20",
        "Windows": "Get-Process | Sort-Object CPU -Descending | Select-Object -First 20 Name,Id,CPU | Format-Table -AutoSize",
    },
    "services": {
        "Linux":   "systemctl list-units --type=service --state=running | head -25",
        "Darwin":  "launchctl list | awk '{print $3}' | grep -v '^$' | head -25",
        "Windows": "Get-Service | Where-Object Status -eq 'Running' | Format-Table Name,DisplayName,Status -AutoSize",
    },
    "logs": {
        "Linux":   "journalctl --no-pager -n 50 2>/dev/null",
        "Darwin":  "log show --last 5m --predicate 'eventMessage contains \"error\"' 2>/dev/null | tail -50",
        "Windows": "Get-EventLog -LogName System -Newest 50 | Format-Table TimeGenerated,EntryType,Message -AutoSize",
    },
    "errors": {
        "Linux":   "journalctl --no-pager -p err -n 30 2>/dev/null",
        "Darwin":  "log show --last 5m --predicate 'eventMessage contains \"error\"' 2>/dev/null | tail -30",
        "Windows": "Get-EventLog -LogName System -EntryType Error -Newest 30 | Format-Table TimeGenerated,Source,Message -AutoSize",
    },
    "users": {
        "Linux":   "w && echo '---' && last -n 10 | head -15",
        "Darwin":  "w && echo '---' && last -n 10 | head -15",
        "Windows": "Get-LocalUser | Format-Table Name,Enabled,LastLogon -AutoSize; Write-Host '---'; query user",
    },
    "ports": {
        "Linux":   "ss -tuln 2>/dev/null | head -30",
        "Darwin":  "lsof -iTCP -sTCP:LISTEN -P -n 2>/dev/null",
        "Windows": "Get-NetTCPConnection -State Listen | Format-Table LocalAddress,LocalPort,State -AutoSize",
    },
    "packages": {
        "Linux":   ("dnf list installed 2>/dev/null | tail -n +3 | wc -l && echo ' RPM packages' && dnf check-update 2>/dev/null | head -20"
                    if shutil_which("dnf") else "apt list --installed 2>/dev/null | tail -n +2 | wc -l"),
        "Darwin":  "brew list 2>/dev/null | wc -l && echo ' Homebrew packages' && brew outdated 2>/dev/null | head -20",
        "Windows": "winget list | Select-Object -Last 30",
    },
    "updates": {
        "Linux":   ("dnf check-update 2>/dev/null | head -30"
                    if shutil_which("dnf") else "apt list --upgradable 2>/dev/null | head -30"),
        "Darwin":  "softwareupdate -l 2>/dev/null | tail -30",
        "Windows": "winget upgrade | Select-Object -Last 30",
    },
    "temperature": {
        "Linux":   "sensors 2>/dev/null || cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | head -5",
        "Darwin":  "sudo powermetrics --samplers smc -i 1 -n 1 2>/dev/null | grep 'CPU die'",
        "Windows": "Get-CimInstance MSAcpi_ThermalZoneTemperature -Namespace root/wmi | Select-Object InstanceName,CurrentTemperature | Format-Table -AutoSize",
    },
    "battery": {
        "Linux":   "upower -i $(upower -e | grep BAT) 2>/dev/null || acpi -V 2>/dev/null",
        "Darwin":  "pmset -g batt 2>/dev/null",
        "Windows": "Get-CimInstance Win32_Battery | Select-Object Name,EstimatedChargeRemaining,EstimatedRunTime | Format-List",
    },
    "firewall": {
        "Linux":   "sudo firewall-cmd --list-all 2>/dev/null || sudo ufw status 2>/dev/null || sudo iptables -L -n 2>/dev/null | head -20",
        "Darwin":  "/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate 2>/dev/null; /usr/libexec/ApplicationFirewall/socketfilterfw --listapps 2>/dev/null | head -20",
        "Windows": "Get-NetFirewallProfile | Select-Object Name,Enabled | Format-Table -AutoSize; Write-Host '---'; Get-NetFirewallRule -Enabled True | Select-Object -First 20 DisplayName,Direction,Action | Format-Table -AutoSize",
    },
    "ssh": {
        "Linux":   "systemctl status sshd 2>/dev/null || systemctl status ssh 2>/dev/null || echo 'No SSH service found'",
        "Darwin":  "systemsetup -getremotelogin 2>/dev/null || sudo launchctl list | grep ssh",
        "Windows": "Get-Service sshd | Format-List Name,Status,StartType",
    },
    "docker": {
        "Linux":   "docker ps -a 2>/dev/null && echo '---' && docker images 2>/dev/null || echo 'Docker not found or not running'",
        "Darwin":  "docker ps -a 2>/dev/null && echo '---' && docker images 2>/dev/null || echo 'Docker not found or not running'",
        "Windows": "docker ps -a 2>$null; Write-Host '---'; docker images 2>$null",
    },
    "git": {
        "Linux":   "git config --list 2>/dev/null | head -30",
        "Darwin":  "git config --list 2>/dev/null | head -30",
        "Windows": "git config --list 2>$null | Select-Object -First 30",
    },
}


def _get_diagnostic_command(target: str) -> str | None:
    """Return diagnostic command for current OS, or None if unsupported."""
    cmds = _DIAGNOSTICS.get(target)
    if not cmds:
        return None
    if _OS in cmds:
        return cmds[_OS]
    closest = {"Linux": "Linux", "Darwin": "Darwin", "Windows": "Windows"}
    for key in closest:
        if key in cmds:
            return cmds[key]
    return None


# ── AI analysis ─────────────────────────────────────────────────────
def _analyze_output(combined: str, context: str = "") -> str:
    """Use Gemini to summarize and analyze command output."""
    if len(combined) < 100:
        return combined

    try:
        from google import genai
        client = genai.Client(api_key=_get_api_key())
        prompt = (
            f"You are JARVIS, an AI assistant. Summarize and analyze this command output.\n"
            f"{context}\n\n"
            f"Rules:\n"
            f"- Be concise, factual, and helpful.\n"
            f"- Highlight key issues, warnings, or anomalies.\n"
            f"- Use bullet points for clarity.\n"
            f"- If everything looks normal, say so briefly.\n"
            f"- Format memory/disk in human-readable terms (GB, MB).\n\n"
            f"OUTPUT:\n{combined[:3000]}"
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
        )
        return response.text.strip()
    except Exception:
        return combined[:2000]


# ── command execution ───────────────────────────────────────────────
def _run_command(command: str, timeout: int = 30, cwd: str = None) -> dict:
    """Run a shell command and return the result."""
    shell_exe = _get_shell_executable()
    try:
        if _OS == "Windows" and shell_exe:
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd or str(Path.home()),
            )
        else:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd or str(Path.home()),
                executable=shell_exe,
            )
        return {
            "command": command,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired:
        return {
            "command": command,
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s",
            "returncode": -1,
            "timed_out": True,
        }
    except Exception as e:
        return {
            "command": command,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1,
            "timed_out": False,
        }


# ── fix commands (platform‑aware) ───────────────────────────────────
_FIX_COMMANDS = {
    "broken": {
        "Linux":   ("sudo dnf distro-sync 2>/dev/null || sudo apt install -f 2>/dev/null || "
                     "echo 'Could not auto-fix packages — try manually'"),
        "Darwin":  "brew doctor 2>/dev/null || echo 'Could not auto-fix — run brew doctor manually'",
        "Windows": "sfc /scannow 2>$null; DISM /Online /Cleanup-Image /RestoreHealth 2>$null",
    },
    "cache": {
        "Linux":   ("sudo dnf clean all 2>/dev/null || sudo apt clean 2>/dev/null || "
                     "rm -rf ~/.cache/* 2>/dev/null; echo 'Cache cleaned'"),
        "Darwin":  "brew cleanup 2>/dev/null; rm -rf ~/Library/Caches/* 2>/dev/null; echo 'Cache cleaned'",
        "Windows": "cmd.exe /c 'ipconfig /flushdns && del /q /s %TEMP%\\* 2>nul'; Write-Host 'Cache cleaned'",
    },
    "journal": {
        "Linux":   "sudo journalctl --vacuum-time=3d 2>/dev/null; echo 'Journals vacuumed'",
        "Darwin":  "sudo log erase --all 2>/dev/null; echo 'Logs erased'",
        "Windows": "wevtutil el | ForEach-Object { wevtutil cl $_ 2>$null }; Write-Host 'Event logs cleared'",
    },
}


def _get_fix_command(target: str) -> str | None:
    cmds = _FIX_COMMANDS.get(target)
    if not cmds:
        return None
    return cmds.get(_OS)


# ── main entry ──────────────────────────────────────────────────────
def system_command(
    parameters: dict = None,
    response=None,
    player=None,
) -> str:
    """
    Execute system commands or diagnostics.

    parameters:
      command:  raw shell command to run
      action:   'diagnose' | 'check' | 'fix' | 'info' | 'status'
      target:   disk, memory, cpu, network, processes, system, services,
                logs, errors, users, ports, packages, updates, temperature,
                battery, firewall, ssh, docker, git
      analyze:  bool (default True) — analyze output with AI
      timeout:  int (default 30, max 120)
    """
    params = parameters or {}
    command = params.get("command", "")
    action = params.get("action", "").lower()
    target = params.get("target", "").lower()
    analyze = params.get("analyze", True)
    timeout = min(params.get("timeout", 30), 120)

    # Dispatch by action
    if action in ("diagnose", "check", "info", "status") and target:
        diag_cmd = _get_diagnostic_command(target)
        if not diag_cmd:
            return (f"No diagnostic available for '{target}' on {_OS}. "
                    f"Try: disk, memory, cpu, network, processes, system, "
                    f"services, logs, errors, users, ports, packages, updates, "
                    f"temperature, battery, firewall, ssh, docker, git.")
        cmd = diag_cmd
        if player:
            print(f"[System] 🔍 Diagnosing: {target}", flush=True)
        context = f"Context: System diagnostic for '{target}' on {_OS}."

    elif action == "fix" and target:
        fix_cmd = _get_fix_command(target)
        if not fix_cmd:
            return f"No fix available for '{target}' on {_OS}."
        cmd = fix_cmd
        if player:
            print(f"[System] 🔧 Fixing: {target}", flush=True)
        context = f"Context: Fix operation for '{target}' on {_OS}."
        if player:
            player.write_log(f"SYS: Running fix for {target}")

    elif command:
        safe, reason = _is_safe_command(command)
        if not safe:
            msg = f"⛔ BLOCKED: {reason}"
            if player:
                print(f"[System] {msg}", flush=True)
            return f"Safety block: {reason}"
        cmd = command
        if player:
            print(f"[System] ⚡ Running: {cmd}", flush=True)
        context = f"Context: User-requested command on {_OS}."

    else:
        return ("Usage: specify an action+target (e.g. action='diagnose', target='disk') "
                "or a raw command (e.g. command='ls -la').")

    result = _run_command(cmd, timeout=timeout)
    output = result["stdout"] or "(no output)"
    err = result["stderr"]

    if result["timed_out"]:
        return f"⏱️ Command timed out after {timeout}s."

    if result["returncode"] != 0 and not output:
        return f"❌ Command failed (exit {result['returncode']}): {err}"

    combined = output
    if err:
        combined += f"\n\n[stderr]\n{err}"

    if analyze and len(combined) > 100:
        if player:
            print(f"[System] 🧠 Analyzing...", flush=True)
        return _analyze_output(combined, context)

    return combined[:3000]
