import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import time
import google.generativeai as genai
import json

# Configure page
st.set_page_config(
    page_title="PayCheck-to-Portfolio AI",
    page_icon="📊",
    layout="wide"
)

# Configure Google AI
genai.configure(api_key="NOT FOR THE PUBLIC")
model = genai.GenerativeModel('gemini-2.5-flash')

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.cash_balance = 2500.00
    st.session_state.portfolio = {
        'VTI': {'shares': 12, 'symbol': 'VTI', 'name': 'Total Stock Market ETF'},
        'VTIAX': {'shares': 8, 'symbol': 'VTIAX', 'name': 'International Stock Index'},
        'BND': {'shares': 15, 'symbol': 'BND', 'name': 'Total Bond Market ETF'},
        'VNQ': {'shares': 5, 'symbol': 'VNQ', 'name': 'Real Estate ETF'}
    }
    st.session_state.target_allocation = {
        'Stocks (US)': 60,
        'Stocks (Intl)': 20,
        'Bonds': 15,
        'Real Estate': 5
    }
    st.session_state.execution_history = []
    st.session_state.market_analysis_cache = None
    st.session_state.ai_recommendations_cache = None
    st.session_state.last_cash_amount = None
    st.session_state.just_invested = False

def get_stock_data(symbols):
    """Fetch real market data"""
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

def calculate_portfolio_value(portfolio, stock_data):
    """Calculate current portfolio value"""
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
    """Categorize assets"""
    categories = {
        'VTI': 'Stocks (US)',
        'VTIAX': 'Stocks (Intl)',
        'BND': 'Bonds',
        'VNQ': 'Real Estate',
        'SPY': 'Stocks (US)',
        'QQQ': 'Stocks (US)',
        'IWM': 'Stocks (US)',
        'EFA': 'Stocks (Intl)',
        'TLT': 'Bonds',
        'IYR': 'Real Estate',
        'VEA': 'Stocks (Intl)',
        'VWO': 'Stocks (Intl)',
        'AGG': 'Bonds',
        'BNDX': 'Bonds',
        'VXUS': 'Stocks (Intl)',
        'VUG': 'Stocks (US)',
        'VTV': 'Stocks (US)',
        'VYM': 'Stocks (US)',
        'SCHD': 'Stocks (US)',
        'DGRO': 'Stocks (US)'
    }
    return categories.get(symbol, 'Other')

def calculate_ai_score(symbol, stock_data):
    """AI scoring algorithm based on multiple factors"""
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

