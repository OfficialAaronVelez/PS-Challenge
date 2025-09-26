"""
PayCheck-to-Portfolio AI - Main Application
Refactored modular version for better maintainability
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Import our custom modules
from config import PAGE_CONFIG, INITIAL_CASH_BALANCE, INITIAL_PORTFOLIO, TARGET_ALLOCATION
from data_utils import fetch_market_data, calculate_portfolio_value
from ai_services import analyze_market_conditions, get_ai_recommendations
from portfolio_manager import execute_recommendations, generate_diversified_recommendations
from ui_components import apply_custom_css, render_header, render_account_overview, render_investment_alert, render_market_research

# Configure page
st.set_page_config(**PAGE_CONFIG)

# Apply custom styling
apply_custom_css()

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.cash_balance = INITIAL_CASH_BALANCE
    st.session_state.portfolio = INITIAL_PORTFOLIO
    st.session_state.target_allocation = TARGET_ALLOCATION
    st.session_state.execution_history = []
    st.session_state.market_analysis_cache = None
    st.session_state.ai_recommendations_cache = None
    st.session_state.last_cash_amount = None
    st.session_state.just_invested = False

# Main App
render_header()

# Demo Controls
col1, col2 = st.columns([3, 1])

with col2:
    if st.button("+ Add $800 Paycheck", type="secondary"):
        st.session_state.cash_balance += 800
        st.success("New paycheck deposit detected!")

# Get market data
stock_data = fetch_market_data(list(st.session_state.portfolio.keys()))

if not stock_data:
    st.error("Unable to fetch market data. Please refresh.")
    st.stop()

# Calculate metrics
total_portfolio_value, current_breakdown = calculate_portfolio_value(st.session_state.portfolio, stock_data)
total_account_value = total_portfolio_value + st.session_state.cash_balance
uninvested_pct = (st.session_state.cash_balance / total_account_value) * 100

# Render account overview
render_account_overview(total_portfolio_value, st.session_state.cash_balance, total_account_value, uninvested_pct)

# AI Analysis & Action
if st.session_state.cash_balance > 500:
    # Market research will be moved to bottom of page

    # Alert and Action
    col_alert, col_action = st.columns([2, 1])

    with col_alert:
        render_investment_alert(st.session_state.cash_balance, uninvested_pct)

    # Get AI-generated recommendations (only if not cached)
    if st.session_state.ai_recommendations_cache is None:
        with st.spinner("🤖 AI is generating investment recommendations..."):
            # Perform market research first
            market_analysis, research_data = analyze_market_conditions(stock_data)
            st.session_state.market_analysis_cache = market_analysis

            # Get AI recommendations
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
        market_analysis = st.session_state.market_analysis_cache

    # Display AI Analysis
    st.markdown("### 🤖 AI Financial Advisor Analysis")
    with st.expander("View AI Analysis", expanded=True):
        st.markdown(f"**Market Assessment:** {ai_data['analysis']}")
        st.markdown(f"**Risk Assessment:** {ai_data['risk_assessment']}")
        st.markdown(f"**Market Timing:** {ai_data['market_timing']}")

    # Convert AI recommendations to our format
    recommendations = []

    for rec in ai_data.get('recommendations', []):
        symbol = rec['symbol']
        # Get expanded stock data for AI recommendations
        from config import RESEARCH_SYMBOLS
        expanded_stock_data = fetch_market_data(RESEARCH_SYMBOLS)

        if symbol in expanded_stock_data:
            price = expanded_stock_data[symbol]['price']
            cost = rec['shares'] * price
            from data_utils import get_asset_category
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
        from config import RESEARCH_SYMBOLS
        expanded_stock_data = fetch_market_data(RESEARCH_SYMBOLS)
        recommendations = generate_diversified_recommendations(
            st.session_state.cash_balance,
            st.session_state.target_allocation,
            expanded_stock_data
        )

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
                    from config import RESEARCH_SYMBOLS
                    expanded_stock_data = fetch_market_data(RESEARCH_SYMBOLS)
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
                from config import RESEARCH_SYMBOLS
                expanded_stock_data = fetch_market_data(RESEARCH_SYMBOLS)
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

# AI Market Research & Analysis (moved to bottom)
if st.session_state.cash_balance > 500:
    market_analysis = st.session_state.market_analysis_cache
    if market_analysis:
        render_market_research(market_analysis)

# Execution History
if st.session_state.execution_history:
    st.markdown("### Recent AI Actions")
    recent_actions = st.session_state.execution_history[:5]
    history_df = pd.DataFrame(recent_actions)
    st.dataframe(history_df, hide_index=True, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("*This AI runs continuously, automatically investing new deposits to maintain optimal portfolio allocation.*")
