#!/usr/bin/env python3
"""
JARVIS M45 - HTTP Server for Web Interface
Serves the static web files and provides API endpoints
"""

import http.server
import socketserver
import json
import os
from urllib.parse import urlparse, parse_qs

# Import JARVIS core
from main import process_command

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class JARVISHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        # API endpoint for processing commands
        if parsed_path.path == '/api/command':
            query_params = parse_qs(parsed_path.query)
            command = query_params.get('q', [''])[0]
            
            if command:
                try:
                    result = process_command(command)
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({'success': True, 'response': result}).encode())
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())
            else:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': 'No command provided'}).encode())
        
        # Health check endpoint
        elif parsed_path.path == '/api/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'online', 'service': 'JARVIS M45'}).encode())
        
        else:
            # Serve static files
            if parsed_path.path == '/':
                self.path = '/index.html'
            return super().do_GET()
    
    def do_POST(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/command':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode())
                command = data.get('command', '')
                
                if command:
                    result = process_command(command)
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({'success': True, 'response': result}).encode())
                else:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({'success': False, 'error': 'No command provided'}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        print(f"[HTTP] {args[0]}")

if __name__ == '__main__':
    with socketserver.TCPServer(("", PORT), JARVISHandler) as httpd:
        print(f"🌐 JARVIS M45 Web Server running at http://localhost:{PORT}")
        print(f"📁 Serving files from: {DIRECTORY}")
        print("Press Ctrl+C to stop the server")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
            httpd.shutdown()