def get_ai_recommendations(market_analysis, stock_data, current_breakdown, target_allocation, total_value, cash_available):
    """Get AI-powered buy/sell recommendations from Google AI Studio"""
    try:
        # Expand available symbols for diversification
        all_available_symbols = ['VTI', 'VTIAX', 'BND', 'VNQ', 'SPY', 'QQQ', 'IWM', 'EFA', 'TLT', 'IYR',
                                'VEA', 'VWO', 'AGG', 'BNDX', 'VXUS', 'VUG', 'VTV', 'VYM', 'SCHD', 'DGRO']

        # Get data for all available symbols
        expanded_stock_data = get_stock_data(all_available_symbols)

        # Prepare current portfolio data
        portfolio_summary = {}
        for symbol, data in expanded_stock_data.items():
            # Include both current holdings and available alternatives
            if symbol in st.session_state.portfolio:
                shares = st.session_state.portfolio[symbol]['shares']
                value = shares * data['price']
                category = get_asset_category(symbol)
                current_pct = (value / (total_value + cash_available)) * 100
                target_pct = target_allocation.get(category, 0)
            else:
                # For new symbols, show as potential additions
                shares = 0
                value = 0
                category = get_asset_category(symbol)
                current_pct = 0
                target_pct = target_allocation.get(category, 0)

            portfolio_summary[symbol] = {
                'shares': shares,
                'value': value,
                'price': data['price'],
                'change': data['change'],
                'dividend_yield': data['dividend_yield'],
                'pe_ratio': data['pe_ratio'],
                'category': category,
                'current_pct': current_pct,
                'target_pct': target_pct,
                'overweight': current_pct > target_pct + 3,
                'underweight': current_pct < target_pct - 3,
                'is_current_holding': symbol in st.session_state.portfolio
            }

        # Prepare market data for AI
        market_summary = {
            'sentiment': market_analysis['market_sentiment'],
            'risk_level': market_analysis['risk_assessment'],
            'recommendation': market_analysis['recommendation'],
            'sector_performance': market_analysis['sector_analysis'],
            'key_insights': market_analysis['key_insights']
        }

        # Create prompt for AI to generate its own recommendations
        prompt = f"""
        You are an expert financial advisor. Analyze the current portfolio and market conditions to provide specific buy/sell recommendations.

        CURRENT PORTFOLIO:
        {json.dumps(portfolio_summary, indent=2)}

        TARGET ALLOCATION:
        {json.dumps(target_allocation, indent=2)}

        MARKET ANALYSIS:
        {json.dumps(market_summary, indent=2)}

        AVAILABLE CASH: ${cash_available:,.0f}

        AVAILABLE SYMBOLS FOR DIVERSIFICATION:
        - US Stocks: VTI, SPY, QQQ, VUG, VTV, VYM, SCHD, DGRO
        - International: VTIAX, EFA, VEA, VWO, VXUS
        - Bonds: BND, TLT, AGG, BNDX
        - Real Estate: VNQ, IYR

        Please provide specific recommendations in this EXACT JSON format (no other text):
        {{
            "analysis": "Your overall market assessment and strategy rationale",
            "recommendations": [
                {{
                    "action": "BUY",
                    "symbol": "VTI",
                    "shares": 5,
                    "reasoning": "Specific reason for this trade",
                    "priority": "High"
                }}
            ],
            "risk_assessment": "Your risk evaluation",
            "market_timing": "Your timing insights"
        }}

        CRITICAL REQUIREMENTS:
        1. DIVERSIFY BEYOND CURRENT HOLDINGS - Use different symbols from the available list above
        2. Consider performance-based selection (choose best performing ETFs in each category)
        3. Portfolio rebalancing to target allocation
        4. Market timing based on current conditions
        5. Risk management
        6. Specific share quantities and reasoning
        7. Avoid contradictory trades (don't sell and buy the same asset)
        8. Ensure total investment equals available cash (${cash_available:,.0f})
        9. PRIORITIZE DIVERSIFICATION - Don't just rebalance existing holdings, add new ones

        EXAMPLES OF GOOD DIVERSIFICATION:
        - Instead of just VTI, consider SPY, QQQ, or VUG for US stocks
        - Instead of just VTIAX, consider EFA, VEA, or VWO for international
        - Instead of just BND, consider TLT, AGG, or BNDX for bonds
        - Add VNQ or IYR for real estate exposure

        IMPORTANT: Return ONLY valid JSON, no explanations or additional text.
        """

        # Get AI response
        response = model.generate_content(prompt)
        if response and response.text:
            try:
                # Clean the response text
                response_text = response.text.strip()

                # Try to extract JSON from the response
                if response_text.startswith('{') and response_text.endswith('}'):
                    ai_data = json.loads(response_text)
                else:
                    # Look for JSON within the response
                    import re
                    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if json_match:
                        ai_data = json.loads(json_match.group())
                    else:
                        # Fallback: create a structured response from the text
                        ai_data = {
                            "analysis": response_text,
                            "recommendations": [],
                            "risk_assessment": "AI provided text analysis",
                            "market_timing": "AI provided text analysis"
                        }

                return ai_data
            except (json.JSONDecodeError, Exception) as e:
                # Fallback: create a structured response from the text
                return {
                    "analysis": f"AI Analysis: {response.text[:500]}...",
                    "recommendations": [],
                    "risk_assessment": "AI provided analysis",
                    "market_timing": "AI provided analysis"
                }
        else:
            return {
                "analysis": "AI analysis completed but no response received. Using algorithmic recommendations.",
                "recommendations": [],
                "risk_assessment": "Unable to assess",
                "market_timing": "Unable to assess"
            }

    except Exception as e:
        st.warning(f"AI analysis unavailable: {e}")
        return {
            "analysis": f"AI analysis temporarily unavailable: {e}. Using algorithmic recommendations.",
            "recommendations": [],
            "risk_assessment": "Unable to assess",
            "market_timing": "Unable to assess"
        }

@st.cache_data(ttl=300)  # Cache for 5 minutes
def analyze_market_conditions(stock_data):
    """AI market research and analysis"""
    research_symbols = ['VTI', 'VTIAX', 'BND', 'VNQ', 'SPY', 'QQQ', 'IWM', 'EFA', 'TLT', 'IYR',
                       'VEA', 'VWO', 'AGG', 'BNDX', 'VXUS', 'VUG', 'VTV', 'VYM', 'SCHD', 'DGRO']
    research_data = get_stock_data(research_symbols)

    analysis = {
        'market_sentiment': 'neutral',
        'key_insights': [],
        'sector_analysis': {},
        'risk_assessment': 'medium',
        'recommendation': 'proceed_with_caution'
    }

    if not research_data:
        return analysis

    # Calculate market sentiment
    positive_moves = sum(1 for data in research_data.values() if data['change'] > 0)
    total_symbols = len(research_data)

    if positive_moves / total_symbols > 0.7:
        analysis['market_sentiment'] = 'bullish'
        analysis['key_insights'].append("Strong positive momentum across major indices")
    elif positive_moves / total_symbols < 0.3:
        analysis['market_sentiment'] = 'bearish'
        analysis['key_insights'].append("Widespread selling pressure in markets")
    else:
        analysis['market_sentiment'] = 'neutral'
        analysis['key_insights'].append("Mixed signals with sector rotation")

    # Analyze each sector
    sectors = {
        'US Large Cap': ['SPY', 'VTI'],
        'US Small Cap': ['IWM'],
        'International': ['EFA', 'VTIAX'],
        'Bonds': ['BND', 'TLT'],
        'Real Estate': ['VNQ', 'IYR'],
        'Tech': ['QQQ']
    }

    for sector_name, symbols in sectors.items():
        sector_data = [research_data[s] for s in symbols if s in research_data]
        if sector_data:
            avg_change = sum(d['change'] for d in sector_data) / len(sector_data)
            avg_dividend = sum(d['dividend_yield'] for d in sector_data) / len(sector_data)

            analysis['sector_analysis'][sector_name] = {
                'performance': avg_change,
                'dividend_yield': avg_dividend,
                'sentiment': 'strong' if avg_change > 1 else 'weak' if avg_change < -1 else 'neutral'
            }

    # Risk assessment
    volatility = sum(abs(d['change']) for d in research_data.values()) / len(research_data)
    if volatility > 2:
        analysis['risk_assessment'] = 'high'
        analysis['key_insights'].append("High volatility detected - markets are unstable")
    elif volatility < 0.5:
        analysis['risk_assessment'] = 'low'
        analysis['key_insights'].append("Low volatility - stable market conditions")

    # Generate recommendation
    if analysis['market_sentiment'] == 'bullish' and analysis['risk_assessment'] == 'low':
        analysis['recommendation'] = 'aggressive_buy'
        analysis['key_insights'].append("Favorable conditions for aggressive investment")
    elif analysis['market_sentiment'] == 'bearish' or analysis['risk_assessment'] == 'high':
        analysis['recommendation'] = 'defensive'
        analysis['key_insights'].append("Consider defensive positioning with bonds")
    else:
        analysis['recommendation'] = 'balanced'
        analysis['key_insights'].append("Balanced approach recommended")

    return analysis, research_data

