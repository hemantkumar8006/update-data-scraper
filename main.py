#!/usr/bin/env python3

import argparse
import sys
import threading
import logging
from flask import Flask, jsonify, request
from mcp_server.server import MCPExamScrapingServer
from config.settings import WEB_HOST, WEB_PORT


def create_web_interface():
    """Create a simple web interface for monitoring"""
    app = Flask(__name__)
    server_instance = None
    
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
                            let html = '<h2>Recent Updates (Last 24 Hours)</h2><table><tr><th>Title</th><th>Source</th><th>Importance</th><th>Date</th></tr>';
                            data.slice(0, 10).forEach(update => {
                                html += '<tr><td>' + update.title + '</td><td>' + update.source + '</td><td>' + (update.importance || 'N/A') + '</td><td>' + update.scraped_at + '</td></tr>';
                            });
                            html += '</table>';
                            document.getElementById('recent-updates').innerHTML = html;
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
    
    @app.route('/updates/importance/<importance>')
    def updates_by_importance(importance):
        if server_instance:
            updates = server_instance.get_updates_by_importance(importance)
            return jsonify(updates)
        return jsonify([])
    
    @app.route('/scrape', methods=['POST'])
    def trigger_scrape():
        if server_instance:
            result = server_instance.run_single_scrape()
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
        
        # Set global server instance for web interface
        global server_instance
        server_instance = server
        
        app = create_web_interface()
        
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
