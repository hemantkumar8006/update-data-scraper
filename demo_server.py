#!/usr/bin/env python3
"""
Simple HTTP server to serve the demo notifications HTML file
This allows the demo scraper to monitor the HTML file via HTTP
"""

import http.server
import socketserver
import os
import webbrowser
import json
from threading import Timer

PORT = 8080

class DemoHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler to serve the demo HTML file"""
    
    def do_GET(self):
        if self.path == '/' or self.path == '/demo':
            # Serve the demo notifications HTML file
            self.path = '/demo_notifications.html'
        return super().do_GET()
    
    def do_POST(self):
        """Handle POST requests for demo notifications"""
        if self.path == '/demo/notifications':
            try:
                # Read the request body
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                # Parse JSON data
                data = json.loads(post_data.decode('utf-8'))
                notifications = data.get('notifications', [])
                
                # Save to demo_notifications.json
                with open('demo_notifications.json', 'w', encoding='utf-8') as f:
                    json.dump(notifications, f, indent=2, ensure_ascii=False)
                
                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = {'success': True, 'message': 'Notifications saved'}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            except Exception as e:
                # Send error response
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = {'success': False, 'error': str(e)}
                self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def end_headers(self):
        # Add CORS headers for cross-origin requests
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def open_browser():
    """Open the demo page in the default browser"""
    webbrowser.open(f'http://localhost:{PORT}')

def main():
    """Start the demo server"""
    # Change to the directory containing the demo HTML file
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with socketserver.TCPServer(("", PORT), DemoHTTPRequestHandler) as httpd:
        print(f"🚀 Demo server running at http://localhost:{PORT}")
        print(f"📝 Demo notifications page: http://localhost:{PORT}/demo")
        print(f"🎓 Main dashboard: http://localhost:5000")
        print("Press Ctrl+C to stop the server")
        
        # Open browser after a short delay
        Timer(1.0, open_browser).start()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Demo server stopped")

if __name__ == '__main__':
    main()
