# Enhanced Capabilities for Jarvis M45

## Overview
This document describes the new capabilities added to Jarvis M45 to make it more powerful and able to perform a wider range of actions.

## New Actions Added

### 1. Automation Engine (`automation.py`)
The automation engine enables Jarvis to execute complex multi-step workflows, scheduled tasks, and automated routines.

**Capabilities:**
- **Workflow Execution**: Run predefined or custom sequences of actions
- **Task Scheduling**: Schedule tasks to run at specific times using OS schedulers (Windows Task Scheduler, cron)
- **Macro Playback**: Execute recorded macros for repetitive tasks
- **System Monitoring**: Monitor system conditions (CPU, memory, disk, processes) and trigger actions
- **Batch Processing**: Execute multiple commands in sequence
- **Loop Operations**: Repeat actions with conditions until completion

**Usage Examples:**
- "Automate my morning routine"
- "Schedule a backup for tonight at 11 PM"
- "Run my daily report macro"
- "Monitor CPU usage and alert me if it goes above 80%"
- "Execute these 5 steps in sequence"
- "Repeat this action until the file is downloaded"

**Parameters:**
- `mode`: workflow | schedule | macro | monitor | batch | loop
- `name`: Name of the workflow/macro/task
- `actions`: List of actions to execute
- `schedule_time`: When to run (YYYY-MM-DD HH:MM or natural language)
- `condition`: Condition to check for loop/monitor modes
- `interval`: Time between repetitions in seconds
- `max_iterations`: Maximum number of iterations
- `variables`: Variables to use in templates

### 2. API Controller (`api_controller.py`)
The API controller provides universal integration with any web service or API, connecting Jarvis to the entire internet.

**Capabilities:**
- **HTTP Requests**: Make GET, POST, PUT, DELETE, PATCH requests to any API
- **Authentication**: Support for API keys, Bearer tokens, Basic auth, OAuth
- **Service Integration**: Pre-configured integrations for popular services:
  - GitHub (repos, issues, PRs)
  - Slack (messages, channels)
  - Discord (messages, servers)
  - Twitter/X (tweets, DMs)
  - Notion (pages, databases)
  - Telegram (bots, messages)
- **Webhook Management**: Create and manage webhooks for real-time notifications
- **Response Parsing**: Parse JSON, XML, HTML, and text responses
- **Request Chaining**: Chain multiple API calls, passing results between them

**Usage Examples:**
- "Post a message to our Slack channel"
- "Create a GitHub issue for this bug"
- "Send a Discord message to the team"
- "Fetch the latest weather data from OpenWeatherMap API"
- "Integrate with our Notion database"
- "Call the payment webhook to process this order"
- "Get my unread emails via Gmail API"

**Parameters:**
- `action`: request | authenticate | integrate | webhook | parse | chain
- `method`: HTTP method (GET, POST, PUT, DELETE, PATCH)
- `url`: Target API endpoint URL
- `headers`: Custom HTTP headers
- `body`: Request body for POST/PUT/PATCH
- `auth_type`: none | api_key | bearer | basic | oauth
- `auth_credentials`: Authentication credentials
- `service`: Pre-configured service name
- `parse_as`: Response format (json | xml | text | html)
- `timeout`: Request timeout in seconds

## Integration with Existing System

Both new actions are fully integrated into Jarvis's tool system:

1. **Tool Declarations**: Added to `TOOL_DECLARATIONS` in `main.py`
2. **Execution Handlers**: Integrated in `_execute_tool()` method
3. **Learning Support**: Actions are tracked for automatic learning
4. **Natural Language**: Jarvis understands natural language commands for these tools

## Configuration

### API Keys
Add API keys for services in `config/api_keys.json`:
```json
{
    "gemini_api_key": "your-gemini-key",
    "github_api_key": "your-github-token",
    "slack_api_key": "your-slack-token",
    "discord_api_key": "your-discord-token",
    "telegram_api_key": "your-telegram-bot-token",
    "notion_api_key": "your-notion-integration-token"
}
```

### Workflows Directory
Create custom workflows in `workflows/` directory:
```json
{
    "name": "morning_routine",
    "variables": {
        "user_name": "Sir"
    },
    "actions": [
        {"action": "open_app", "parameters": {"app_name": "Chrome"}},
        {"action": "browser_control", "parameters": {"action": "go_to", "url": "https://news.ycombinator.com"}},
        {"action": "computer_settings", "parameters": {"action": "volume_set", "value": "50"}}
    ]
}
```

### Macros Directory
Create macros in `macros/` directory:
```json
{
    "name": "daily_report",
    "actions": [
        {"type": "hotkey", "data": {"keys": "ctrl+n"}},
        {"type": "type", "data": {"text": "Daily Report"}},
        {"type": "click", "data": {"selector": "#submit"}}
    ]
}
```

## Security Considerations

1. **API Key Storage**: Keys are stored in `config/api_keys.json` - ensure this file is protected
2. **Command Validation**: All system commands are validated against dangerous patterns
3. **Confirmation Required**: Destructive actions require user confirmation
4. **Sandboxed Execution**: Automated tasks run with appropriate permissions

## Future Enhancements

Potential future additions:
- Visual workflow builder UI
- More pre-configured service integrations (Salesforce, HubSpot, etc.)
- Advanced monitoring with alerting rules
- Machine learning for workflow optimization
- Collaboration features (shared workflows/macros)
- Voice-controlled automation creation

## Example Commands

Here are some example commands you can give to Jarvis:

### Automation
- "Jarvis, automate my deployment workflow"
- "Schedule a system backup every night at 2 AM"
- "Run my testing macro on the project"
- "Monitor disk space and warn me when it's below 10GB"
- "Execute this batch of commands: open Chrome, go to gmail, check emails"
- "Keep checking if the download is complete"

### API Integration
- "Jarvis, post this update to our Slack #general channel"
- "Create a GitHub issue: 'Fix login bug'"
- "Send a Discord message to the dev team"
- "Fetch the latest stock price for AAPL"
- "Add a new page to my Notion workspace"
- "Send a Telegram message to my phone"
- "Call the weather API for London"

## Technical Details

### Automation Modes

1. **Workflow**: Sequential execution of defined actions with variable substitution
2. **Schedule**: Uses OS-native schedulers (schtasks for Windows, cron for Unix)
3. **Macro**: Low-level input simulation (keyboard, mouse)
4. **Monitor**: Background threads checking conditions at intervals
5. **Batch**: Simple sequential command execution
6. **Loop**: Conditional repetition with exit criteria

### API Controller Features

1. **Retry Logic**: Exponential backoff on failures
2. **Timeout Handling**: Configurable timeouts prevent hanging
3. **Response Parsing**: Automatic detection and parsing of response formats
4. **Error Handling**: Comprehensive error reporting
5. **Chaining**: Context passing between sequential requests

---

**Note**: These enhancements make Jarvis significantly more capable while maintaining the core principles of being obedient, safe, and user-controlled. Always confirm destructive actions and never execute commands without explicit user authorization.