def generate_detailed_reasoning(symbol, category, market_analysis, stock_data, action, shares, cost):
    """Generate detailed reasoning for each investment recommendation"""
    data = stock_data[symbol]
    sector_data = None

    # Get sector-specific data
    if category == 'Stocks (US)':
        sector_data = market_analysis['sector_analysis'].get('US Large Cap', {})
    elif category == 'Stocks (Intl)':
        sector_data = market_analysis['sector_analysis'].get('International', {})
    elif category == 'Bonds':
        sector_data = market_analysis['sector_analysis'].get('Bonds', {})
    elif category == 'Real Estate':
        sector_data = market_analysis['sector_analysis'].get('Real Estate', {})

    reasons = []

    if action == 'SELL':
        # Sell-specific reasoning
        if sector_data:
            perf = sector_data.get('performance', 0)
            sentiment = sector_data.get('sentiment', 'neutral')

            if sentiment == 'weak' and perf < -1:
                reasons.append(f"Poor sector performance ({perf:.1f}%) - reducing exposure")
            elif sentiment == 'strong' and perf > 2:
                reasons.append(f"Strong sector performance ({perf:.1f}%) - profit taking opportunity")
            else:
                reasons.append(f"Mixed sector signals ({perf:.1f}%) - strategic rebalancing")

        # Price momentum for sells
        if data['change'] < -3:
            reasons.append(f"Significant price decline ({data['change']:.1f}%) - cutting losses")
        elif data['change'] > 5:
            reasons.append(f"Strong gains ({data['change']:.1f}%) - taking profits")
        else:
            reasons.append(f"Moderate price action ({data['change']:+.1f}%) - portfolio rebalancing")

        # Valuation for sells
        if isinstance(data['pe_ratio'], (int, float)):
            if data['pe_ratio'] > 30:
                reasons.append(f"Overvalued (PE {data['pe_ratio']:.1f}) - profit taking")
            elif data['pe_ratio'] < 10:
                reasons.append(f"Undervalued but poor fundamentals (PE {data['pe_ratio']:.1f}) - strategic exit")
            else:
                reasons.append(f"Fair valuation (PE {data['pe_ratio']:.1f}) - rebalancing decision")

        # Risk management for sells
        if market_analysis['risk_assessment'] == 'high':
            reasons.append("High volatility environment - reducing risk exposure")
        elif market_analysis['risk_assessment'] == 'low':
            reasons.append("Stable conditions - strategic portfolio optimization")
        else:
            reasons.append("Moderate risk - tactical position adjustment")

    else:  # BUY recommendations
        # Market sentiment reasoning
        if sector_data:
            perf = sector_data.get('performance', 0)
            sentiment = sector_data.get('sentiment', 'neutral')

            if sentiment == 'strong' and perf > 1:
                reasons.append(f"Strong sector momentum (+{perf:.1f}%) - favorable entry point")
            elif sentiment == 'weak' and perf < -1:
                reasons.append(f"Weak sector performance ({perf:.1f}%) - potential value opportunity")
            else:
                reasons.append(f"Stable sector performance ({perf:.1f}%) - balanced risk/reward")

        # Price momentum reasoning
        if data['change'] > 2:
            reasons.append(f"Strong price momentum (+{data['change']:.1f}%) - bullish trend")
        elif data['change'] < -2:
            reasons.append(f"Price weakness ({data['change']:.1f}%) - potential oversold opportunity")
        else:
            reasons.append(f"Stable price action ({data['change']:+.1f}%) - steady performance")

        # Dividend yield reasoning
        if data['dividend_yield'] > 3:
            reasons.append(f"Attractive dividend yield ({data['dividend_yield']:.1f}%) - income generation")
        elif data['dividend_yield'] > 1:
            reasons.append(f"Modest dividend yield ({data['dividend_yield']:.1f}%) - some income")
        else:
            reasons.append(f"Growth-focused (low dividend {data['dividend_yield']:.1f}%) - capital appreciation")

        # PE ratio reasoning (if available)
        if isinstance(data['pe_ratio'], (int, float)):
            if data['pe_ratio'] < 15:
                reasons.append(f"Undervalued (PE {data['pe_ratio']:.1f}) - potential upside")
            elif data['pe_ratio'] > 25:
                reasons.append(f"Premium valuation (PE {data['pe_ratio']:.1f}) - growth expectations")
            else:
                reasons.append(f"Fair valuation (PE {data['pe_ratio']:.1f}) - reasonable pricing")

        # Market condition reasoning
        if market_analysis['recommendation'] == 'aggressive_buy':
            reasons.append("Market conditions favor growth - aggressive positioning")
        elif market_analysis['recommendation'] == 'defensive':
            reasons.append("Defensive market conditions - capital preservation focus")
        else:
            reasons.append("Balanced market approach - diversified allocation")

        # Risk assessment reasoning
        if market_analysis['risk_assessment'] == 'low':
            reasons.append("Low volatility environment - stable investment climate")
        elif market_analysis['risk_assessment'] == 'high':
            reasons.append("High volatility detected - cautious positioning")
        else:
            reasons.append("Moderate risk environment - standard allocation")

    return reasons

