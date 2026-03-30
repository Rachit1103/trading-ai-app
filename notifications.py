import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class NotificationSystem:
    """Class to handle various notification methods for trading signals"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Email configuration
        self.email_enabled = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_username = os.getenv('EMAIL_USERNAME')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.email_recipient = os.getenv('EMAIL_RECIPIENT')
        
        # Telegram configuration
        self.telegram_enabled = os.getenv('TELEGRAM_ENABLED', 'false').lower() == 'true'
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        # Webhook configuration
        self.webhook_enabled = os.getenv('WEBHOOK_ENABLED', 'false').lower() == 'true'
        self.webhook_url = os.getenv('WEBHOOK_URL')
    
    def send_signal_alert(self, signal: Dict, notification_types: List[str] = None) -> bool:
        """Send trading signal alert through specified notification channels"""
        if notification_types is None:
            notification_types = ['telegram'] if self.telegram_enabled else ['email']
        
        success = True
        
        for notification_type in notification_types:
            try:
                if notification_type == 'email' and self.email_enabled:
                    success &= self._send_email_alert(signal)
                elif notification_type == 'telegram' and self.telegram_enabled:
                    success &= self._send_telegram_alert(signal)
                elif notification_type == 'webhook' and self.webhook_enabled:
                    success &= self._send_webhook_alert(signal)
                else:
                    self.logger.warning(f"Notification type {notification_type} not configured")
                    success &= False
                    
            except Exception as e:
                self.logger.error(f"Error sending {notification_type} alert: {e}")
                success &= False
        
        return success
    
    def _send_email_alert(self, signal: Dict) -> bool:
        """Send email alert for trading signal"""
        try:
            subject = f"🚀 Trading Signal: {signal['overall_action']} for {signal['symbol']}"
            
            # Create email content
            body = self._format_email_body(signal)
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_username
            msg['To'] = self.email_recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_username, self.email_password)
            text = msg.as_string()
            server.sendmail(self.email_username, self.email_recipient, text)
            server.quit()
            
            self.logger.info(f"Email alert sent for {signal['symbol']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
            return False
    
    def _send_telegram_alert(self, signal: Dict) -> bool:
        """Send Telegram alert for trading signal"""
        try:
            message = self._format_telegram_message(signal)
            
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            
            payload = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            self.logger.info(f"Telegram alert sent for {signal['symbol']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send Telegram alert: {e}")
            return False
    
    def _send_webhook_alert(self, signal: Dict) -> bool:
        """Send webhook alert for trading signal"""
        try:
            payload = {
                'event': 'trading_signal',
                'timestamp': datetime.now().isoformat(),
                'signal': signal
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            self.logger.info(f"Webhook alert sent for {signal['symbol']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send webhook alert: {e}")
            return False
    
    def _format_email_body(self, signal: Dict) -> str:
        """Format email body for trading signal"""
        action = signal['overall_action']
        action_color = 'green' if action == 'CALL' else 'red'
        action_icon = '📈' if action == 'CALL' else '📉'
        
        # Options recommendation
        opt_rec = signal.get('options_recommendation', {})
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #333; margin: 0;">{action_icon} Trading Signal Alert</h1>
                    <p style="color: #666; margin: 5px 0;">Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h2 style="color: {action_color}; margin: 0 0 10px 0;">{action} Signal - {signal['symbol']}</h2>
                    <p style="margin: 5px 0;"><strong>Current Price:</strong> ₹{signal['current_price']:.2f}</p>
                    <p style="margin: 5px 0;"><strong>Confidence:</strong> {signal['confidence']:.2%}</p>
                    <p style="margin: 5px 0;"><strong>Signal Count:</strong> {signal['signal_count']} (CALL: {signal['call_signals']}, PUT: {signal['put_signals']})</p>
                </div>
                
                <div style="background-color: #e3f2fd; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="color: #1976d2; margin: 0 0 10px 0;">📊 Options Recommendation</h3>
                    <p style="margin: 5px 0;"><strong>Expiry:</strong> {opt_rec.get('suggested_expiry', 'N/A')}</p>
                    <p style="margin: 5px 0;"><strong>Strike Prices:</strong> {', '.join(opt_rec.get('strike_prices', []))}</p>
                    <p style="margin: 5px 0;"><strong>Stop Loss:</strong> ₹{opt_rec.get('stop_loss', 0):.2f}</p>
                    <p style="margin: 5px 0;"><strong>Target Price:</strong> ₹{opt_rec.get('target_price', 0):.2f}</p>
                    <p style="margin: 5px 0;"><strong>Position Size:</strong> {opt_rec.get('position_size', 'N/A')}</p>
                </div>
                
                <div style="background-color: #fff3e0; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="color: #f57c00; margin: 0 0 10px 0;">🔍 Technical Indicators</h3>
        """
        
        # Add individual signal details
        for sig in signal.get('signals', []):
            body += f"""
                    <p style="margin: 5px 0;"><strong>{sig['indicator']}:</strong> {sig['reason']} (Confidence: {sig['confidence']:.2%})</p>
            """
        
        body += """
                </div>
                
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                    <p style="color: #999; font-size: 0.9em; margin: 0;">
                        ⚠️ Disclaimer: This signal is generated by AI and should not be considered as financial advice. 
                        Always do your own research before making investment decisions.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return body
    
    def _format_telegram_message(self, signal: Dict) -> str:
        """Format Telegram message for trading signal"""
        action = signal['overall_action']
        action_icon = '📈' if action == 'CALL' else '📉'
        
        # Options recommendation
        opt_rec = signal.get('options_recommendation', {})
        
        message = f"""
{action_icon} <b>Trading Signal Alert</b>

