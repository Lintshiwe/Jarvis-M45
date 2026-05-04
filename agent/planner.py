import json
import re
import sys
from pathlib import Path


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR        = get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"


PLANNER_PROMPT = """You are the planning module of JARVIS M45, a personal AI assistant.
Your job: break any user goal into a sequence of steps using ONLY the tools listed below.

ABSOLUTE RULES:
- NEVER use generated_code or write Python scripts. It does not exist.
- NEVER reference previous step results in parameters. Every step is independent.
- Use web_search for ANY information retrieval, research, or current data.
- Use file_controller to save content to disk.
- Max 5 steps. Use the minimum steps needed.

AVAILABLE TOOLS AND THEIR PARAMETERS:

open_app
  app_name: string (required)

web_search
  query: string (required) — write a clear, focused search query
  mode: "search" | "compare" | "deep" (optional, default: search)
    - "search": standard search (returns summary)
    - "compare": compare multiple items (use items list)
    - "deep": deep research (multi-source, content extraction, synthesis)
  items: list of strings (optional, for compare mode)
  aspect: string (optional, for compare mode)
  url: string (optional) — extract text content from a specific URL
  deep: boolean (optional) — enable deep research mode
  depth: int (optional, default: 3) — number of sources to extract in deep mode

game_updater
  action: "update" | "install" | "list" | "download_status" | "schedule" (required)
  platform: "steam" | "epic" | "both" (optional, default: both)
  game_name: string (optional)
  app_id: string (optional)
  shutdown_when_done: boolean (optional)

browser_control
  action: "go_to" | "search" | "click" | "type" | "scroll" | "get_text" | "extract_content" | "extract_links" | "capture_social_media" | "press" | "close" | "screenshot" (required)
  url: string (for go_to)
  query: string (for search)
  text: string (for click/type)
  selector: string (for click/type — CSS selector)
  direction: "up" | "down" (for scroll)
  description: string (for smart_click/smart_type)
  platform: string (for capture_social_media — twitter, reddit, instagram, facebook, linkedin)
  count: int (for capture_social_media — number of posts to extract)
  full_page: boolean (for extract_content)
  browser: string (optional — chrome, edge, firefox, brave, opera)

file_controller
  action: "write" | "create_file" | "read" | "list" | "delete" | "move" | "copy" | "find" | "disk_usage" (required)
  path: string — use "desktop" for Desktop folder
  name: string — filename
  content: string — file content (for write/create_file)

computer_settings
  action: string — volume_up | volume_down | mute | unmute | brightness_up | brightness_down | close_app (close/quit/kill/terminate/exit an app) | maximize | minimize | full_screen | snap_left | snap_right | lock_screen | dark_mode | toggle_wifi | restart | shutdown | sleep_display | screenshot | pause_video | task_manager | file_explorer | open_settings | show_desktop | scroll_up | scroll_down | scroll_top | scroll_bottom | page_up | page_down | next_tab | prev_tab | close_tab | new_tab | zoom_in | zoom_out | zoom_reset | copy | paste | cut | undo | redo | select_all | save | refresh_page | go_back | go_forward | find_on_page | switch_window | focus_search | open_run | enter | escape | type_text | press_key | volume_set
  description: string — natural language description (fallback if action is empty)
  value: string — for close_app: the app name (e.g. "spotify", "chrome") | for volume_set: 0-100 | for type_text: text to type | for press_key: key name
  confirmed: "yes" to confirm dangerous actions (restart, shutdown)

system
  command: string — the shell command to run (e.g. "df -h", "systemctl status nginx", "ps aux | grep firefox")
  action: "diagnose" | "check" | "fix" | "info" — shorthand for common system tasks
  target: string — what to diagnose: disk, memory, cpu, network, processes, system, services, logs, errors, users, ports, drivers, packages, updates, temperature, battery, firewall, ssh, docker, git
  analyze: boolean (optional, default: true)
  timeout: int (optional, default: 30)

system_explorer
  action: "search_files" | "search_content" | "find_apps" | "analyze_processes" | "analyze_disk" | "explore_env" | "explore_all"
  pattern: string — filename pattern (e.g. "*.py"), text to search in files, or process name filter
  path: string — starting directory (default: home directory)
  max_results: int (default: 50)
  file_type: "file" | "dir" (optional)

system_learning
  action: "view_context" | "view_history" | "view_patterns" | "view_preferences" | "view_stats" | "reset_learning" | "learn_preference"
  category: string (for learn_preference)
  key: string (for learn_preference)
  value: string (for learn_preference)

computer_control
  action: "type" | "click" | "hotkey" | "press" | "scroll" | "screenshot" | "screen_find" | "screen_click" (required)
  text: string (for type)
  x, y: int (for click)
  keys: string (for hotkey, e.g. "ctrl+c")
  key: string (for press)
  direction: "up" | "down" (for scroll)
  description: string (for screen_find/screen_click)

screen_process
  text: string (required) — what to analyze or ask about the screen
  angle: "screen" | "camera" (optional)

send_message
  receiver: string (required)
  message_text: string (required)
  platform: string (required)

reminder
  date: string YYYY-MM-DD (required)
  time: string HH:MM (required)
  message: string (required)

desktop_control
  action: "wallpaper" | "organize" | "clean" | "list" | "task" (required)
  path: string (optional)
  task: string (optional)

youtube_video
  action: "play" | "summarize" | "trending" (required)
  query: string (for play)

weather_report
  city: string (required)

flight_finder
  origin: string (required)
  destination: string (required)
  date: string (required)

code_helper
  action: "write" | "edit" | "run" | "explain" (required)
  description: string (required)
  language: string (optional)
  output_path: string (optional)
  file_path: string (optional)

dev_agent
  description: string (required)
  language: string (optional)
EXAMPLES:

Goal: "research mechanical engineering and save it to a notepad file"
Steps:

web_search | query: "mechanical engineering overview history applications future trends" | mode: deep
file_controller | action: write, path: desktop, name: mechanical_engineering.txt, content: "MECHANICAL ENGINEERING RESEARCH\n\n[research results will be injected here]"

Goal: "What is the price of Bitcoin"
Steps:

web_search | query: "Bitcoin price today USD 2026"

Goal: "What are people saying about AI on Twitter right now"
Steps:

browser_control | action: go_to, url: "https://x.com/search?q=AI%20artificial%20intelligence&src=typed_query&f=live"
browser_control | action: capture_social_media, platform: "x", count: 15

Goal: "Extract all the content and links from this article"
Steps:

browser_control | action: go_to, url: "https://example.com/article"
browser_control | action: extract_content

Goal: "List the files on the desktop and find the largest 5 files"
Steps:

file_controller | action: list, path: desktop
file_controller | action: largest, path: desktop, count: 5

Goal: "Install PUBG from Steam"
Steps:

game_updater | action: install, platform: steam, game_name: "PUBG"

Goal: "Update all my Steam games"
Steps:

game_updater | action: update, platform: steam

Goal: "Send John a message on WhatsApp saying there is a meeting tomorrow"
Steps:

send_message | receiver: John, message_text: "There is a meeting tomorrow", platform: WhatsApp

Goal: "Open the clock and set a reminder for 30 minutes later"
Steps:

reminder | date: [today], time: [now+30min], message: "Reminder"

Goal: "Do a deep analysis of the latest Tesla earnings report"
Steps:

web_search | query: "Tesla Q1 2026 earnings report revenue profit margins" | mode: deep | depth: 5

OUTPUT — return ONLY valid JSON, no markdown, no explanation, no code blocks:
{
  "goal": "...",
  "steps": [
    {
      "step": 1,
      "tool": "tool_name",
      "description": "what this step does",
      "parameters": {},
      "critical": true
    }
  ]
}
"""


