# system_explorer.py — Jarvis M45 Deep Computer Exploration
"""
Jarvis explores the computer like a detective. Capabilities:
- Search entire filesystem for files by name/content
- Analyze directory structures and disk usage
- Find and list installed applications
- Check running processes in detail
- Explore system configuration and environment
- Find files by extension, size, modification time
- Search within file contents (grep)
"""
import fnmatch
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

_OS = platform.system()

# ── Safe search paths ───────────────────────────────────────────────
if _OS == "Windows":
    _SEARCH_ROOTS = [
        Path(os.environ.get("USERPROFILE", str(Path.home()))),
        Path("C:/"),
    ]
    _SKIP_DIRS = {
        "C:\\Windows", "C:\\$Recycle.Bin", "C:\\System Volume Information",
        "C:\\ProgramData\\Microsoft", "C:\\Program Files\\WindowsApps",
    }
elif _OS == "Darwin":
    _SEARCH_ROOTS = [Path.home(), Path("/Applications"), Path("/usr/local")]
    _SKIP_DIRS = {"/System", "/private/var/db", "/.fseventsd", "/.Spotlight-V100"}
else:
    _SEARCH_ROOTS = [Path.home(), Path("/")]
    _SKIP_DIRS = {
        "/proc", "/sys", "/dev", "/run", "/boot", "/etc/ssl",
        "/var/lib/snapd", "/snap", "/var/cache",
    }

_FORBIDDEN_PATHS = {
    "/etc/shadow", "/etc/sudoers", "/etc/passwd", "/root/.ssh",
    "/var/log/auth.log", "/var/log/secure",
    "C:\\Windows\\System32\\config\\SAM",
    "C:\\Windows\\System32\\config\\SECURITY",
}

def _is_safe_to_read(path: Path) -> bool:
    """Check if a path is safe to read (not a sensitive system file)."""
    path_str = str(path)
    for forbidden in _FORBIDDEN_PATHS:
        if path_str.endswith(forbidden) or forbidden in path_str:
            return False
    return True

# ── Search Filesystem ────────────────────────────────────────────────
def search_filesystem(
    pattern: str = "*",
    path: str = None,
    max_depth: int = 4,
    max_results: int = 100,
    min_size_kb: int = 0,
    max_size_kb: int = 0,
    newer_than_days: int = 0,
    file_type: str = None,  # "file", "dir", or None for both
) -> list[dict]:
    """
    Search the filesystem for files matching criteria.
    
    Args:
        pattern: Glob pattern (e.g. "*.py", "*.pdf", "project*")
        path: Starting directory (default: home)
        max_depth: Max directory depth
        max_results: Max results to return
        min_size_kb: Minimum file size in KB
        max_size_kb: Maximum file size in KB (0 = no limit)
        newer_than_days: Only files modified in last N days
        file_type: "file" or "dir" filter
    """
    start = Path(path).expanduser().resolve() if path else Path.home()
    if not start.exists():
        return [{"error": f"Path does not exist: {start}"}]
    
    results = []
    now = time.time()
    cutoff = now - (newer_than_days * 86400) if newer_than_days > 0 else 0
    
    try:
        for root, dirs, files in os.walk(str(start)):
            # Calculate depth
            rel = Path(root).relative_to(start)
            depth = len(rel.parts)
            if depth > max_depth:
                dirs.clear()
                continue
            
            # Skip system dirs
            root_str = str(Path(root).resolve())
            skip = False
            for s in _SKIP_DIRS:
                if root_str.startswith(s):
                    skip = True
                    break
            if skip:
                dirs.clear()
                continue
            
            # Search directories
            if file_type != "file":
                for d in dirs:
                    if fnmatch.fnmatch(d, pattern):
                        dp = Path(root) / d
                        results.append({
                            "path": str(dp),
                            "type": "directory",
                            "size": _get_dir_size(dp),
                        })
                        if len(results) >= max_results:
                            return results
            
            # Search files
            if file_type != "dir":
                for f in files:
                    if not fnmatch.fnmatch(f, pattern):
                        continue
                    fp = Path(root) / f
                    
                    # Size filter
                    try:
                        size_kb = fp.stat().st_size / 1024
                    except Exception:
                        continue
                    
                    if min_size_kb > 0 and size_kb < min_size_kb:
                        continue
                    if max_size_kb > 0 and size_kb > max_size_kb:
                        continue
                    
                    # Date filter
                    if newer_than_days > 0:
                        try:
                            if fp.stat().st_mtime < cutoff:
                                continue
                        except Exception:
                            continue
                    
                    if not _is_safe_to_read(fp):
                        continue
                    
                    results.append({
                        "path": str(fp),
                        "type": "file",
                        "size_kb": round(size_kb, 1),
                        "extension": fp.suffix.lower(),
                        "modified": datetime.fromtimestamp(
                            fp.stat().st_mtime
                        ).strftime("%Y-%m-%d %H:%M") if fp.exists() else "unknown",
                    })
                    
                    if len(results) >= max_results:
                        return results
    
    except PermissionError:
        pass
    except Exception as e:
        if not results:
            return [{"error": str(e)}]
    
    return results

