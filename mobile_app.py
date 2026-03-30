import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime, timedelta
import time
import logging
from typing import List, Dict
from stock_scanner import StockScanner
from data_fetcher import StockDataFetcher
from signal_generator import SignalGenerator
from enhanced_signal_generator import UltraHighAccuracySignalGenerator
from backtester import ComprehensiveBacktester

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mobile-optimized configuration
st.set_page_config(
    page_title="Trading AI Mobile",
    page_icon="📱",
    layout="centered",  # Better for mobile
    initial_sidebar_state="collapsed"  # Mobile-friendly
)

# Mobile-responsive CSS
st.markdown("""
<style>
    .mobile-header {
        font-size: 1.8rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .mobile-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        color: white;
    }
    .mobile-metric {
        background: white;
        padding: 0.8rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        margin: 0.5rem 0;
    }
    @media (max-width: 768px) {
        .stButton > button {
            width: 100%;
            margin: 0.5rem 0;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'scanner' not in st.session_state:
    st.session_state.scanner = StockScanner()
if 'enhanced_generator' not in st.session_state:
    st.session_state.enhanced_generator = UltraHighAccuracySignalGenerator()
if 'backtester' not in st.session_state:
    st.session_state.backtester = ComprehensiveBacktester()
if 'signals' not in st.session_state:
    st.session_state.signals = []
if 'last_scan_time' not in st.session_state:
    st.session_state.last_scan_time = None

def main():
    # Mobile-optimized header
    st.markdown('<h1 class="mobile-header">📱 Trading AI Mobile</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666;">Ultra-High Accuracy Trading Signals</p>', unsafe_allow_html=True)
    
    # Quick action buttons for mobile
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 Quick Scan", type="primary", use_container_width=True):
            run_quick_scan()
    
    with col2:
        if st.button("🎯 Ultra Accuracy", use_container_width=True):
            run_ultra_accuracy_scan()
    
    # Mobile settings (expandable)
    with st.expander("⚙️ Settings", expanded=False):
        risk_level = st.selectbox(
            "Risk Level",
            ["low", "medium", "high"],
            index=1,
            help="Select your risk tolerance level"
        )
        
        if st.session_state.enhanced_generator.risk_level != risk_level:
            st.session_state.enhanced_generator.risk_level = risk_level
    
    # Display signals in mobile-friendly format
    if st.session_state.signals:
        display_mobile_signals()
    else:
        display_mobile_welcome()
    
    # Performance summary (compact)
    if st.session_state.signals:
        display_mobile_performance()

def run_quick_scan():
    """Quick scan for mobile users"""
    with st.spinner("Quick scanning..."):
        try:
            # Get top 10 Nifty 50 stocks for faster processing
            symbols = st.session_state.scanner.data_fetcher.get_nifty50_stocks()[:10]
            signals = st.session_state.scanner.scan_custom_symbols(symbols)
            
            st.session_state.signals = signals[:3]  # Show top 3 for mobile
            st.session_state.last_scan_time = datetime.now()
            
            if signals:
                st.success(f"Found {len(signals)} signals!")
            else:
                st.warning("No signals found")
                
        except Exception as e:
            st.error(f"Scan error: {str(e)}")

def run_ultra_accuracy_scan():
    """Ultra-accuracy scan for mobile"""
    with st.spinner("Ultra-accuracy scan... This may take 2-3 minutes"):
        try:
            # Get top 5 stocks for mobile (faster processing)
            symbols = st.session_state.scanner.data_fetcher.get_nifty50_stocks()[:5]
            all_signals = []
            
            for symbol in symbols:
                try:
                    data = st.session_state.scanner.data_fetcher.get_yfinance_data(symbol, period="1y")
                    
                    if not data.empty and len(data) > 200:
                        # Quick training (reduced for mobile)
                        training_results = st.session_state.enhanced_generator.train_ml_models(data)
                        signal = st.session_state.enhanced_generator.generate_ultra_accuracy_signal(data, symbol)
                        
                        if signal['action'] != 'HOLD' and signal['confidence'] > 0.85:
                            all_signals.append(signal)
                except:
                    continue
            
            # Sort by confidence
            all_signals.sort(key=lambda x: x['confidence'], reverse=True)
            st.session_state.signals = all_signals[:2]  # Show top 2 for mobile
            st.session_state.last_scan_time = datetime.now()
            
            if all_signals:
                st.success(f"Found {len(all_signals)} ultra-accuracy signals!")
            else:
                st.warning("No high-confidence signals found")
                
        except Exception as e:
            st.error(f"Ultra-accuracy scan error: {str(e)}")

def display_mobile_signals():
    """Display signals in mobile-friendly format"""
    st.subheader("🎯 Trading Signals")
    
    for signal in st.session_state.signals:
        # Mobile card layout
        action = signal.get('action', signal.get('overall_action', 'HOLD'))
        confidence = signal.get('confidence', 0)
        
        # Color coding
        if action == 'CALL':
            bg_color = 'linear-gradient(135deg, #00ff00 0%, #00cc00 100%)'
        elif action == 'PUT':
            bg_color = 'linear-gradient(135deg, #ff0000 0%, #cc0000 100%)'
        else:
            bg_color = 'linear-gradient(135deg, #888888 0%, #666666 100%)'
        
        st.markdown(f'''
        <div class="mobile-card" style="background: {bg_color};">
            <h3>{signal['symbol']} - {action}</h3>
            <p><strong>Confidence:</strong> {confidence:.1%}</p>
            <p><strong>Price:</strong> ₹{signal.get('current_price', signal.get('current_price', 0)):.2f}</p>
        </div>
        ''', unsafe_allow_html=True)
        
        # Options recommendation (if available)
        if 'options_recommendation' in signal:
            opt_rec = signal['options_recommendation']
            st.markdown(f'''
            <div style="background: #f0f2f6; padding: 0.8rem; border-radius: 8px; margin: 0.5rem 0;">
                <p><strong>📊 Options:</strong></p>
                <p>• Target: ₹{opt_rec.get('target_price', 0):.2f}</p>
                <p>• Stop Loss: ₹{opt_rec.get('stop_loss', 0):.2f}</p>
                <p>• Position: {opt_rec.get('position_size', 'N/A')}</p>
            </div>
            ''', unsafe_allow_html=True)

def display_mobile_welcome():
    """Mobile-friendly welcome screen"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h2>📱 Welcome to Trading AI Mobile</h2>
        <p style="font-size: 1.1rem; color: #666; margin: 2rem 0;">
            Get ultra-high accuracy trading signals on your mobile!
        </p>
        
        <div style="background: #f0f2f6; padding: 1.5rem; border-radius: 10px; margin: 2rem 0;">
            <h3>🚀 Quick Start:</h3>
            <ol style="text-align: left; max-width: 300px; margin: 0 auto;">
                <li>Tap "Quick Scan" for fast signals</li>
                <li>Try "Ultra Accuracy" for ML-powered analysis</li>
                <li>Review signals and options recommendations</li>
                <li>Adjust risk settings as needed</li>
            </ol>
        </div>
        
        <div style="background: #fff3e0; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
            <p style="color: #f57c00; font-size: 0.9rem; margin: 0;">
                ⚠️ Trading involves risk. Always do your own research.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_mobile_performance():
    """Compact performance summary for mobile"""
    st.subheader("📊 Performance")
    
    # Calculate metrics
    total_signals = len(st.session_state.signals)
    call_signals = len([s for s in st.session_state.signals if s.get('action', s.get('overall_action', 'HOLD')) == 'CALL'])
    put_signals = len([s for s in st.session_state.signals if s.get('action', s.get('overall_action', 'HOLD')) == 'PUT'])
    avg_confidence = sum(s.get('confidence', 0) for s in st.session_state.signals) / total_signals if total_signals > 0 else 0
    
    # Mobile metrics grid
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f'''
        <div class="mobile-metric">
            <h4>{total_signals}</h4>
            <p>Total Signals</p>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown(f'''
        <div class="mobile-metric">
            <h4>{call_signals}</h4>
            <p>CALL Signals</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'''
        <div class="mobile-metric">
            <h4>{put_signals}</h4>
            <p>PUT Signals</p>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown(f'''
        <div class="mobile-metric">
            <h4>{avg_confidence:.1%}</h4>
            <p>Avg Confidence</p>
        </div>
        ''', unsafe_allow_html=True)
    
    # Last scan time
    if st.session_state.last_scan_time:
        st.info(f"Last scan: {st.session_state.last_scan_time.strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()
