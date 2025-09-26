"""
AI services for PayCheck-to-Portfolio AI
Handles market analysis, AI recommendations, and investment strategy
"""

import streamlit as st
import google.generativeai as genai
import json
from config import GOOGLE_AI_API_KEY, GEMINI_MODEL, RESEARCH_SYMBOLS, SECTORS, TARGET_ALLOCATION
from data_utils import get_stock_data, get_asset_category, calculate_ai_score

# Configure Google AI
genai.configure(api_key=GOOGLE_AI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def analyze_market_conditions(stock_data):
    """AI market research and analysis"""
    research_data = get_stock_data(RESEARCH_SYMBOLS)

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
    for sector_name, symbols in SECTORS.items():
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

def get_ai_recommendations(market_analysis, stock_data, current_breakdown, target_allocation, total_value, cash_available):
    """Get AI-powered buy/sell recommendations from Google AI Studio"""
    try:
        # Expand available symbols for diversification
        all_available_symbols = RESEARCH_SYMBOLS
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
