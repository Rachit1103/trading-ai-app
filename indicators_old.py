import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

class TechnicalIndicators:
    """Class to calculate various technical indicators for stock analysis"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        macd, macd_signal, macd_hist = talib.MACD(prices.values, fastperiod=fast, slowperiod=slow, signalperiod=signal)
        return {
            'macd': pd.Series(macd, index=prices.index),
            'signal': pd.Series(macd_signal, index=prices.index),
            'histogram': pd.Series(macd_hist, index=prices.index)
        }
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: int = 2) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands"""
        upper, middle, lower = talib.BBANDS(prices.values, timeperiod=period, nbdevup=std_dev, nbdevdn=std_dev)
        return {
            'upper': pd.Series(upper, index=prices.index),
            'middle': pd.Series(middle, index=prices.index),
            'lower': pd.Series(lower, index=prices.index)
        }
    
    def calculate_moving_averages(self, prices: pd.Series, periods: List[int] = [5, 10, 20, 50, 200]) -> Dict[str, pd.Series]:
        """Calculate Simple Moving Averages"""
        mas = {}
        for period in periods:
            mas[f'ma_{period}'] = talib.SMA(prices.values, timeperiod=period)
            mas[f'ma_{period}'] = pd.Series(mas[f'ma_{period}'], index=prices.index)
        return mas
    
    def calculate_ema(self, prices: pd.Series, period: int = 20) -> pd.Series:
        """Calculate Exponential Moving Average"""
        ema = talib.EMA(prices.values, timeperiod=period)
        return pd.Series(ema, index=prices.index)
    
    def calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                           k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
        """Calculate Stochastic Oscillator"""
        slowk, slowd = talib.STOCH(high.values, low.values, close.values, 
                                  fastk_period=k_period, slowk_period=d_period, slowd_period=d_period)
        return {
            'k': pd.Series(slowk, index=close.index),
            'd': pd.Series(slowd, index=close.index)
        }
    
    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        atr = talib.ATR(high.values, low.values, close.values, timeperiod=period)
        return pd.Series(atr, index=close.index)
    
    def calculate_obv(self, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Calculate On-Balance Volume"""
        obv = talib.OBV(close.values, volume.values)
        return pd.Series(obv, index=close.index)
    
    def calculate_williams_r(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Williams %R"""
        williams_r = talib.WILLR(high.values, low.values, close.values, timeperiod=period)
        return pd.Series(williams_r, index=close.index)
    
    def calculate_cci(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
        """Calculate Commodity Channel Index"""
        cci = talib.CCI(high.values, low.values, close.values, timeperiod=period)
        return pd.Series(cci, index=close.index)
    
    def calculate_all_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators and return as DataFrame"""
        indicators = data.copy()
        
        # Basic indicators
        indicators['rsi'] = self.calculate_rsi(data['Close'])
        indicators['ema_20'] = self.calculate_ema(data['Close'], 20)
        
        # MACD
        macd_data = self.calculate_macd(data['Close'])
        indicators['macd'] = macd_data['macd']
        indicators['macd_signal'] = macd_data['signal']
        indicators['macd_histogram'] = macd_data['histogram']
        
        # Bollinger Bands
        bb_data = self.calculate_bollinger_bands(data['Close'])
        indicators['bb_upper'] = bb_data['upper']
        indicators['bb_middle'] = bb_data['middle']
        indicators['bb_lower'] = bb_data['lower']
        
        # Moving Averages
        ma_data = self.calculate_moving_averages(data['Close'])
        for key, value in ma_data.items():
            indicators[key] = value
        
        # Stochastic
        stoch_data = self.calculate_stochastic(data['High'], data['Low'], data['Close'])
        indicators['stoch_k'] = stoch_data['k']
        indicators['stoch_d'] = stoch_data['d']
        
        # ATR
        indicators['atr'] = self.calculate_atr(data['High'], data['Low'], data['Close'])
        
        # OBV
        if 'Volume' in data.columns:
            indicators['obv'] = self.calculate_obv(data['Close'], data['Volume'])
        
        # Williams %R
        indicators['williams_r'] = self.calculate_williams_r(data['High'], data['Low'], data['Close'])
        
        # CCI
        indicators['cci'] = self.calculate_cci(data['High'], data['Low'], data['Close'])
        
        return indicators
