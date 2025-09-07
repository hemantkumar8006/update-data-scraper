#!/usr/bin/env python3
"""
Start Configurable Exam Scraper - Entry point for the new configurable system
"""

import argparse
import sys
import logging
from mcp_server.configurable_server import ConfigurableExamScrapingServer
from main import create_web_interface
from api.config_api import config_api
from flask import Flask

def main():
    parser = argparse.ArgumentParser(description='Configurable Exam Scraping Server')
    parser.add_argument('--mode', choices=['server', 'single-run', 'web', 'config'], 
                       default='server', help='Run mode')
    parser.add_argument('--port', type=int, default=5000, 
                       help='Web interface port')
    parser.add_argument('--host', type=str, default='0.0.0.0',
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
        logger.info("Running single scraping cycle with configurable system...")
        server = ConfigurableExamScrapingServer()
        result = server.scrape_all_websites()
        print(f"Single run completed. Found {result['new_updates_count']} new updates.")
        
    elif args.mode == 'web':
        # Start web interface only
        logger.info(f"Starting web interface on {args.host}:{args.port}")
        app = create_web_interface()
        app.run(host=args.host, port=args.port, debug=False)
        
    elif args.mode == 'config':
        # Start configuration interface only
        logger.info(f"Starting configuration interface on {args.host}:{args.port}")
        app = Flask(__name__)
        
        @app.route('/')
        def config_interface():
            with open('templates/config_interface.html', 'r', encoding='utf-8') as f:
                return f.read()
        
        # Register configuration API
        app.register_blueprint(config_api)
        
        app.run(host=args.host, port=args.port, debug=False)
        
    elif args.mode == 'server':
        # Start full server with web interface
        logger.info("Starting Configurable Exam Scraping Server...")
        server = ConfigurableExamScrapingServer()
        
        app = create_web_interface(server)
        
        # Register configuration API
        app.register_blueprint(config_api)
        
        # Add configuration interface route
        @app.route('/config')
        def config_interface():
            with open('templates/config_interface.html', 'r', encoding='utf-8') as f:
                return f.read()
        
        # Start server in background thread
        import threading
        server_thread = threading.Thread(target=server.start_scheduler)
        server_thread.daemon = True
        server_thread.start()
        
        # Start web interface
        logger.info(f"Starting web interface on {args.host}:{args.port}")
        logger.info(f"Visit http://{args.host}:{args.port}/ for dashboard")
        logger.info(f"Visit http://{args.host}:{args.port}/config for configuration interface")
        logger.info(f"API endpoints available at http://{args.host}:{args.port}/status")
        
        try:
            app.run(host=args.host, port=args.port, debug=False)
        except KeyboardInterrupt:
            logger.info("Shutting down server...")
            server.stop_scheduler()
            sys.exit(0)

if __name__ == '__main__':
    main()
