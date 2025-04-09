from dataclasses import dataclass
from typing import Dict, List
import numpy as np
from loguru import logger
from datetime import datetime, timedelta

@dataclass
class PositionRisk:
    symbol: str
    position_size: float
    entry_price: float
    current_price: float
    stop_loss: float
    take_profit: float
    quantity: int
    is_option: bool
    delta: float = 1.0  # For options, represents the delta
    vega: float = 0.0   # For options, represents the vega
    theta: float = 0.0  # For options, represents the theta

class RiskManager:
    def __init__(self, max_portfolio_risk: float = 0.02, max_position_risk: float = 0.01):
        self.max_portfolio_risk = max_portfolio_risk  # Maximum risk as a percentage of portfolio
        self.max_position_risk = max_position_risk    # Maximum risk per position
        self.positions: Dict[str, PositionRisk] = {}
        self.portfolio_value = 0.0
        self.risk_metrics = {
            'portfolio_beta': 0.0,
            'portfolio_volatility': 0.0,
            'value_at_risk': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0
        }
        
    def add_position(self, position: PositionRisk):
        """Add a new position to risk management"""
        self.positions[position.symbol] = position
        self._update_risk_metrics()
        
    def remove_position(self, symbol: str):
        """Remove a position from risk management"""
        if symbol in self.positions:
            del self.positions[symbol]
            self._update_risk_metrics()
            
    def update_position(self, symbol: str, current_price: float):
        """Update position with current market price"""
        if symbol in self.positions:
            self.positions[symbol].current_price = current_price
            self._update_risk_metrics()
            
    def _update_risk_metrics(self):
        """Update all risk metrics"""
        self._calculate_portfolio_beta()
        self._calculate_portfolio_volatility()
        self._calculate_value_at_risk()
        self._calculate_max_drawdown()
        self._calculate_sharpe_ratio()
        
    def _calculate_portfolio_beta(self):
        """Calculate portfolio beta"""
        if not self.positions:
            self.risk_metrics['portfolio_beta'] = 0.0
            return
            
        total_beta = sum(
            (position.position_size / self.portfolio_value) * position.delta
            for position in self.positions.values()
        )
        self.risk_metrics['portfolio_beta'] = total_beta
        
    def _calculate_portfolio_volatility(self):
        """Calculate portfolio volatility"""
        if not self.positions:
            self.risk_metrics['portfolio_volatility'] = 0.0
            return
            
        # This is a simplified calculation. In production, use historical returns
        position_volatilities = [
            abs(position.current_price - position.entry_price) / position.entry_price
            for position in self.positions.values()
        ]
        self.risk_metrics['portfolio_volatility'] = np.std(position_volatilities)
        
    def _calculate_value_at_risk(self, confidence_level: float = 0.95):
        """Calculate Value at Risk (VaR)"""
        if not self.positions:
            self.risk_metrics['value_at_risk'] = 0.0
            return
            
        # Simplified VaR calculation
        portfolio_returns = [
            (position.current_price - position.entry_price) / position.entry_price
            for position in self.positions.values()
        ]
        var = np.percentile(portfolio_returns, (1 - confidence_level) * 100)
        self.risk_metrics['value_at_risk'] = abs(var * self.portfolio_value)
        
    def _calculate_max_drawdown(self):
        """Calculate maximum drawdown"""
        if not self.positions:
            self.risk_metrics['max_drawdown'] = 0.0
            return
            
        # Simplified drawdown calculation
        drawdowns = [
            (position.current_price - position.entry_price) / position.entry_price
            for position in self.positions.values()
        ]
        self.risk_metrics['max_drawdown'] = min(drawdowns) if drawdowns else 0.0
        
    def _calculate_sharpe_ratio(self, risk_free_rate: float = 0.02):
        """Calculate Sharpe ratio"""
        if not self.positions or self.risk_metrics['portfolio_volatility'] == 0:
            self.risk_metrics['sharpe_ratio'] = 0.0
            return
            
        portfolio_return = sum(
            (position.current_price - position.entry_price) / position.entry_price
            for position in self.positions.values()
        ) / len(self.positions)
        
        self.risk_metrics['sharpe_ratio'] = (
            (portfolio_return - risk_free_rate) / self.risk_metrics['portfolio_volatility']
        )
        
    def check_position_risk(self, position: PositionRisk) -> bool:
        """Check if a new position meets risk requirements"""
        # Calculate position risk
        position_risk = abs(position.entry_price - position.stop_loss) * position.quantity
        
        # Check if position risk is within limits
        if position_risk > self.max_position_risk * self.portfolio_value:
            logger.warning(f"Position risk {position_risk} exceeds maximum allowed")
            return False
            
        # Check if adding this position would exceed portfolio risk
        total_risk = sum(
            abs(pos.entry_price - pos.stop_loss) * pos.quantity
            for pos in self.positions.values()
        ) + position_risk
        
        if total_risk > self.max_portfolio_risk * self.portfolio_value:
            logger.warning(f"Portfolio risk {total_risk} would exceed maximum allowed")
            return False
            
        return True
        
    def get_risk_report(self) -> dict:
        """Generate a comprehensive risk report"""
        return {
            'portfolio_value': self.portfolio_value,
            'number_of_positions': len(self.positions),
            'total_position_risk': sum(
                abs(pos.entry_price - pos.stop_loss) * pos.quantity
                for pos in self.positions.values()
            ),
            'risk_metrics': self.risk_metrics,
            'positions': {
                symbol: {
                    'position_size': pos.position_size,
                    'risk_amount': abs(pos.entry_price - pos.stop_loss) * pos.quantity,
                    'risk_percentage': abs(pos.entry_price - pos.stop_loss) / pos.entry_price
                }
                for symbol, pos in self.positions.items()
            }
        } 