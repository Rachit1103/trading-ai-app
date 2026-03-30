import yfinance as yf
import pandas as pd
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

class StockDataFetcher:
    """Class to fetch stock data from various sources including Groww integration"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.driver = None
        
    def setup_selenium_driver(self):
        """Setup Chrome WebDriver for Groww scraping"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
    def get_yfinance_data(self, symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        """Fetch stock data using yfinance"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            return data
        except Exception as e:
            self.logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_groww_trending_stocks(self) -> List[Dict]:
        """Scrape trending stocks from Groww website"""
        if not self.driver:
            self.setup_selenium_driver()
        
        try:
            self.driver.get("https://groww.in/stocks/explore/trending")
            time.sleep(3)
            
            # Wait for the table to load
            wait = WebDriverWait(self.driver, 10)
            table = wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            
            stocks = []
            rows = table.find_elements(By.TAG_NAME, "tr")
            
            for row in rows[1:]:  # Skip header
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) >= 4:
                    stock_data = {
                        'symbol': cols[0].text.strip(),
                        'name': cols[1].text.strip(),
                        'price': float(cols[2].text.replace('₹', '').replace(',', '').strip()),
                        'change': cols[3].text.strip()
                    }
                    stocks.append(stock_data)
            
            return stocks
            
        except Exception as e:
            self.logger.error(f"Error scraping Groww trending stocks: {e}")
            return []
    
    def get_groww_stock_details(self, symbol: str) -> Dict:
        """Get detailed stock information from Groww"""
        if not self.driver:
            self.setup_selenium_driver()
        
        try:
            url = f"https://groww.in/stocks/{symbol.lower()}"
            self.driver.get(url)
            time.sleep(3)
            
            stock_info = {
                'symbol': symbol,
                'name': '',
                'price': 0,
                'change': 0,
                'volume': 0,
                'market_cap': 0,
                'pe_ratio': 0
            }
            
            # Extract basic information
            try:
                name_element = self.driver.find_element(By.CLASS_NAME, "stock-name")
                stock_info['name'] = name_element.text.strip()
            except:
                pass
            
            try:
                price_element = self.driver.find_element(By.CLASS_NAME, "current-price")
                stock_info['price'] = float(price_element.text.replace('₹', '').replace(',', '').strip())
            except:
                pass
            
            # Extract additional details
            details_elements = self.driver.find_elements(By.CLASS_NAME, "stock-detail")
            for element in details_elements:
                text = element.text.strip()
                if 'Volume' in text:
                    stock_info['volume'] = self._parse_number(text.split(':')[-1].strip())
                elif 'Market Cap' in text:
                    stock_info['market_cap'] = self._parse_number(text.split(':')[-1].strip())
                elif 'P/E' in text:
                    stock_info['pe_ratio'] = self._parse_number(text.split(':')[-1].strip())
            
            return stock_info
            
        except Exception as e:
            self.logger.error(f"Error fetching details for {symbol}: {e}")
            return {}
    
    def _parse_number(self, text: str) -> float:
        """Parse number from text with suffixes like Cr, Lakhs"""
        try:
            text = text.replace('₹', '').replace(',', '').strip()
            
            if 'Cr' in text:
                return float(text.replace('Cr', '').strip()) * 10000000
            elif 'Lakhs' in text:
                return float(text.replace('Lakhs', '').strip()) * 100000
            elif 'K' in text:
                return float(text.replace('K', '').strip()) * 1000
            else:
                return float(text)
        except:
            return 0
    
    def get_nifty50_stocks(self) -> List[str]:
        """Get list of Nifty 50 stock symbols"""
        nifty50_stocks = [
            "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
            "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS", "ITC.NS",
            "AXISBANK.NS", "DMART.NS", "ASIANPAINT.NS", "M&M.NS", "HCLTECH.NS",
            "TATAMOTORS.NS", "SUNPHARMA.NS", "BAJFINANCE.NS", "MARUTI.NS", "WIPRO.NS",
            "NESTLEIND.NS", "POWERGRID.NS", "NTPC.NS", "ULTRACEMCO.NS", "GRASIM.NS",
            "TECHM.NS", "TITAN.NS", "COALINDIA.NS", "JSWSTEEL.NS", "BPCL.NS",
            "ONGC.NS", "ADANIPORTS.NS", "TATASTEEL.NS", "DRREDDY.NS", "CIPLA.NS",
            "HEROMOTOCO.NS", "DIVISLAB.NS", "UPL.NS", "SBILIFE.NS", "BRITANNIA.NS",
            "HDFCLIFE.NS", "IOC.NS", "EICHERMOT.NS", "APOLLOHOSP.NS", "BAJAJFINSV.NS",
            "HDFC.NS", "TATACONSUM.NS"
        ]
        return nifty50_stocks
    
    def get_multiple_stocks_data(self, symbols: List[str], period: str = "6mo") -> Dict[str, pd.DataFrame]:
        """Fetch data for multiple stocks"""
        all_data = {}
        
        for symbol in symbols:
            try:
                data = self.get_yfinance_data(symbol, period=period)
                if not data.empty:
                    all_data[symbol] = data
                    self.logger.info(f"Successfully fetched data for {symbol}")
                else:
                    self.logger.warning(f"No data found for {symbol}")
            except Exception as e:
                self.logger.error(f"Error fetching data for {symbol}: {e}")
        
        return all_data
    
    def close_driver(self):
        """Close the Selenium WebDriver"""
        if self.driver:
            self.driver.quit()