def _get_api_key() -> str:
    with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["gemini_api_key"]


def create_plan(goal: str, context: str = "") -> dict:
    from google import genai

    client = genai.Client(api_key=_get_api_key())

    user_input = f"Goal: {goal}"
    if context:
        user_input += f"\n\nContext: {context}"

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=user_input,
            config={"system_instruction": PLANNER_PROMPT},
        )
        text     = response.text.strip()
        text     = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()

        plan = json.loads(text)

        if "steps" not in plan or not isinstance(plan["steps"], list):
            raise ValueError("Invalid plan structure")

        for step in plan["steps"]:
            if step.get("tool") in ("generated_code",):
                print(f"[Planner] ⚠️ generated_code detected in step {step.get('step')} — replacing with web_search")
                desc = step.get("description", goal)
                step["tool"] = "web_search"
                step["parameters"] = {"query": desc[:200]}

        print(f"[Planner] ✅ Plan: {len(plan['steps'])} steps")
        for s in plan["steps"]:
            print(f"  Step {s['step']}: [{s['tool']}] {s['description']}")

        return plan

    except json.JSONDecodeError as e:
        print(f"[Planner] ⚠️ JSON parse failed: {e}")
        return _fallback_plan(goal)
    except Exception as e:
        print(f"[Planner] ⚠️ Planning failed: {e}")
        return _fallback_plan(goal)


def _fallback_plan(goal: str) -> dict:
    print("[Planner] 🔄 Fallback plan")
    return {
        "goal": goal,
        "steps": [
            {
                "step": 1,
                "tool": "web_search",
                "description": f"Search for: {goal}",
                "parameters": {"query": goal},
                "critical": True
            }
        ]
    }


def replan(goal: str, completed_steps: list, failed_step: dict, error: str) -> dict:
    from google import genai

    client = genai.Client(api_key=_get_api_key())

    completed_summary = "\n".join(
        f"  - Step {s['step']} ({s['tool']}): DONE" for s in completed_steps
    )

    prompt = f"""Goal: {goal}

Already completed:
{completed_summary if completed_summary else '  (none)'}

Failed step: [{failed_step.get('tool')}] {failed_step.get('description')}
Error: {error}

Create a REVISED plan for the remaining work only. Do not repeat completed steps."""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"system_instruction": PLANNER_PROMPT},
        )
        text     = response.text.strip()
        text     = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
        plan     = json.loads(text)

        for step in plan.get("steps", []):
            if step.get("tool") == "generated_code":
                step["tool"] = "web_search"
                step["parameters"] = {"query": step.get("description", goal)[:200]}

        print(f"[Planner] 🔄 Revised plan: {len(plan['steps'])} steps")
        return plan
    except Exception as e:
        print(f"[Planner] ⚠️ Replan failed: {e}")
        return _fallback_plan(goal)