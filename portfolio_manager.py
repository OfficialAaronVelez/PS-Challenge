"""
Portfolio management for PayCheck-to-Portfolio AI
Handles portfolio operations, recommendations, and execution
"""

import streamlit as st
from datetime import datetime
from config import TARGET_ALLOCATION, DIVERSIFIED_ETF_MAP
from data_utils import get_stock_data, get_asset_category, calculate_ai_score
from ai_services import generate_detailed_reasoning

def execute_recommendations(recommendations):
    """Execute AI recommendations (both buy and sell)"""
    total_invested = 0
    total_sold = 0

    # Clear caches since portfolio and cash will change
    st.session_state.market_analysis_cache = None
    st.session_state.ai_recommendations_cache = None
    st.session_state.just_invested = True
    # Clear the stock data cache to fetch data for new symbols
    from data_utils import fetch_market_data
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

def generate_algorithmic_recommendations(current_breakdown, target_allocation, total_value, cash_available, stock_data, market_analysis):
    """Generate investment recommendations using algorithmic approach when AI fails"""
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

def generate_diversified_recommendations(cash_available, target_allocation, stock_data):
    """Generate diversified recommendations when AI recommendations are empty"""
    recommendations = []
    remaining_cash = cash_available

    for category, target_pct in target_allocation.items():
        # Get all available symbols for this category
        available_symbols = DIVERSIFIED_ETF_MAP.get(category, [])

        # Find the best performing symbol in this category
        best_symbol = None
        best_performance = -999

        for symbol in available_symbols:
            if symbol in stock_data:
                performance = stock_data[symbol]['change']
                if performance > best_performance:
                    best_performance = performance
                    best_symbol = symbol

        # Use the best performing symbol, or fallback to first available
        if not best_symbol and available_symbols:
            best_symbol = available_symbols[0]

        if best_symbol and best_symbol in stock_data:
            price = stock_data[best_symbol]['price']
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

    return recommendations
