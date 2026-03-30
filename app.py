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

# Page configuration
st.set_page_config(
    page_title="Trading AI App - Options Signal Generator",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .signal-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        color: white;
    }
    .call-signal {
        border-left: 5px solid #00ff00;
        background-color: #f0fff0;
    }
    .put-signal {
        border-left: 5px solid #ff0000;
        background-color: #fff0f0;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
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
    # Header
    st.markdown('<h1 class="main-header">🤖 Trading AI App</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666;">Advanced Options Signal Generator with Technical Analysis</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Risk level selection
        risk_level = st.selectbox(
            "Risk Level",
            ["low", "medium", "high"],
            index=1,
            help="Select your risk tolerance level"
        )
        
        # Update scanner risk level
        if st.session_state.scanner.risk_level != risk_level:
            st.session_state.scanner.risk_level = risk_level
            st.session_state.scanner.signal_generator.risk_level = risk_level
            st.session_state.scanner.signal_generator.risk_thresholds = \
                st.session_state.scanner.signal_generator._set_risk_thresholds(risk_level)
        
        # Scan interval for continuous scanning
        scan_interval = st.slider(
            "Scan Interval (seconds)",
            min_value=60,
            max_value=3600,
            value=300,
            step=60,
            help="Interval between automatic scans"
        )
        
        st.session_state.scanner.scan_interval = scan_interval
        
        st.markdown("---")
        
        # Scan controls
        st.header("🔍 Scan Controls")
        
        # Scan type selection
        scan_type = st.selectbox(
            "Scan Type",
            ["nifty50", "groww_trending", "custom", "ultra_accuracy"],
            help="Choose what to scan"
        )
        
        # Ultra-high accuracy mode
        if scan_type == "ultra_accuracy":
            st.markdown("**🎯 Ultra-High Accuracy Mode**")
            st.markdown("*Uses ML ensemble + technical analysis for maximum accuracy*")
            
            # Training data period
            training_period = st.selectbox(
                "Training Data Period",
                ["1y", "2y", "3y"],
                index=1,
                help="Historical data period for ML model training"
            )
        
        # Custom symbols input
        custom_symbols = []
        if scan_type == "custom":
            symbols_input = st.text_area(
                "Enter stock symbols (one per line)",
                placeholder="RELIANCE\nTCS\nHDFCBANK",
                height=100
            )
            if symbols_input:
                custom_symbols = [s.strip().upper() for s in symbols_input.split('\n') if s.strip()]
        
        # Scan buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 Start Scan", type="primary", use_container_width=True):
                run_scan(scan_type, custom_symbols)
        
        with col2:
            if st.button("🔄 Continuous Scan", use_container_width=True):
                toggle_continuous_scan(scan_type)
        
        st.markdown("---")
        
        # Backtesting controls
        st.header("📊 Backtesting")
        
        if st.button("🔬 Run Backtest", use_container_width=True):
            run_backtest()
        
        st.markdown("---")
        
        # Export options
        st.header("📊 Export")
        if st.button("📥 Export to CSV", use_container_width=True):
            export_signals()
        
        st.markdown("---")
        
        # Last scan info
        if st.session_state.last_scan_time:
            st.info(f"Last scan: {st.session_state.last_scan_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Main content area
    if st.session_state.signals:
        display_signals()
    else:
        display_welcome()
    
    # Footer
    st.markdown("---")
    st.markdown(
        '<p style="text-align: center; color: #999; font-size: 0.8rem;">'
        '⚠️ Disclaimer: This app is for educational purposes only. Trading involves risk. '
        'Always do your own research before making investment decisions.'
        '</p>',
        unsafe_allow_html=True
    )

def run_scan(scan_type: str, custom_symbols: list = None, training_period: str = "2y"):
    """Run a scan based on the selected type"""
    with st.spinner("Scanning stocks... Please wait"):
        try:
            if scan_type == "nifty50":
                signals = st.session_state.scanner.scan_nifty50_stocks()
            elif scan_type == "groww_trending":
                signals = st.session_state.scanner.scan_groww_trending_stocks()
            elif scan_type == "custom" and custom_symbols:
                signals = st.session_state.scanner.scan_custom_symbols(custom_symbols)
            elif scan_type == "ultra_accuracy":
                signals = run_ultra_accuracy_scan(training_period)
            else:
                st.error("Please enter valid stock symbols for custom scan")
                return
            
            st.session_state.signals = signals
            st.session_state.last_scan_time = datetime.now()
            
            if signals:
                st.success(f"Scan completed! Found {len(signals)} trading signals")
            else:
                st.warning("No trading signals found")
                
        except Exception as e:
            st.error(f"Error during scan: {str(e)}")
            logger.error(f"Scan error: {e}")

def run_ultra_accuracy_scan(training_period: str) -> List[Dict]:
    """Run ultra-high accuracy scan with ML models"""
    st.info("🧠 Training ML models for ultra-high accuracy...")
    
    # Get Nifty 50 symbols
    symbols = st.session_state.scanner.data_fetcher.get_nifty50_stocks()
    
    # Limit to top 20 for faster processing
    symbols = symbols[:20]
    
    all_signals = []
    
    for symbol in symbols:
        try:
            # Fetch historical data
            data = st.session_state.scanner.data_fetcher.get_yfinance_data(symbol, period=training_period)
            
            if not data.empty and len(data) > 200:
                # Train ML models for this symbol
                training_results = st.session_state.enhanced_generator.train_ml_models(data)
                
                # Generate ultra-accuracy signal
                signal = st.session_state.enhanced_generator.generate_ultra_accuracy_signal(data, symbol)
                
                if signal['action'] != 'HOLD' and signal['confidence'] > 0.85:
                    all_signals.append(signal)
                    
        except Exception as e:
            logger.error(f"Error in ultra-accuracy scan for {symbol}: {e}")
    
    # Sort by confidence
    all_signals.sort(key=lambda x: x['confidence'], reverse=True)
    
    return all_signals[:5]  # Return top 5 signals

def run_backtest():
    """Run comprehensive backtesting"""
    with st.spinner("Running comprehensive backtesting... This may take several minutes"):
        try:
            # Get sample symbols for backtesting
            symbols = st.session_state.scanner.data_fetcher.get_nifty50_stocks()[:10]
            
            # Define backtest period
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            
            # Run backtest
            results = st.session_state.backtester.run_comprehensive_backtest(
                symbols, start_date, end_date, 'ultra_accuracy'
            )
            
            if results:
                st.success("Backtesting completed successfully!")
                
                # Display results
                st.subheader("📊 Backtest Results")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Avg Return", f"{results['avg_total_return']:.2%}")
                with col2:
                    st.metric("Sharpe Ratio", f"{results['avg_sharpe_ratio']:.3f}")
                with col3:
                    st.metric("Win Rate", f"{results['avg_win_rate']:.2%}")
                with col4:
                    st.metric("Profitability", f"{results['profitability_rate']:.2%}")
                
                # Generate and display report
                report = st.session_state.backtester.generate_performance_report('ultra_accuracy')
                st.markdown(report)
                
            else:
                st.error("Backtesting failed or no results available")
                
        except Exception as e:
            st.error(f"Error during backtesting: {str(e)}")
            logger.error(f"Backtest error: {e}")

def toggle_continuous_scan(scan_type: str):
    """Toggle continuous scanning"""
    if st.session_state.scanner.is_scanning:
        st.session_state.scanner.stop_continuous_scan()
        st.info("Continuous scanning stopped")
    else:
        st.session_state.scanner.start_continuous_scan(scan_type)
        st.success("Continuous scanning started")

def display_signals():
    """Display the trading signals"""
    signals = st.session_state.signals
    
    # Summary metrics
    st.header("📊 Scan Summary")
    summary = st.session_state.scanner.get_scan_summary()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Signals", summary['total_signals'])
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("CALL Signals", summary['call_signals'], delta="📈")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("PUT Signals", summary['put_signals'], delta="📉")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Avg Confidence", f"{summary['avg_confidence']:.2%}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Signals table
    st.header("🎯 Trading Signals")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        action_filter = st.selectbox("Filter by Action", ["All", "CALL", "PUT"])
    
    with col2:
        confidence_filter = st.slider("Min Confidence", 0.0, 1.0, 0.5, 0.1)
    
    with col3:
        max_results = st.number_input("Max Results", min_value=1, max_value=50, value=10)
    
    # Apply filters
    filtered_signals = st.session_state.scanner.filter_signals(
        action=action_filter if action_filter != "All" else None,
        min_confidence=confidence_filter,
        max_results=max_results
    )
    
    if filtered_signals:
        # Display signals as cards
        for signal in filtered_signals:
            display_signal_card(signal)
        
        # Detailed table
        st.subheader("Detailed Analysis")
        
        # Prepare data for table
        table_data = []
        for signal in filtered_signals:
            row = {
                'Symbol': signal['symbol'],
                'Price': f"₹{signal['current_price']:.2f}",
                'Action': signal['overall_action'],
                'Confidence': f"{signal['confidence']:.2%}",
                'Signals': signal['signal_count'],
                'Expiry': signal.get('options_recommendation', {}).get('suggested_expiry', 'N/A'),
                'Stop Loss': f"₹{signal.get('options_recommendation', {}).get('stop_loss', 0):.2f}",
                'Target': f"₹{signal.get('options_recommendation', {}).get('target_price', 0):.2f}"
            }
            table_data.append(row)
        
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True)
        
        # Charts
        if len(filtered_signals) > 1:
            display_charts(filtered_signals)
    
    else:
        st.info("No signals match the selected filters")

def display_signal_card(signal: dict):
    """Display a single trading signal as a card"""
    action = signal['overall_action']
    card_class = "call-signal" if action == "CALL" else "put-signal"
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f'<div class="signal-card {card_class}">', unsafe_allow_html=True)
        
        # Header
        symbol_col, action_col = st.columns([2, 1])
        with symbol_col:
            st.markdown(f"### {signal['symbol']}")
        with action_col:
            st.markdown(f"<h4 style='color: {'green' if action == 'CALL' else 'red'}; text-align: right;'>{action}</h4>", unsafe_allow_html=True)
        
        # Key metrics
        price_col, conf_col = st.columns(2)
        with price_col:
            st.metric("Current Price", f"₹{signal['current_price']:.2f}")
        with conf_col:
            st.metric("Confidence", f"{signal['confidence']:.2%}")
        
        # Signal details
        st.markdown(f"**Signal Count:** {signal['signal_count']} (CALL: {signal['call_signals']}, PUT: {signal['put_signals']})")
        
        # Options recommendation
        if 'options_recommendation' in signal:
            opt_rec = signal['options_recommendation']
            st.markdown("**Options Recommendation:**")
            st.markdown(f"- **Expiry:** {opt_rec.get('suggested_expiry', 'N/A')}")
            st.markdown(f"- **Strike Prices:** {', '.join(opt_rec.get('strike_prices', []))}")
            st.markdown(f"- **Stop Loss:** ₹{opt_rec.get('stop_loss', 0):.2f}")
            st.markdown(f"- **Target:** ₹{opt_rec.get('target_price', 0):.2f}")
            st.markdown(f"- **Position Size:** {opt_rec.get('position_size', 'N/A')}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # Mini chart placeholder
        st.info("📈 Chart\n(Click 'Analyze' for detailed chart)")
        
        if st.button(f"Analyze {signal['symbol']}", key=f"analyze_{signal['symbol']}"):
            show_detailed_analysis(signal)

def display_charts(signals: list):
    """Display charts and visualizations"""
    st.subheader("📈 Visualizations")
    
    # Confidence distribution
    col1, col2 = st.columns(2)
    
    with col1:
        fig_confidence = px.histogram(
            [s['confidence'] for s in signals],
            nbins=10,
            title="Confidence Distribution",
            labels={'value': 'Confidence', 'count': 'Number of Signals'}
        )
        st.plotly_chart(fig_confidence, use_container_width=True)
    
    with col2:
        # Action distribution
        actions = [s['overall_action'] for s in signals]
        action_counts = pd.Series(actions).value_counts()
        
        fig_pie = px.pie(
            values=action_counts.values,
            names=action_counts.index,
            title="Signal Distribution"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Signal strength vs price
    fig_scatter = px.scatter(
        x=[s['current_price'] for s in signals],
        y=[s['confidence'] for s in signals],
        color=[s['overall_action'] for s in signals],
        size=[s['signal_count'] for s in signals],
        hover_name=[s['symbol'] for s in signals],
        title="Signal Strength vs Stock Price",
        labels={'x': 'Stock Price', 'y': 'Confidence', 'color': 'Action'}
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

def show_detailed_analysis(signal: dict):
    """Show detailed technical analysis for a stock"""
    st.subheader(f"🔍 Detailed Analysis: {signal['symbol']}")
    
    try:
        # Fetch historical data
        data_fetcher = StockDataFetcher()
        data = data_fetcher.get_yfinance_data(signal['symbol'], period="3mo")
        
        if not data.empty:
            # Create candlestick chart
            fig = make_subplots(
                rows=3, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.1,
                subplot_titles=('Price', 'RSI', 'MACD'),
                row_width=[0.2, 0.2, 0.7]
            )
            
            # Candlestick chart
            fig.add_trace(
                go.Candlestick(
                    x=data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'],
                    name='Price'
                ),
                row=1, col=1
            )
            
            # RSI
            from indicators import TechnicalIndicators
            indicators = TechnicalIndicators()
            rsi = indicators.calculate_rsi(data['Close'])
            
            fig.add_trace(
                go.Scatter(x=data.index, y=rsi, name='RSI', line=dict(color='purple')),
                row=2, col=1
            )
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
            
            # MACD
            macd_data = indicators.calculate_macd(data['Close'])
            fig.add_trace(
                go.Scatter(x=data.index, y=macd_data['macd'], name='MACD', line=dict(color='blue')),
                row=3, col=1
            )
            fig.add_trace(
                go.Scatter(x=data.index, y=macd_data['signal'], name='Signal', line=dict(color='red')),
                row=3, col=1
            )
            
            fig.update_layout(height=800, title_text=f"Technical Analysis - {signal['symbol']}")
            st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.error("Could not fetch historical data for detailed analysis")
            
    except Exception as e:
        st.error(f"Error in detailed analysis: {str(e)}")

def display_welcome():
    """Display welcome message when no signals are available"""
    st.markdown("""
    <div style="text-align: center; padding: 3rem;">
        <h2>👋 Welcome to Trading AI App</h2>
        <p style="font-size: 1.2rem; color: #666; margin: 2rem 0;">
            Start by selecting your scan preferences and clicking "Start Scan" in the sidebar.
        </p>
        <div style="background: #f0f2f6; padding: 2rem; border-radius: 10px; margin: 2rem 0;">
            <h3>🚀 Features:</h3>
            <ul style="text-align: left; max-width: 600px; margin: 0 auto;">
                <li>📊 Multi-indicator analysis (RSI, MACD, Bollinger Bands, and more)</li>
                <li>🎯 CALL/PUT signal generation for options trading</li>
                <li>🔄 Integration with Groww app for trending stocks</li>
                <li>⚡ Real-time scanning with customizable intervals</li>
                <li>📈 Detailed technical analysis and charts</li>
                <li>📥 Export signals to CSV for further analysis</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)

def export_signals():
    """Export signals to CSV"""
    try:
        filename = st.session_state.scanner.export_signals_to_csv()
        st.success(f"Signals exported to {filename}")
    except Exception as e:
        st.error(f"Error exporting signals: {str(e)}")

if __name__ == "__main__":
    main()
