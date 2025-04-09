from dataclasses import dataclass
from typing import Optional
from loguru import logger
from config import MAX_POSITION_SIZE, RISK_PER_TRADE, MIN_RISK_REWARD_RATIO
from datetime import datetime

@dataclass
class TradeSignal:
    symbol: str
    entry_price: float
    stop_loss: float
    take_profit: float
    quantity: int
    direction: str  # 'BUY' or 'SELL'
    # Options specific parameters
    is_option: bool = False
    strike: float = None
    expiry: str = None  # Format: YYYYMMDD
    option_type: str = None  # 'C' for call, 'P' for put
    
    def validate(self) -> bool:
        """Validate the trade signal"""
        try:
            # Calculate risk per share/contract
            risk_per_unit = abs(self.entry_price - self.stop_loss)
            
            # Calculate position size
            if self.is_option:
                # For options, multiply by 100 (standard multiplier)
                position_size = self.quantity * self.entry_price * 100
            else:
                position_size = self.quantity * self.entry_price
            
            # Calculate risk:reward ratio
            reward_per_unit = abs(self.take_profit - self.entry_price)
            risk_reward_ratio = reward_per_unit / risk_per_unit
            
            # Validate position size
            if position_size > MAX_POSITION_SIZE:
                logger.warning(f"Position size {position_size} exceeds maximum allowed {MAX_POSITION_SIZE}")
                return False
                
            # Validate risk:reward ratio
            if risk_reward_ratio < MIN_RISK_REWARD_RATIO:
                logger.warning(f"Risk:reward ratio {risk_reward_ratio} below minimum {MIN_RISK_REWARD_RATIO}")
                return False
                
            # Validate options parameters if it's an options trade
            if self.is_option:
                if not all([self.strike, self.expiry, self.option_type]):
                    logger.warning("Missing required options parameters")
                    return False
                    
                # Validate expiry format (YYYYMMDD)
                try:
                    datetime.strptime(self.expiry, "%Y%m%d")
                except ValueError:
                    logger.warning(f"Invalid expiry date format: {self.expiry}")
                    return False
                    
                # Validate option type
                if self.option_type not in ['C', 'P']:
                    logger.warning(f"Invalid option type: {self.option_type}")
                    return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating trade signal: {e}")
            return False

class TradingStrategy:
    def __init__(self):
        self.active_trades = {}
        
    def generate_signal(self, 
                       symbol: str,
                       entry_price: float,
                       stop_loss: float,
                       take_profit: float,
                       quantity: int,
                       direction: str,
                       is_option: bool = False,
                       strike: float = None,
                       expiry: str = None,
                       option_type: str = None) -> Optional[TradeSignal]:
        """Generate a trade signal based on the provided parameters"""
        signal = TradeSignal(
            symbol=symbol,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            quantity=quantity,
            direction=direction,
            is_option=is_option,
            strike=strike,
            expiry=expiry,
            option_type=option_type
        )
        
        if signal.validate():
            logger.info(f"Valid trade signal generated for {symbol}")
            return signal
        else:
            logger.warning(f"Invalid trade signal for {symbol}")
            return None
            
    def add_active_trade(self, signal: TradeSignal):
        """Add a trade to the active trades list"""
        self.active_trades[signal.symbol] = signal
        logger.info(f"Added active trade for {signal.symbol}")
        
    def remove_active_trade(self, symbol: str):
        """Remove a trade from the active trades list"""
        if symbol in self.active_trades:
            del self.active_trades[symbol]
            logger.info(f"Removed active trade for {symbol}")
            
    def get_active_trades(self):
        """Get all active trades"""
        return self.active_trades 