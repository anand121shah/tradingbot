from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from trading_bot import TradingBot
from strategy import TradingStrategy
from loguru import logger
import threading
import time
from datetime import datetime, timedelta
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
from risk_manager import RiskManager, PositionRisk
from market_analyzer import MarketAnalyzer, MarketAlert

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

bot = TradingBot()
strategy = TradingStrategy()

# Global variables for dashboard data
dashboard_data = {
    'active_trades': {},
    'account_summary': {},
    'system_status': 'Disconnected',
    'last_update': None,
    'trade_history': [],
    'pnl_data': {
        'daily': [],
        'weekly': [],
        'monthly': []
    }
}

# Initialize risk manager and market analyzer
risk_manager = RiskManager()
market_analyzer = MarketAnalyzer()

# Mock user database (replace with proper database in production)
class User(UserMixin):
    def __init__(self, id):
        self.id = id
        self.name = users[id]['name']

users = {
    'admin': {
        'password': generate_password_hash('admin'),
        'name': 'Admin User'
    }
}

@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id)
    return None

def update_dashboard_data():
    """Update dashboard data periodically"""
    while True:
        try:
            # Update active trades
            dashboard_data['active_trades'] = strategy.get_active_trades()
            
            # Update system status
            dashboard_data['system_status'] = 'Connected' if bot.connected else 'Disconnected'
            
            # Update timestamp
            dashboard_data['last_update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Update trade history (mock data for now)
            if len(dashboard_data['trade_history']) == 0:
                dashboard_data['trade_history'] = generate_mock_trade_history()
            
            # Update P&L data (mock data for now)
            dashboard_data['pnl_data'] = generate_mock_pnl_data()
            
            time.sleep(5)  # Update every 5 seconds
            
        except Exception as e:
            logger.error(f"Error updating dashboard data: {e}")
            time.sleep(5)

def generate_mock_trade_history():
    """Generate mock trade history data"""
    history = []
    for i in range(20):
        history.append({
            'id': i,
            'symbol': 'AAPL',
            'type': 'Option' if i % 2 == 0 else 'Stock',
            'direction': 'BUY' if i % 3 == 0 else 'SELL',
            'entry_price': 150.0 + i,
            'exit_price': 155.0 + i,
            'quantity': 100,
            'pnl': (155.0 + i - 150.0 - i) * 100,
            'entry_time': (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d %H:%M:%S"),
            'exit_time': (datetime.now() - timedelta(days=i-1)).strftime("%Y-%m-%d %H:%M:%S")
        })
    return history

def generate_mock_pnl_data():
    """Generate mock P&L data"""
    return {
        'daily': [{'date': (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"), 'pnl': 100 * i} for i in range(7)],
        'weekly': [{'week': f'Week {i}', 'pnl': 500 * i} for i in range(4)],
        'monthly': [{'month': f'Month {i}', 'pnl': 2000 * i} for i in range(6)]
    }

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in users and check_password_hash(users[username]['password'], password):
            user = User(username)
            login_user(user)
            return redirect(url_for('index'))
            
        return render_template('login.html', error='Invalid credentials')
        
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    risk_report = risk_manager.get_risk_report()
    return render_template('index.html', 
                         risk_report=risk_report,
                         current_user=current_user)

@app.route('/api/status')
@login_required
def get_status():
    """Get current system status"""
    return jsonify(dashboard_data)

@app.route('/api/trades')
@login_required
def get_trades():
    """Get active trades"""
    return jsonify({
        'active_trades': dashboard_data['active_trades'],
        'last_update': dashboard_data['last_update']
    })

@app.route('/api/account')
@login_required
def get_account():
    """Get account summary"""
    return jsonify({
        'account_summary': dashboard_data['account_summary'],
        'last_update': dashboard_data['last_update']
    })

@app.route('/api/history')
@login_required
def get_history():
    """Get trade history"""
    return jsonify({
        'trade_history': dashboard_data['trade_history'],
        'last_update': dashboard_data['last_update']
    })

@app.route('/api/pnl')
@login_required
def get_pnl():
    """Get P&L data"""
    return jsonify(dashboard_data['pnl_data'])

@app.route('/api/close_trade', methods=['POST'])
@login_required
def close_trade():
    """Close a trade"""
    try:
        data = request.json
        symbol = data.get('symbol')
        if symbol in dashboard_data['active_trades']:
            # Add to trade history
            trade = dashboard_data['active_trades'][symbol]
            dashboard_data['trade_history'].append({
                'id': len(dashboard_data['trade_history']),
                'symbol': symbol,
                'type': 'Option' if trade.is_option else 'Stock',
                'direction': trade.direction,
                'entry_price': trade.entry_price,
                'exit_price': data.get('exit_price', trade.entry_price),
                'quantity': trade.quantity,
                'pnl': (data.get('exit_price', trade.entry_price) - trade.entry_price) * trade.quantity,
                'entry_time': dashboard_data['last_update'],
                'exit_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            # Remove from active trades
            del dashboard_data['active_trades'][symbol]
            
            return jsonify({'status': 'success'})
        return jsonify({'status': 'error', 'message': 'Trade not found'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/positions', methods=['GET', 'POST'])
@login_required
def positions():
    if request.method == 'POST':
        data = request.json
        position = PositionRisk(
            symbol=data['symbol'],
            position_size=float(data['position_size']),
            entry_price=float(data['entry_price']),
            current_price=float(data['current_price']),
            stop_loss=float(data['stop_loss']),
            take_profit=float(data['take_profit']),
            quantity=int(data['quantity']),
            is_option=data.get('is_option', False),
            delta=float(data.get('delta', 1.0)),
            vega=float(data.get('vega', 0.0)),
            theta=float(data.get('theta', 0.0))
        )
        
        if risk_manager.check_position_risk(position):
            risk_manager.add_position(position)
            # Update market analyzer with new position data
            market_analyzer.update_market_data(
                symbol=position.symbol,
                price=position.current_price,
                volume=position.quantity,
                timestamp=datetime.now()
            )
            return jsonify({'status': 'success'})
        return jsonify({'status': 'error', 'message': 'Position risk exceeds limits'})
        
    return jsonify(risk_manager.get_risk_report())

@app.route('/api/market-analysis/<symbol>')
@login_required
def market_analysis(symbol):
    analysis = market_analyzer.get_market_analysis(symbol)
    return jsonify(analysis)

@app.route('/api/alerts')
@login_required
def alerts():
    symbol = request.args.get('symbol')
    priority = request.args.get('priority')
    alerts = market_analyzer.get_alerts(symbol=symbol, priority=priority)
    return jsonify([{
        'symbol': alert.symbol,
        'type': alert.alert_type,
        'message': alert.message,
        'timestamp': alert.timestamp.isoformat(),
        'priority': alert.priority,
        'data': alert.data
    } for alert in alerts])

def start_dashboard():
    """Start the dashboard server"""
    # Start the data update thread
    update_thread = threading.Thread(target=update_dashboard_data)
    update_thread.daemon = True
    update_thread.start()
    
    # Start the Flask server
    app.run(host='0.0.0.0', port=5001, debug=True)

if __name__ == '__main__':
    start_dashboard() 