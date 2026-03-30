import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.model_selection import train_test_split, cross_val_score, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
import xgboost as xgb
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
import warnings
warnings.filterwarnings('ignore')
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import joblib
import os

class AdvancedMLPredictor:
    """Advanced Machine Learning predictor for maximum trading accuracy"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
        self.accuracy_history = []
        self.model_path = "ml_models"
        
        # Create models directory
        if not os.path.exists(self.model_path):
            os.makedirs(self.model_path)
        
        # Initialize ensemble models
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize multiple ML models for ensemble prediction"""
        # Random Forest
        self.models['rf'] = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1
        )
        
        # XGBoost
        self.models['xgb'] = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1
        )
        
        # Gradient Boosting
        self.models['gb'] = GradientBoostingClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            random_state=42
        )
        
        # Neural Network
        self.models['nn'] = MLPClassifier(
            hidden_layer_sizes=(100, 50, 25),
            activation='relu',
            solver='adam',
            alpha=0.001,
            learning_rate='adaptive',
            max_iter=1000,
            random_state=42
        )
        
        # SVM
        self.models['svm'] = SVC(
            C=1.0,
            kernel='rbf',
            gamma='scale',
            probability=True,
            random_state=42
        )
        
        # Ensemble model (Voting Classifier)
        self.models['ensemble'] = VotingClassifier(
            estimators=[
                ('rf', self.models['rf']),
                ('xgb', self.models['xgb']),
                ('gb', self.models['gb']),
                ('nn', self.models['nn'])
            ],
            voting='soft'
        )
    
    def create_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create advanced features for ML models"""
        features = data.copy()
        
        # Price-based features
        features['price_change'] = features['Close'].pct_change()
        features['price_change_2d'] = features['Close'].pct_change(2)
        features['price_change_5d'] = features['Close'].pct_change(5)
        features['price_change_10d'] = features['Close'].pct_change(10)
        
        # High-Low spread
        features['hl_spread'] = (features['High'] - features['Low']) / features['Close']
        features['hl_spread_5d_avg'] = features['hl_spread'].rolling(5).mean()
        
        # Open-Close gap
        features['oc_gap'] = (features['Close'] - features['Open']) / features['Open']
        
        # Volume features
        if 'Volume' in features.columns:
            features['volume_change'] = features['Volume'].pct_change()
            features['volume_ma_ratio'] = features['Volume'] / features['Volume'].rolling(20).mean()
            features['volume_price_trend'] = features['volume_change'] * features['price_change']
        
        # Volatility features
        features['volatility_5d'] = features['price_change'].rolling(5).std()
        features['volatility_10d'] = features['price_change'].rolling(10).std()
        features['volatility_20d'] = features['price_change'].rolling(20).std()
        
        # Moving average crossovers
        features['ma_5'] = features['Close'].rolling(5).mean()
        features['ma_10'] = features['Close'].rolling(10).mean()
        features['ma_20'] = features['Close'].rolling(20).mean()
        features['ma_50'] = features['Close'].rolling(50).mean()
        
        features['ma_5_10_cross'] = (features['ma_5'] > features['ma_10']).astype(int)
        features['ma_10_20_cross'] = (features['ma_10'] > features['ma_20']).astype(int)
        features['ma_20_50_cross'] = (features['ma_20'] > features['ma_50']).astype(int)
        
        # Price relative to moving averages
        features['price_vs_ma5'] = (features['Close'] - features['ma_5']) / features['ma_5']
        features['price_vs_ma20'] = (features['Close'] - features['ma_20']) / features['ma_20']
        features['price_vs_ma50'] = (features['Close'] - features['ma_50']) / features['ma_50']
        
        # RSI features
        from indicators import TechnicalIndicators
        ti = TechnicalIndicators()
        features['rsi'] = ti.calculate_rsi(features['Close'])
        features['rsi_overbought'] = (features['rsi'] > 70).astype(int)
        features['rsi_oversold'] = (features['rsi'] < 30).astype(int)
        features['rsi_change'] = features['rsi'].diff()
        
        # MACD features
        macd_data = ti.calculate_macd(features['Close'])
        features['macd'] = macd_data['macd']
        features['macd_signal'] = macd_data['signal']
        features['macd_histogram'] = macd_data['histogram']
        features['macd_cross'] = (features['macd'] > features['macd_signal']).astype(int)
        features['macd_histogram_change'] = features['macd_histogram'].diff()
        
        # Bollinger Bands features
        bb_data = ti.calculate_bollinger_bands(features['Close'])
        features['bb_upper'] = bb_data['upper']
        features['bb_lower'] = bb_data['lower']
        features['bb_middle'] = bb_data['middle']
        features['bb_position'] = (features['Close'] - features['bb_lower']) / (features['bb_upper'] - features['bb_lower'])
        features['bb_squeeze'] = (features['bb_upper'] - features['bb_lower']) / features['bb_middle']
        
        # Stochastic features
        stoch_data = ti.calculate_stochastic(features['High'], features['Low'], features['Close'])
        features['stoch_k'] = stoch_data['k']
        features['stoch_d'] = stoch_data['d']
        features['stoch_overbought'] = (features['stoch_k'] > 80).astype(int)
        features['stoch_oversold'] = (features['stoch_k'] < 20).astype(int)
        features['stoch_cross'] = (features['stoch_k'] > features['stoch_d']).astype(int)
        
        # ATR features
        features['atr'] = ti.calculate_atr(features['High'], features['Low'], features['Close'])
        features['atr_ratio'] = features['atr'] / features['Close']
        
        # Williams %R features
        features['williams_r'] = ti.calculate_williams_r(features['High'], features['Low'], features['Close'])
        features['williams_r_overbought'] = (features['williams_r'] > -20).astype(int)
        features['williams_r_oversold'] = (features['williams_r'] < -80).astype(int)
        
        # CCI features
        features['cci'] = ti.calculate_cci(features['High'], features['Low'], features['Close'])
        features['cci_overbought'] = (features['cci'] > 100).astype(int)
        features['cci_oversold'] = (features['cci'] < -100).astype(int)
        
        # Time-based features
        features['day_of_week'] = pd.to_datetime(features.index).dayofweek
        features['month'] = pd.to_datetime(features.index).month
        features['quarter'] = pd.to_datetime(features.index).quarter
        
        # Trend features
        features['trend_5d'] = (features['Close'] > features['Close'].shift(5)).astype(int)
        features['trend_10d'] = (features['Close'] > features['Close'].shift(10)).astype(int)
        features['trend_20d'] = (features['Close'] > features['Close'].shift(20)).astype(int)
        
        return features
    
    def create_target_variable(self, data: pd.DataFrame, horizon: int = 5, threshold: float = 0.02) -> pd.Series:
        """Create target variable for ML models"""
        future_return = data['Close'].shift(-horizon) / data['Close'] - 1
        
        # Create 3 classes: 0 = HOLD, 1 = CALL, 2 = PUT
        target = pd.Series(0, index=data.index)
        target[future_return > threshold] = 1  # CALL
        target[future_return < -threshold] = 2  # PUT
        
        return target
    
    def prepare_data(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare data for ML training"""
        # Create features
        features = self.create_features(data)
        
        # Create target
        target = self.create_target_variable(features)
        
        # Remove NaN values
        valid_idx = ~(features.isnull().any(axis=1) | target.isnull())
        features_clean = features[valid_idx]
        target_clean = target[valid_idx]
        
        # Remove non-numeric columns
        numeric_cols = features_clean.select_dtypes(include=[np.number]).columns
        features_clean = features_clean[numeric_cols]
        
        return features_clean, target_clean
    
    def train_models(self, data: pd.DataFrame, test_size: float = 0.2) -> Dict[str, float]:
        """Train all ML models and return accuracy scores"""
        # Prepare data
        X, y = self.prepare_data(data)
        
        if len(X) < 100:
            self.logger.warning("Insufficient data for training")
            return {}
        
        # Split data (time series split for better validation)
        tscv = TimeSeriesSplit(n_splits=5)
        
        results = {}
        
        for model_name, model in self.models.items():
            try:
                # Cross-validation
                cv_scores = cross_val_score(model, X, y, cv=tscv, scoring='accuracy')
                avg_accuracy = cv_scores.mean()
                
                # Train on full dataset
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=test_size, random_state=42, stratify=y
                )
                
                # Scale features for neural network and SVM
                if model_name in ['nn', 'svm']:
                    scaler = StandardScaler()
                    X_train_scaled = scaler.fit_transform(X_train)
                    X_test_scaled = scaler.transform(X_test)
                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)
                    self.scalers[model_name] = scaler
                else:
                    model.fit(X_train, y_train)
                    y_pred = model.predict(X_test)
                
                # Calculate metrics
                accuracy = accuracy_score(y_test, y_pred)
                precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
                recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
                f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
                
                results[model_name] = {
                    'cv_accuracy': avg_accuracy,
                    'test_accuracy': accuracy,
                    'precision': precision,
                    'recall': recall,
                    'f1_score': f1
                }
                
                # Store feature importance for tree-based models
                if model_name in ['rf', 'xgb', 'gb']:
                    self.feature_importance[model_name] = dict(zip(X.columns, model.feature_importances_))
                
                # Save model
                joblib.dump(model, f"{self.model_path}/{model_name}_model.pkl")
                if model_name in self.scalers:
                    joblib.dump(self.scalers[model_name], f"{self.model_path}/{model_name}_scaler.pkl")
                
                self.logger.info(f"{model_name} trained - Accuracy: {accuracy:.4f}")
                
            except Exception as e:
                self.logger.error(f"Error training {model_name}: {e}")
                results[model_name] = {'error': str(e)}
        
        # Store accuracy history
        self.accuracy_history.append({
            'timestamp': datetime.now(),
            'results': results
        })
        
        return results
    
    def predict(self, data: pd.DataFrame, model_name: str = 'ensemble') -> Dict:
        """Make predictions using trained model"""
        try:
            # Load model if not in memory
            if model_name not in self.models:
                self.models[model_name] = joblib.load(f"{self.model_path}/{model_name}_model.pkl")
                if model_name in self.scalers or os.path.exists(f"{self.model_path}/{model_name}_scaler.pkl"):
                    self.scalers[model_name] = joblib.load(f"{self.model_path}/{model_name}_scaler.pkl")
            
            # Prepare features
            features = self.create_features(data)
            numeric_cols = features.select_dtypes(include=[np.number]).columns
            X = features[numeric_cols].iloc[-1:]  # Get latest data
            
            # Handle NaN values
            X = X.fillna(method='ffill').fillna(0)
            
            # Scale if necessary
            if model_name in ['nn', 'svm'] and model_name in self.scalers:
                X_scaled = self.scalers[model_name].transform(X)
                prediction = self.models[model_name].predict(X_scaled)[0]
                probabilities = self.models[model_name].predict_proba(X_scaled)[0]
            else:
                prediction = self.models[model_name].predict(X)[0]
                probabilities = self.models[model_name].predict_proba(X)[0]
            
            # Convert prediction to action
            action_map = {0: 'HOLD', 1: 'CALL', 2: 'PUT'}
            action = action_map[prediction]
            
            # Calculate confidence
            confidence = max(probabilities)
            
            return {
                'action': action,
                'confidence': confidence,
                'probabilities': {
                    'HOLD': probabilities[0],
                    'CALL': probabilities[1],
                    'PUT': probabilities[2]
                },
                'model_used': model_name,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Prediction error: {e}")
            return {
                'action': 'HOLD',
                'confidence': 0.0,
                'error': str(e),
                'timestamp': datetime.now()
            }
    
    def ensemble_predict(self, data: pd.DataFrame) -> Dict:
        """Make ensemble prediction using multiple models"""
        predictions = {}
        confidences = []
        
        # Get predictions from all models
        for model_name in ['rf', 'xgb', 'gb', 'nn']:
            pred = self.predict(data, model_name)
            if 'error' not in pred:
                predictions[model_name] = pred
                confidences.append(pred['confidence'])
        
        if not predictions:
            return {'action': 'HOLD', 'confidence': 0.0, 'error': 'No valid predictions'}
        
        # Weight voting by confidence
        action_votes = {'CALL': 0, 'PUT': 0, 'HOLD': 0}
        total_weight = 0
        
        for model_name, pred in predictions.items():
            weight = pred['confidence']
            action_votes[pred['action']] += weight
            total_weight += weight
        
        # Determine final action
        if total_weight > 0:
            final_action = max(action_votes, key=action_votes.get)
            final_confidence = action_votes[final_action] / total_weight
        else:
            final_action = 'HOLD'
            final_confidence = 0.0
        
        return {
            'action': final_action,
            'confidence': final_confidence,
            'individual_predictions': predictions,
            'vote_breakdown': action_votes,
            'timestamp': datetime.now()
        }
    
    def get_feature_importance(self, model_name: str = 'ensemble') -> Dict[str, float]:
        """Get feature importance from trained models"""
        if model_name in self.feature_importance:
            return self.feature_importance[model_name]
        
        # Average feature importance across models
        avg_importance = {}
        for model_name, importance in self.feature_importance.items():
            for feature, score in importance.items():
                if feature not in avg_importance:
                    avg_importance[feature] = []
                avg_importance[feature].append(score)
        
        # Calculate average
        for feature in avg_importance:
            avg_importance[feature] = np.mean(avg_importance[feature])
        
        return dict(sorted(avg_importance.items(), key=lambda x: x[1], reverse=True))
    
    def get_model_performance(self) -> Dict:
        """Get performance metrics for all models"""
        if not self.accuracy_history:
            return {}
        
        latest_results = self.accuracy_history[-1]['results']
        
        performance = {}
        for model_name, metrics in latest_results.items():
            if 'error' not in metrics:
                performance[model_name] = {
                    'accuracy': metrics['test_accuracy'],
                    'precision': metrics['precision'],
                    'recall': metrics['recall'],
                    'f1_score': metrics['f1_score']
                }
        
        return performance