def _get_dir_size(path: Path) -> float:
    """Get directory size in KB."""
    try:
        total = sum(
            f.stat().st_size
            for f in path.rglob("*")
            if f.is_file() and f.stat().st_size < 10_000_000
        )
        return round(total / 1024, 1)
    except Exception:
        return 0

# ── Search File Contents ─────────────────────────────────────────────
def search_file_contents(
    pattern: str,
    path: str = None,
    file_patterns: str = "*.py,*.txt,*.md,*.json,*.xml,*.csv,*.log,*.html,*.css,*.js,*.yml,*.yaml,*.cfg,*.ini,*.conf,*.sh,*.bat,*.env,*.toml",
    max_results: int = 50,
    case_sensitive: bool = False,
    max_file_size_kb: int = 500,
) -> list[dict]:
    """
    Search inside file contents for a pattern (like grep).
    
    Args:
        pattern: Text pattern to search for
        path: Starting directory
        file_patterns: Comma-separated file extensions to search
        max_results: Maximum matches
        case_sensitive: Case-sensitive search
    """
    start = Path(path).expanduser().resolve() if path else Path.home()
    if not start.exists():
        return [{"error": f"Path does not exist: {start}"}]
    
    extensions = [e.strip() for e in file_patterns.split(",")]
    results = []
    flags = 0 if case_sensitive else os.path.getsize
    
    try:
        for root, dirs, files in os.walk(str(start)):
            # Skip system dirs
            root_str = str(Path(root).resolve())
            if any(root_str.startswith(s) for s in _SKIP_DIRS):
                dirs.clear()
                continue
            
            depth = len(Path(root).relative_to(start).parts)
            if depth > 5:
                dirs.clear()
                continue
            
            for f in files:
                if not any(f.endswith(ext.lstrip("*")) for ext in extensions):
                    continue
                
                fp = Path(root) / f
                
                try:
                    if fp.stat().st_size > max_file_size_kb * 1024:
                        continue
                except Exception:
                    continue
                
                if not _is_safe_to_read(fp):
                    continue
                
                try:
                    content = fp.read_text(encoding="utf-8", errors="ignore")
                    search_pattern = pattern if case_sensitive else pattern.lower()
                    search_content = content if case_sensitive else content.lower()
                    
                    lines = search_content.split("\n")
                    for i, line in enumerate(lines):
                        if search_pattern in line:
                            results.append({
                                "file": str(fp),
                                "line": i + 1,
                                "content": content.split("\n")[i][:200].strip(),
                            })
                            if len(results) >= max_results:
                                return results
                except Exception:
                    continue
    except Exception as e:
        if not results:
            return [{"error": str(e)}]
    
    return results

# ── Find Installed Applications ──────────────────────────────────────
def find_applications() -> dict:
    """Discover installed applications on the system."""
    apps = {"os": _OS, "applications": [], "total": 0}
    
    if _OS == "Linux":
        # Check common bin directories
        bin_dirs = [
            "/usr/bin", "/usr/local/bin", "/usr/sbin",
            "/snap/bin", str(Path.home() / ".local/bin"),
        ]
        seen = set()
        for d in bin_dirs:
            path = Path(d)
            if path.exists():
                for f in path.iterdir():
                    if f.is_file() and os.access(str(f), os.X_OK):
                        name = f.name
                        if name not in seen:
                            seen.add(name)
                            apps["applications"].append({"name": name, "path": str(f), "type": "binary"})
        
        # Check desktop entries
        desktop_dirs = [
            "/usr/share/applications",
            str(Path.home() / ".local/share/applications"),
            "/var/lib/snapd/desktop/applications",
        ]
        for d in desktop_dirs:
            path = Path(d)
            if path.exists():
                for df in path.glob("*.desktop"):
                    try:
                        content = df.read_text(encoding="utf-8", errors="ignore")
                        name = None
                        for line in content.split("\n"):
                            if line.startswith("Name="):
                                name = line.split("=", 1)[1].strip()
                                break
                        if name:
                            apps["applications"].append({"name": name, "path": str(df), "type": "desktop_entry"})
                    except Exception:
                        pass
    
    elif _OS == "Darwin":
        for d in ["/Applications", str(Path.home() / "Applications")]:
            path = Path(d)
            if path.exists():
                for app in path.glob("*.app"):
                    apps["applications"].append({"name": app.stem, "path": str(app), "type": "app_bundle"})
    
    elif _OS == "Windows":
        # Check Start Menu
        for d in [
            os.environ.get("APPDATA", "") + "\\Microsoft\\Windows\\Start Menu\\Programs",
            "C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs",
        ]:
            path = Path(d)
            if path.exists():
                for lnk in path.rglob("*.lnk"):
                    apps["applications"].append({"name": lnk.stem, "path": str(lnk), "type": "shortcut"})
    
    apps["total"] = len(apps["applications"])
    return apps

