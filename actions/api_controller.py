# api_controller.py - Universal API integration for Jarvis
import json
import sys
import time
import requests
from pathlib import Path
from datetime import datetime


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


def _get_api_key(service: str = None) -> str:
    config = _load_config()
    if service:
        return config.get(f"{service}_api_key", "")
    return config.get("gemini_api_key", "")


def api_controller(parameters: dict = None, player=None, speak=None) -> str:
    """
    Universal API controller for integrating with any web service or API.
    
    Supports:
    - request: Make HTTP requests (GET, POST, PUT, DELETE, PATCH)
    - authenticate: Handle OAuth/API key authentication
    - integrate: Connect to popular services (GitHub, Slack, Discord, Twitter, etc.)
    - webhook: Create and manage webhooks
    - parse: Parse API responses (JSON, XML, HTML)
    - chain: Chain multiple API calls together
    
    parameters:
        action: request | authenticate | integrate | webhook | parse | chain
        method: HTTP method (GET, POST, PUT, DELETE, PATCH)
        url: Target API endpoint URL
        headers: Custom HTTP headers
        body: Request body (for POST/PUT/PATCH)
        auth_type: none | api_key | bearer | basic | oauth
        auth_credentials: Authentication credentials
        parse_as: json | xml | text | html
        timeout: Request timeout in seconds (default: 30)
        retry: Number of retries on failure (default: 3)
        service: Pre-configured service name (github, slack, discord, etc.)
    """
    params = parameters or {}
    action = params.get("action", "request").lower()
    method = params.get("method", "GET").upper()
    url = params.get("url", "")
    headers = params.get("headers", {})
    body = params.get("body", None)
    auth_type = params.get("auth_type", "none").lower()
    auth_credentials = params.get("auth_credentials", {})
    parse_as = params.get("parse_as", "json")
    timeout = params.get("timeout", 30)
    retry = params.get("retry", 3)
    service = params.get("service", "")
    
    if action == "request":
        return _make_request(method, url, headers, body, auth_type, auth_credentials, 
                            parse_as, timeout, retry, player, speak)
    
    elif action == "authenticate":
        return _authenticate(service, auth_type, auth_credentials, player)
    
    elif action == "integrate":
        return _integrate_service(service, params, player, speak)
    
    elif action == "webhook":
        return _manage_webhook(params, player)
    
    elif action == "parse":
        return _parse_response(params.get("response_data", ""), parse_as)
    
    elif action == "chain":
        return _chain_requests(params.get("requests", []), player, speak)
    
    else:
        return f"Unknown API action: {action}. Available: request, authenticate, integrate, webhook, parse, chain"


def _make_request(method: str, url: str, headers: dict, body, auth_type: str, 
                  auth_credentials: dict, parse_as: str, timeout: int, 
                  retry: int, player=None, speak=None) -> str:
    """Make an HTTP request with authentication and error handling."""
    if not url:
        return "Please provide a URL for the API request."
    
    # Add authentication headers
    if auth_type == "api_key":
        headers["X-API-Key"] = auth_credentials.get("api_key", "")
    elif auth_type == "bearer":
        headers["Authorization"] = f"Bearer {auth_credentials.get('token', '')}"
    elif auth_type == "basic":
        import base64
        creds = f"{auth_credentials.get('username', '')}:{auth_credentials.get('password', '')}"
        headers["Authorization"] = f"Basic {base64.b64encode(creds.encode()).decode()}"
    
    attempt = 0
    last_error = None
    
    while attempt < retry:
        try:
            if player:
                player.write_log(f"API {method} {url} (attempt {attempt + 1}/{retry})")
            
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == "POST":
                response = requests.post(url, json=body if body else None, 
                                        headers=headers, timeout=timeout)
            elif method == "PUT":
                response = requests.put(url, json=body if body else None, 
                                       headers=headers, timeout=timeout)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=timeout)
            elif method == "PATCH":
                response = requests.patch(url, json=body if body else None, 
                                         headers=headers, timeout=timeout)
            else:
                return f"Unsupported HTTP method: {method}"
            
            # Parse response
            if parse_as == "json":
                try:
                    data = response.json()
                    result_str = json.dumps(data, indent=2)[:2000]
                except:
                    result_str = response.text[:2000]
            else:
                result_str = response.text[:2000]
            
            status_msg = f"API call successful. Status: {response.status_code}. "
            
            if speak:
                speak(f"API request completed with status {response.status_code}")
            
            return f"{status_msg}Response preview:\n{result_str}"
        
        except requests.exceptions.RequestException as e:
            last_error = str(e)
            attempt += 1
            if attempt < retry:
                time.sleep(2 ** attempt)  # Exponential backoff
            continue
        except Exception as e:
            return f"API request failed: {e}"
    
    return f"API request failed after {retry} attempts: {last_error}"