def generate_recommendations(current_breakdown, target_allocation, total_value, cash_available, stock_data, market_analysis):
    """Generate investment recommendations based on AI market research"""
    recommendations = []
    sell_recommendations = []

    etf_map = {
                'Stocks (US)': 'VTI',
                'Stocks (Intl)': 'VTIAX',
                'Bonds': 'BND',
                'Real Estate': 'VNQ'
            }

    # Adjust allocation based on market conditions
    adjusted_allocation = target_allocation.copy()

    if market_analysis['recommendation'] == 'aggressive_buy':
        # Favor stocks over bonds
        adjusted_allocation['Stocks (US)'] = min(70, target_allocation['Stocks (US)'] + 10)
        adjusted_allocation['Bonds'] = max(5, target_allocation['Bonds'] - 10)
    elif market_analysis['recommendation'] == 'defensive':
        # Favor bonds over stocks
        adjusted_allocation['Bonds'] = min(30, target_allocation['Bonds'] + 15)
        adjusted_allocation['Stocks (US)'] = max(40, target_allocation['Stocks (US)'] - 15)

    # Check for sell recommendations first
    total_available = total_value + cash_available
    for category, target_pct in adjusted_allocation.items():
        current_pct = (current_breakdown.get(category, 0) / total_available) * 100
        symbol = etf_map.get(category)

        if symbol in st.session_state.portfolio:
            current_shares = st.session_state.portfolio[symbol]['shares']
            if current_shares > 0:
                price = stock_data[symbol]['price']
                data = stock_data[symbol]

                # Multiple reasons to sell
                should_sell = False
                sell_reasons = []

                # 1. Portfolio rebalancing - overweight by more than 3%
                if current_pct > target_pct + 3:
                    should_sell = True
                    excess_pct = current_pct - target_pct
                    sell_reasons.append(f"Portfolio overweight by {excess_pct:.1f}% - rebalancing needed")

                # 2. Poor performance - significant negative momentum
                if data['change'] < -3:
                    should_sell = True
                    sell_reasons.append(f"Poor performance ({data['change']:.1f}%) - cutting losses")

                # 3. High valuation - PE ratio too high
                if isinstance(data['pe_ratio'], (int, float)) and data['pe_ratio'] > 30:
                    should_sell = True
                    sell_reasons.append(f"Overvalued (PE {data['pe_ratio']:.1f}) - profit taking")

                # 4. Market conditions favor selling this category
                category_sentiment = 'neutral'
                if category == 'Stocks (US)':
                    category_sentiment = market_analysis['sector_analysis'].get('US Large Cap', {}).get('sentiment', 'neutral')
                elif category == 'Bonds':
                    category_sentiment = market_analysis['sector_analysis'].get('Bonds', {}).get('sentiment', 'neutral')
                elif category == 'Stocks (Intl)':
                    category_sentiment = market_analysis['sector_analysis'].get('International', {}).get('sentiment', 'neutral')
                elif category == 'Real Estate':
                    category_sentiment = market_analysis['sector_analysis'].get('Real Estate', {}).get('sentiment', 'neutral')

                if category_sentiment == 'weak' and current_pct > 5:
                    should_sell = True
                    sell_reasons.append(f"Weak sector sentiment - reducing exposure")

                # 5. Risk management - if high volatility and large position
                if market_analysis['risk_assessment'] == 'high' and current_pct > 15:
                    should_sell = True
                    sell_reasons.append(f"High volatility environment - reducing risk exposure")

                if should_sell:
                    # Calculate how much to sell
                    if current_pct > target_pct + 3:
                        # Rebalancing sell - sell excess
                        excess_pct = current_pct - target_pct
                        shares_to_sell = int((excess_pct / 100) * total_available / price)
                    else:
                        # Other reasons - sell a portion (10-30% of holdings)
                        sell_pct = 0.2 if market_analysis['risk_assessment'] == 'high' else 0.15
                        shares_to_sell = int(current_shares * sell_pct)

                    shares_to_sell = min(shares_to_sell, current_shares)
                    shares_to_sell = max(1, shares_to_sell)  # At least 1 share

                    if shares_to_sell > 0:
                        # Generate detailed reasoning for sell
                        detailed_sell_reasons = generate_detailed_reasoning(
                            symbol, category, market_analysis, stock_data, 'SELL', shares_to_sell, shares_to_sell * price
                        )

                        sell_recommendations.append({
                            'symbol': symbol,
                            'shares': shares_to_sell,
                            'cost': shares_to_sell * price,
                            'category': category,
                            'current_pct': current_pct,
                            'target_pct': target_pct,
                            'ai_score': calculate_ai_score(symbol, stock_data),
                            'market_sentiment': category_sentiment,
                            'action': 'SELL',
                            'reasoning': f"Sell {shares_to_sell} shares of {symbol} - {', '.join(sell_reasons)}",
                            'detailed_reasons': detailed_sell_reasons
                        })

    # Calculate total cash available after sells
    total_sell_proceeds = sum(rec['cost'] for rec in sell_recommendations)
    total_cash_available = cash_available + total_sell_proceeds

    # Generate buy recommendations using total available cash
    remaining_cash = total_cash_available

    for i, (category, target_pct) in enumerate(adjusted_allocation.items()):
            symbol = etf_map.get(category)
            if symbol and symbol in stock_data:
                price = stock_data[symbol]['price']

            if i == len(adjusted_allocation) - 1:  # Last category gets all remaining cash
                shares_needed = int(remaining_cash / price)
                cost = shares_needed * price  # Use actual cost, not remaining_cash
            else:
                # Calculate proportional amount based on total available cash
                cash_for_category = total_cash_available * (target_pct / 100)
                shares_needed = int(cash_for_category / price)
                cost = shares_needed * price
                remaining_cash -= cost

            if shares_needed > 0:  # Only recommend if we can buy at least 1 share
                # Get market sentiment for this category
                category_sentiment = 'neutral'
                if category == 'Stocks (US)':
                    category_sentiment = market_analysis['sector_analysis'].get('US Large Cap', {}).get('sentiment', 'neutral')
                elif category == 'Bonds':
                    category_sentiment = market_analysis['sector_analysis'].get('Bonds', {}).get('sentiment', 'neutral')
                elif category == 'Stocks (Intl)':
                    category_sentiment = market_analysis['sector_analysis'].get('International', {}).get('sentiment', 'neutral')
                elif category == 'Real Estate':
                    category_sentiment = market_analysis['sector_analysis'].get('Real Estate', {}).get('sentiment', 'neutral')

                # Generate detailed reasoning
                detailed_reasons = generate_detailed_reasoning(
                    symbol, category, market_analysis, stock_data, 'BUY', shares_needed, cost
                )

                recommendations.append({
                    'symbol': symbol,
                    'shares': shares_needed,
                    'cost': cost,
                    'category': category,
                    'target_pct': target_pct,
                    'ai_score': calculate_ai_score(symbol, stock_data),
                    'market_sentiment': category_sentiment,
                    'action': 'BUY',
                    'reasoning': f"AI-adjusted allocation: {target_pct}% in {category} (Market: {category_sentiment})",
                    'detailed_reasons': detailed_reasons
                })

    # Combine buy and sell recommendations
    all_recommendations = sell_recommendations + recommendations
    return sorted(all_recommendations, key=lambda x: x['cost'], reverse=True)

