"""
Data utilities for PayCheck-to-Portfolio AI
Handles market data fetching, portfolio calculations, and data processing
"""

import yfinance as yf
import streamlit as st
from config import ASSET_CATEGORIES, CACHE_TTL

def get_stock_data(symbols):
    """Fetch real market data for given symbols"""
    try:
        data = {}
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                hist = ticker.history(period="5d")

                # Calculate price change from historical data if not available in info
                price_change = 0
                if len(hist) >= 2:
                    current_price = hist['Close'].iloc[-1]
                    previous_price = hist['Close'].iloc[-2]
                    price_change = ((current_price - previous_price) / previous_price) * 100

                data[symbol] = {
                    'price': info.get('regularMarketPrice', hist['Close'].iloc[-1] if len(hist) > 0 else 100),
                    'change': info.get('regularMarketChangePercent', price_change),
                    'dividend_yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
                    'pe_ratio': info.get('trailingPE', None)
                }
            except Exception as symbol_error:
                st.warning(f"Error fetching data for {symbol}: {symbol_error}")
                # Provide fallback data
                data[symbol] = {
                    'price': 100.0,
                    'change': 0.0,
                    'dividend_yield': 0.0,
                    'pe_ratio': None
                }
        return data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        # Return fallback data for all symbols
        return {symbol: {
            'price': 100.0,
            'change': 0.0,
            'dividend_yield': 0.0,
            'pe_ratio': None
        } for symbol in symbols}

@st.cache_data(ttl=CACHE_TTL)
def fetch_market_data(portfolio_symbols):
    """Fetch market data for portfolio symbols with caching"""
    return get_stock_data(portfolio_symbols)

def calculate_portfolio_value(portfolio, stock_data):
    """Calculate current portfolio value and breakdown by category"""
    total_value = 0
    portfolio_breakdown = {}

    for symbol, holding in portfolio.items():
        if symbol in stock_data:
            value = holding['shares'] * stock_data[symbol]['price']
            total_value += value

            category = get_asset_category(symbol)
            if category not in portfolio_breakdown:
                portfolio_breakdown[category] = 0
            portfolio_breakdown[category] += value

    return total_value, portfolio_breakdown

def get_asset_category(symbol):
    """Get asset category for a given symbol"""
    return ASSET_CATEGORIES.get(symbol, 'Other')

def calculate_ai_score(symbol, stock_data):
    """Calculate AI score for a symbol based on multiple factors"""
    if symbol not in stock_data:
        return 50

    data = stock_data[symbol]
    score = 50

    # Price momentum
    if data['change'] > 0:
        score += min(data['change'] * 2, 15)
    else:
        score += max(data['change'] * 2, -15)

    # Dividend yield bonus
    if data['dividend_yield'] > 2:
        score += 10

    # PE ratio consideration
    if isinstance(data['pe_ratio'], (int, float)) and 10 <= data['pe_ratio'] <= 25:
        score += 10

    return max(20, min(95, score))
