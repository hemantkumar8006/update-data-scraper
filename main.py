#!/usr/bin/env python3

import argparse
import sys
import threading
import logging
from flask import Flask, jsonify, request
from mcp_server.server import MCPExamScrapingServer
from config.settings import WEB_HOST, WEB_PORT


def create_web_interface(server_instance=None):
    """Create a simple web interface for monitoring"""
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return '''
        <html>
        <head>
            <title>Exam Scraper Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
                .success { background-color: #d4edda; border: 1px solid #c3e6cb; }
                .error { background-color: #f8d7da; border: 1px solid #f5c6cb; }
                .info { background-color: #d1ecf1; border: 1px solid #bee5eb; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <h1>Exam Update Scraping System</h1>
            <div id="status"></div>
            <div id="recent-updates"></div>
            <script>
                function loadStatus() {
                    fetch('/status')
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('status').innerHTML = 
                                '<div class="status success">System Status: ' + data.status + '</div>' +
                                '<div class="status info">Active Scrapers: ' + data.total_scrapers + '</div>' +
                                '<div class="status info">Recent Updates (24h): ' + data.recent_updates_24h + '</div>';
                        });
                }
                
                function loadRecentUpdates() {
                    fetch('/recent_updates/24')
                        .then(response => response.json())
                        .then(data => {
                            let html = '<h2>Recent Updates (Last 24 Hours)</h2><table><tr><th>Title</th><th>Source</th><th>Exam Type</th><th>Date</th></tr>';
                            data.slice(0, 10).forEach(update => {
                                html += '<tr><td>' + update.title + '</td><td>' + update.source + '</td><td>' + (update.exam_type || 'N/A') + '</td><td>' + update.scraped_at + '</td></tr>';
                            });
                            html += '</table>';
                            html += '<div style="margin-top: 20px;">';
                            html += '<button onclick="exportData()" style="background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin-right: 10px;">Export All Data</button>';
                            html += '<button onclick="exportLatestData()" style="background: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;">Export Latest Data</button>';
                            html += '</div>';
                            document.getElementById('recent-updates').innerHTML = html;
                        });
                }
                
                function exportData() {
                    fetch('/export/data')
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                alert('Data exported successfully!\\nFile: ' + data.filepath);
                            } else {
                                alert('Export failed: ' + data.error);
                            }
                        })
                        .catch(error => {
                            alert('Export failed: ' + error);
                        });
                }
                
                function exportLatestData() {
                    fetch('/export/latest')
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                alert('Latest data exported successfully!\\nFile: ' + data.filepath);
                            } else {
                                alert('Export failed: ' + data.error);
                            }
                        })
                        .catch(error => {
                            alert('Export failed: ' + error);
                        });
                }
                
                loadStatus();
                loadRecentUpdates();
                setInterval(loadStatus, 30000); // Refresh every 30 seconds
                setInterval(loadRecentUpdates, 60000); // Refresh every minute
            </script>
        </body>
        </html>
        '''
    
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
