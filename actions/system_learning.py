# system_learning.py — Jarvis M45 Learning & Adaptation Engine
"""
Jarvis learns from every interaction. This module:
- Records interactions and outcomes
- Builds a knowledge graph of user preferences
- Learns successful tool/parameter patterns
- Adapts behavior over time
- Provides training data for future interactions
"""
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from threading import Lock

_OS = sys.platform

def _get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

_BASE = _get_base_dir()
_LEARN_DIR = _BASE / "learning"
_LEARN_DIR.mkdir(parents=True, exist_ok=True)

_lock = Lock()

# ── Learning Data Stores ─────────────────────────────────────────────
def _load_store(filename: str, default: dict | list = None) -> dict | list:
    path = _LEARN_DIR / filename
    if not path.exists():
        return default if default is not None else {}
    try:
        with _lock:
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}

def _save_store(filename: str, data: dict | list) -> None:
    path = _LEARN_DIR / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

# ── Interaction History ──────────────────────────────────────────────
def record_interaction(
    user_input: str,
    tool_called: str,
    parameters: dict,
    result: str,
    success: bool,
    response_time_ms: float = 0,
):
    """Record every interaction for learning."""
    history = _load_store("interaction_history.json", [])
    entry = {
        "timestamp": datetime.now().isoformat(),
        "user_input": user_input[:500],
        "tool_called": tool_called,
        "parameters": {k: str(v)[:200] for k, v in (parameters or {}).items()},
        "result_preview": str(result)[:300],
        "success": success,
        "response_time_ms": response_time_ms,
    }
    history.append(entry)
    
    # Keep last 500 interactions
    if len(history) > 500:
        history = history[-500:]
    
    _save_store("interaction_history.json", history)

# ── Tool Pattern Learning ────────────────────────────────────────────
def learn_tool_pattern(user_input: str, tool_called: str, parameters: dict):
    """Learn which tool and parameters map to which user phrases."""
    patterns = _load_store("tool_patterns.json", {})
    
    # Extract intent keywords from user input
    words = user_input.lower().split()
    keywords = [w for w in words if len(w) > 2][:8]
    
    for keyword in keywords:
        if keyword not in patterns:
            patterns[keyword] = {}
        if tool_called not in patterns[keyword]:
            patterns[keyword][tool_called] = {"count": 0, "parameters": {}}
        
        patterns[keyword][tool_called]["count"] += 1
        
        # Learn common parameters
        for k, v in (parameters or {}).items():
            if k not in patterns[keyword][tool_called]["parameters"]:
                patterns[keyword][tool_called]["parameters"][k] = {}
            v_str = str(v)[:100]
            patterns[keyword][tool_called]["parameters"][k][v_str] = \
                patterns[keyword][tool_called]["parameters"][k].get(v_str, 0) + 1
    
    # Clean up - keep only top patterns
    for kw in list(patterns.keys()):
        if len(patterns[kw]) > 20:
            sorted_tools = sorted(patterns[kw].items(), key=lambda x: x[1]["count"], reverse=True)
            patterns[kw] = dict(sorted_tools[:20])
    
    _save_store("tool_patterns.json", patterns)

# ── Preference Learning ──────────────────────────────────────────────
def learn_preference(category: str, key: str, value: str):
    """Learn user preferences over time."""
    prefs = _load_store("learned_preferences.json", {})
    if category not in prefs:
        prefs[category] = {}
    
    if key not in prefs[category]:
        prefs[category][key] = {"values": {}, "updated": None}
    
    v_str = str(value)[:200]
    prefs[category][key]["values"][v_str] = prefs[category][key]["values"].get(v_str, 0) + 1
    prefs[category][key]["updated"] = datetime.now().isoformat()
    
    _save_store("learned_preferences.json", prefs)

def get_learned_preferences() -> dict:
    """Get all learned preferences formatted for prompt context."""
    prefs = _load_store("learned_preferences.json", {})
    lines = []
    for category, items in prefs.items():
        lines.append(f"\n[{category.upper()}]")
        for key, data in list(items.items())[:5]:
            if "values" in data:
                top = sorted(data["values"].items(), key=lambda x: x[1], reverse=True)[:2]
                vals = ", ".join(f"{v} ({c}x)" for v, c in top)
                lines.append(f"  {key}: {vals}")
    
    return "\n".join(lines) if lines else ""

# ── Success Rate Tracking ────────────────────────────────────────────
def track_tool_success(tool_name: str, success: bool):
    """Track success/failure rates per tool."""
    stats = _load_store("tool_stats.json", {})
    if tool_name not in stats:
        stats[tool_name] = {"success": 0, "failure": 0, "last_used": None}
    
    if success:
        stats[tool_name]["success"] += 1
    else:
        stats[tool_name]["failure"] += 1
    
    stats[tool_name]["last_used"] = datetime.now().isoformat()
    _save_store("tool_stats.json", stats)

def get_tool_stats() -> dict:
    """Get tool stats for prompt context."""
    return _load_store("tool_stats.json", {})

def get_best_tool(keywords: list[str]) -> str | None:
    """Given keywords, find the most likely tool based on past patterns."""
    patterns = _load_store("tool_patterns.json", {})
    scores = {}
    
    for keyword in keywords:
        if keyword in patterns:
            for tool, data in patterns[keyword].items():
                scores[tool] = scores.get(tool, 0) + data["count"]
    
    if scores:
        return max(scores, key=scores.get)
    return None

# ── Context-Aware Suggestions ────────────────────────────────────────
def get_learning_context() -> str:
    """Build a context string for the system prompt based on everything learned."""
    parts = []
    
    # Learned preferences
    prefs = get_learned_preferences()
    if prefs:
        parts.append(prefs)
    
    # Frequent tools
    stats = get_tool_stats()
    if stats:
        sorted_tools = sorted(stats.items(), key=lambda x: x[1]["success"], reverse=True)[:5]
        tools_str = ", ".join(f"{t} ({s['success']}✓)" for t, s in sorted_tools if s["success"] > 0)
        if tools_str:
            parts.append(f"\n[FREQUENTLY SUCCESSFUL TOOLS]\n{tools_str}")
    
    # Recent interactions
    history = _load_store("interaction_history.json", [])
    if history:
        recent = history[-10:]
        recent_str = "\n".join(
            f"  \"{h['user_input'][:80]}\" → {h['tool_called']} ({'✓' if h['success'] else '✗'})"
            for h in reversed(recent)
        )
        if recent_str:
            parts.append(f"\n[RECENT INTERACTIONS]\n{recent_str}")
    
    return "\n".join(parts) if parts else ""

# ── High-level learn function (called after every tool execution) ────
def learn(
    user_input: str,
    tool_called: str = "",
    parameters: dict = None,
    result: str = "",
    success: bool = True,
    response_time_ms: float = 0,
):
    """Main learning function — call after every interaction."""
    try:
        record_interaction(user_input, tool_called, parameters, result, success, response_time_ms)
        if tool_called:
            track_tool_success(tool_called, success)
            learn_tool_pattern(user_input, tool_called, parameters)
    except Exception as e:
        print(f"[Learning] ⚠️ Record failed: {e}")

# ── Reset learning data ──────────────────────────────────────────────
def reset_learning():
    """Clear all learned data."""
    for f in ["interaction_history.json", "tool_patterns.json", 
              "learned_preferences.json", "tool_stats.json"]:
        path = _LEARN_DIR / f
        if path.exists():
            path.unlink()
    return "All learning data has been reset."
