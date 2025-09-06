import argparse
import sys
import threading
import logging
import json
import time
import os
from datetime import datetime
from flask import Flask, jsonify, request, render_template
from mcp_server.server import MCPExamScrapingServer
from config.settings import WEB_HOST, WEB_PORT


def create_web_interface(server_instance=None):
    """Create a modern web interface for monitoring"""
    app = Flask(__name__, template_folder='templates')
    logger = logging.getLogger(__name__)
    
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
                # Check if file exists and has content
                if not os.path.exists('demo_notifications.json'):
                    return jsonify({'success': True, 'notifications': []})
                
                # Check file size
                if os.path.getsize('demo_notifications.json') == 0:
                    return jsonify({'success': True, 'notifications': []})
                
                with open('demo_notifications.json', 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        return jsonify({'success': True, 'notifications': []})
                    notifications = json.loads(content)
                return jsonify({'success': True, 'notifications': notifications})
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.error(f"Error reading demo notifications: {e}")
                # Try to restore from backup
                try:
                    if os.path.exists('demo_notifications_backup.json'):
                        logger.info("Attempting to restore from backup file")
                        with open('demo_notifications_backup.json', 'r', encoding='utf-8') as f:
                            notifications = json.load(f)
                        # Restore the main file
                        with open('demo_notifications.json', 'w', encoding='utf-8') as f:
                            json.dump(notifications, f, indent=2, ensure_ascii=False)
                        logger.info("Successfully restored demo notifications from backup")
                        return jsonify({'success': True, 'notifications': notifications})
                except Exception as restore_error:
                    logger.error(f"Failed to restore from backup: {restore_error}")
                
                # Return empty array if file is corrupted and backup fails
                return jsonify({'success': True, 'notifications': []})
            except Exception as e:
                logger.error(f"Unexpected error reading demo notifications: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        elif request.method == 'POST':
            # Save demo notifications
            try:
                data = request.get_json()
                notifications = data.get('notifications', [])
                
                # Validate notifications data
                if not isinstance(notifications, list):
                    return jsonify({'success': False, 'error': 'Notifications must be a list'}), 400
                
                # Create backup before saving
                if os.path.exists('demo_notifications.json'):
                    try:
                        import shutil
                        shutil.copy2('demo_notifications.json', 'demo_notifications_backup.json')
                    except Exception as backup_error:
                        logger.warning(f"Failed to create backup: {backup_error}")
                
                # Write to a temporary file first, then rename to prevent corruption
                temp_file = 'demo_notifications_temp.json'
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(notifications, f, indent=2, ensure_ascii=False)
                
                # Atomic rename to prevent corruption
                if os.path.exists('demo_notifications.json'):
                    os.remove('demo_notifications.json')
                os.rename(temp_file, 'demo_notifications.json')
                
                return jsonify({'success': True, 'message': 'Notifications saved'})
            except Exception as e:
                logger.error(f"Error saving demo notifications: {e}")
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
    
    @app.route('/notifications/send-webhook', methods=['POST'])
    def send_webhook_notifications():
        """Send notifications to webhook API"""
        if server_instance:
            try:
                # Get latest notifications
                notification_data = server_instance.notification_manager.get_notification_data()
                notifications = []
                
                # Collect all notifications from different exam types
                for exam_type in ['jee', 'gate', 'jee_adv', 'upsc']:
                    if exam_type in notification_data and notification_data[exam_type]:
                        notifications.extend(notification_data[exam_type])
                
                # Send to webhook
                webhook_result = server_instance.notification_manager.send_webhook_notifications(notifications)
                
                return jsonify({
                    'success': webhook_result['success'],
                    'message': webhook_result['message'],
                    'webhook_results': webhook_result.get('webhook_results', {}),
                    'notifications_sent': len(notifications)
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        return jsonify({'error': 'Server not running'})
    
    @app.route('/webhook/test', methods=['POST'])
    def test_webhook():
        """Test webhook connectivity"""
        if server_instance:
            try:
                webhook_result = server_instance.notification_manager.webhook_service.test_webhook()
                return jsonify({
                    'success': webhook_result['success'],
                    'message': 'Webhook test completed',
                    'webhook_response': webhook_result.get('webhook_response', {}),
                    'error': webhook_result.get('error')
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        return jsonify({'error': 'Server not running'})
    
    @app.route('/backups/cleanup', methods=['POST'])
    def cleanup_backups():
        """Clean up old backup files"""
        if server_instance:
            try:
                # Get the notification manager
                notification_manager = server_instance.notification_manager
                
                # Clean up old backups (keep only last 5)
                notification_manager.cleanup_old_backups(keep_count=5)
                
                return jsonify({
                    'success': True,
                    'message': 'Backup cleanup completed'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        return jsonify({'error': 'Server not running'})
    
    @app.route('/backups/cleanup-all', methods=['POST'])
    def cleanup_all_backups():
        """Remove all backup files (use with caution)"""
        if server_instance:
            try:
                # Get the notification manager
                notification_manager = server_instance.notification_manager
                
                # Remove all backups
                notification_manager.cleanup_all_backups()
                
                return jsonify({
                    'success': True,
                    'message': 'All backup files removed'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
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
    
    @app.route('/notifications/queue/status')
    def get_queue_status():
        """Get notification queue status"""
        if server_instance:
            try:
                queue_status = server_instance.notification_manager.get_queue_status()
                return jsonify({
                    'success': True,
                    'queue_status': queue_status,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        return jsonify({'error': 'Server not running'})
    
    @app.route('/notifications/queue/clear', methods=['POST'])
    def clear_notification_queue():
        """Clear the notification queue"""
        if server_instance:
            try:
                server_instance.notification_manager.clear_queue()
                return jsonify({
                    'success': True,
                    'message': 'Notification queue cleared successfully'
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
