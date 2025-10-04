# PayCheck-to-Portfolio AI

An AI-powered investment portfolio management system that automatically invests paycheck deposits using intelligent market analysis and portfolio optimization.

## Features

- 🤖 **AI-Powered Analysis**: Real-time market sentiment and risk assessment
- 📊 **Smart Recommendations**: Intelligent buy/sell recommendations based on market conditions
- 💰 **Automatic Execution**: One-click investment execution with real-time portfolio updates
- 📈 **Portfolio Visualization**: Interactive charts and breakdowns of current holdings
- 🎯 **Target Allocation**: Maintains optimal asset allocation across stocks, bonds, and real estate
- ⚡ **Real-Time Data**: Live market data from multiple sources

## Setup

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd "Paystand Challenge"
```

### 2. Create Virtual Environment
```bash
python -m venv investment_ai_env
source investment_ai_env/bin/activate  # On Windows: investment_ai_env\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
```bash
# Copy the example environment file
cp env.example .env

# Edit .env and add your API key
nano .env  # or use your preferred editor
```

Add your Google AI API key to the `.env` file:
```
GOOGLE_AI_API_KEY=your_actual_api_key_here
```

**Get your Google AI API key from:** https://makersuite.google.com/app/apikey

### 5. Run the Application
```bash
streamlit run investment_ai_refactored.py
```

## Project Structure

```
Paystand Challenge/
├── investment_ai_refactored.py  # Main application (refactored)
├── investment_ai.py            # Original application (backup)
├── config.py                   # Configuration and constants
├── data_utils.py              # Market data and portfolio calculations
├── ai_services.py             # AI analysis and recommendations
├── ui_components.py           # UI components and styling
├── portfolio_manager.py       # Portfolio operations and execution
├── requirements.txt           # Python dependencies
├── env.example               # Environment variables template
├── .env                      # Your environment variables (create this)
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

## Usage

1. **Add Paycheck**: Click "+ Add $800 Paycheck" to simulate a paycheck deposit
2. **Review Analysis**: The AI analyzes market conditions and generates recommendations
3. **Execute Strategy**: Click "Invest $X" to execute the AI's investment strategy
4. **Monitor Portfolio**: View your updated portfolio allocation and recent actions

## Key Components

### AI Market Analysis
- Analyzes 20+ ETFs across multiple sectors
- Calculates market sentiment and risk assessment
- Provides sector-specific performance insights

### Investment Recommendations
- AI-generated buy/sell recommendations with detailed reasoning
- Considers portfolio balance, market conditions, and risk factors
- Supports both AI-powered and algorithmic fallback strategies

### Portfolio Management
- Real-time portfolio value calculations
- Automatic rebalancing to target allocations
- Execution history tracking

## Security

- API keys are stored in environment variables (not in code)
- `.env` file is gitignored to prevent accidental commits
- All sensitive configuration is externalized

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for educational and demonstration purposes.

## Support

For issues or questions, please open an issue in the GitHub repository.
