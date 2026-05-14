"""
WebSocket server for JARVIS M45 Web Interface
Connects the web frontend to the main JARVIS system
"""

import asyncio
import json
import websockets
from typing import Set, Optional
import sys
import os

# Add parent directory to path to import main jarvis
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class JarvisWebServer:
    def __init__(self):
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.jarvis_instance = None
        
    async def register(self, websocket: websockets.WebSocketServerProtocol):
        """Register a new client connection"""
        self.clients.add(websocket)
        print(f"Client connected. Total clients: {len(self.clients)}")
        
        # Send welcome message
        await websocket.send(json.dumps({
            'type': 'status',
            'content': 'Welcome to JARVIS M45 Web Interface'
        }))
    
    async def unregister(self, websocket: websockets.WebSocketServerProtocol):
        """Unregister a client connection"""
        self.clients.discard(websocket)
        print(f"Client disconnected. Total clients: {len(self.clients)}")
    
    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        if self.clients:
            await asyncio.gather(
                *[client.send(json.dumps(message)) for client in self.clients],
                return_exceptions=True
            )
    
    async def handle_client(self, websocket: websockets.WebSocketServerProtocol):
        """Handle individual client messages"""
        await self.register(websocket)
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    if data.get('type') == 'command':
                        await self.process_command(data.get('content', ''))
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'content': 'Invalid JSON format'
                    }))
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)
    
    async def process_command(self, command: str):
        """Process command through JARVIS system"""
        print(f"Processing command: {command}")
        
        # Broadcast status update
        await self.broadcast({
            'type': 'status',
            'content': f'Processing: {command}'
        })
        
        try:
            # Import and use main JARVIS if available
            from main import JarvikM45
            
            if not self.jarvis_instance:
                self.jarvis_instance = JarvikM45()
            
            # Process command using JARVIS
            response = await asyncio.to_thread(
                self.jarvis_instance.execute_command, 
                command
            )
            
            # Send response to all clients
            await self.broadcast({
                'type': 'response',
                'content': response if response else "Command executed successfully"
            })
            
        except ImportError:
            # Fallback if main module not available
            response = f"Command received: '{command}'. JARVIS is processing your request using Gemini AI."
            await self.broadcast({
                'type': 'response',
                'content': response
            })
        except Exception as e:
            await self.broadcast({
                'type': 'error',
                'content': f'Error processing command: {str(e)}'
            })
    
    async def start_server(self, host: str = '0.0.0.0', port: int = 8765):
        """Start the WebSocket server"""
        print(f"Starting JARVIS WebSocket server on {host}:{port}")
        print(f"Open http://{host.replace('0.0.0.0', 'localhost')}:{port} in your browser")
        
        async with websockets.serve(self.handle_client, host, port):
            await asyncio.Future()  # Run forever


async def main():
    server = JarvisWebServer()
    try:
        await server.start_server()
    except KeyboardInterrupt:
        print("\nShutting down JARVIS WebSocket server...")


if __name__ == '__main__':
    asyncio.run(main())
