# Trading AI App for Options

An AI-powered trading application that generates buy/sell signals for options trading using technical indicators and integrates with the Groww app for stock data.

## Features

- **Multi-Indicator Analysis**: Uses RSI, MACD, Bollinger Bands, Moving Averages, and more
- **Options Signal Generation**: Generates call/put signals based on technical analysis
- **Groww Integration**: Scans stocks from the Groww app
- **Real-time Alerts**: Sends trading signals via notifications
- **Web Interface**: User-friendly dashboard for viewing signals and analysis

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Set up your configuration in `.env` file
2. Run the main application:
   ```bash
   streamlit run app.py
   ```

## Configuration

Create a `.env` file with the following variables:
- `GROWW_USERNAME`: Your Groww username
- `GROWW_PASSWORD`: Your Groww password
- `TELEGRAM_BOT_TOKEN`: Optional, for Telegram notifications

## Disclaimer

This app is for educational purposes only. Trading stocks and options involves risk. Always do your own research before making investment decisions.
