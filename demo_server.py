import http.server
import socketserver
import os
import webbrowser
import json
from threading import Timer
from utils.webhook_service import create_webhook_service
from data.notification_queue import create_notification_queue

PORT = 8080

class DemoHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    
    def do_GET(self):
        if self.path == '/' or self.path == '/demo':
            self.path = '/demo_notifications.html'
        return super().do_GET()
    
    def do_POST(self):
        if self.path == '/demo/notifications':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                data = json.loads(post_data.decode('utf-8'))
                notifications = data.get('notifications', [])
                
                with open('demo_notifications.json', 'w', encoding='utf-8') as f:
                    json.dump(notifications, f, indent=2, ensure_ascii=False)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = {'success': True, 'message': 'Notifications saved'}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = {'success': False, 'error': str(e)}
                self.wfile.write(json.dumps(response).encode('utf-8'))
        elif self.path == '/demo/send_to_bot':
            try:
                content_length = int(self.headers.get('Content-Length', '0'))
                body = self.rfile.read(content_length) if content_length else b'{}'
                data = json.loads(body.decode('utf-8'))

                notification = {
                    'title': data.get('title', ''),
                    'content_summary': data.get('content', ''),
                    'content': data.get('content', ''),
                    'source': data.get('source', 'demo'),
                    'priority': data.get('priority', 'medium'),
                    'url': data.get('url', ''),
                    'date': data.get('date', ''),
                    'scraped_at': data.get('scrapedAt', ''),
                    'exam_type': data.get('examType', data.get('exam_type', 'demo')),
                }

                service = create_webhook_service()
                result = service.send_notification(notification)

                if not result.get('success'):
                    try:
                        queue_manager = getattr(self.server, 'queue_manager', None)
                        if queue_manager is None:
                            queue_manager = create_notification_queue()
                            setattr(self.server, 'queue_manager', queue_manager)
                        queue_id = queue_manager.add_notification(notification, notification.get('exam_type', 'demo'))
                        result['queued'] = True
                        result['queue_id'] = queue_id
                    except Exception as qe:
                        result['queued'] = False
                        result['queue_error'] = str(qe)

                self.send_response(200 if result.get('success') else 500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def open_browser():
    webbrowser.open(f'http://localhost:{PORT}')

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with socketserver.TCPServer(("", PORT), DemoHTTPRequestHandler) as httpd:
        print(f"🚀 Demo server running at http://localhost:{PORT}")
        print(f"📝 Demo notifications page: http://localhost:{PORT}/demo")
        print(f"🎓 Main dashboard: http://localhost:5000")
        print("Press Ctrl+C to stop the server")
        
        Timer(1.0, open_browser).start()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Demo server stopped")

if __name__ == '__main__':
    main()