def execute_recommendations(recommendations):
    """Execute AI recommendations (both buy and sell)"""
    total_invested = 0
    total_sold = 0

    # Clear caches since portfolio and cash will change
    st.session_state.market_analysis_cache = None
    st.session_state.ai_recommendations_cache = None
    st.session_state.just_invested = True
    # Clear the stock data cache to fetch data for new symbols
    fetch_market_data.clear()

    for rec in recommendations:
        symbol = rec['symbol']
        shares = rec['shares']
        cost = rec['cost']
        action = rec['action']

        if action == 'BUY' and cost <= st.session_state.cash_balance:
            # Execute buy order
            if symbol in st.session_state.portfolio:
                st.session_state.portfolio[symbol]['shares'] += shares
            else:
                st.session_state.portfolio[symbol] = {
                    'shares': shares,
                    'symbol': symbol,
                    'name': f'{symbol} ETF'
                }

            # Update cash
            st.session_state.cash_balance -= cost
            total_invested += cost

            # Log execution
            st.session_state.execution_history.insert(0, {
                'Time': datetime.now().strftime("%H:%M:%S"),
                'Action': f"Bought {shares} shares of {symbol}",
                'Amount': f"${cost:.2f}"
            })

        elif action == 'SELL' and symbol in st.session_state.portfolio:
            # Execute sell order
            current_shares = st.session_state.portfolio[symbol]['shares']
            if shares <= current_shares:
                st.session_state.portfolio[symbol]['shares'] -= shares

                # Add cash
                st.session_state.cash_balance += cost
                total_sold += cost

                # Remove holding if shares reach zero
                if st.session_state.portfolio[symbol]['shares'] == 0:
                    del st.session_state.portfolio[symbol]

                # Log execution
                st.session_state.execution_history.insert(0, {
                    'Time': datetime.now().strftime("%H:%M:%S"),
                    'Action': f"Sold {shares} shares of {symbol}",
                    'Amount': f"${cost:.2f}"
                })

    return total_invested, total_sold

