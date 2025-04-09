from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger

@dataclass
class MarketAlert:
    symbol: str
    alert_type: str
    message: str
    timestamp: datetime
    priority: str  # 'high', 'medium', 'low'
    data: dict

class MarketAnalyzer:
    def __init__(self):
        self.price_history: Dict[str, pd.DataFrame] = {}
        self.volume_history: Dict[str, pd.DataFrame] = {}
        self.alerts: List[MarketAlert] = []
        self.indicators = {
            'rsi': self._calculate_rsi,
            'macd': self._calculate_macd,
            'bollinger_bands': self._calculate_bollinger_bands,
            'volume_profile': self._calculate_volume_profile
        }
        
    def update_market_data(self, symbol: str, price: float, volume: int, timestamp: datetime):
        """Update market data for a symbol"""
        if symbol not in self.price_history:
            self.price_history[symbol] = pd.DataFrame(columns=['timestamp', 'price'])
            self.volume_history[symbol] = pd.DataFrame(columns=['timestamp', 'volume'])
            
        self.price_history[symbol] = self.price_history[symbol].append({
            'timestamp': timestamp,
            'price': price
        }, ignore_index=True)
        
        self.volume_history[symbol] = self.volume_history[symbol].append({
            'timestamp': timestamp,
            'volume': volume
        }, ignore_index=True)
        
        # Keep only last 1000 data points
        self.price_history[symbol] = self.price_history[symbol].tail(1000)
        self.volume_history[symbol] = self.volume_history[symbol].tail(1000)
        
        # Analyze new data
        self._analyze_market_data(symbol)
        
    def _analyze_market_data(self, symbol: str):
        """Analyze market data and generate alerts"""
        if len(self.price_history[symbol]) < 20:  # Need minimum data points
            return
            
        # Calculate technical indicators
        indicators = {}
        for name, func in self.indicators.items():
            indicators[name] = func(symbol)
            
        # Check for potential alerts
        self._check_rsi_alerts(symbol, indicators['rsi'])
        self._check_macd_alerts(symbol, indicators['macd'])
        self._check_volume_alerts(symbol, indicators['volume_profile'])
        self._check_bollinger_alerts(symbol, indicators['bollinger_bands'])
        
    def _calculate_rsi(self, symbol: str, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        prices = self.price_history[symbol]['price']
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
        
    def _calculate_macd(self, symbol: str) -> Dict[str, pd.Series]:
        """Calculate MACD indicator"""
        prices = self.price_history[symbol]['price']
        exp1 = prices.ewm(span=12, adjust=False).mean()
        exp2 = prices.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        return {'macd': macd, 'signal': signal}
        
    def _calculate_bollinger_bands(self, symbol: str, period: int = 20) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands"""
        prices = self.price_history[symbol]['price']
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = sma + (std * 2)
        lower_band = sma - (std * 2)
        return {'upper': upper_band, 'middle': sma, 'lower': lower_band}
        
    def _calculate_volume_profile(self, symbol: str) -> Dict[str, float]:
        """Calculate volume profile metrics"""
        volumes = self.volume_history[symbol]['volume']
        return {
            'average_volume': volumes.mean(),
            'volume_std': volumes.std(),
            'current_volume': volumes.iloc[-1]
        }
        
    def _check_rsi_alerts(self, symbol: str, rsi: pd.Series):
        """Check for RSI-based alerts"""
        current_rsi = rsi.iloc[-1]
        
        if current_rsi > 70:
            self.alerts.append(MarketAlert(
                symbol=symbol,
                alert_type='RSI Overbought',
                message=f'RSI ({current_rsi:.2f}) indicates overbought conditions',
                timestamp=datetime.now(),
                priority='medium',
                data={'rsi': current_rsi}
            ))
        elif current_rsi < 30:
            self.alerts.append(MarketAlert(
                symbol=symbol,
                alert_type='RSI Oversold',
                message=f'RSI ({current_rsi:.2f}) indicates oversold conditions',
                timestamp=datetime.now(),
                priority='medium',
                data={'rsi': current_rsi}
            ))
            
    def _check_macd_alerts(self, symbol: str, macd_data: Dict[str, pd.Series]):
        """Check for MACD-based alerts"""
        macd = macd_data['macd']
        signal = macd_data['signal']
        
        if macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-2] <= signal.iloc[-2]:
            self.alerts.append(MarketAlert(
                symbol=symbol,
                alert_type='MACD Bullish Crossover',
                message='MACD line crossed above signal line',
                timestamp=datetime.now(),
                priority='medium',
                data={'macd': macd.iloc[-1], 'signal': signal.iloc[-1]}
            ))
        elif macd.iloc[-1] < signal.iloc[-1] and macd.iloc[-2] >= signal.iloc[-2]:
            self.alerts.append(MarketAlert(
                symbol=symbol,
                alert_type='MACD Bearish Crossover',
                message='MACD line crossed below signal line',
                timestamp=datetime.now(),
                priority='medium',
                data={'macd': macd.iloc[-1], 'signal': signal.iloc[-1]}
            ))
            
    def _check_volume_alerts(self, symbol: str, volume_profile: Dict[str, float]):
        """Check for volume-based alerts"""
        current_volume = volume_profile['current_volume']
        avg_volume = volume_profile['average_volume']
        volume_std = volume_profile['volume_std']
        
        if current_volume > avg_volume + (2 * volume_std):
            self.alerts.append(MarketAlert(
                symbol=symbol,
                alert_type='High Volume',
                message=f'Unusually high volume detected: {current_volume:.0f} vs avg {avg_volume:.0f}',
                timestamp=datetime.now(),
                priority='high',
                data=volume_profile
            ))
            
    def _check_bollinger_alerts(self, symbol: str, bands: Dict[str, pd.Series]):
        """Check for Bollinger Bands alerts"""
        current_price = self.price_history[symbol]['price'].iloc[-1]
        
        if current_price > bands['upper'].iloc[-1]:
            self.alerts.append(MarketAlert(
                symbol=symbol,
                alert_type='Price Above Upper Band',
                message='Price moved above upper Bollinger Band',
                timestamp=datetime.now(),
                priority='medium',
                data={'price': current_price, 'upper_band': bands['upper'].iloc[-1]}
            ))
        elif current_price < bands['lower'].iloc[-1]:
            self.alerts.append(MarketAlert(
                symbol=symbol,
                alert_type='Price Below Lower Band',
                message='Price moved below lower Bollinger Band',
                timestamp=datetime.now(),
                priority='medium',
                data={'price': current_price, 'lower_band': bands['lower'].iloc[-1]}
            ))
            
    def get_alerts(self, symbol: Optional[str] = None, priority: Optional[str] = None) -> List[MarketAlert]:
        """Get filtered alerts"""
        filtered_alerts = self.alerts
        
        if symbol:
            filtered_alerts = [alert for alert in filtered_alerts if alert.symbol == symbol]
            
        if priority:
            filtered_alerts = [alert for alert in filtered_alerts if alert.priority == priority]
            
        return filtered_alerts
        
    def get_market_analysis(self, symbol: str) -> dict:
        """Get comprehensive market analysis for a symbol"""
        if symbol not in self.price_history:
            return {}
            
        indicators = {}
        for name, func in self.indicators.items():
            indicators[name] = func(symbol)
            
        return {
            'price_data': {
                'current_price': self.price_history[symbol]['price'].iloc[-1],
                'price_change': self.price_history[symbol]['price'].iloc[-1] - self.price_history[symbol]['price'].iloc[-2],
                'price_change_percent': (self.price_history[symbol]['price'].iloc[-1] - self.price_history[symbol]['price'].iloc[-2]) / self.price_history[symbol]['price'].iloc[-2] * 100
            },
            'volume_data': self._calculate_volume_profile(symbol),
            'technical_indicators': indicators,
            'recent_alerts': self.get_alerts(symbol=symbol)
        } 