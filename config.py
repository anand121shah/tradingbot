from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Create necessary directories
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Interactive Brokers configuration
IB_PORT = int(os.getenv("IB_PORT", 7497))  # 7497 for paper trading, 7496 for live trading
IB_HOST = os.getenv("IB_HOST", "127.0.0.1")
IB_CLIENT_ID = int(os.getenv("IB_CLIENT_ID", 1))

# Trading parameters
MAX_POSITION_SIZE = float(os.getenv("MAX_POSITION_SIZE", 10000))  # Maximum position size in USD
RISK_PER_TRADE = float(os.getenv("RISK_PER_TRADE", 0.01))  # Risk per trade as a percentage of account
MIN_RISK_REWARD_RATIO = float(os.getenv("MIN_RISK_REWARD_RATIO", 2.0))  # Minimum risk:reward ratio

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "trading_bot.log" 