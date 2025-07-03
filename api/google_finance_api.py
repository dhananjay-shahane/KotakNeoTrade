
"""Google Finance API for live CMP updates"""
from flask import Blueprint, request, jsonify
import logging
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

google_finance_bp = Blueprint('google_finance', __name__, url_prefix='/api/google-finance/update-etf-cmp')
logger = logging.getLogger(__name__)

# Database connection string
DATABASE_URL = "postgresql://kotak_trading_db_user:JRUlk8RutdgVcErSiUXqljDUdK8sBsYO@dpg-d1cjd66r433s73fsp4n0-a.oregon-postgres.render.com/kotak_trading_db"

def get_google_finance_price(symbol: str) -> Optional[float]:
    """Fetch live price from Google Finance using the exact URL format"""
    try:
        # Use Google Finance URL format as specified
        google_url = f"https://www.google.com/finance/quote/{symbol}:NSE"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        logger.info(f"🌐 Fetching Google Finance data for {symbol} from: {google_url}")
        
        response = requests.get(google_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for price in various possible selectors
            price_selectors = [
                'div[data-last-price]',
                '.YMlKec.fxKbKc',
                '.kf1m0',
                '.YMlKec',
                'div.YMlKec.fxKbKc',
                'c-wiz div[data-last-price]'
            ]
            
            for selector in price_selectors:
                price_element = soup.select_one(selector)
                if price_element:
                    # Try data attribute first
                    price_text = price_element.get('data-last-price')
                    if not price_text:
                        price_text = price_element.get_text(strip=True)
                    
                    if price_text:
                        # Clean and extract price
                        price_clean = price_text.replace('₹', '').replace(',', '').strip()
                        try:
                            price = float(price_clean)
                            logger.info(f"✅ Google Finance price for {symbol}: ₹{price}")
                            return round(price, 2)
                        except ValueError:
                            continue
            
            logger.warning(f"⚠️ Could not parse price from Google Finance for {symbol}")
        else:
            logger.warning(f"⚠️ Google Finance returned status {response.status_code} for {symbol}")
            
    except Exception as e:
        logger.error(f"❌ Google Finance error for {symbol}: {str(e)}")