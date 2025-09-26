"""
UI components for PayCheck-to-Portfolio AI
Handles styling, layout components, and user interface elements
"""

import streamlit as st

def apply_custom_css():
    """Apply custom CSS styling for the app"""
    st.markdown("""
    <style>
        /* Light theme styling */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        /* Custom metric styling */
        .metric-container {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 1rem;
            border-radius: 10px;
            border: 1px solid #dee2e6;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }

        /* Success message styling */
        .stSuccess {
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            border: 1px solid #c3e6cb;
            border-radius: 8px;
            padding: 1rem;
        }

        /* Error message styling */
        .stError {
            background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
            border: 1px solid #f5c6cb;
            border-radius: 8px;
            padding: 1rem;
        }

        /* Warning message styling */
        .stWarning {
            background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 1rem;
        }

        /* Button styling */
        .stButton > button {
            background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-weight: 600;
            box-shadow: 0 2px 4px rgba(0,123,255,0.3);
            transition: all 0.3s ease;
        }

        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,123,255,0.4);
        }

        /* Secondary button styling */
        .stButton > button[kind="secondary"] {
            background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
            box-shadow: 0 2px 4px rgba(108,117,125,0.3);
        }

        .stButton > button[kind="secondary"]:hover {
            box-shadow: 0 4px 8px rgba(108,117,125,0.4);
        }

        /* Expander styling */
        .streamlit-expanderHeader {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border: 1px solid #dee2e6;
            border-radius: 8px;
            font-weight: 600;
        }

        /* Chart container styling */
        .plotly-chart {
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        /* Dataframe styling */
        .dataframe {
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        /* Section headers */
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 2rem;
            font-weight: 700;
        }

        h2 {
            color: #34495e;
            border-bottom: 3px solid #3498db;
            padding-bottom: 0.5rem;
            margin-top: 2rem;
        }

        h3 {
            color: #2c3e50;
            margin-top: 1.5rem;
        }

        /* Alert styling */
        .alert-box {
            background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
            border: 1px solid #ffeaa7;
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
    </style>
    """, unsafe_allow_html=True)

def render_header():
    """Render the main app header"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin-bottom: 2rem;">
        <h1 style="color: white; margin: 0; font-size: 3rem; font-weight: 700;">💰 PayCheck-to-Portfolio AI</h1>
        <p style="color: #f8f9fa; font-size: 1.2rem; margin: 0.5rem 0 0 0;">Automatically invests your paycheck deposits using AI-powered portfolio optimization</p>
    </div>
    """, unsafe_allow_html=True)

def render_account_overview(total_portfolio_value, cash_balance, total_account_value, uninvested_pct):
    """Render the account overview metrics"""
    st.markdown("### 💼 Account Overview")
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

    with metric_col1:
        st.markdown(f"""
        <div class="metric-container">
            <h4 style="color: #495057; margin: 0 0 0.5rem 0;">📈 Total Portfolio</h4>
            <h2 style="color: #28a745; margin: 0;">${total_portfolio_value:,.0f}</h2>
        </div>
        """, unsafe_allow_html=True)

    with metric_col2:
        st.markdown(f"""
        <div class="metric-container">
            <h4 style="color: #495057; margin: 0 0 0.5rem 0;">💵 Cash Available</h4>
            <h2 style="color: #007bff; margin: 0;">${cash_balance:,.0f}</h2>
        </div>
        """, unsafe_allow_html=True)

    with metric_col3:
        st.markdown(f"""
        <div class="metric-container">
            <h4 style="color: #495057; margin: 0 0 0.5rem 0;">💰 Total Account Value</h4>
            <h2 style="color: #6f42c1; margin: 0;">${total_account_value:,.0f}</h2>
        </div>
        """, unsafe_allow_html=True)

    with metric_col4:
        color = "#dc3545" if uninvested_pct > 15 else "#28a745"
        st.markdown(f"""
        <div class="metric-container">
            <h4 style="color: #495057; margin: 0 0 0.5rem 0;">⚠️ Cash Uninvested</h4>
            <h2 style="color: {color}; margin: 0;">{uninvested_pct:.1f}%</h2>
        </div>
        """, unsafe_allow_html=True)

def render_investment_alert(cash_balance, uninvested_pct):
    """Render the investment alert section"""
    st.markdown(f"""
    <div class="alert-box">
        <h4 style="color: #856404; margin: 0 0 0.5rem 0;">⚠️ Investment Alert</h4>
        <p style="margin: 0; font-size: 1.1rem;"><strong>${cash_balance:,.0f}</strong> sitting uninvested ({uninvested_pct:.1f}% of portfolio)</p>
        <p style="margin: 0.5rem 0 0 0; color: #6c757d;">AI has completed market research and generated investment strategy...</p>
    </div>
    """, unsafe_allow_html=True)

def render_market_research(market_analysis):
    """Render the market research section"""
    st.markdown("### 🔍 AI Market Research & Analysis")

    # Display market research in a more compact format
    col_research1, col_research2 = st.columns(2)

    with col_research1:
        st.markdown("#### 📊 Market Sentiment")
        sentiment_color = "🟢" if market_analysis['market_sentiment'] == 'bullish' else "🔴" if market_analysis['market_sentiment'] == 'bearish' else "🟡"
        st.write(f"{sentiment_color} **{market_analysis['market_sentiment'].upper()}**")

        st.markdown("#### ⚠️ Risk Assessment")
        risk_color = "🔴" if market_analysis['risk_assessment'] == 'high' else "🟢" if market_analysis['risk_assessment'] == 'low' else "🟡"
        st.write(f"{risk_color} **{market_analysis['risk_assessment'].upper()}**")

        st.markdown("#### 🤖 AI Recommendation")
        rec_color = "🟢" if market_analysis['recommendation'] == 'aggressive_buy' else "🔴" if market_analysis['recommendation'] == 'defensive' else "🟡"
        st.write(f"{rec_color} **{market_analysis['recommendation'].replace('_', ' ').upper()}**")

    with col_research2:
        st.markdown("#### 💡 Key Market Insights")
        for insight in market_analysis['key_insights']:
            st.write(f"• {insight}")

    # Sector Analysis in a more compact format
    st.markdown("#### 📈 Sector Performance Analysis")
    sector_cols = st.columns(len(market_analysis['sector_analysis']))

    for i, (sector, data) in enumerate(market_analysis['sector_analysis'].items()):
        with sector_cols[i]:
            perf_color = "🟢" if data['performance'] > 0 else "🔴"
            st.markdown(f"**{sector}**")
            st.write(f"{perf_color} {data['performance']:+.2f}%")
            st.write(f"Yield: {data['dividend_yield']:.2f}%")
            st.write(f"Sentiment: {data['sentiment']}")

    st.markdown("---")
