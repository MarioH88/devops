#!/usr/bin/env python3
"""
Web Server for LIVE DevOps Demo Dashboard
Designed for Cloud Run deployment
"""
import json
import os
import time
from datetime import datetime
from pytz import timezone
import pandas as pd
import alpaca_trade_api as alpaca
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
ORDERS_CSV_FILE = 'Orders.csv'
UNNAMED_COLUMN = 'Unnamed: 0'
AUTH_FILE = 'AUTH/auth.txt'
TICKERS_FILE = 'TICKERS/my_tickers.txt'
CONTENT_TYPE_HTML = 'text/html'
CONTENT_TYPE_JSON = 'application/json'
DEMO_GRADIENT = 'linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%)'

class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/dashboard':
            self.send_response(200)
            self.send_header('Content-type', CONTENT_TYPE_HTML)
            self.end_headers()
            html = self.generate_dashboard_html()
            self.wfile.write(html.encode('utf-8'))
        
        elif self.path == '/health':
            # Health check endpoint for Cloud Run
            self.send_response(200)
            self.send_header('Content-type', CONTENT_TYPE_HTML)
            self.end_headers()
            health_html = '''
            <html><head><title>Health Check</title></head>
            <body style="font-family: Arial; text-align: center; padding: 30px; background: #2ecc71; color: white;">
                <h1>✅ LIVE DevOps Demo - System Healthy!</h1>
                <p>Deployment Pipeline: <strong>ACTIVE</strong></p>
                <p>Auto-scaling: <strong>ENABLED</strong></p>
                <p>Time: <strong>{}</strong></p>
                <div style="margin-top: 20px; padding: 15px; background: rgba(0,0,0,0.2); border-radius: 5px;">
                    <small>This page proves the DevOps pipeline deployed successfully!</small>
                </div>
            </body></html>
            '''.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'))
            self.wfile.write(health_html.encode('utf-8'))
        
        elif self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-type', CONTENT_TYPE_JSON)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            status_data = self.get_bot_status_json()
            self.wfile.write(status_data.encode('utf-8'))
        
        else:
            self.send_response(404)
            self.send_header('Content-type', CONTENT_TYPE_HTML)
            self.end_headers()
            error_html = '''
            <html><head><title>🚀 DevOps Demo - Page Not Found</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px; background: linear-gradient(45deg, #FF6B6B, #4ECDC4); color: white;">
                <h1>🚀 LIVE DevOps DEMO!</h1>
                <h2>Page Not Found - But The Pipeline Works!</h2>
                <p>Try: <a href="/" style="color: yellow;">Dashboard Home</a> | <a href="/health" style="color: yellow;">Health Check</a></p>
                <div style="margin-top: 30px; padding: 20px; background: rgba(0,0,0,0.3); border-radius: 10px;">
                    <h3>🎯 This change was deployed automatically via:</h3>
                    <p>GitHub → Cloud Build → Container Registry → Cloud Run</p>
                </div>
            </body></html>
            '''
            self.wfile.write(error_html.encode('utf-8'))
    
    def get_bot_status_json(self):
        """Get bot status as JSON for API endpoint"""
        try:
            # Check if configuration files exist
            if not os.path.exists(AUTH_FILE) or not os.path.exists(TICKERS_FILE):
                return json.dumps({
                    'error': 'Configuration files not found',
                    'status': 'Configuration Error',
                    'message': f'{AUTH_FILE} or {TICKERS_FILE} not found'
                })
            
            # Load configuration
            key = json.loads(open(AUTH_FILE, 'r').read())
            api = alpaca.REST(
                key['APCA-API-KEY-ID'], 
                key['APCA-API-SECRET-KEY'], 
                base_url='https://paper-api.alpaca.markets', 
                api_version='v2'
            )
            
            # Get current data
            account = api.get_account()
            clock = api.get_clock()
            positions = api.list_positions()
            
            with open(TICKERS_FILE, 'r') as f:
                tickers = f.read().upper().split()
            
            # Get ticker prices (limit to first 3 for performance)
            ticker_prices = {}
            for ticker in tickers[:3]:
                try:
                    trade = api.get_latest_trade(ticker)
                    ticker_prices[ticker] = float(trade.price)
                except Exception:
                    ticker_prices[ticker] = 0
            
            # Get trading history
            trades_count = 0
            recent_trades = []
            if os.path.exists(ORDERS_CSV_FILE):
                try:
                    df = pd.read_csv(ORDERS_CSV_FILE)
                    if UNNAMED_COLUMN in df.columns:
                        df = df.drop(columns=[UNNAMED_COLUMN])
                    trades_count = len(df)
                    recent_trades = df.tail(5).to_dict('records')
                except Exception:
                    pass
            
            # Bot status
            first_trade_made = os.path.exists('FirstTrade.csv')
            
            status = {
                'timestamp': datetime.now().isoformat(),
                'market_open': clock.is_open,
                'next_open': str(clock.next_open),
                'account': {
                    'cash': float(account.cash),
                    'portfolio_value': float(account.portfolio_value),
                    'buying_power': float(account.buying_power),
                    'positions_count': len(positions)
                },
                'bot': {
                    'first_trade_made': first_trade_made,
                    'mode': '1-minute analysis' if first_trade_made else '30-minute analysis'
                },
                'tickers': ticker_prices,
                'trading': {
                    'total_trades': trades_count,
                    'recent_trades': recent_trades
                }
            }
            
            return json.dumps(status, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting bot status: {e}")
            return json.dumps({
                'error': str(e),
                'status': 'Error',
                'message': 'Unable to fetch bot status'
            })
    
    def load_dashboard_data(self):
        """Load all data needed for dashboard"""
        try:
            # Check if configuration files exist
            if not os.path.exists(AUTH_FILE) or not os.path.exists(TICKERS_FILE):
                return None
            
            # Load configuration
            key = json.loads(open(AUTH_FILE, 'r').read())
            api = alpaca.REST(
                key['APCA-API-KEY-ID'], 
                key['APCA-API-SECRET-KEY'], 
                base_url='https://paper-api.alpaca.markets', 
                api_version='v2'
            )
            
            # Get current data
            account = api.get_account()
            clock = api.get_clock()
            positions = api.list_positions()
            et_tz = timezone('America/New_York')
            current_time = datetime.now(et_tz)
            
            with open(TICKERS_FILE, 'r') as f:
                tickers = f.read().upper().split()
            
            return {
                'api': api,
                'account': account,
                'clock': clock,
                'positions': positions,
                'current_time': current_time,
                'tickers': tickers
            }
        except Exception as e:
            logger.error(f"Error loading dashboard data: {e}")
            return None

    def get_ticker_data(self, api, tickers):
        """Get ticker price data (limited for performance)"""
        ticker_data = []
        # Limit to first 4 tickers for Cloud Run performance
        for ticker in tickers[:4]:
            try:
                trade = api.get_latest_trade(ticker)
                ticker_data.append({
                    'symbol': ticker,
                    'price': float(trade.price)
                })
            except Exception:
                ticker_data.append({
                    'symbol': ticker,
                    'price': 'Error'
                })
        return ticker_data

    def get_dashboard_trading_history(self):
        """Get trading history for dashboard"""
        trading_history = []
        if os.path.exists(ORDERS_CSV_FILE):
            try:
                df = pd.read_csv(ORDERS_CSV_FILE)
                if UNNAMED_COLUMN in df.columns:
                    df = df.drop(columns=[UNNAMED_COLUMN])
                trading_history = df.tail(10).to_dict('records')
            except Exception:
                pass
        return trading_history

    def generate_dashboard_html(self):
        """Generate the main dashboard HTML"""
        # Load all data
        data = self.load_dashboard_data()
        if not data:
            return self.generate_error_html("Configuration Error", 
                                           f"Unable to load configuration. Please check {AUTH_FILE} and {TICKERS_FILE} files.")
        
        try:
            # Extract data
            account = data['account']
            clock = data['clock']
            positions = data['positions']
            tickers = data['tickers']
            
            # Get additional data
            ticker_data = self.get_ticker_data(data['api'], tickers)
            trading_history = self.get_dashboard_trading_history()
            
            # Bot status
            first_trade_made = os.path.exists('FirstTrade.csv')
            bot_mode = '1-minute analysis' if first_trade_made else '30-minute analysis (first trade)'
            
            return self.generate_main_html_template(
                clock, account, positions, 
                bot_mode, first_trade_made, ticker_data, trading_history
            )
        except Exception as e:
            logger.error(f"Error generating dashboard: {e}")
            return self.generate_error_html("Dashboard Error", f"Error generating dashboard: {str(e)}")

    def generate_error_html(self, title, message):
        """Generate error page HTML"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title} - DevOps Demo</title>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%);
                    color: white;
                    min-height: 100vh;
                    padding: 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .error-container {{
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(10px);
                    border-radius: 15px;
                    padding: 40px;
                    text-align: center;
                    max-width: 600px;
                }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <h1>🚀 DevOps Demo Dashboard</h1>
                <h2>❌ {title}</h2>
                <p>{message}</p>
                <p><small>Check logs for more details</small></p>
                <button onclick="location.reload()" style="background: #FF6B6B; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">
                    🔄 Retry
                </button>
            </div>
        </body>
        </html>
        """

    def generate_main_html_template(self, clock, account, positions, bot_mode, first_trade_made, ticker_data, trading_history):
        """Generate the main HTML template"""
        market_status_emoji = "🟢" if clock.is_open else "🔴"
        market_status_text = "OPEN" if clock.is_open else "CLOSED"
        market_status_class = "status-open" if clock.is_open else "status-closed"
        
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <title>🚀 Live Trading Dashboard</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta http-equiv="refresh" content="60">
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%);
                    color: white;
                    min-height: 100vh;
                    padding: 20px;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    padding: 20px;
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(10px);
                    border-radius: 15px;
                }}
                .status-banner {{
                    background: rgba(255, 255, 255, 0.15);
                    padding: 15px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                    text-align: center;
                    font-size: 1.2em;
                    font-weight: bold;
                }}
                .status-bar {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin-bottom: 20px;
                }}
                .status-item {{
                    background: rgba(255, 255, 255, 0.1);
                    padding: 15px;
                    border-radius: 10px;
                    text-align: center;
                }}
                .status-value {{
                    font-size: 1.5em;
                    font-weight: bold;
                    margin-bottom: 5px;
                }}
                .dashboard-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .card {{
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(10px);
                    border-radius: 15px;
                    padding: 20px;
                }}
                .card h3 {{
                    margin-top: 0;
                    color: #ffd700;
                    border-bottom: 2px solid #ffd700;
                    padding-bottom: 10px;
                    margin-bottom: 15px;
                }}
                .metric {{
                    display: flex;
                    justify-content: space-between;
                    margin: 10px 0;
                    padding: 8px 0;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                }}
                .metric:last-child {{
                    border-bottom: none;
                }}
                .status-open {{ color: #4ade80; }}
                .status-closed {{ color: #f87171; }}
                .positive {{ color: #4ade80; }}
                .negative {{ color: #f87171; }}
                .ticker-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                    gap: 15px;
                }}
                .ticker-card {{
                    background: rgba(255, 255, 255, 0.05);
                    padding: 15px;
                    border-radius: 10px;
                    text-align: center;
                }}
                .refresh-info {{
                    text-align: center;
                    margin-top: 20px;
                    opacity: 0.7;
                }}
                .working-indicator {{
                    display: inline-block;
                    width: 12px;
                    height: 12px;
                    background: #4ade80;
                    border-radius: 50%;
                    animation: pulse 2s infinite;
                    margin-right: 8px;
                }}
                @keyframes pulse {{
                    0% {{ opacity: 1; transform: scale(1); }}
                    50% {{ opacity: 0.7; transform: scale(1.1); }}
                    100% {{ opacity: 1; transform: scale(1); }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Group 2 DevOps Project</h1>
                    <p><span class="working-indicator"></span>DevOps Pipeline Status: ACTIVE</p>
                    <p>🌐 Auto-deployed via GitHub → Cloud Build → Cloud Run</p>
                </div>
                
                <div style="background: linear-gradient(45deg, #FF6B6B, #4ECDC4); padding: 15px; margin: 20px 0; border-radius: 10px; color: white; text-align: center; font-weight: bold; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                    🚀 asdads asd sda dasd asdda  successy to https://devops-backup-1002595611169.europe-west1.run.app/ 🚀
                </div>
                
                <div class="status-banner">
                    {market_status_emoji} Market is {market_status_text}
                    {' - Next open: ' + str(clock.next_open)[:16] if not clock.is_open else ''}
                </div>
                
                <div class="status-bar">
                    <div class="status-item">
                        <div class="status-value {market_status_class}">
                            {market_status_emoji} {market_status_text}
                        </div>
                        <div>Market Status</div>
                    </div>
                    <div class="status-item">
                        <div class="status-value">${float(account.cash):,.0f}</div>
                        <div>Available Cash</div>
                    </div>
                    <div class="status-item">
                        <div class="status-value">${float(account.portfolio_value):,.0f}</div>
                        <div>Portfolio Value</div>
                    </div>
                    <div class="status-item">
                        <div class="status-value">{len(positions)}</div>
                        <div>Open Positions</div>
                    </div>
                </div>
                
                <div class="dashboard-grid">
                    <!-- Bot Status -->
                    <div class="card">
                        <h3>🔥 Live System Status</h3>
                        <div class="metric">
                            <span>Mode:</span>
                            <span>{bot_mode}</span>
                        </div>
                        <div class="metric">
                            <span>First Trade:</span>
                            <span>{'✅ Yes' if first_trade_made else '⏳ Pending'}</span>
                        </div>
                        <div class="metric">
                            <span>PDT Status:</span>
                            <span class="{'negative' if account.pattern_day_trader else 'positive'}">
                                {'❌ Yes' if account.pattern_day_trader else '✅ No'}
                            </span>
                        </div>
                        <div class="metric">
                            <span>Connection:</span>
                            <span class="positive">✅ Connected</span>
                        </div>
                    </div>
                    
                    <!-- Account Details -->
                    <div class="card">
                        <h3>💰 Account Details</h3>
                        <div class="metric">
                            <span>Cash:</span>
                            <span>${float(account.cash):,.2f}</span>
                        </div>
                        <div class="metric">
                            <span>Buying Power:</span>
                            <span>${float(account.buying_power):,.2f}</span>
                        </div>
                        <div class="metric">
                            <span>Day Trades:</span>
                            <span>{account.daytrade_count}/3</span>
                        </div>
                        <div class="metric">
                            <span>Account Type:</span>
                            <span>Paper Trading</span>
                        </div>
                    </div>
                </div>
                
                <!-- Ticker Prices -->
                <div class="card">
                    <h3>📈 Live Ticker Prices</h3>
                    <div class="ticker-grid">
                        {self.generate_tickers_html(ticker_data)}
                    </div>
                </div>
                
                <!-- Trading History -->
                {self.generate_history_html(trading_history)}
                
                <div class="refresh-info">
                    <p>🔄 Page auto-refreshes every 60 seconds</p>
                    <p>📊 <a href="/api/status" style="color: #ffd700;">View Raw JSON Data</a></p>
                    <p>🏥 <a href="/health" style="color: #ffd700;">Health Check</a></p>
                </div>
            </div>
        </body>
        </html>
        """

    def generate_tickers_html(self, ticker_data):
        """Generate ticker prices HTML"""
        html = ""
        for ticker in ticker_data:
            if ticker['price'] != 'Error':
                html += f'''
                <div class="ticker-card">
                    <div style="font-weight: bold;">{ticker['symbol']}</div>
                    <div style="font-size: 1.2em; color: #ffd700;">${ticker['price']:.2f}</div>
                </div>
                '''
            else:
                html += f'''
                <div class="ticker-card">
                    <div style="font-weight: bold;">{ticker['symbol']}</div>
                    <div style="color: #f87171;">Error</div>
                </div>
                '''
        return html

    def generate_history_html(self, trading_history):
        """Generate trading history HTML"""
        if not trading_history:
            return '<div class="card"><h3>📋 Trading History</h3><p>No trades yet - Ready for action!</p></div>'
        
        html = '<div class="card"><h3>📋 Recent Trading History</h3>'
        html += '<div style="overflow-x: auto;">'
        
        for trade in trading_history[-5:]:  # Last 5 trades
            trade_class = "positive" if trade['Type'] == 'sell' else "status-open"
            html += f'''
            <div class="metric">
                <span>{trade['Time']} - {trade['Type'].upper()} {trade['Ticker']}</span>
                <span class="{trade_class}">${trade['Total']:,.2f}</span>
            </div>
            '''
        
        html += '</div></div>'
        return html
    
    def log_message(self, format, *args):
        """Override to use proper logging"""
        logger.info("%s - - [%s] %s" % (self.address_string(), self.log_date_time_string(), format % args))

def start_dashboard_server(port=8080):
    """Start the dashboard web server for Cloud Run"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, DashboardHandler)
    
    logger.info(f"🚀 LIVE DevOps Demo Dashboard starting on port {port}")
    logger.info("✅ Ready to accept HTTP traffic")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down dashboard server...")
        httpd.shutdown()

if __name__ == "__main__":
    # Get port from environment variable (Cloud Run provides this)
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🌐 Starting server on 0.0.0.0:{port}")
    start_dashboard_server(port)
