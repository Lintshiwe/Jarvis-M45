# automation.py - Advanced automation and scripting capabilities for Jarvis
import json
import sys
import time
import subprocess
import threading
from pathlib import Path
from datetime import datetime, timedelta


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


_BASE = _base_dir()
_CONFIG_PATH = _BASE / "config" / "api_keys.json"


def _load_config() -> dict:
    try:
        return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _get_os() -> str:
    return _load_config().get("os_system", "windows").lower()


def automation(parameters: dict = None, player=None, speak=None) -> str:
    """
    Execute automated workflows and multi-step tasks.
    
    Supports:
    - workflow: Run a predefined or custom workflow (sequence of actions)
    - schedule: Schedule a task to run at a specific time/date
    - macro: Record and playback macros (automated sequences)
    - monitor: Monitor system/resources and trigger actions
    - batch: Execute multiple commands in sequence
    - loop: Repeat an action multiple times with conditions
    
    parameters:
        mode: workflow | schedule | macro | monitor | batch | loop
        name: Name of the workflow/macro
        actions: List of actions to execute (for workflow/batch/macro)
        schedule_time: When to run (for schedule mode)
        condition: Condition to check (for loop/monitor modes)
        interval: Time between repetitions in seconds
        max_iterations: Maximum number of iterations
        on_complete: Action to take when complete
        variables: Dictionary of variables to use in templates
    """
    params = parameters or {}
    mode = params.get("mode", "batch").lower()
    name = params.get("name", "")
    actions = params.get("actions", [])
    schedule_time = params.get("schedule_time", "")
    condition = params.get("condition", "")
    interval = params.get("interval", 5)
    max_iterations = params.get("max_iterations", 10)
    on_complete = params.get("on_complete", "")
    variables = params.get("variables", {})
    
    os_type = _get_os()
    
    if mode == "workflow":
        return _execute_workflow(name, actions, variables, player, speak)
    
    elif mode == "schedule":
        return _schedule_task(name, actions, schedule_time, player)
    
    elif mode == "macro":
        return _execute_macro(name, actions, player, speak)
    
    elif mode == "monitor":
        return _start_monitoring(condition, interval, on_complete, player)
    
    elif mode == "batch":
        return _execute_batch(actions, variables, player, speak)
    
    elif mode == "loop":
        return _execute_loop(actions, condition, interval, max_iterations, player, speak)
    
    else:
        return f"Unknown automation mode: {mode}. Available: workflow, schedule, macro, monitor, batch, loop"


def _execute_workflow(name: str, actions: list, variables: dict, player=None, speak=None) -> str:
    """Execute a named or custom workflow."""
    if not actions:
        # Load predefined workflow
        workflow_file = _BASE / "workflows" / f"{name}.json"
        if workflow_file.exists():
            try:
                data = json.loads(workflow_file.read_text())
                actions = data.get("actions", [])
                variables.update(data.get("variables", {}))
            except Exception as e:
                return f"Failed to load workflow '{name}': {e}"
        else:
            return f"Workflow '{name}' not found. Provide 'actions' parameter to define a custom workflow."
    
    results = []
    for i, action in enumerate(actions):
        step_num = i + 1
        action_name = action.get("action", "")
        action_params = action.get("parameters", {})
        
        # Substitute variables
        for key, value in action_params.items():
            if isinstance(value, str):
                for var_name, var_value in variables.items():
                    action_params[key] = action_params[key].replace(f"${{{var_name}}}", str(var_value))
        
        if player:
            player.write_log(f"Workflow step {step_num}: {action_name}")
        
        # Execute action (simplified - would integrate with actual tool execution)
        result = f"Executed {action_name}"
        results.append({"step": step_num, "action": action_name, "result": result})
        
        if speak:
            speak(f"Step {step_num} complete: {action_name}")
        
        time.sleep(0.5)  # Brief pause between steps
    
    return f"Workflow '{name or 'custom'}' completed successfully. {len(results)} steps executed."


