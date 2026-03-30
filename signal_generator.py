import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta
from indicators import TechnicalIndicators

class SignalGenerator:
    """Class to generate trading signals for options based on technical analysis"""
    
    def __init__(self, risk_level: str = "medium"):
        self.logger = logging.getLogger(__name__)
        self.risk_level = risk_level
        self.indicators = TechnicalIndicators()
        
        # Risk thresholds based on risk level
        self.risk_thresholds = self._set_risk_thresholds(risk_level)
    
    def _set_risk_thresholds(self, risk_level: str) -> Dict:
        """Set risk thresholds based on risk level"""
        thresholds = {
            "low": {
                "rsi_overbought": 70,
                "rsi_oversold": 30,
                "min_confidence": 0.7,
                "max_positions": 3
            },
            "medium": {
                "rsi_overbought": 75,
                "rsi_oversold": 25,
                "min_confidence": 0.6,
                "max_positions": 5
            },
            "high": {
                "rsi_overbought": 80,
                "rsi_oversold": 20,
                "min_confidence": 0.5,
                "max_positions": 8
            }
        }
        return thresholds.get(risk_level, thresholds["medium"])
    
    def generate_signals(self, data: pd.DataFrame, symbol: str) -> Dict:
        """Generate comprehensive trading signals for a stock"""
        try:
            # Calculate all indicators
            indicators_data = self.indicators.calculate_all_indicators(data)
            
            # Get the latest data point
            latest = indicators_data.iloc[-1]
            previous = indicators_data.iloc[-2] if len(indicators_data) > 1 else latest
            
            # Generate individual signals
            signals = {
                'symbol': symbol,
                'timestamp': datetime.now(),
                'current_price': latest['Close'],
                'signals': []
            }
            
            # RSI Signal
            rsi_signal = self._analyze_rsi(latest['rsi'], previous['rsi'])
            if rsi_signal:
                signals['signals'].append(rsi_signal)
            
            # MACD Signal
            macd_signal = self._analyze_macd(latest, previous)
            if macd_signal:
                signals['signals'].append(macd_signal)
            
            # Bollinger Bands Signal
            bb_signal = self._analyze_bollinger_bands(latest)
            if bb_signal:
                signals['signals'].append(bb_signal)
            
            # Moving Average Signal
            ma_signal = self._analyze_moving_averages(latest)
            if ma_signal:
                signals['signals'].append(ma_signal)
            
            # Stochastic Signal
            stoch_signal = self._analyze_stochastic(latest)
            if stoch_signal:
                signals['signals'].append(stoch_signal)
            
            # Volume Signal
            volume_signal = self._analyze_volume(latest, indicators_data)
            if volume_signal:
                signals['signals'].append(volume_signal)
            
            # Overall signal
            overall_signal = self._generate_overall_signal(signals['signals'])
            signals.update(overall_signal)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Error generating signals for {symbol}: {e}")
            return {'symbol': symbol, 'error': str(e)}
    
    def _analyze_rsi(self, current_rsi: float, previous_rsi: float) -> Optional[Dict]:
        """Analyze RSI for signal generation"""
        if pd.isna(current_rsi) or pd.isna(previous_rsi):
            return None
        
        signal = {
            'indicator': 'RSI',
            'value': current_rsi,
            'confidence': 0
        }
        
        if current_rsi < self.risk_thresholds['rsi_oversold'] and previous_rsi >= self.risk_thresholds['rsi_oversold']:
            signal['action'] = 'CALL'
            signal['reason'] = f'RSI oversold at {current_rsi:.2f}, potential bounce'
            signal['confidence'] = min(0.8, (self.risk_thresholds['rsi_oversold'] - current_rsi) / 10)
        elif current_rsi > self.risk_thresholds['rsi_overbought'] and previous_rsi <= self.risk_thresholds['rsi_overbought']:
            signal['action'] = 'PUT'
            signal['reason'] = f'RSI overbought at {current_rsi:.2f}, potential correction'
            signal['confidence'] = min(0.8, (current_rsi - self.risk_thresholds['rsi_overbought']) / 10)
        else:
            return None
        
        return signal
    
    def _analyze_macd(self, current: pd.Series, previous: pd.Series) -> Optional[Dict]:
        """Analyze MACD for signal generation"""
        if pd.isna(current['macd']) or pd.isna(current['macd_signal']):
            return None
        
        signal = {
            'indicator': 'MACD',
            'confidence': 0
        }
        
        # MACD crossover
        if (current['macd'] > current['macd_signal'] and 
            previous['macd'] <= previous['macd_signal']):
            signal['action'] = 'CALL'
            signal['reason'] = 'MACD bullish crossover'
            signal['confidence'] = 0.7
        elif (current['macd'] < current['macd_signal'] and 
              previous['macd'] >= previous['macd_signal']):
            signal['action'] = 'PUT'
            signal['reason'] = 'MACD bearish crossover'
            signal['confidence'] = 0.7
        else:
            return None
        
        signal['value'] = current['macd'] - current['macd_signal']
        return signal
    
    def _analyze_bollinger_bands(self, current: pd.Series) -> Optional[Dict]:
        """Analyze Bollinger Bands for signal generation"""
        if pd.isna(current['bb_upper']) or pd.isna(current['bb_lower']):
            return None
        
        signal = {
            'indicator': 'Bollinger Bands',
            'confidence': 0
        }
        
        price = current['Close']
        upper = current['bb_upper']
        lower = current['bb_lower']
        
        if price <= lower:
            signal['action'] = 'CALL'
            signal['reason'] = f'Price at lower Bollinger Band ({price:.2f} <= {lower:.2f})'
            signal['confidence'] = 0.6
        elif price >= upper:
            signal['action'] = 'PUT'
            signal['reason'] = f'Price at upper Bollinger Band ({price:.2f} >= {upper:.2f})'
            signal['confidence'] = 0.6
        else:
            return None
        
        signal['value'] = (price - lower) / (upper - lower)
        return signal
    
    def _analyze_moving_averages(self, current: pd.Series) -> Optional[Dict]:
        """Analyze moving averages for signal generation"""
        if pd.isna(current['ma_20']) or pd.isna(current['ma_50']):
            return None
        
        signal = {
            'indicator': 'Moving Averages',
            'confidence': 0
        }
        
        price = current['Close']
        ma_20 = current['ma_20']
        ma_50 = current['ma_50']
        
        # Price above/below moving averages
        if price > ma_20 > ma_50:
            signal['action'] = 'CALL'
            signal['reason'] = f'Price above MA20 and MA50 (uptrend)'
            signal['confidence'] = 0.5
        elif price < ma_20 < ma_50:
            signal['action'] = 'PUT'
            signal['reason'] = f'Price below MA20 and MA50 (downtrend)'
            signal['confidence'] = 0.5
        else:
            return None
        
        signal['value'] = price - ma_20
        return signal
    
    def _analyze_stochastic(self, current: pd.Series) -> Optional[Dict]:
        """Analyze Stochastic oscillator for signal generation"""
        if pd.isna(current['stoch_k']) or pd.isna(current['stoch_d']):
            return None
        
        signal = {
            'indicator': 'Stochastic',
            'confidence': 0
        }
        
        k = current['stoch_k']
        d = current['stoch_d']
        
        if k < 20 and d < 20:
            signal['action'] = 'CALL'
            signal['reason'] = f'Stochastic oversold (K={k:.2f}, D={d:.2f})'
            signal['confidence'] = 0.4
        elif k > 80 and d > 80:
            signal['action'] = 'PUT'
            signal['reason'] = f'Stochastic overbought (K={k:.2f}, D={d:.2f})'
            signal['confidence'] = 0.4
        else:
            return None
        
        signal['value'] = k
        return signal
    
    def _analyze_volume(self, current: pd.Series, data: pd.DataFrame) -> Optional[Dict]:
        """Analyze volume for signal confirmation"""
        if 'Volume' not in current or pd.isna(current['Volume']):
            return None
        
        current_volume = current['Volume']
        avg_volume = data['Volume'].rolling(20).mean().iloc[-1]
        
        if current_volume > avg_volume * 1.5:
            return {
                'indicator': 'Volume',
                'action': 'CONFIRM',
                'reason': f'High volume ({current_volume:,.0f} vs avg {avg_volume:,.0f})',
                'confidence': 0.3,
                'value': current_volume / avg_volume
            }
        
        return None
    
    def _generate_overall_signal(self, signals: List[Dict]) -> Dict:
        """Generate overall trading signal from individual signals"""
        if not signals:
            return {'overall_action': 'HOLD', 'confidence': 0, 'signal_count': 0}
        
        call_signals = [s for s in signals if s['action'] == 'CALL']
        put_signals = [s for s in signals if s['action'] == 'PUT']
        
        overall = {
            'signal_count': len(signals),
            'call_signals': len(call_signals),
            'put_signals': len(put_signals)
        }
        
        # Determine overall action
        if len(call_signals) > len(put_signals):
            overall['overall_action'] = 'CALL'
            overall['confidence'] = sum(s['confidence'] for s in call_signals) / len(call_signals)
        elif len(put_signals) > len(call_signals):
            overall['overall_action'] = 'PUT'
            overall['confidence'] = sum(s['confidence'] for s in put_signals) / len(put_signals)
        else:
            overall['overall_action'] = 'HOLD'
            overall['confidence'] = 0
        
        # Adjust confidence based on signal count
        if len(signals) >= 3:
            overall['confidence'] *= 1.2
        elif len(signals) == 1:
            overall['confidence'] *= 0.8
        
        overall['confidence'] = min(overall['confidence'], 1.0)
        
        return overall
    
    def scan_multiple_stocks(self, stock_data: Dict[str, pd.DataFrame]) -> List[Dict]:
        """Scan multiple stocks and generate signals for each"""
        all_signals = []
        
        for symbol, data in stock_data.items():
            if not data.empty:
                signal = self.generate_signals(data, symbol)
                if 'error' not in signal and signal.get('confidence', 0) >= self.risk_thresholds['min_confidence']:
                    all_signals.append(signal)
        
        # Sort by confidence
        all_signals.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        # Limit to max positions
        max_positions = self.risk_thresholds['max_positions']
        return all_signals[:max_positions]
    
    def get_options_recommendation(self, signal: Dict) -> Dict:
        """Get options trading recommendation based on signal"""
        if signal.get('overall_action') == 'HOLD':
            return {'recommendation': 'NO TRADE', 'reason': 'No clear signal'}
        
        current_price = signal.get('current_price', 0)
        confidence = signal.get('confidence', 0)
        
        recommendation = {
            'action': signal['overall_action'],
            'confidence': confidence,
            'entry_price': current_price,
            'suggested_expiry': self._get_suggested_expiry(),
            'strike_prices': self._get_strike_prices(current_price, signal['overall_action']),
            'stop_loss': self._calculate_stop_loss(current_price, signal['overall_action']),
            'target_price': self._calculate_target_price(current_price, signal['overall_action']),
            'position_size': self._calculate_position_size(confidence)
        }
        
        return recommendation
    
    def _get_suggested_expiry(self) -> str:
        """Get suggested options expiry date"""
        today = datetime.now()
        # Suggest weekly expiry (assuming Thursday expiry for Indian markets)
        days_until_thursday = (3 - today.weekday()) % 7
        if days_until_thursday == 0:
            days_until_thursday = 7
        expiry_date = today + timedelta(days=days_until_thursday)
        return expiry_date.strftime('%Y-%m-%d')
    
    def _get_strike_prices(self, current_price: float, action: str) -> List[str]:
        """Get suggested strike prices for options"""
        strike_interval = 50 if current_price > 1000 else 25
        strikes = []
        
        if action == 'CALL':
            # OTM call strikes
            for i in range(1, 4):
                strike = int((current_price // strike_interval + i) * strike_interval)
                strikes.append(str(strike))
        else:  # PUT
            # OTM put strikes
            for i in range(1, 4):
                strike = int((current_price // strike_interval - i) * strike_interval)
                strikes.append(str(strike))
        
        return strikes
    
    def _calculate_stop_loss(self, current_price: float, action: str) -> float:
        """Calculate stop loss level"""
        if action == 'CALL':
            return current_price * 0.95  # 5% below entry
        else:
            return current_price * 1.05  # 5% above entry
    
    def _calculate_target_price(self, current_price: float, action: str) -> float:
        """Calculate target price"""
        if action == 'CALL':
            return current_price * 1.10  # 10% above entry
        else:
            return current_price * 0.90  # 10% below entry
    
    def _calculate_position_size(self, confidence: float) -> str:
        """Calculate recommended position size"""
        if confidence > 0.8:
            return "LARGE"
        elif confidence > 0.6:
            return "MEDIUM"
        else:
            return "SMALL"
