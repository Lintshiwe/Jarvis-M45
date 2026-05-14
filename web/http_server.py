"""
Simple HTTP server to serve the JARVIS web interface
Run this to access the web UI at http://localhost:8080
"""

import http.server
import socketserver
import os
import webbrowser
import threading
import time

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def log_message(self, format, *args):
        print(f"[Web Server] {args[0]}")


def start_server():
    """Start the HTTP server"""
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        print(f"=" * 60)
        print(f"JARVIS M45 Web Interface Server")
        print(f"=" * 60)
        print(f"Serving at: http://localhost:{PORT}")
        print(f"Directory: {DIRECTORY}")
        print(f"=" * 60)
        print(f"\nOpen your browser and navigate to: http://localhost:{PORT}")
        print(f"\nPress Ctrl+C to stop the server\n")
        
        # Open browser automatically
        threading.Thread(target=lambda: webbrowser.open(f'http://localhost:{PORT}'), daemon=True).start()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nShutting down server...")
            httpd.shutdown()


if __name__ == '__main__':
    start_server()
