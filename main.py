#!/usr/bin/env python3

import argparse
import sys
import threading
import logging
import json
import time
from datetime import datetime
from flask import Flask, jsonify, request, render_template
from mcp_server.server import MCPExamScrapingServer
from config.settings import WEB_HOST, WEB_PORT


def create_web_interface(server_instance=None):
    """Create a modern web interface for monitoring"""
    app = Flask(__name__, template_folder='templates')
    
    @app.route('/')
    def index():
        return render_template('dashboard.html')
    
    @app.route('/demo')
    def demo():
        """Serve the demo notifications page"""
        try:
            with open('demo_notifications.html', 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return "Demo page not found. Please ensure demo_notifications.html exists.", 404
    
    @app.route('/demo/notifications', methods=['GET', 'POST'])
    def demo_notifications():
        """API endpoint for demo notifications"""
        if request.method == 'GET':
            # Return current demo notifications
            try:
                with open('demo_notifications.json', 'r', encoding='utf-8') as f:
                    notifications = json.load(f)
                return jsonify({'success': True, 'notifications': notifications})
            except FileNotFoundError:
                return jsonify({'success': True, 'notifications': []})
        
        elif request.method == 'POST':
            # Save demo notifications
            try:
                data = request.get_json()
                notifications = data.get('notifications', [])
                
                with open('demo_notifications.json', 'w', encoding='utf-8') as f:
                    json.dump(notifications, f, indent=2, ensure_ascii=False)
                
                return jsonify({'success': True, 'message': 'Notifications saved'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/status')
    def status():
        if server_instance:
            return jsonify(server_instance.get_status())
        return jsonify({'status': 'not_running'})
    
    @app.route('/recent_updates/<int:hours>')
    def recent_updates(hours=24):
        if server_instance:
            updates = server_instance.get_recent_updates(hours)
            return jsonify(updates)
        return jsonify([])
    
    @app.route('/updates/source/<source>')
    def updates_by_source(source):
        if server_instance:
            updates = server_instance.get_updates_by_source(source)
            return jsonify(updates)
        return jsonify([])
    
    @app.route('/updates/exam_type/<exam_type>')
    def updates_by_exam_type(exam_type):
        if server_instance:
            updates = server_instance.get_updates_by_exam_type(exam_type)
            return jsonify(updates)
        return jsonify([])
    
    @app.route('/exam_types')
    def get_exam_types():
        if server_instance:
            exam_types = server_instance.get_all_exam_types()
            return jsonify(exam_types)
        return jsonify([])
    
    @app.route('/export/data')
    def export_data():
        if server_instance:
            try:
                from data.export_data import DataExporter
                exporter = DataExporter(server_instance.storage)
                filepath = exporter.export_to_json()
                return jsonify({
                    'success': True,
                    'filepath': filepath,
                    'message': 'Data exported successfully'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        return jsonify({'error': 'Server not running'}), 500
    
    @app.route('/export/latest')
    def export_latest_data():
        if server_instance:
            try:
                from data.export_data import DataExporter
                exporter = DataExporter(server_instance.storage)
                filepath = exporter.export_latest_data()
                return jsonify({
                    'success': True,
                    'filepath': filepath,
                    'message': 'Latest data exported successfully'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        return jsonify({'error': 'Server not running'}), 500
    
    @app.route('/export/<exam_type>')
    def export_exam_type_data(exam_type):
        if server_instance:
            try:
                from data.export_data import DataExporter
                exporter = DataExporter(server_instance.storage)
                filepath = exporter.export_by_exam_type(exam_type)
                return jsonify({
                    'success': True,
                    'filepath': filepath,
                    'message': f'{exam_type.upper()} data exported successfully'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        return jsonify({'error': 'Server not running'}), 500
    
    @app.route('/scrape', methods=['POST'])
    def trigger_scrape():
        if server_instance:
            result = server_instance.run_single_scrape()
            return jsonify(result)
        return jsonify({'error': 'Server not running'})
    
    @app.route('/notifications/init', methods=['POST'])
    def init_notifications():
        if server_instance:
            result = server_instance.initial_setup()
            return jsonify(result)
        return jsonify({'error': 'Server not running'})
    
    @app.route('/notifications/status')
    def notification_status():
        if server_instance:
            result = server_instance.get_notification_status()
            return jsonify(result)
        return jsonify({'error': 'Server not running'})
    
    @app.route('/notifications/clear', methods=['POST'])
    def clear_notifications():
        if server_instance:
            result = server_instance.clear_notifications()
            return jsonify(result)
        return jsonify({'error': 'Server not running'})
    
    @app.route('/websites', methods=['GET'])
    def get_websites():
        if server_instance:
            websites = []
            for name, scraper in server_instance.scrapers.items():
                websites.append({
                    'name': name,
                    'url': scraper.config['url'],
                    'enabled': scraper.config.get('enabled', True),
                    'priority': scraper.config.get('priority', 'medium')
                })
            return jsonify(websites)
        return jsonify([])
    
    @app.route('/websites/<website_name>/toggle', methods=['POST'])
    def toggle_website(website_name):
        if server_instance:
            data = request.get_json()
            enabled = data.get('enabled', True)
            
            if enabled:
                result = server_instance.enable_website(website_name)
            else:
                result = server_instance.disable_website(website_name)
            
            return jsonify({'success': result})
        return jsonify({'error': 'Server not running'})
    
    @app.route('/notifications/latest')
    def get_latest_notifications():
        """Get the latest notifications from the notification manager"""
        if server_instance:
            try:
                # Get notifications from the notification manager
                notification_data = server_instance.notification_manager.get_notification_data()
                return jsonify({
                    'success': True,
                    'notifications': notification_data,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        return jsonify({'error': 'Server not running'})
    
    @app.route('/notifications/stream')
    def stream_notifications():
        """Stream real-time notifications using Server-Sent Events"""
        if not server_instance:
            return jsonify({'error': 'Server not running'}), 500
        
        def generate():
            last_count = 0
            heartbeat_interval = 30  # seconds
            last_heartbeat = time.time()
            
            while True:
                try:
                    current_time = time.time()
                    
                    # Get current notification count
                    notification_data = server_instance.notification_manager.get_notification_data()
                    current_count = notification_data.get('total_new_notifications', 0)
                    
                    # If there are new notifications, send them
                    if current_count > last_count:
                        yield f"data: {json.dumps({
                            'type': 'new_notifications',
                            'count': current_count - last_count,
                            'notifications': notification_data,
                            'timestamp': datetime.now().isoformat()
                        })}\n\n"
                        last_count = current_count
                    
                    # Send heartbeat every 30 seconds
                    if current_time - last_heartbeat >= heartbeat_interval:
                        yield f"data: {json.dumps({
                            'type': 'heartbeat',
                            'timestamp': datetime.now().isoformat()
                        })}\n\n"
                        last_heartbeat = current_time
                    
                    time.sleep(5)  # Check every 5 seconds for responsiveness
                    
                except Exception as e:
                    yield f"data: {json.dumps({
                        'type': 'error',
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })}\n\n"
                    break
        
        return app.response_class(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Cache-Control'
            }
        )
    
    return app


def main():
    parser = argparse.ArgumentParser(description='Exam Update Scraping Server')
    parser.add_argument('--mode', choices=['server', 'single-run', 'web'], 
                       default='server', help='Run mode')
    parser.add_argument('--port', type=int, default=WEB_PORT, 
                       help='Web interface port')
    parser.add_argument('--host', type=str, default=WEB_HOST,
                       help='Web interface host')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    if args.mode == 'single-run':
        # Run scraping once and exit
        logger.info("Running single scraping cycle...")
        server = MCPExamScrapingServer()
        result = server.scrape_all_websites()
        print(f"Single run completed. Found {result['new_updates_count']} new updates.")
        
    elif args.mode == 'web':
        # Start web interface only
        logger.info(f"Starting web interface on {args.host}:{args.port}")
        app = create_web_interface()
        app.run(host=args.host, port=args.port, debug=False)
        
    elif args.mode == 'server':
        # Start full server with web interface
        logger.info("Starting MCP Exam Scraping Server...")
        server = MCPExamScrapingServer()
        
        app = create_web_interface(server)
        
        # Start server in background thread
        server_thread = threading.Thread(target=server.start_scheduler)
        server_thread.daemon = True
        server_thread.start()
        
        # Start web interface
        logger.info(f"Starting web interface on {args.host}:{args.port}")
        logger.info(f"Visit http://{args.host}:{args.port}/ for dashboard")
        logger.info(f"API endpoints available at http://{args.host}:{args.port}/status")
        
        try:
            app.run(host=args.host, port=args.port, debug=False)
        except KeyboardInterrupt:
            logger.info("Shutting down server...")
            server.stop_scheduler()
            sys.exit(0)


if __name__ == '__main__':
    main()