# Main App
st.title("PayCheck-to-Portfolio AI")
st.markdown("**Automatically invests your paycheck deposits using AI-powered portfolio optimization**")
st.markdown("---")

# Demo Controls
col1, col2 = st.columns([3, 1])

with col2:
    if st.button("+ Add $800 Paycheck", type="secondary"):
        st.session_state.cash_balance += 800
        st.success("New paycheck deposit detected!")

# Get market data
@st.cache_data(ttl=300)
def fetch_market_data():
    symbols = list(st.session_state.portfolio.keys())
    return get_stock_data(symbols)

stock_data = fetch_market_data()

if not stock_data:
    st.error("Unable to fetch market data. Please refresh.")
    st.stop()

# Calculate metrics
total_portfolio_value, current_breakdown = calculate_portfolio_value(st.session_state.portfolio, stock_data)
total_account_value = total_portfolio_value + st.session_state.cash_balance
uninvested_pct = (st.session_state.cash_balance / total_account_value) * 100

# Key Metrics
st.markdown("### Account Overview")
metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

with metric_col1:
    st.metric("Total Portfolio", f"${total_portfolio_value:,.0f}")
with metric_col2:
    st.metric("Cash Available", f"${st.session_state.cash_balance:,.0f}")
with metric_col3:
    st.metric("Total Account Value", f"${total_account_value:,.0f}")
with metric_col4:
    color = "inverse" if uninvested_pct > 15 else "normal"
    st.metric("Cash Uninvested", f"{uninvested_pct:.1f}%")

