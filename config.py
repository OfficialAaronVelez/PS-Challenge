"""
Configuration file for PayCheck-to-Portfolio AI
Contains API keys, constants, and app settings
"""

# Google AI Configuration
GOOGLE_AI_API_KEY = "AIzaSyDnWWA_BrdGi54GV9mh7xUPJfYTLKeE1mk"
GEMINI_MODEL = "gemini-2.5-flash"

# Streamlit Page Configuration
PAGE_CONFIG = {
    "page_title": "PayCheck-to-Portfolio AI",
    "page_icon": "📊",
    "layout": "wide"
}

# Initial Portfolio Settings
INITIAL_CASH_BALANCE = 2500.00
INITIAL_PORTFOLIO = {
    'VTI': {'shares': 12, 'symbol': 'VTI', 'name': 'Total Stock Market ETF'},
    'VTIAX': {'shares': 8, 'symbol': 'VTIAX', 'name': 'International Stock Index'},
    'BND': {'shares': 15, 'symbol': 'BND', 'name': 'Total Bond Market ETF'},
    'VNQ': {'shares': 5, 'symbol': 'VNQ', 'name': 'Real Estate ETF'}
}

TARGET_ALLOCATION = {
    'Stocks (US)': 60,
    'Stocks (Intl)': 20,
    'Bonds': 15,
    'Real Estate': 5
}

# Market Data Settings
CACHE_TTL = 300  # 5 minutes
RESEARCH_SYMBOLS = [
    'VTI', 'VTIAX', 'BND', 'VNQ', 'SPY', 'QQQ', 'IWM', 'EFA', 'TLT', 'IYR',
    'VEA', 'VWO', 'AGG', 'BNDX', 'VXUS', 'VUG', 'VTV', 'VYM', 'SCHD', 'DGRO'
]

# Asset Categories
ASSET_CATEGORIES = {
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

# Sector Analysis
SECTORS = {
    'US Large Cap': ['SPY', 'VTI'],
    'US Small Cap': ['IWM'],
    'International': ['EFA', 'VTIAX'],
    'Bonds': ['BND', 'TLT'],
    'Real Estate': ['VNQ', 'IYR'],
    'Tech': ['QQQ']
}

# Diversified ETF Mapping
DIVERSIFIED_ETF_MAP = {
    'Stocks (US)': ['VTI', 'SPY', 'QQQ', 'VUG', 'VTV', 'VYM', 'SCHD', 'DGRO'],
    'Stocks (Intl)': ['VTIAX', 'EFA', 'VEA', 'VWO', 'VXUS'],
    'Bonds': ['BND', 'TLT', 'AGG', 'BNDX'],
    'Real Estate': ['VNQ', 'IYR']
}
