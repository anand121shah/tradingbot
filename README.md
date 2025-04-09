# Interactive Brokers Trading Bot

A Python-based trading bot that connects to Interactive Brokers for automated trading of stocks, options, and futures.

## Features

- Connects to Interactive Brokers TWS or IB Gateway
- Supports stocks, options, and futures trading
- Implements risk management with position sizing and stop-loss orders
- Paper trading support
- Comprehensive logging
- Configurable trading parameters

## Prerequisites

1. Interactive Brokers TWS or IB Gateway installed and running
2. Python 3.7 or higher
3. Active Interactive Brokers account (paper trading or live)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd tradingbot
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your configuration:
```env
IB_PORT=7497  # 7497 for paper trading, 7496 for live trading
IB_HOST=127.0.0.1
IB_CLIENT_ID=1
MAX_POSITION_SIZE=10000
RISK_PER_TRADE=0.01
MIN_RISK_REWARD_RATIO=2.0
LOG_LEVEL=INFO
```

## Usage

1. Start Interactive Brokers TWS or IB Gateway
2. Log in to your account
3. Run the trading bot:
```bash
python main.py
```

## Project Structure

- `main.py`: Main script to run the trading bot
- `trading_bot.py`: Core trading bot implementation
- `strategy.py`: Trading strategy implementation
- `config.py`: Configuration settings
- `requirements.txt`: Python dependencies
- `data/`: Directory for storing data
- `logs/`: Directory for log files

## Customizing Your Strategy

To implement your own trading strategy:

1. Modify the `generate_signal` method in `strategy.py`
2. Update the trade parameters in `main.py`
3. Add any additional validation rules in the `TradeSignal` class

## Risk Management

The bot includes several risk management features:

- Maximum position size limit
- Risk per trade as a percentage of account
- Minimum risk:reward ratio requirement
- Automatic stop-loss and take-profit orders

## Logging

Logs are stored in the `logs/` directory with daily rotation. The log level can be configured in the `.env` file.

## Disclaimer

This trading bot is for educational purposes only. Use at your own risk. Always test thoroughly in paper trading before using with real money. 