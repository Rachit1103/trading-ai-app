import logging
import schedule
import time
from datetime import datetime
from stock_scanner import StockScanner
from notifications import NotificationSystem
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_ai.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class TradingBot:
    """Main trading bot that runs automated scans and sends notifications"""
    
    def __init__(self):
        self.scanner = StockScanner(risk_level=os.getenv('RISK_LEVEL', 'medium'))
        self.notification_system = NotificationSystem()
        self.is_running = False
        
    def run_scheduled_scan(self, scan_type: str = "nifty50"):
        """Run a scheduled scan and send notifications"""
        try:
            logger.info(f"Starting scheduled {scan_type} scan...")
            
            # Perform scan
            if scan_type == "nifty50":
                signals = self.scanner.scan_nifty50_stocks()
            elif scan_type == "groww":
                signals = self.scanner.scan_groww_trending_stocks()
            else:
                logger.error(f"Unknown scan type: {scan_type}")
                return
            
            # Send notifications for high-confidence signals
            high_confidence_signals = [s for s in signals if s['confidence'] >= 0.7]
            
            if high_confidence_signals:
                logger.info(f"Found {len(high_confidence_signals)} high-confidence signals")
                
                # Send individual alerts for top signals
                top_signals = sorted(high_confidence_signals, key=lambda x: x['confidence'], reverse=True)[:3]
                
                for signal in top_signals:
                    success = self.notification_system.send_signal_alert(signal)
                    if success:
                        logger.info(f"Alert sent for {signal['symbol']}")
                    else:
                        logger.error(f"Failed to send alert for {signal['symbol']}")
                
                # Send scan summary
                self.notification_system.send_scan_summary(signals)
                
            else:
                logger.info("No high-confidence signals found")
            
            # Export signals to CSV
            if signals:
                filename = self.scanner.export_signals_to_csv()
                logger.info(f"Signals exported to {filename}")
            
        except Exception as e:
            logger.error(f"Error in scheduled scan: {e}")
    
    def start_scheduled_scans(self):
        """Start the scheduled scanning system"""
        self.is_running = True
        
        # Schedule scans
        schedule.every(15).minutes.do(self.run_scheduled_scan, "nifty50")
        schedule.every(30).minutes.do(self.run_scheduled_scan, "groww")
        
        # Market hours check (9:15 AM to 3:30 PM IST)
        schedule.every().day.at("09:15").do(self.run_scheduled_scan, "nifty50")
        schedule.every().day.at("13:00").do(self.run_scheduled_scan, "nifty50")
        schedule.every().day.at("15:00").do(self.run_scheduled_scan, "nifty50")
        
        logger.info("Scheduled scans started")
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Stopping scheduled scans...")
            self.stop_scheduled_scans()
    
    def stop_scheduled_scans(self):
        """Stop the scheduled scanning system"""
        self.is_running = False
        schedule.clear()
        logger.info("Scheduled scans stopped")
    
    def test_system(self):
        """Test the complete system"""
        logger.info("Testing trading system...")
        
        # Test scanner
        try:
            signals = self.scanner.scan_nifty50_stocks()
            logger.info(f"Scanner test: Found {len(signals)} signals")
        except Exception as e:
            logger.error(f"Scanner test failed: {e}")
        
        # Test notifications
        try:
            results = self.notification_system.test_notifications()
            logger.info(f"Notification test results: {results}")
        except Exception as e:
            logger.error(f"Notification test failed: {e}")
        
        logger.info("System test completed")

if __name__ == "__main__":
    bot = TradingBot()
    
    # Run system test first
    bot.test_system()
    
    # Start scheduled scans
    try:
        bot.start_scheduled_scans()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        bot.scanner.cleanup()