# AI Analysis & Action
if st.session_state.cash_balance > 500:
    st.markdown("### AI Market Research & Analysis")

    # Perform market research (only if not cached)
    if st.session_state.market_analysis_cache is None:
        with st.spinner("🔍 AI is analyzing market conditions..."):
            market_analysis, research_data = analyze_market_conditions(stock_data)
            st.session_state.market_analysis_cache = market_analysis
    else:
        market_analysis = st.session_state.market_analysis_cache
        research_data = None  # We don't need to store this separately

    # Display market research
    col_research1, col_research2 = st.columns(2)

    with col_research1:
        st.markdown("#### Market Sentiment")
        sentiment_color = "🟢" if market_analysis['market_sentiment'] == 'bullish' else "🔴" if market_analysis['market_sentiment'] == 'bearish' else "🟡"
        st.write(f"{sentiment_color} **{market_analysis['market_sentiment'].upper()}**")

        st.markdown("#### Risk Assessment")
        risk_color = "🔴" if market_analysis['risk_assessment'] == 'high' else "🟢" if market_analysis['risk_assessment'] == 'low' else "🟡"
        st.write(f"{risk_color} **{market_analysis['risk_assessment'].upper()}**")

        st.markdown("#### AI Recommendation")
        rec_color = "🟢" if market_analysis['recommendation'] == 'aggressive_buy' else "🔴" if market_analysis['recommendation'] == 'defensive' else "🟡"
        st.write(f"{rec_color} **{market_analysis['recommendation'].replace('_', ' ').upper()}**")

    with col_research2:
        st.markdown("#### Key Market Insights")
        for insight in market_analysis['key_insights']:
            st.write(f"• {insight}")

    # Sector Analysis
    st.markdown("#### Sector Performance Analysis")
    sector_cols = st.columns(len(market_analysis['sector_analysis']))

    for i, (sector, data) in enumerate(market_analysis['sector_analysis'].items()):
        with sector_cols[i]:
            perf_color = "🟢" if data['performance'] > 0 else "🔴"
            st.write(f"**{sector}**")
            st.write(f"{perf_color} {data['performance']:+.2f}%")
            st.write(f"Yield: {data['dividend_yield']:.2f}%")
            st.write(f"Sentiment: {data['sentiment']}")

    st.markdown("---")

    # Alert and Action
    col_alert, col_action = st.columns([2, 1])

    with col_alert:
        st.error(f"**Alert:** ${st.session_state.cash_balance:,.0f} sitting uninvested ({uninvested_pct:.1f}% of portfolio)")
        st.write("AI has completed market research and generated investment strategy...")

    # Get AI-generated recommendations (only if not cached)
    if st.session_state.ai_recommendations_cache is None:
        with st.spinner("🤖 AI is generating investment recommendations..."):
            ai_data = get_ai_recommendations(
                market_analysis,
                stock_data,
                current_breakdown,
                st.session_state.target_allocation,
                total_portfolio_value,
                st.session_state.cash_balance
            )
            st.session_state.ai_recommendations_cache = ai_data
    else:
        ai_data = st.session_state.ai_recommendations_cache

    # Display AI Analysis
    st.markdown("### 🤖 AI Financial Advisor Analysis")
    with st.expander("View AI Analysis", expanded=True):
        st.markdown(f"**Market Assessment:** {ai_data['analysis']}")
        st.markdown(f"**Risk Assessment:** {ai_data['risk_assessment']}")
        st.markdown(f"**Market Timing:** {ai_data['market_timing']}")

    # Convert AI recommendations to our format
    recommendations = []

    # Debug: Show what AI returned


    for rec in ai_data.get('recommendations', []):
        symbol = rec['symbol']
        # Get expanded stock data for AI recommendations
        expanded_symbols = ['VTI', 'VTIAX', 'BND', 'VNQ', 'SPY', 'QQQ', 'IWM', 'EFA', 'TLT', 'IYR',
                           'VEA', 'VWO', 'AGG', 'BNDX', 'VXUS', 'VUG', 'VTV', 'VYM', 'SCHD', 'DGRO']
        expanded_stock_data = get_stock_data(expanded_symbols)

        if symbol in expanded_stock_data:
            price = expanded_stock_data[symbol]['price']
            cost = rec['shares'] * price
            category = get_asset_category(symbol)

            recommendations.append({
                'symbol': symbol,
                'shares': rec['shares'],
                'cost': cost,
                'category': category,
                'action': rec['action'],
                'reasoning': rec['reasoning'],
                'priority': rec.get('priority', 'Medium'),
                'ai_generated': True
            })

    # If no AI recommendations, generate basic algorithmic ones with diversification
    if not recommendations and st.session_state.cash_balance > 0:
        # Generate diversified buy recommendations for available cash
        expanded_symbols = ['VTI', 'VTIAX', 'BND', 'VNQ', 'SPY', 'QQQ', 'IWM', 'EFA', 'TLT', 'IYR',
                           'VEA', 'VWO', 'AGG', 'BNDX', 'VXUS', 'VUG', 'VTV', 'VYM', 'SCHD', 'DGRO']
        expanded_stock_data = get_stock_data(expanded_symbols)

        # Diversified ETF mapping with more options
        diversified_etf_map = {
            'Stocks (US)': ['VTI', 'SPY', 'QQQ', 'VUG', 'VTV', 'VYM', 'SCHD', 'DGRO'],
            'Stocks (Intl)': ['VTIAX', 'EFA', 'VEA', 'VWO', 'VXUS'],
            'Bonds': ['BND', 'TLT', 'AGG', 'BNDX'],
            'Real Estate': ['VNQ', 'IYR']
        }

        remaining_cash = st.session_state.cash_balance

        for category, target_pct in st.session_state.target_allocation.items():
            # Get all available symbols for this category
            available_symbols = diversified_etf_map.get(category, [])

            # Find the best performing symbol in this category
            best_symbol = None
            best_performance = -999

            for symbol in available_symbols:
                if symbol in expanded_stock_data:
                    performance = expanded_stock_data[symbol]['change']
                    if performance > best_performance:
                        best_performance = performance
                        best_symbol = symbol

            # Use the best performing symbol, or fallback to first available
            if not best_symbol and available_symbols:
                best_symbol = available_symbols[0]

            if best_symbol and best_symbol in expanded_stock_data:
                price = expanded_stock_data[best_symbol]['price']
                cash_for_category = remaining_cash * (target_pct / 100)
                shares_needed = int(cash_for_category / price)

                if shares_needed > 0:
                    cost = shares_needed * price
                    recommendations.append({
                        'symbol': best_symbol,
                        'shares': shares_needed,
                        'cost': cost,
                        'category': category,
                        'action': 'BUY',
                        'reasoning': f'Diversified allocation: {target_pct}% in {category} (Best performer: {best_symbol})',
                        'priority': 'Medium',
                        'ai_generated': False
                    })
                    remaining_cash -= cost

    if recommendations:
        st.markdown("---")

        # Calculate totals for button
        total_buy = sum(rec['cost'] for rec in recommendations if rec['action'] == 'BUY')
        total_sell = sum(rec['cost'] for rec in recommendations if rec['action'] == 'SELL')

        # Display button outside the loop
        col_button1, col_button2 = st.columns([2, 1])

        with col_button2:
            if total_sell > 0:
                button_text = f"Execute Strategy (Buy ${total_buy:,.0f}, Sell ${total_sell:,.0f})"
            else:
                button_text = f"Invest ${total_buy:,.0f}"

            if st.button(button_text, type="primary", use_container_width=True):
                invested, sold = execute_recommendations(recommendations)
                if sold > 0:
                    st.success(f"✅ Executed: Bought ${invested:,.0f}, Sold ${sold:,.0f}")
                else:
                    st.success(f"✅ Successfully invested ${invested:,.0f}!")
                st.rerun()  # Refresh display to show updated portfolio values

        st.markdown("### AI Investment Strategy")

        for rec in recommendations:
            priority_color = "🔴" if rec['priority'] == 'High' else "🟡" if rec['priority'] == 'Medium' else "🟢"
            with st.expander(f"{priority_color} {rec['action']} {rec['shares']} shares of {rec['symbol']} - {rec['category']} (${rec['cost']:.0f})"):
                # Header with key metrics
                col_header1, col_header2, col_header3, col_header4 = st.columns(4)

                with col_header1:
                    action_color = "🟢" if rec['action'] == 'BUY' else "🔴"
                    st.write(f"**Action:** {action_color} {rec['action']}")
                    st.write(f"**Shares:** {rec['shares']}")
                    # Get price from expanded stock data
                    expanded_symbols = ['VTI', 'VTIAX', 'BND', 'VNQ', 'SPY', 'QQQ', 'IWM', 'EFA', 'TLT', 'IYR',
                                     'VEA', 'VWO', 'AGG', 'BNDX', 'VXUS', 'VUG', 'VTV', 'VYM', 'SCHD', 'DGRO']
                    expanded_stock_data = get_stock_data(expanded_symbols)
                    price = expanded_stock_data.get(rec['symbol'], {}).get('price', stock_data.get(rec['symbol'], {}).get('price', 0))
                    st.write(f"**Price:** ${price:.2f}")

                with col_header2:
                    st.write(f"**Amount:** ${rec['cost']:.0f}")
                    st.write(f"**Category:** {rec['category']}")
                    st.write(f"**Priority:** {priority_color} {rec['priority']}")

                with col_header3:
                    st.write(f"**AI Generated:** 🤖 Yes")
                    st.write(f"**Reasoning:** {rec['reasoning'][:50]}...")

                with col_header4:
                    st.write(f"**Strategy:** AI Portfolio Optimization")
                    st.write(f"**Type:** {rec['action']} Order")

                    # AI reasoning
                st.markdown("#### 🤖 AI Reasoning:")
                st.write(f"**{rec['reasoning']}**")

                # Market data for this specific asset
                expanded_symbols = ['VTI', 'VTIAX', 'BND', 'VNQ', 'SPY', 'QQQ', 'IWM', 'EFA', 'TLT', 'IYR',
                                 'VEA', 'VWO', 'AGG', 'BNDX', 'VXUS', 'VUG', 'VTV', 'VYM', 'SCHD', 'DGRO']
                expanded_stock_data = get_stock_data(expanded_symbols)
                data = expanded_stock_data.get(rec['symbol'], stock_data.get(rec['symbol'], {}))
                st.markdown("#### Current Market Data:")
                col_data1, col_data2, col_data3 = st.columns(3)

                with col_data1:
                    change = data.get('change', 0)
                    dividend = data.get('dividend_yield', 0)
                    st.write(f"**Price Change:** {change:+.2f}%")
                    st.write(f"**Dividend Yield:** {dividend:.2f}%")

                with col_data2:
                    pe_ratio = data.get('pe_ratio')
                    if isinstance(pe_ratio, (int, float)):
                        st.write(f"**PE Ratio:** {pe_ratio:.1f}")
                    else:
                        st.write(f"**PE Ratio:** N/A")
                    st.write(f"**AI Generated:** 🤖")

                with col_data3:
                    st.write(f"**Action Type:** {rec['action']}")
                    st.write(f"**Priority:** {rec['priority']}")

        st.markdown("---")

