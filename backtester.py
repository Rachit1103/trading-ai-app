import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta
from enhanced_signal_generator import UltraHighAccuracySignalGenerator
from data_fetcher import StockDataFetcher
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report
import warnings
warnings.filterwarnings('ignore')

class ComprehensiveBacktester:
    """Comprehensive backtesting system for validating trading strategies"""
    
    def __init__(self, initial_capital: float = 100000):
        self.logger = logging.getLogger(__name__)
        self.initial_capital = initial_capital
        self.signal_generator = UltraHighAccuracySignalGenerator()
        self.data_fetcher = StockDataFetcher()
        
        # Backtracking results storage
        self.backtest_results = {}
        self.performance_metrics = {}
        
    def run_comprehensive_backtest(self, symbols: List[str], start_date: str, end_date: str,
                                 strategy: str = 'ultra_accuracy') -> Dict:
        """Run comprehensive backtest on multiple symbols"""
        self.logger.info(f"Starting comprehensive backtest for {len(symbols)} symbols...")
        
        all_results = []
        
        for symbol in symbols:
            try:
                result = self._backtest_single_symbol(symbol, start_date, end_date, strategy)
                if result:
                    all_results.append(result)
                    self.logger.info(f"Backtest completed for {symbol}: {result['total_return']:.2%}")
            except Exception as e:
                self.logger.error(f"Backtest failed for {symbol}: {e}")
        
        # Aggregate results
        aggregated_results = self._aggregate_backtest_results(all_results)
        
        self.backtest_results[strategy] = {
            'individual_results': all_results,
            'aggregated': aggregated_results,
            'backtest_period': f"{start_date} to {end_date}",
            'symbols_tested': symbols,
            'timestamp': datetime.now()
        }
        
        return aggregated_results
    
    def _backtest_single_symbol(self, symbol: str, start_date: str, end_date: str, 
                              strategy: str) -> Optional[Dict]:
        """Backtest a single symbol"""
        try:
            # Fetch historical data
            data = self.data_fetcher.get_yfinance_data(symbol, period="2y")
            
            if data.empty:
                return None
            
            # Filter by date range
            data = data.loc[start_date:end_date]
            
            if len(data) < 100:  # Need sufficient data
                return None
            
            # Initialize backtest variables
            capital = self.initial_capital
            positions = []
            trades = []
            equity_curve = [capital]
            
            # Walk through data
            for i in range(50, len(data)):  # Start from 50 to have enough history
                current_data = data.iloc[:i+1]
                current_date = current_data.index[-1]
                current_price = current_data['Close'].iloc[-1]
                
                # Generate signal
                if strategy == 'ultra_accuracy':
                    signal = self.signal_generator.generate_ultra_accuracy_signal(current_data, symbol)
                else:
                    signal = self.signal_generator.technical_generator.generate_signals(current_data, symbol)
                
                # Execute trades based on signal
                trade_result = self._execute_trade_logic(
                    signal, current_price, current_date, capital, positions
                )
                
                if trade_result:
                    trades.append(trade_result)
                    capital = trade_result['capital_after_trade']
                
                equity_curve.append(capital)
            
            # Calculate performance metrics
            metrics = self._calculate_performance_metrics(
                equity_curve, trades, data['Close'], symbol
            )
            
            return {
                'symbol': symbol,
                'metrics': metrics,
                'trades': trades,
                'equity_curve': equity_curve,
                'price_data': data['Close'],
                'total_trades': len(trades)
            }
            
        except Exception as e:
            self.logger.error(f"Error in backtest for {symbol}: {e}")
            return None
    
    def _execute_trade_logic(self, signal: Dict, current_price: float, date: datetime,
                           capital: float, positions: List) -> Optional[Dict]:
        """Execute trade logic based on signal"""
        action = signal.get('action', 'HOLD')
        confidence = signal.get('confidence', 0)
        
        # Only trade with high confidence
        if confidence < 0.8:
            return None
        
        # Position sizing based on confidence
        if confidence > 0.95:
            position_size = 0.3  # 30% of capital
        elif confidence > 0.9:
            position_size = 0.2  # 20% of capital
        else:
            position_size = 0.1  # 10% of capital
        
        # Close existing positions if signal changes
        for position in positions[:]:
            if (position['action'] == 'CALL' and action == 'PUT') or \
               (position['action'] == 'PUT' and action == 'CALL'):
                # Close position
                pnl = self._calculate_pnl(position, current_price)
                capital += pnl
                positions.remove(position)
        
        # Open new position
        if action in ['CALL', 'PUT'] and confidence > 0.85:
            # Calculate position value
            position_value = capital * position_size
            
            # Create position
            position = {
                'action': action,
                'entry_price': current_price,
                'position_value': position_value,
                'entry_date': date,
                'confidence': confidence,
                'stop_loss': signal.get('options_recommendation', {}).get('stop_loss', current_price * 0.95),
                'target_price': signal.get('options_recommendation', {}).get('target_price', current_price * 1.1)
            }
            
            positions.append(position)
            
            return {
                'type': 'ENTRY',
                'action': action,
                'price': current_price,
                'position_value': position_value,
                'capital_after_trade': capital,
                'date': date,
                'confidence': confidence
            }
        
        return None
    
    def _calculate_pnl(self, position: Dict, current_price: float) -> float:
        """Calculate PnL for a position"""
        entry_price = position['entry_price']
        action = position['action']
        position_value = position['position_value']
        
        if action == 'CALL':
            # For CALL options, profit when price goes up
            price_change = (current_price - entry_price) / entry_price
            # Leverage effect for options (simplified)
            leverage = 5  # 5x leverage for options
            pnl = position_value * price_change * leverage
        else:  # PUT
            # For PUT options, profit when price goes down
            price_change = (entry_price - current_price) / entry_price
            leverage = 5
            pnl = position_value * price_change * leverage
        
        return pnl
    
    def _calculate_performance_metrics(self, equity_curve: List[float], trades: List[Dict],
                                     price_data: pd.Series, symbol: str) -> Dict:
        """Calculate comprehensive performance metrics"""
        equity_returns = pd.Series(equity_curve).pct_change().dropna()
        
        # Basic metrics
        total_return = (equity_curve[-1] - equity_curve[0]) / equity_curve[0]
        annualized_return = (1 + total_return) ** (252 / len(equity_curve)) - 1
        
        # Risk metrics
        volatility = equity_returns.std() * np.sqrt(252)
        sharpe_ratio = annualized_return / volatility if volatility != 0 else 0
        
        # Drawdown metrics
        equity_series = pd.Series(equity_curve)
        running_max = equity_series.expanding().max()
        drawdown = (equity_series - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Trade metrics
        winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in trades if t.get('pnl', 0) < 0]
        
        win_rate = len(winning_trades) / len(trades) if trades else 0
        
        if winning_trades:
            avg_win = np.mean([t['pnl'] for t in winning_trades])
        else:
            avg_win = 0
            
        if losing_trades:
            avg_loss = np.mean([abs(t['pnl']) for t in losing_trades])
        else:
            avg_loss = 0
        
        profit_factor = avg_win / avg_loss if avg_loss > 0 else float('inf')
        
        # Accuracy metrics
        if trades:
            trade_accuracy = len([t for t in trades if t.get('confidence', 0) > 0.8]) / len(trades)
        else:
            trade_accuracy = 0
        
        # Benchmark comparison (buy and hold)
        buy_hold_return = (price_data.iloc[-1] - price_data.iloc[0]) / price_data.iloc[0]
        alpha = annualized_return - buy_hold_return
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': len(trades),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'trade_accuracy': trade_accuracy,
            'alpha': alpha,
            'buy_hold_return': buy_hold_return,
            'final_capital': equity_curve[-1]
        }
    
    def _aggregate_backtest_results(self, individual_results: List[Dict]) -> Dict:
        """Aggregate results from multiple symbols"""
        if not individual_results:
            return {}
        
        # Aggregate metrics
        total_return = np.mean([r['metrics']['total_return'] for r in individual_results])
        annualized_return = np.mean([r['metrics']['annualized_return'] for r in individual_results])
        sharpe_ratio = np.mean([r['metrics']['sharpe_ratio'] for r in individual_results])
        max_drawdown = np.mean([r['metrics']['max_drawdown'] for r in individual_results])
        win_rate = np.mean([r['metrics']['win_rate'] for r in individual_results])
        profit_factor = np.mean([r['metrics']['profit_factor'] for r in individual_results])
        alpha = np.mean([r['metrics']['alpha'] for r in individual_results])
        
        # Count profitable symbols
        profitable_symbols = len([r for r in individual_results if r['metrics']['total_return'] > 0])
        profitability_rate = profitable_symbols / len(individual_results)
        
        return {
            'avg_total_return': total_return,
            'avg_annualized_return': annualized_return,
            'avg_sharpe_ratio': sharpe_ratio,
            'avg_max_drawdown': max_drawdown,
            'avg_win_rate': win_rate,
            'avg_profit_factor': profit_factor,
            'avg_alpha': alpha,
            'profitability_rate': profitability_rate,
            'symbols_tested': len(individual_results),
            'profitable_symbols': profitable_symbols
        }
    
    def calculate_accuracy_validation(self, test_data: pd.DataFrame) -> Dict:
        """Calculate accuracy validation using out-of-sample data"""
        self.logger.info("Running accuracy validation...")
        
        try:
            # Split data for training and testing
            train_size = int(len(test_data) * 0.7)
            train_data = test_data.iloc[:train_size]
            test_data_actual = test_data.iloc[train_size:]
            
            # Train models on training data
            training_results = self.signal_generator.train_ml_models(train_data)
            
            # Test on out-of-sample data
            predictions = []
            actuals = []
            
            for i in range(50, len(test_data_actual)):
                current_data = test_data_actual.iloc[:i+1]
                
                # Generate prediction
                signal = self.signal_generator.generate_ultra_accuracy_signal(current_data, "TEST")
                
                # Calculate actual outcome (next 5 days return)
                if i + 5 < len(test_data_actual):
                    future_price = test_data_actual.iloc[i+5]['Close']
                    current_price = test_data_actual.iloc[i]['Close']
                    actual_return = (future_price - current_price) / current_price
                    
                    # Convert to action
                    if actual_return > 0.02:
                        actual_action = 'CALL'
                    elif actual_return < -0.02:
                        actual_action = 'PUT'
                    else:
                        actual_action = 'HOLD'
                    
                    predictions.append(signal['action'])
                    actuals.append(actual_action)
            
            # Calculate accuracy metrics
            if predictions and actuals:
                accuracy = np.mean([p == a for p, a in zip(predictions, actuals)])
                
                # Detailed classification report
                report = classification_report(actuals, predictions, output_dict=True, zero_division=0)
                
                # Confusion matrix
                cm = confusion_matrix(actuals, predictions, labels=['CALL', 'PUT', 'HOLD'])
                
                return {
                    'out_of_sample_accuracy': accuracy,
                    'classification_report': report,
                    'confusion_matrix': cm.tolist(),
                    'total_predictions': len(predictions),
                    'training_results': training_results
                }
            else:
                return {'error': 'Insufficient data for validation'}
                
        except Exception as e:
            self.logger.error(f"Accuracy validation failed: {e}")
            return {'error': str(e)}
    
    def generate_performance_report(self, strategy: str = 'ultra_accuracy') -> str:
        """Generate comprehensive performance report"""
        if strategy not in self.backtest_results:
            return "No backtest results available for this strategy"
        
        results = self.backtest_results[strategy]
        aggregated = results['aggregated']
        
        report = f"""
# COMPREHENSIVE BACKTESTING REPORT
## Strategy: {strategy.upper()}
## Period: {results['backtest_period']}
## Symbols Tested: {len(results['symbols_tested'])}

### AGGREGATED PERFORMANCE METRICS:
- **Average Total Return**: {aggregated['avg_total_return']:.2%}
- **Average Annualized Return**: {aggregated['avg_annualized_return']:.2%}
- **Average Sharpe Ratio**: {aggregated['avg_sharpe_ratio']:.3f}
- **Average Maximum Drawdown**: {aggregated['avg_max_drawdown']:.2%}
- **Average Win Rate**: {aggregated['avg_win_rate']:.2%}
- **Average Profit Factor**: {aggregated['avg_profit_factor']:.2f}
- **Average Alpha**: {aggregated['avg_alpha']:.2%}
- **Profitability Rate**: {aggregated['profitability_rate']:.2%} ({aggregated['profitable_symbols']}/{aggregated['symbols_tested']} symbols)

### TOP PERFORMING SYMBOLS:
"""
        
        # Add top performers
        individual_results = results['individual_results']
        top_performers = sorted(individual_results, key=lambda x: x['metrics']['total_return'], reverse=True)[:5]
        
        for i, result in enumerate(top_performers, 1):
            metrics = result['metrics']
            report += f"""
{i}. **{result['symbol']}**
   - Total Return: {metrics['total_return']:.2%}
   - Sharpe Ratio: {metrics['sharpe_ratio']:.3f}
   - Win Rate: {metrics['win_rate']:.2%}
   - Total Trades: {metrics['total_trades']}
"""
        
        report += f"""

### ACCURACY VALIDATION:
"""
        
        # Add accuracy validation if available
        if hasattr(self, 'accuracy_validation'):
            validation = self.accuracy_validation
            if 'out_of_sample_accuracy' in validation:
                report += f"""
- **Out-of-Sample Accuracy**: {validation['out_of_sample_accuracy']:.2%}
- **Total Validation Predictions**: {validation['total_predictions']}
"""
        
        report += f"""

### RISK ANALYSIS:
- **Maximum Drawdown**: {aggregated['avg_max_drawdown']:.2%}
- **Volatility**: Based on equity curve volatility
- **Risk-Adjusted Returns**: Sharpe ratio of {aggregated['avg_sharpe_ratio']:.3f}

### RECOMMENDATIONS:
"""
        
        if aggregated['avg_total_return'] > 0.15:
            report += "- ✅ Strategy shows strong positive returns\n"
        else:
            report += "- ⚠️ Strategy returns are modest\n"
        
        if aggregated['avg_sharpe_ratio'] > 1.0:
            report += "- ✅ Excellent risk-adjusted returns\n"
        elif aggregated['avg_sharpe_ratio'] > 0.5:
            report += "- ⚠️ Moderate risk-adjusted returns\n"
        else:
            report += "- ❌ Poor risk-adjusted returns\n"
        
        if aggregated['profitability_rate'] > 0.6:
            report += "- ✅ High success rate across symbols\n"
        else:
            report += "- ⚠️ Moderate success rate across symbols\n"
        
        report += f"""

### IMPORTANT NOTES:
⚠️ **Past performance does not guarantee future results**
⚠️ **Backtesting has limitations and may not account for all market conditions**
⚠️ **Real trading involves slippage, transaction costs, and emotional factors**
⚠️ **Always use proper risk management in live trading**

### NEXT STEPS:
1. **Forward Testing**: Test the strategy in real-time with paper trading
2. **Parameter Optimization**: Fine-tune risk thresholds and position sizing
3. **Market Condition Analysis**: Analyze performance in different market regimes
4. **Continuous Monitoring**: Track performance and adjust as needed

**Report Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return report
    
    def save_backtest_results(self, filename: str = None) -> str:
        """Save backtest results to file"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"backtest_results_{timestamp}.json"
        
        import json
        
        # Convert datetime objects to strings for JSON serialization
        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, np.float64):
                return float(obj)
            elif isinstance(obj, np.int64):
                return int(obj)
            return obj
        
        # Prepare data for JSON
        json_data = {}
        for strategy, results in self.backtest_results.items():
            json_data[strategy] = json.loads(json.dumps(results, default=convert_datetime))
        
        with open(filename, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        self.logger.info(f"Backtest results saved to {filename}")
        return filename