<b>{action} Signal - {signal['symbol']}</b>
🔸 Current Price: ₹{signal['current_price']:.2f}
🔸 Confidence: {signal['confidence']:.2%}
🔸 Signal Count: {signal['signal_count']} (CALL: {signal['call_signals']}, PUT: {signal['put_signals']})

<b>📊 Options Recommendation</b>
🔸 Expiry: {opt_rec.get('suggested_expiry', 'N/A')}
🔸 Strike Prices: {', '.join(opt_rec.get('strike_prices', []))}
🔸 Stop Loss: ₹{opt_rec.get('stop_loss', 0):.2f}
🔸 Target: ₹{opt_rec.get('target_price', 0):.2f}
🔸 Position Size: {opt_rec.get('position_size', 'N/A')}

<b>🔍 Key Indicators</b>
        """
        
        # Add top 3 signals
        top_signals = sorted(signal.get('signals', []), key=lambda x: x['confidence'], reverse=True)[:3]
        for sig in top_signals:
            message += f"\n🔸 {sig['indicator']}: {sig['reason']}"
        
        message += f"\n\n⏰ Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        message += "\n\n⚠️ <i>Disclaimer: AI-generated signal. Do your own research.</i>"
        
        return message
    
    def send_scan_summary(self, signals: List[Dict]) -> bool:
        """Send summary of scan results"""
        if not signals:
            return True
        
        try:
            summary = {
                'total_signals': len(signals),
                'call_signals': len([s for s in signals if s['overall_action'] == 'CALL']),
                'put_signals': len([s for s in signals if s['overall_action'] == 'PUT']),
                'avg_confidence': sum(s['confidence'] for s in signals) / len(signals),
                'timestamp': datetime.now().isoformat()
            }
            
            # Send summary via Telegram if enabled
            if self.telegram_enabled:
                message = f"""
📊 <b>Scan Summary</b>

🔸 Total Signals: {summary['total_signals']}
🔸 CALL Signals: {summary['call_signals']}
🔸 PUT Signals: {summary['put_signals']}
🔸 Average Confidence: {summary['avg_confidence']:.2%}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """
                
                url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
                payload = {
                    'chat_id': self.telegram_chat_id,
                    'text': message,
                    'parse_mode': 'HTML'
                }
                
                response = requests.post(url, json=payload, timeout=10)
                response.raise_for_status()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send scan summary: {e}")
            return False
    
    def test_notifications(self) -> Dict[str, bool]:
        """Test all notification systems"""
        results = {}
        
        # Test signal for testing
        test_signal = {
            'symbol': 'TEST',
            'overall_action': 'CALL',
            'current_price': 1000.0,
            'confidence': 0.75,
            'signal_count': 3,
            'call_signals': 2,
            'put_signals': 1,
            'signals': [
                {'indicator': 'RSI', 'reason': 'RSI oversold', 'confidence': 0.8},
                {'indicator': 'MACD', 'reason': 'MACD bullish crossover', 'confidence': 0.7}
            ],
            'options_recommendation': {
                'suggested_expiry': '2024-01-25',
                'strike_prices': ['1050', '1100', '1150'],
                'stop_loss': 950.0,
                'target_price': 1100.0,
                'position_size': 'MEDIUM'
            }
        }
        
        # Test email
        if self.email_enabled:
            results['email'] = self._send_email_alert(test_signal)
        else:
            results['email'] = False
        
        # Test Telegram
        if self.telegram_enabled:
            results['telegram'] = self._send_telegram_alert(test_signal)
        else:
            results['telegram'] = False
        
        # Test webhook
        if self.webhook_enabled:
            results['webhook'] = self._send_webhook_alert(test_signal)
        else:
            results['webhook'] = False
        
        return results
