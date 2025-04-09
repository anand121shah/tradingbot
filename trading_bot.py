from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
from loguru import logger
import threading
import time
from config import IB_PORT, IB_HOST, IB_CLIENT_ID, LOG_FILE, LOG_LEVEL
from datetime import datetime, timedelta

# Configure logging
logger.add(LOG_FILE, rotation="1 day", level=LOG_LEVEL)

class TradingBot(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.next_order_id = None
        self.connected = False
        self.account_summary = {}
        
    def connect_to_ib(self):
        """Connect to Interactive Brokers TWS or IB Gateway"""
        try:
            self.connect(IB_HOST, IB_PORT, IB_CLIENT_ID)
            logger.info(f"Connecting to IB on {IB_HOST}:{IB_PORT} with client ID {IB_CLIENT_ID}")
            
            # Start the connection in a separate thread
            thread = threading.Thread(target=self.run)
            thread.start()
            
            # Wait for connection
            time.sleep(1)
            if self.connected:
                logger.info("Successfully connected to Interactive Brokers")
                return True
            else:
                logger.error("Failed to connect to Interactive Brokers")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to Interactive Brokers: {e}")
            return False

    def nextValidId(self, orderId: int):
        """Callback when the next valid order ID is received"""
        super().nextValidId(orderId)
        self.next_order_id = orderId
        logger.info(f"Next valid order ID: {orderId}")

    def error(self, reqId, errorCode, errorString):
        """Callback for error messages"""
        logger.error(f"Error {errorCode}: {errorString}")

    def connectionClosed(self):
        """Callback when the connection is closed"""
        logger.info("Connection closed")
        self.connected = False

    def create_option_contract(self, 
                             symbol: str, 
                             strike: float, 
                             right: str,  # 'C' for call, 'P' for put
                             expiry: str,  # Format: YYYYMMDD
                             exchange: str = "SMART",
                             currency: str = "USD") -> Contract:
        """Create an options contract object"""
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "OPT"
        contract.exchange = exchange
        contract.currency = currency
        contract.lastTradeDateOrContractMonth = expiry
        contract.strike = strike
        contract.right = right
        contract.multiplier = "100"  # Standard options multiplier
        return contract

    def create_stock_contract(self, symbol: str, exchange: str = "SMART", currency: str = "USD") -> Contract:
        """Create a stock contract object"""
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = exchange
        contract.currency = currency
        return contract

    def create_order(self, action: str, quantity: int, order_type: str, price: float = None) -> Order:
        """Create an order object"""
        order = Order()
        order.action = action
        order.totalQuantity = quantity
        order.orderType = order_type
        if price:
            order.lmtPrice = price
        return order

    def place_order(self, contract: Contract, order: Order):
        """Place an order with Interactive Brokers"""
        if not self.connected or not self.next_order_id:
            logger.error("Not connected to IB or no valid order ID")
            return False
            
        try:
            self.placeOrder(self.next_order_id, contract, order)
            logger.info(f"Placed order: {order.action} {order.totalQuantity} {contract.symbol} {contract.secType}")
            self.next_order_id += 1
            return True
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return False

    def disconnect(self):
        """Disconnect from Interactive Brokers"""
        if self.connected:
            super().disconnect()
            logger.info("Disconnected from Interactive Brokers") 