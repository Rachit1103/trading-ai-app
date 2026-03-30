import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import logging
from datetime import datetime, timedelta
import threading
import time
from data_fetcher import StockDataFetcher
from signal_generator import SignalGenerator

class StockScanner:
    """Main scanner class that orchestrates stock scanning and signal generation"""
    
    def __init__(self, risk_level: str = "medium", scan_interval: int = 300):
        self.logger = logging.getLogger(__name__)
        self.risk_level = risk_level
        self.scan_interval = scan_interval  # seconds
        self.data_fetcher = StockDataFetcher()
        self.signal_generator = SignalGenerator(risk_level)
        self.is_scanning = False
        self.scan_results = []
        self.scan_thread = None
        
    def scan_nifty50_stocks(self, period: str = "6mo") -> List[Dict]:
        """Scan all Nifty 50 stocks for trading signals"""
        self.logger.info("Starting Nifty 50 stock scan...")
        
        # Get Nifty 50 symbols
        symbols = self.data_fetcher.get_nifty50_stocks()
        
        # Fetch data for all stocks
        self.logger.info(f"Fetching data for {len(symbols)} stocks...")
        stock_data = self.data_fetcher.get_multiple_stocks_data(symbols, period=period)
        
        # Generate signals
        self.logger.info("Generating trading signals...")
        signals = self.signal_generator.scan_multiple_stocks(stock_data)
        
        # Add additional metadata
        for signal in signals:
            signal['scan_time'] = datetime.now()
            signal['risk_level'] = self.risk_level
            
            # Get options recommendation
            options_rec = self.signal_generator.get_options_recommendation(signal)
            signal['options_recommendation'] = options_rec
        
        self.scan_results = signals
        self.logger.info(f"Scan completed. Found {len(signals)} trading signals.")
        
        return signals
    
    def scan_groww_trending_stocks(self, period: str = "3mo") -> List[Dict]:
        """Scan trending stocks from Groww"""
        self.logger.info("Scanning Groww trending stocks...")
        
        # Get trending stocks from Groww
        trending_stocks = self.data_fetcher.get_groww_trending_stocks()
        
        if not trending_stocks:
            self.logger.warning("No trending stocks found from Groww")
            return []
        
        # Convert to yfinance symbols
        symbols = []
        for stock in trending_stocks:
            symbol = stock['symbol'].replace('.NS', '') + '.NS'
            symbols.append(symbol)
        
        # Fetch data and generate signals
        stock_data = self.data_fetcher.get_multiple_stocks_data(symbols, period=period)
        signals = self.signal_generator.scan_multiple_stocks(stock_data)
        
        # Add Groww metadata
        for signal in signals:
            signal['scan_time'] = datetime.now()
            signal['risk_level'] = self.risk_level
            signal['source'] = 'Groww Trending'
            
            # Find corresponding Groww stock data
            for stock in trending_stocks:
                if stock['symbol'].replace('.NS', '') in signal['symbol']:
                    signal['groww_data'] = stock
                    break
            
            # Get options recommendation
            options_rec = self.signal_generator.get_options_recommendation(signal)
            signal['options_recommendation'] = options_rec
        
        self.scan_results = signals
        self.logger.info(f"Groww scan completed. Found {len(signals)} signals.")
        
        return signals
    
    def scan_custom_symbols(self, symbols: List[str], period: str = "6mo") -> List[Dict]:
        """Scan custom list of stock symbols"""
        self.logger.info(f"Scanning {len(symbols)} custom symbols...")
        
        # Ensure symbols have .NS suffix for Indian stocks
        formatted_symbols = []
        for symbol in symbols:
            if not symbol.endswith('.NS'):
                symbol = symbol.replace('.NS', '') + '.NS'
            formatted_symbols.append(symbol)
        
        # Fetch data and generate signals
        stock_data = self.data_fetcher.get_multiple_stocks_data(formatted_symbols, period=period)
        signals = self.signal_generator.scan_multiple_stocks(stock_data)
        
        # Add metadata
        for signal in signals:
            signal['scan_time'] = datetime.now()
            signal['risk_level'] = self.risk_level
            signal['source'] = 'Custom Scan'
            
            # Get options recommendation
            options_rec = self.signal_generator.get_options_recommendation(signal)
            signal['options_recommendation'] = options_rec
        
        self.scan_results = signals
        self.logger.info(f"Custom scan completed. Found {len(signals)} signals.")
        
        return signals
    
    def start_continuous_scan(self, scan_type: str = "nifty50"):
        """Start continuous scanning in background"""
        if self.is_scanning:
            self.logger.warning("Scanner is already running")
            return
        
        self.is_scanning = True
        self.scan_thread = threading.Thread(
            target=self._continuous_scan_worker,
            args=(scan_type,),
            daemon=True
        )
        self.scan_thread.start()
        self.logger.info(f"Started continuous {scan_type} scanning")
    
    def stop_continuous_scan(self):
        """Stop continuous scanning"""
        self.is_scanning = False
        if self.scan_thread:
            self.scan_thread.join(timeout=10)
        self.logger.info("Stopped continuous scanning")
    
    def _continuous_scan_worker(self, scan_type: str):
        """Worker function for continuous scanning"""
        while self.is_scanning:
            try:
                if scan_type == "nifty50":
                    self.scan_nifty50_stocks()
                elif scan_type == "groww":
                    self.scan_groww_trending_stocks()
                else:
                    self.logger.error(f"Unknown scan type: {scan_type}")
                    break
                
                # Wait for next scan
                time.sleep(self.scan_interval)
                
            except Exception as e:
                self.logger.error(f"Error in continuous scan: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def get_latest_signals(self, limit: int = 10) -> List[Dict]:
        """Get latest trading signals"""
        return self.scan_results[:limit]
    
    def get_signal_by_symbol(self, symbol: str) -> Optional[Dict]:
        """Get signal for a specific symbol"""
        for signal in self.scan_results:
            if signal['symbol'] == symbol:
                return signal
        return None
    
    def filter_signals(self, 
                      action: Optional[str] = None,
                      min_confidence: Optional[float] = None,
                      max_results: Optional[int] = None) -> List[Dict]:
        """Filter signals based on criteria"""
        filtered = self.scan_results.copy()
        
        if action:
            filtered = [s for s in filtered if s.get('overall_action') == action.upper()]
        
        if min_confidence:
            filtered = [s for s in filtered if s.get('confidence', 0) >= min_confidence]
        
        # Sort by confidence
        filtered.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        if max_results:
            filtered = filtered[:max_results]
        
        return filtered
    
    def get_scan_summary(self) -> Dict:
        """Get summary of latest scan results"""
        if not self.scan_results:
            return {'total_signals': 0, 'message': 'No scan results available'}
        
        total_signals = len(self.scan_results)
        call_signals = len([s for s in self.scan_results if s.get('overall_action') == 'CALL'])
        put_signals = len([s for s in self.scan_results if s.get('overall_action') == 'PUT'])
        
        avg_confidence = np.mean([s.get('confidence', 0) for s in self.scan_results])
        
        summary = {
            'total_signals': total_signals,
            'call_signals': call_signals,
            'put_signals': put_signals,
            'avg_confidence': avg_confidence,
            'scan_time': self.scan_results[0].get('scan_time') if self.scan_results else None,
            'risk_level': self.risk_level
        }
        
        return summary
    
    def export_signals_to_csv(self, filename: str = None) -> str:
        """Export signals to CSV file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"trading_signals_{timestamp}.csv"
        
        # Prepare data for export
        export_data = []
        for signal in self.scan_results:
            row = {
                'symbol': signal.get('symbol'),
                'timestamp': signal.get('scan_time'),
                'current_price': signal.get('current_price'),
                'action': signal.get('overall_action'),
                'confidence': signal.get('confidence'),
                'signal_count': signal.get('signal_count'),
                'call_signals': signal.get('call_signals'),
                'put_signals': signal.get('put_signals'),
                'risk_level': signal.get('risk_level'),
                'source': signal.get('source', 'Unknown')
            }
            
            # Add options recommendation
            if 'options_recommendation' in signal:
                opt_rec = signal['options_recommendation']
                row.update({
                    'options_action': opt_rec.get('action'),
                    'suggested_expiry': opt_rec.get('suggested_expiry'),
                    'stop_loss': opt_rec.get('stop_loss'),
                    'target_price': opt_rec.get('target_price'),
                    'position_size': opt_rec.get('position_size')
                })
            
            export_data.append(row)
        
        # Create DataFrame and save
        df = pd.DataFrame(export_data)
        df.to_csv(filename, index=False)
        
        self.logger.info(f"Signals exported to {filename}")
        return filename
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_continuous_scan()
        if self.data_fetcher:
            self.data_fetcher.close_driver()