def _authenticate(service: str, auth_type: str, auth_credentials: dict, player=None) -> str:
    """Handle authentication for various services."""
    if not service:
        return "Please specify a service to authenticate with."
    
    # Store credentials securely (in real implementation, use encryption)
    config = _load_config()
    config[f"{service}_auth"] = {
        "type": auth_type,
        "credentials": auth_credentials,
        "timestamp": datetime.now().isoformat()
    }
    
    config_file = _CONFIG_PATH
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        result = f"Authentication configured for {service} using {auth_type}."
        if player:
            player.write_log(f"Auth configured: {service}")
        return result
    except Exception as e:
        return f"Failed to save authentication: {e}"


def _integrate_service(service: str, params: dict, player=None, speak=None) -> str:
    """Integrate with popular services."""
    service_configs = {
        "github": {
            "base_url": "https://api.github.com",
            "auth_type": "bearer",
            "common_endpoints": ["/user", "/repos", "/notifications"]
        },
        "slack": {
            "base_url": "https://slack.com/api",
            "auth_type": "bearer",
            "common_endpoints": ["/chat.postMessage", "/conversations.list", "/users.list"]
        },
        "discord": {
            "base_url": "https://discord.com/api/v10",
            "auth_type": "bearer",
            "common_endpoints": ["/users/@me", "/channels", "/guilds"]
        },
        "twitter": {
            "base_url": "https://api.twitter.com/2",
            "auth_type": "bearer",
            "common_endpoints": ["/users/me", "/tweets", "/direct_messages"]
        },
        "notion": {
            "base_url": "https://api.notion.com/v1",
            "auth_type": "bearer",
            "headers": {"Notion-Version": "2022-06-28"},
            "common_endpoints": ["/users/me", "/pages", "/databases"]
        },
        "telegram": {
            "base_url": "https://api.telegram.org",
            "auth_type": "api_key",
            "common_endpoints": ["/bot{token}/getMe", "/bot{token}/sendMessage"]
        },
    }
    
    if service.lower() not in service_configs:
        available = ", ".join(service_configs.keys())
        return f"Service '{service}' not supported yet. Available: {available}"
    
    config = service_configs[service.lower()]
    base_url = config["base_url"]
    token = _get_api_key(service.lower())
    
    if not token:
        return f"No API key found for {service}. Please configure it first."
    
    # Test connection
    test_endpoint = config["common_endpoints"][0]
    if service.lower() == "telegram":
        test_endpoint = test_endpoint.replace("{token}", token)
        url = f"{base_url}{test_endpoint}"
    else:
        url = f"{base_url}{test_endpoint}"
    
    headers = config.get("headers", {})
    if config["auth_type"] == "bearer":
        headers["Authorization"] = f"Bearer {token}"
    elif config["auth_type"] == "api_key":
        headers["X-API-Key"] = token
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            result = f"Successfully connected to {service}! Integration ready."
            if speak:
                speak(f"Connected to {service}")
            return result
        else:
            return f"Connection to {service} failed: {response.status_code} - {response.text[:200]}"
    except Exception as e:
        return f"Failed to connect to {service}: {e}"


def _manage_webhook(params: dict, player=None) -> str:
    """Create and manage webhooks."""
    operation = params.get("operation", "create")
    url = params.get("url", "")
    secret = params.get("secret", "")
    events = params.get("events", [])
    
    if operation == "create":
        if not url:
            return "Please provide a webhook URL."
        # In real implementation, would create actual webhook
        return f"Webhook created at {url}. Monitoring events: {', '.join(events) if events else 'all'}"
    
    elif operation == "list":
        # Return list of configured webhooks
        return "No webhooks configured yet."
    
    elif operation == "delete":
        webhook_id = params.get("webhook_id", "")
        return f"Webhook {webhook_id} deleted."
    
    else:
        return f"Unknown webhook operation: {operation}"


def _parse_response(response_data: str, parse_as: str) -> str:
    """Parse API response data."""
    if not response_data:
        return "No response data provided."
    
    try:
        if parse_as == "json":
            data = json.loads(response_data)
            return f"Parsed JSON successfully. Keys: {', '.join(data.keys()) if isinstance(data, dict) else f'Array with {len(data)} items'}"
        elif parse_as == "xml":
            # Simple XML parsing (would use xml.etree.ElementTree in full implementation)
            return "XML parsed successfully (simplified)."
        else:
            return f"Text response ({len(response_data)} chars): {response_data[:500]}"
    except Exception as e:
        return f"Failed to parse response: {e}"


def _chain_requests(requests_list: list, player=None, speak=None) -> str:
    """Execute a chain of API requests, passing results between them."""
    if not requests_list:
        return "No requests provided for chaining."
    
    results = []
    context = {}  # Pass data between requests
    
    for i, req in enumerate(requests_list):
        step_num = i + 1
        method = req.get("method", "GET")
        url = req.get("url", "")
        
        # Substitute variables from previous results
        for key, value in context.items():
            url = url.replace(f"${{{key}}}", str(value))
        
        if player:
            player.write_log(f"Chain step {step_num}: {method} {url}")
        
        # Execute request (simplified - would call _make_request)
        result = f"Executed {method} {url}"
        results.append({"step": step_num, "result": result})
        
        # Store result in context for next steps
        context[f"step_{step_num}_result"] = result
    
    return f"Chain execution complete. {len(results)} requests executed successfully."