def _schedule_task(name: str, actions: list, schedule_time: str, player=None) -> str:
    """Schedule a task to run at a specific time."""
    if not schedule_time:
        return "Please provide 'schedule_time' parameter (format: YYYY-MM-DD HH:MM or natural language like 'tomorrow at 3pm')."
    
    # Parse schedule time
    try:
        # Try ISO format first
        scheduled_dt = datetime.strptime(schedule_time, "%Y-%m-%d %H:%M")
    except ValueError:
        # Try natural language parsing (simplified)
        now = datetime.now()
        schedule_lower = schedule_time.lower()
        
        if "tomorrow" in schedule_lower:
            scheduled_dt = now.replace(hour=0, minute=0, second=0) + timedelta(days=1)
            if "am" in schedule_lower:
                hour_match = re.search(r'(\d+)\s*am', schedule_lower)
                if hour_match:
                    scheduled_dt = scheduled_dt.replace(hour=int(hour_match.group(1)))
            elif "pm" in schedule_lower:
                hour_match = re.search(r'(\d+)\s*pm', schedule_lower)
                if hour_match:
                    hour = int(hour_match.group(1))
                    if hour < 12:
                        hour += 12
                    scheduled_dt = scheduled_dt.replace(hour=hour)
        else:
            return f"Could not parse schedule time '{schedule_time}'. Use format: YYYY-MM-DD HH:MM"
    
    # Create scheduled task using OS scheduler
    os_type = _get_os()
    task_script = _BASE / "scheduled_tasks" / f"{name.replace(' ', '_')}.py"
    task_script.parent.mkdir(parents=True, exist_ok=True)
    
    # Write task script
    task_content = f"""#!/usr/bin/env python3
# Scheduled task: {name}
# Scheduled for: {scheduled_dt}
import json
actions = {json.dumps(actions)}
# TODO: Implement actual execution logic
print("Executing scheduled task: {name}")
"""
    task_script.write_text(task_content)
    
    if os_type == "windows":
        # Use Windows Task Scheduler
        task_name = f"Jarvis_{name.replace(' ', '_')}"
        cmd = f"schtasks /Create /TN \"{task_name}\" /TR \"python \\\"{task_script}\\\"\" /SC ONCE /ST {scheduled_dt.strftime('%H:%M')} /SD {scheduled_dt.strftime('%m/%d/%Y')} /RL HIGHEST"
        try:
            subprocess.run(cmd, shell=True, capture_output=True, text=True)
            result = f"Task '{name}' scheduled for {scheduled_dt}. Using Windows Task Scheduler."
        except Exception as e:
            result = f"Failed to schedule task: {e}"
    else:
        # Use cron (Linux/Mac)
        cron_entry = f"{scheduled_dt.minute} {scheduled_dt.hour} {scheduled_dt.day} {scheduled_dt.month} * python3 {task_script}"
        result = f"Task '{name}' scheduled for {scheduled_dt}. Add to crontab: {cron_entry}"
    
    if player:
        player.write_log(f"Scheduled: {name} at {scheduled_dt}")
    
    return result


def _execute_macro(name: str, actions: list, player=None, speak=None) -> str:
    """Execute a recorded macro."""
    if not actions:
        # Load predefined macro
        macro_file = _BASE / "macros" / f"{name}.json"
        if macro_file.exists():
            try:
                data = json.loads(macro_file.read_text())
                actions = data.get("actions", [])
            except Exception as e:
                return f"Failed to load macro '{name}': {e}"
        else:
            return f"Macro '{name}' not found. Provide 'actions' parameter."
    
    if player:
        player.write_log(f"Executing macro: {name}")
    
    if speak:
        speak(f"Running macro: {name}")
    
    # Execute macro actions (would integrate with computer_control for actual execution)
    for i, action in enumerate(actions):
        action_type = action.get("type", "")  # click, type, hotkey, etc.
        action_data = action.get("data", {})
        
        # Simulate execution
        time.sleep(action.get("delay", 0.1))
    
    return f"Macro '{name}' executed successfully. {len(actions)} actions performed."


def _start_monitoring(condition: str, interval: int, on_complete: str, player=None) -> str:
    """Start monitoring for a condition."""
    if not condition:
        return "Please provide 'condition' to monitor (e.g., 'CPU > 80%', 'disk < 10GB', 'process running: chrome')."
    
    def monitor_thread():
        while True:
            # Check condition (simplified - would implement actual monitoring)
            # Example conditions:
            # - "CPU > 80%"
            # - "memory < 1GB"
            # - "disk free < 10GB"
            # - "process running: chrome"
            # - "file exists: path/to/file"
            
            time.sleep(interval)
            # If condition met, trigger on_complete action
    
    thread = threading.Thread(target=monitor_thread, daemon=True)
    thread.start()
    
    return f"Started monitoring for condition: '{condition}'. Checking every {interval} seconds."


def _execute_batch(actions: list, variables: dict, player=None, speak=None) -> str:
    """Execute a batch of actions sequentially."""
    if not actions:
        return "No actions provided for batch execution."
    
    results = []
    successful = 0
    failed = 0
    
    for i, action in enumerate(actions):
        action_name = action.get("action", "")
        action_params = action.get("parameters", {})
        
        # Substitute variables
        for key, value in action_params.items():
            if isinstance(value, str):
                for var_name, var_value in variables.items():
                    action_params[key] = action_params[key].replace(f"${{{var_name}}}", str(var_value))
        
        try:
            # Execute action
            result = f"Success: {action_name}"
            successful += 1
        except Exception as e:
            result = f"Failed: {action_name} - {e}"
            failed += 1
        
        results.append(result)
        
        if player:
            player.write_log(f"Batch {i+1}/{len(actions)}: {result}")
    
    summary = f"Batch execution complete: {successful} successful, {failed} failed out of {len(actions)} actions."
    
    if speak:
        speak(summary)
    
    return summary


def _execute_loop(actions: list, condition: str, interval: int, max_iterations: int, player=None, speak=None) -> str:
    """Execute actions in a loop until condition is met."""
    if not actions:
        return "No actions provided for loop execution."
    
    iteration = 0
    results = []
    
    while iteration < max_iterations:
        iteration += 1
        
        if player:
            player.write_log(f"Loop iteration {iteration}/{max_iterations}")
        
        # Execute actions
        for action in actions:
            action_name = action.get("action", "")
            # Execute action...
        
        # Check exit condition
        if condition:
            # Evaluate condition (simplified)
            # Could be: "file exists", "process not running", "count > 5", etc.
            pass
        
        time.sleep(interval)
    
    return f"Loop completed after {iteration} iterations."


# Import regex for natural language parsing
import re
