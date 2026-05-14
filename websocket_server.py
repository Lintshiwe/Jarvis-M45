#!/usr/bin/env python3
"""
JARVIS M45 - WebSocket Server for Real-time Communication
Enables bidirectional communication between web interface and JARVIS
"""

import asyncio
import websockets
import json

# Import JARVIS core
from main import process_command

connected_clients = set()

async def handle_client(websocket, path):
    """Handle individual client connections"""
    connected_clients.add(websocket)
    print(f"🔌 Client connected. Total clients: {len(connected_clients)}")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            'type': 'welcome',
            'message': 'Connected to JARVIS M45',
            'status': 'online'
        }))
        
        async for message in websocket:
            try:
                data = json.loads(message)
                
                if data.get('type') == 'command':
                    command = data.get('content', '')
                    print(f"📥 Received command: {command}")
                    
                    # Process command using JARVIS
                    response = process_command(command)
                    
                    # Send response back
                    await websocket.send(json.dumps({
                        'type': 'response',
                        'content': response,
                        'success': True
                    }))
                    
                elif data.get('type') == 'ping':
                    await websocket.send(json.dumps({
                        'type': 'pong',
                        'timestamp': data.get('timestamp')
                    }))
                    
            except json.JSONDecodeError:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': 'Invalid JSON format'
                }))
            except Exception as e:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': str(e)
                }))
                
    except websockets.exceptions.ConnectionClosed:
        print("🔌 Client disconnected")
    finally:
        connected_clients.discard(websocket)
        print(f"🔌 Client removed. Total clients: {len(connected_clients)}")

async def broadcast(message):
    """Broadcast message to all connected clients"""
    if connected_clients:
        await asyncio.gather(
            *[client.send(message) for client in connected_clients],
            return_exceptions=True
        )

async def main():
    """Start WebSocket server"""
    server = await websockets.serve(handle_client, "localhost", 8765)
    print("🌐 JARVIS M45 WebSocket Server running at ws://localhost:8765")
    print("Waiting for client connections...")
    await server.wait_closed()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 WebSocket server stopped by user")
