import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta
from indicators import TechnicalIndicators
from signal_generator import SignalGenerator
from ml_predictor import AdvancedMLPredictor

class UltraHighAccuracySignalGenerator:
    """Ultra-high accuracy signal generator combining ML and technical analysis"""
    
    def __init__(self, risk_level: str = "medium"):
        self.logger = logging.getLogger(__name__)
        self.risk_level = risk_level
        self.technical_indicators = TechnicalIndicators()
        self.technical_generator = SignalGenerator(risk_level)
        self.ml_predictor = AdvancedMLPredictor()
        
        # Enhanced risk thresholds for maximum accuracy
        self.accuracy_thresholds = self._set_accuracy_thresholds(risk_level)
        
        # Performance tracking
        self.prediction_history = []
        self.accuracy_metrics = {
            'total_predictions': 0,
            'correct_predictions': 0,
            'high_confidence_predictions': 0,
            'high_confidence_correct': 0
        }
    
    def _set_accuracy_thresholds(self, risk_level: str) -> Dict:
        """Set ultra-strict thresholds for maximum accuracy"""
        thresholds = {
            "conservative": {
                "min_ml_confidence": 0.85,
                "min_technical_confidence": 0.75,
                "min_ensemble_confidence": 0.90,
                "min_signal_count": 4,
                "max_volatility": 0.05,
                "min_volume_confirmation": 1.5
            },
            "moderate": {
                "min_ml_confidence": 0.80,
                "min_technical_confidence": 0.70,
                "min_ensemble_confidence": 0.85,
                "min_signal_count": 3,
                "max_volatility": 0.08,
                "min_volume_confirmation": 1.3
            },
            "aggressive": {
                "min_ml_confidence": 0.75,
                "min_technical_confidence": 0.65,
                "min_ensemble_confidence": 0.80,
                "min_signal_count": 2,
                "max_volatility": 0.12,
                "min_volume_confirmation": 1.2
            }
        }
        
        risk_mapping = {
            "low": "conservative",
            "medium": "moderate", 
            "high": "aggressive"
        }
        
        return thresholds.get(risk_mapping.get(risk_level, "moderate"), thresholds["moderate"])
    
    def train_ml_models(self, historical_data: pd.DataFrame) -> Dict:
        """Train ML models on historical data"""
        self.logger.info("Training ML models for maximum accuracy...")
        
        try:
            # Train models
            training_results = self.ml_predictor.train_models(historical_data)
            
            self.logger.info(f"ML training completed. Best model accuracy: {max([r.get('test_accuracy', 0) for r in training_results.values()]):.4f}")
            
            return training_results
            
        except Exception as e:
            self.logger.error(f"ML training failed: {e}")
            return {}
    
    def generate_ultra_accuracy_signal(self, data: pd.DataFrame, symbol: str) -> Dict:
        """Generate ultra-high accuracy trading signal"""
        try:
            # Get technical analysis signals
            technical_signal = self.technical_generator.generate_signals(data, symbol)
            
            # Get ML predictions
            ml_prediction = self.ml_predictor.ensemble_predict(data)
            
            # Get individual model predictions for diversity
            individual_predictions = {}
            for model_name in ['rf', 'xgb', 'gb', 'nn']:
                pred = self.ml_predictor.predict(data, model_name)
                if 'error' not in pred:
                    individual_predictions[model_name] = pred
            
            # Calculate ensemble confidence
            ensemble_confidence = self._calculate_ensemble_confidence(
                technical_signal, ml_prediction, individual_predictions, data
            )
            
            # Apply ultra-strict filtering
            if not self._meets_accuracy_criteria(technical_signal, ml_prediction, ensemble_confidence, data):
                return self._create_hold_signal(symbol, "Failed accuracy criteria")
            
            # Generate final signal
            final_signal = self._create_final_signal(
                symbol, technical_signal, ml_prediction, individual_predictions, ensemble_confidence, data
            )
            
            # Track prediction
            self._track_prediction(final_signal)
            
            return final_signal
            
        except Exception as e:
            self.logger.error(f"Error generating ultra-accuracy signal for {symbol}: {e}")
            return self._create_hold_signal(symbol, f"Error: {str(e)}")
    
    def _calculate_ensemble_confidence(self, technical_signal: Dict, ml_prediction: Dict, 
                                      individual_predictions: Dict, data: pd.DataFrame) -> float:
        """Calculate weighted ensemble confidence"""
        confidences = []
        weights = []
        
        # Technical analysis confidence (weight: 0.3)
        tech_confidence = technical_signal.get('confidence', 0)
        if tech_confidence > self.accuracy_thresholds['min_technical_confidence']:
            confidences.append(tech_confidence)
            weights.append(0.3)
        
        # ML ensemble confidence (weight: 0.4)
        ml_confidence = ml_prediction.get('confidence', 0)
        if ml_confidence > self.accuracy_thresholds['min_ml_confidence']:
            confidences.append(ml_confidence)
            weights.append(0.4)
        
        # Individual model consensus (weight: 0.2)
        if len(individual_predictions) >= 3:
            model_confidences = [pred['confidence'] for pred in individual_predictions.values()]
            avg_model_confidence = np.mean(model_confidences)
            if avg_model_confidence > self.accuracy_thresholds['min_ml_confidence']:
                confidences.append(avg_model_confidence)
                weights.append(0.2)
        
        # Volume confirmation (weight: 0.1)
        volume_confidence = self._calculate_volume_confidence(data)
        if volume_confidence > 0.5:
            confidences.append(volume_confidence)
            weights.append(0.1)
        
        if confidences and weights:
            ensemble_confidence = np.average(confidences, weights=weights)
        else:
            ensemble_confidence = 0
        
        return ensemble_confidence
    
    def _calculate_volume_confidence(self, data: pd.DataFrame) -> float:
        """Calculate volume-based confidence"""
        if 'Volume' not in data.columns or len(data) < 20:
            return 0.5
        
        current_volume = data['Volume'].iloc[-1]
        avg_volume = data['Volume'].rolling(20).mean().iloc[-1]
        
        if avg_volume == 0:
            return 0.5
        
        volume_ratio = current_volume / avg_volume
        
        if volume_ratio >= self.accuracy_thresholds['min_volume_confirmation']:
            return min(0.9, 0.5 + (volume_ratio - 1) * 0.4)
        else:
            return max(0.1, 0.5 - (1 - volume_ratio) * 0.4)
    
    def _meets_accuracy_criteria(self, technical_signal: Dict, ml_prediction: Dict, 
                                ensemble_confidence: float, data: pd.DataFrame) -> bool:
        """Check if signal meets ultra-strict accuracy criteria"""
        # Minimum ensemble confidence
        if ensemble_confidence < self.accuracy_thresholds['min_ensemble_confidence']:
            return False
        
        # Minimum ML confidence
        if ml_prediction.get('confidence', 0) < self.accuracy_thresholds['min_ml_confidence']:
            return False
        
        # Minimum technical confidence
        if technical_signal.get('confidence', 0) < self.accuracy_thresholds['min_technical_confidence']:
            return False
        
        # Minimum signal count
        if technical_signal.get('signal_count', 0) < self.accuracy_thresholds['min_signal_count']:
            return False
        
        # Volatility check
        if 'Close' in data.columns and len(data) > 20:
            volatility = data['Close'].pct_change().rolling(20).std().iloc[-1]
            if volatility > self.accuracy_thresholds['max_volatility']:
                return False
        
        # Consensus check
        tech_action = technical_signal.get('overall_action', 'HOLD')
        ml_action = ml_prediction.get('action', 'HOLD')
        
        if tech_action != ml_action and tech_action != 'HOLD' and ml_action != 'HOLD':
            return False
        
        return True
    
    def _create_final_signal(self, symbol: str, technical_signal: Dict, ml_prediction: Dict,
                           individual_predictions: Dict, ensemble_confidence: float, data: pd.DataFrame) -> Dict:
        """Create final ultra-accuracy signal"""
        # Determine final action (prioritize ML if high confidence)
        if ml_prediction.get('confidence', 0) > 0.85:
            final_action = ml_prediction.get('action', 'HOLD')
        else:
            final_action = technical_signal.get('overall_action', 'HOLD')
        
        # Calculate enhanced options recommendation
        options_rec = self._calculate_enhanced_options_recommendation(
            final_action, data, ensemble_confidence
        )
        
        # Create comprehensive signal
        signal = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'action': final_action,
            'confidence': ensemble_confidence,
            'signal_type': 'ULTRA_HIGH_ACCURACY',
            
            # Technical analysis details
            'technical_analysis': {
                'action': technical_signal.get('overall_action', 'HOLD'),
                'confidence': technical_signal.get('confidence', 0),
                'signal_count': technical_signal.get('signal_count', 0),
                'individual_signals': technical_signal.get('signals', [])
            },
            
            # ML prediction details
            'ml_analysis': {
                'ensemble_action': ml_prediction.get('action', 'HOLD'),
                'ensemble_confidence': ml_prediction.get('confidence', 0),
                'individual_predictions': individual_predictions,
                'probabilities': ml_prediction.get('probabilities', {})
            },
            
            # Ensemble details
            'ensemble_analysis': {
                'final_confidence': ensemble_confidence,
                'consensus_strength': self._calculate_consensus_strength(technical_signal, ml_prediction),
                'prediction_diversity': len(set([p.get('action') for p in individual_predictions.values()]))
            },
            
            # Market conditions
            'market_conditions': self._analyze_market_conditions(data),
            
            # Enhanced options recommendation
            'options_recommendation': options_rec,
            
            # Risk metrics
            'risk_metrics': self._calculate_risk_metrics(data, ensemble_confidence),
            
            # Expected accuracy
            'expected_accuracy': self._estimate_expected_accuracy(ensemble_confidence)
        }
        
        return signal
    
    def _calculate_consensus_strength(self, technical_signal: Dict, ml_prediction: Dict) -> float:
        """Calculate strength of consensus between technical and ML analysis"""
        tech_action = technical_signal.get('overall_action', 'HOLD')
        ml_action = ml_prediction.get('action', 'HOLD')
        
        if tech_action == ml_action and tech_action != 'HOLD':
            return 0.9
        elif tech_action == 'HOLD' or ml_action == 'HOLD':
            return 0.5
        else:
            return 0.2
    
    def _analyze_market_conditions(self, data: pd.DataFrame) -> Dict:
        """Analyze current market conditions"""
        if len(data) < 50:
            return {'status': 'insufficient_data'}
        
        current_price = data['Close'].iloc[-1]
        
        # Trend analysis
        ma_20 = data['Close'].rolling(20).mean().iloc[-1]
        ma_50 = data['Close'].rolling(50).mean().iloc[-1]
        
        trend = 'neutral'
        if current_price > ma_20 > ma_50:
            trend = 'strong_uptrend'
        elif current_price > ma_20:
            trend = 'uptrend'
        elif current_price < ma_20 < ma_50:
            trend = 'strong_downtrend'
        elif current_price < ma_20:
            trend = 'downtrend'
        
        # Volatility analysis
        volatility = data['Close'].pct_change().rolling(20).std().iloc[-1]
        volatility_level = 'low' if volatility < 0.02 else 'medium' if volatility < 0.05 else 'high'
        
        # Volume analysis
        if 'Volume' in data.columns:
            current_volume = data['Volume'].iloc[-1]
            avg_volume = data['Volume'].rolling(20).mean().iloc[-1]
            volume_level = 'high' if current_volume > avg_volume * 1.5 else 'normal'
        else:
            volume_level = 'unknown'
        
        return {
            'trend': trend,
            'volatility_level': volatility_level,
            'volatility_value': volatility,
            'volume_level': volume_level,
            'price_vs_ma20': (current_price - ma_20) / ma_20,
            'price_vs_ma50': (current_price - ma_50) / ma_50
        }
    
    def _calculate_enhanced_options_recommendation(self, action: str, data: pd.DataFrame, 
                                                  confidence: float) -> Dict:
        """Calculate enhanced options recommendation based on ML confidence"""
        current_price = data['Close'].iloc[-1]
        
        # Dynamic position sizing based on confidence
        if confidence > 0.95:
            position_size = "MAXIMUM"
            risk_reward_ratio = "1:3"
        elif confidence > 0.90:
            position_size = "LARGE"
            risk_reward_ratio = "1:2.5"
        elif confidence > 0.85:
            position_size = "MEDIUM"
            risk_reward_ratio = "1:2"
        else:
            position_size = "SMALL"
            risk_reward_ratio = "1:1.5"
        
        # Calculate ATR-based stop loss and target
        if len(data) > 14:
            from indicators import TechnicalIndicators
            ti = TechnicalIndicators()
            atr = ti.calculate_atr(data['High'], data['Low'], data['Close']).iloc[-1]
            
            if action == 'CALL':
                stop_loss = current_price - (atr * 2)
                target_price = current_price + (atr * 3)
            else:  # PUT
                stop_loss = current_price + (atr * 2)
                target_price = current_price - (atr * 3)
        else:
            # Fallback to percentage-based
            if action == 'CALL':
                stop_loss = current_price * 0.95
                target_price = current_price * 1.08
            else:
                stop_loss = current_price * 1.05
                target_price = current_price * 0.92
        
        # Calculate strike prices based on confidence
        strike_interval = 50 if current_price > 1000 else 25
        if action == 'CALL':
            base_strike = int((current_price // strike_interval + 1) * strike_interval)
            strikes = [str(base_strike + i * strike_interval) for i in range(3)]
        else:
            base_strike = int((current_price // strike_interval) * strike_interval)
            strikes = [str(base_strike - i * strike_interval) for i in range(1, 4)]
        
        return {
            'action': action,
            'confidence': confidence,
            'position_size': position_size,
            'risk_reward_ratio': risk_reward_ratio,
            'current_price': current_price,
            'stop_loss': stop_loss,
            'target_price': target_price,
            'strike_prices': strikes,
            'suggested_expiry': self._get_optimal_expiry(),
            'atr_based': True if len(data) > 14 else False
        }
    
    def _get_optimal_expiry(self) -> str:
        """Get optimal options expiry based on current date"""
        today = datetime.now()
        # Find next Thursday (standard weekly expiry)
        days_until_thursday = (3 - today.weekday()) % 7
        if days_until_thursday == 0:
            days_until_thursday = 7
        expiry_date = today + timedelta(days=days_until_thursday)
        return expiry_date.strftime('%Y-%m-%d')
    
    def _calculate_risk_metrics(self, data: pd.DataFrame, confidence: float) -> Dict:
        """Calculate comprehensive risk metrics"""
        if len(data) < 20:
            return {'status': 'insufficient_data'}
        
        returns = data['Close'].pct_change().dropna()
        
        # Value at Risk (VaR)
        var_95 = np.percentile(returns, 5)
        var_99 = np.percentile(returns, 1)
        
        # Maximum drawdown
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Sharpe ratio (assuming risk-free rate = 0)
        sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() != 0 else 0
        
        # Volatility
        volatility = returns.std() * np.sqrt(252)
        
        # Risk score based on confidence and metrics
        risk_score = (1 - confidence) * 0.5 + abs(var_95) * 0.3 + abs(max_drawdown) * 0.2
        
        return {
            'var_95_daily': var_95,
            'var_99_daily': var_99,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'annualized_volatility': volatility,
            'risk_score': min(risk_score, 1.0),
            'risk_level': 'LOW' if risk_score < 0.3 else 'MEDIUM' if risk_score < 0.6 else 'HIGH'
        }
    
    def _estimate_expected_accuracy(self, confidence: float) -> float:
        """Estimate expected accuracy based on confidence and historical performance"""
        # Base accuracy from confidence
        base_accuracy = confidence
        
        # Adjust based on historical performance
        if self.accuracy_metrics['high_confidence_predictions'] > 0:
            historical_accuracy = (self.accuracy_metrics['high_confidence_correct'] / 
                                self.accuracy_metrics['high_confidence_predictions'])
            # Weight historical accuracy more heavily if we have enough data
            if self.accuracy_metrics['high_confidence_predictions'] > 50:
                base_accuracy = base_accuracy * 0.3 + historical_accuracy * 0.7
            else:
                base_accuracy = base_accuracy * 0.6 + historical_accuracy * 0.4
        
        return min(base_accuracy, 0.98)  # Cap at 98% to maintain realistic expectations
    
    def _track_prediction(self, signal: Dict):
        """Track prediction for accuracy monitoring"""
        self.accuracy_metrics['total_predictions'] += 1
        
        if signal['confidence'] > 0.85:
            self.accuracy_metrics['high_confidence_predictions'] += 1
        
        self.prediction_history.append({
            'timestamp': signal['timestamp'],
            'symbol': signal['symbol'],
            'action': signal['action'],
            'confidence': signal['confidence'],
            'expected_accuracy': signal.get('expected_accuracy', 0)
        })
    
    def _create_hold_signal(self, symbol: str, reason: str) -> Dict:
        """Create a hold signal with explanation"""
        return {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'action': 'HOLD',
            'confidence': 0.0,
            'signal_type': 'ULTRA_HIGH_ACCURACY',
            'reason': reason,
            'options_recommendation': None,
            'expected_accuracy': 0.0
        }
    
    def get_performance_summary(self) -> Dict:
        """Get comprehensive performance summary"""
        return {
            'accuracy_metrics': self.accuracy_metrics,
            'total_predictions': len(self.prediction_history),
            'average_confidence': np.mean([p['confidence'] for p in self.prediction_history]) if self.prediction_history else 0,
            'high_confidence_rate': (self.accuracy_metrics['high_confidence_predictions'] / 
                                   max(1, self.accuracy_metrics['total_predictions'])),
            'ml_model_performance': self.ml_predictor.get_model_performance(),
            'top_features': list(self.ml_predictor.get_feature_importance().keys())[:10]
        }
