from trading_bot import TradingBot
from strategy import TradingStrategy, TradeSignal
from loguru import logger
import time
from datetime import datetime, timedelta

def get_next_friday():
    """Get the next Friday's date in YYYYMMDD format"""
    today = datetime.now()
    days_ahead = 4 - today.weekday()  # 4 is Friday
    if days_ahead <= 0:  # If today is Friday or later in the week
        days_ahead += 7
    next_friday = today + timedelta(days=days_ahead)
    return next_friday.strftime("%Y%m%d")

def main():
    # Initialize the trading bot and strategy
    bot = TradingBot()
    strategy = TradingStrategy()
    
    # Connect to Interactive Brokers
    if not bot.connect_to_ib():
        logger.error("Failed to connect to Interactive Brokers. Exiting...")
        return
        
    try:
        # Example 1: Stock trade
        stock_signal = strategy.generate_signal(
            symbol="AAPL",
            entry_price=150.0,
            stop_loss=145.0,
            take_profit=160.0,
            quantity=100,
            direction="BUY"
        )
        
        if stock_signal:
            # Create stock contract
            contract = bot.create_stock_contract(symbol=stock_signal.symbol)
            
            # Create entry order
            entry_order = bot.create_order(
                action=stock_signal.direction,
                quantity=stock_signal.quantity,
                order_type="LMT",
                price=stock_signal.entry_price
            )
            
            # Place entry order
            if bot.place_order(contract, entry_order):
                strategy.add_active_trade(stock_signal)
                
            # Create stop loss order
            stop_order = bot.create_order(
                action="SELL" if stock_signal.direction == "BUY" else "BUY",
                quantity=stock_signal.quantity,
                order_type="STP",
                price=stock_signal.stop_loss
            )
            
            # Place stop loss order
            bot.place_order(contract, stop_order)
            
            # Create take profit order
            take_profit_order = bot.create_order(
                action="SELL" if stock_signal.direction == "BUY" else "BUY",
                quantity=stock_signal.quantity,
                order_type="LMT",
                price=stock_signal.take_profit
            )
            
            # Place take profit order
            bot.place_order(contract, take_profit_order)

        # Example 2: Options trade
        next_friday = get_next_friday()
        option_signal = strategy.generate_signal(
            symbol="AAPL",
            entry_price=2.50,  # Option premium
            stop_loss=1.50,
            take_profit=4.00,
            quantity=10,  # Number of contracts
            direction="BUY",
            is_option=True,
            strike=150.0,
            expiry=next_friday,
            option_type="C"  # Call option
        )
        
        if option_signal:
            # Create options contract
            contract = bot.create_option_contract(
                symbol=option_signal.symbol,
                strike=option_signal.strike,
                right=option_signal.option_type,
                expiry=option_signal.expiry
            )
            
            # Create entry order
            entry_order = bot.create_order(
                action=option_signal.direction,
                quantity=option_signal.quantity,
                order_type="LMT",
                price=option_signal.entry_price
            )
            
            # Place entry order
            if bot.place_order(contract, entry_order):
                strategy.add_active_trade(option_signal)
                
            # Create stop loss order
            stop_order = bot.create_order(
                action="SELL" if option_signal.direction == "BUY" else "BUY",
                quantity=option_signal.quantity,
                order_type="STP",
                price=option_signal.stop_loss
            )
            
            # Place stop loss order
            bot.place_order(contract, stop_order)
            
            # Create take profit order
            take_profit_order = bot.create_order(
                action="SELL" if option_signal.direction == "BUY" else "BUY",
                quantity=option_signal.quantity,
                order_type="LMT",
                price=option_signal.take_profit
            )
            
            # Place take profit order
            bot.place_order(contract, take_profit_order)
            
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
        
    finally:
        # Disconnect from Interactive Brokers
        bot.disconnect()

if __name__ == "__main__":
    main() 