else:
    st.success("Portfolio is optimally invested. AI will monitor for new deposits.")

# Recalculate portfolio values after potential investments
total_portfolio_value, current_breakdown = calculate_portfolio_value(st.session_state.portfolio, stock_data)
total_account_value = total_portfolio_value + st.session_state.cash_balance
uninvested_pct = (st.session_state.cash_balance / total_account_value) * 100

# Portfolio Visualization
st.markdown("### Portfolio Allocation")

col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.markdown("**Target vs Current**")
    categories = list(st.session_state.target_allocation.keys())
    target_values = [st.session_state.target_allocation[cat] for cat in categories]
    current_values = [(current_breakdown.get(cat, 0) / total_account_value) * 100 for cat in categories]

    fig = go.Figure()
    fig.add_trace(go.Bar(name='Target', x=categories, y=target_values, marker_color='lightblue'))
    fig.add_trace(go.Bar(name='Current', x=categories, y=current_values, marker_color='darkblue'))
    fig.update_layout(barmode='group', height=300, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

with col_chart2:
    st.markdown("**Current Holdings**")
    holdings_data = []
    for symbol, holding in st.session_state.portfolio.items():
        if symbol in stock_data:
            value = holding['shares'] * stock_data[symbol]['price']
            holdings_data.append({
                'Symbol': symbol,
                'Shares': holding['shares'],
                'Value': f"${value:,.0f}",
                'Price': f"${stock_data[symbol]['price']:.2f}"
            })

    if holdings_data:
        st.dataframe(pd.DataFrame(holdings_data), hide_index=True, use_container_width=True)

# Execution History
if st.session_state.execution_history:
    st.markdown("### Recent AI Actions")
    recent_actions = st.session_state.execution_history[:5]
    history_df = pd.DataFrame(recent_actions)
    st.dataframe(history_df, hide_index=True, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("*This AI runs continuously, automatically investing new deposits to maintain optimal portfolio allocation.*")