# ── Analyze Running Processes ────────────────────────────────────────
def analyze_processes(filter_name: str = None) -> list[dict]:
    """Get detailed information about running processes."""
    try:
        import psutil
    except ImportError:
        return [{"error": "psutil not installed"}]
    
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status', 'create_time', 'exe', 'cmdline']):
        try:
            info = proc.info
            name = info.get("name", "")
            
            if filter_name and filter_name.lower() not in name.lower():
                continue
            
            processes.append({
                "pid": info["pid"],
                "name": name,
                "cpu_percent": round(info.get("cpu_percent", 0), 1),
                "memory_percent": round(info.get("memory_percent", 0), 1),
                "status": info.get("status", "unknown"),
                "exe_path": info.get("exe", ""),
                "started": datetime.fromtimestamp(
                    info.get("create_time", 0)
                ).strftime("%H:%M:%S") if info.get("create_time") else "unknown",
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Sort by memory usage
    processes.sort(key=lambda x: x["memory_percent"], reverse=True)
    return processes[:50]

# ── Analyze Disk Usage ───────────────────────────────────────────────
def analyze_disk_usage(path: str = None) -> dict:
    """Get detailed disk usage analysis for a directory."""
    p = Path(path).expanduser().resolve() if path else Path.home()
    if not p.exists():
        return {"error": f"Path does not exist: {p}"}
    
    # Get disk usage with shutil
    try:
        total, used, free = shutil.disk_usage(str(p))
        disk_info = {
            "path": str(p),
            "total_gb": round(total / (1024**3), 1),
            "used_gb": round(used / (1024**3), 1),
            "free_gb": round(free / (1024**3), 1),
            "used_percent": round(used / total * 100, 1),
        }
    except Exception:
        disk_info = {"path": str(p), "error": "Could not get disk usage"}
    
    # Get top-level directory sizes
    try:
        dirs = []
        for item in p.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                size_kb = _get_dir_size(item)
                dirs.append({"name": item.name, "size_kb": size_kb, "size_mb": round(size_kb / 1024, 1)})
        dirs.sort(key=lambda x: x["size_kb"], reverse=True)
        disk_info["top_directories"] = dirs[:20]
    except PermissionError:
        disk_info["top_directories"] = []
    
    return disk_info

# ── System Environment ───────────────────────────────────────────────
def explore_environment() -> dict:
    """Explore system environment variables and configuration."""
    env_vars = {}
    for key in sorted(os.environ.keys()):
        val = os.environ[key]
        # Mask sensitive values
        if any(s in key.upper() for s in ["KEY", "TOKEN", "SECRET", "PASSWORD", "PASS", "AUTH"]):
            val = val[:4] + "****" if len(val) > 4 else "****"
        elif len(val) > 200:
            val = val[:200] + "..."
        env_vars[key] = val
    
    return {
        "os": _OS,
        "platform": platform.platform(),
        "python_version": sys.version,
        "username": os.environ.get("USER", os.environ.get("USERNAME", "unknown")),
        "home": str(Path.home()),
        "shell": os.environ.get("SHELL", os.environ.get("COMSPEC", "unknown")),
        "path": os.environ.get("PATH", ""),
        "env_count": len(env_vars),
    }

# ── Main Entry Point ─────────────────────────────────────────────────
def system_explorer(parameters: dict = None) -> str:
    """
    Deeply explore the computer system.
    
    parameters:
      action: search_files | search_content | find_apps | analyze_processes |
              analyze_disk | explore_env | explore_all
      pattern: search term (for search_files, search_content)
      path: starting directory
      filter_name: process name filter (for analyze_processes)
      max_results: max results (default: 50)
      file_type: "file" | "dir" | None
    """
    params = parameters or {}
    action = params.get("action", "explore_all").lower()
    pattern = params.get("pattern", params.get("query", "*"))
    path = params.get("path", None)
    filter_name = params.get("filter_name", params.get("name", None))
    max_results = min(params.get("max_results", 50), 200)
    file_type = params.get("file_type", None)
    
    try:
        if action in ("search_files", "find_files", "list_files"):
            results = search_filesystem(
                pattern=pattern, path=path,
                max_results=max_results,
                file_type=file_type,
            )
            if not results:
                return f"No files found matching '{pattern}'."
            
            lines = [f"Found {len(results)} items matching '{pattern}':"]
            for r in results[:30]:
                if r.get("type") == "directory":
                    lines.append(f"  📁 {r['path']} ({r.get('size', 0):.0f} KB)")
                else:
                    lines.append(f"  📄 {r['path']} ({r.get('size_kb', 0):.0f} KB) [{r.get('modified', '')}]")
            if len(results) > 30:
                lines.append(f"  ... and {len(results) - 30} more")
            return "\n".join(lines)
        
        elif action in ("search_content", "grep", "find_in_files"):
            results = search_file_contents(
                pattern=pattern, path=path,
                max_results=max_results,
            )
            if not results:
                return f"No matches found for '{pattern}' in files."
            
            lines = [f"Found {len(results)} matches for '{pattern}':"]
            for r in results[:30]:
                lines.append(f"  {r['file']}:{r['line']} → {r['content']}")
            if len(results) > 30:
                lines.append(f"  ... and {len(results) - 30} more")
            return "\n".join(lines)
        
        elif action in ("find_apps", "list_apps", "installed_apps"):
            apps = find_applications()
            if not apps["applications"]:
                return f"No applications found on {_OS}."
            
            lines = [f"Found {apps['total']} applications on {_OS}:"]
            for app in sorted(apps["applications"][:40], key=lambda x: x["name"].lower()):
                lines.append(f"  • {app['name']} ({app['type']})")
            if apps["total"] > 40:
                lines.append(f"  ... and {apps['total'] - 40} more")
            return "\n".join(lines)
        
        elif action in ("analyze_processes", "running_processes", "processes", "ps"):
            procs = analyze_processes(filter_name=filter_name)
            if not procs:
                return "No processes found."
            
            lines = [f"Top processes by memory:"]
            for p in procs[:25]:
                lines.append(
                    f"  PID {p['pid']:>6} | {p['memory_percent']:>5.1f}% MEM | "
                    f"{p['cpu_percent']:>5.1f}% CPU | {p['name'][:30]}"
                )
            return "\n".join(lines)
        
        elif action in ("analyze_disk", "disk_usage", "du"):
            usage = analyze_disk_usage(path=path)
            if "error" in usage:
                return f"Disk analysis error: {usage['error']}"
            
            lines = [
                f"Disk usage for {usage['path']}:",
                f"  Total: {usage['total_gb']} GB",
                f"  Used:  {usage['used_gb']} GB ({usage['used_percent']}%)",
                f"  Free:  {usage['free_gb']} GB",
            ]
            if "top_directories" in usage and usage["top_directories"]:
                lines.append("\nLargest directories:")
                for d in usage["top_directories"][:15]:
                    lines.append(f"  {d['size_mb']:>8.1f} MB  {d['name']}")
            return "\n".join(lines)
        
        elif action in ("explore_env", "environment", "env"):
            env = explore_environment()
            lines = [
                f"System Environment:",
                f"  OS: {env['os']}",
                f"  Platform: {env['platform']}",
                f"  Python: {env['python_version'].split()[0]}",
                f"  User: {env['username']}",
                f"  Home: {env['home']}",
                f"  Shell: {env['shell']}",
                f"  Environment variables: {env['env_count']}",
            ]
            return "\n".join(lines)
        
        elif action in ("explore_all", "explore", "analyze"):
            # Run all exploration and return combined summary
            parts = []
            
            env = explore_environment()
            parts.append(f"System: {env['os']} ({env['platform']})")
            parts.append(f"User: {env['username']} | Home: {env['home']}")
            
            try:
                usage = analyze_disk_usage()
                if "error" not in usage:
                    parts.append(f"Disk: {usage['used_gb']}/{usage['total_gb']} GB used ({usage['used_percent']}%)")
            except Exception:
                pass
            
            try:
                procs = analyze_processes()
                parts.append(f"Running processes: {len(procs)} (top: {procs[0]['name'] if procs else 'none'})")
            except Exception:
                pass
            
            parts.append(f"\nFor detailed exploration, specify: action='search_files', 'analyze_processes', 'find_apps', 'analyze_disk', or 'explore_env'.")
            return "\n".join(parts)
        
        else:
            return (
                f"Unknown exploration action: '{action}'. "
                f"Available: search_files, search_content, find_apps, analyze_processes, "
                f"analyze_disk, explore_env, explore_all"
            )
    
    except Exception as e:
        return f"Exploration error: {str(e)}"
