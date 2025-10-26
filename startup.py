#!/usr/bin/env python3
"""
Startup script for Cloud Run deployment
Handles configuration and starts the web server
"""
import os
import sys
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_configuration():
    """Check if required configuration files exist"""
    config_files = [
        'AUTH/auth.txt',
        'TICKERS/my_tickers.txt'
    ]
    
    missing_files = []
    for file_path in config_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
            logger.warning(f"Missing configuration file: {file_path}")
    
    return len(missing_files) == 0, missing_files

def create_sample_config():
    """Create sample configuration files if they don't exist"""
    # Create AUTH directory if it doesn't exist
    os.makedirs('AUTH', exist_ok=True)
    
    # Create sample auth.txt
    if not os.path.exists('AUTH/auth.txt'):
        sample_auth = {
            "APCA-API-KEY-ID": "YOUR_API_KEY_HERE",
            "APCA-API-SECRET-KEY": "YOUR_SECRET_KEY_HERE"
        }
        with open('AUTH/auth.txt', 'w') as f:
            json.dump(sample_auth, f, indent=2)
        logger.info("Created sample AUTH/auth.txt")
    
    # Create TICKERS directory if it doesn't exist
    os.makedirs('TICKERS', exist_ok=True)
    
    # Create sample my_tickers.txt
    if not os.path.exists('TICKERS/my_tickers.txt'):
        sample_tickers = "AAPL\nAMZN\nTSLA\nMA"
        with open('TICKERS/my_tickers.txt', 'w') as f:
            f.write(sample_tickers)
        logger.info("Created sample TICKERS/my_tickers.txt")

def main():
    """Main startup function"""
    logger.info("🚀 Starting Alpaca Trading Bot Dashboard")
    
    # Check configuration
    config_ok, missing_files = check_configuration()
    
    if not config_ok:
        logger.warning(f"Missing configuration files: {missing_files}")
        logger.info("Creating sample configuration files...")
        create_sample_config()
    
    # Start the web server
    logger.info("Starting web server...")
    try:
        from web_server import start_dashboard_server
        port = int(os.environ.get("PORT", 8080))
        start_dashboard_server(port)
    except Exception as e:
        logger.error(f"Failed to start web server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()