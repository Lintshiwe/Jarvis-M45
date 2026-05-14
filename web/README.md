# JARVIS M45 Web Interface

Access your JARVIS AI assistant through a modern web interface with real-time communication.

## 🚀 Quick Start

### Option 1: Simple Web UI (Static)
```bash
cd /workspace/web
python http_server.py
```
Then open http://localhost:8080 in your browser.

### Option 2: Full WebSocket Integration (Real-time)
```bash
# Terminal 1: Start WebSocket server
cd /workspace/web
python websocket_server.py

# Terminal 2: Start HTTP server
cd /workspace/web
python http_server.py
```

## ✨ Features

- **Modern UI**: Sleek, futuristic interface with animations
- **Real-time Chat**: WebSocket-based instant communication
- **Voice Input**: Speech-to-text support (Chrome/Edge)
- **Quick Actions**: Pre-configured command buttons
- **Status Indicators**: Connection status and typing indicators
- **Responsive Design**: Works on desktop and mobile

## 🎨 Interface Components

1. **Header**: Shows JARVIS logo and connection status
2. **Sidebar**: Quick action buttons for common tasks
3. **Chat Area**: Message history with user/JARVIS bubbles
4. **Input Area**: Text input, voice button, and send button

## 🔧 Configuration

The web interface connects to:
- **WebSocket Server**: `ws://localhost:8765` (for real-time commands)
- **HTTP Server**: `http://localhost:8080` (for UI)

## 📋 Requirements

Install required packages:
```bash
pip install websockets
```

## 🎯 Usage Examples

Once running, you can:
- Type commands in the chat input
- Click quick action buttons for common tasks
- Use voice input (microphone button)
- See real-time responses from JARVIS

## 🌐 Access from Other Devices

To access from other devices on your network:
1. Find your IP address: `ipconfig` (Windows) or `ifconfig` (Linux/Mac)
2. The servers bind to `0.0.0.0` by default
3. Access via: `http://YOUR_IP:8080`

## 🔒 Security Notes

- Default setup is for local development only
- For production use, add authentication and HTTPS
- Don't expose directly to the internet without proper security

## 🛠️ Troubleshooting

**Port already in use:**
```bash
# Change port in http_server.py or websocket_server.py
PORT = 8081  # or any available port
```

**WebSocket connection failed:**
- Ensure websocket_server.py is running
- Check firewall settings
- Verify port 8765 is not blocked

**Voice input not working:**
- Use Chrome or Edge browser
- Grant microphone permissions
- Ensure HTTPS in production (required for voice API)
