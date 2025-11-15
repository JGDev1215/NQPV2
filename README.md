# Enhanced Market Predictor

A Flask web application that implements an Enhanced Market Predictor for **NQ=F (NASDAQ-100 Futures)**, **ES=1 and **FTSE100 Index**, providing real-time market analysis with weighted signal calculations.

## Features

- **Dual Instrument Tracking**: Simultaneous analysis of NQ=F and FTSE100
- **9 Reference Levels**: Previous Day High/Low, 30-Min/Hourly/4-Hourly/Daily/Weekly/Monthly Opens, Previous Week Open
- **Weighted Signal System**: Normalized weights summing to 1.0 for accurate predictions
- **Real-time Updates**: Auto-refresh every 60 seconds
- **Responsive UI**: Bootstrap 5 mobile-first design
- **Smart Caching**: 60-second cache to avoid API rate limiting
- **Production Ready**: Configured for Render.com deployment

## Signal Logic

### Reference Levels & Weights

| Reference Level | Weight |
|----------------|--------|
| Previous Day High | 0.0709 |
| Previous Day Low | 0.0709 |
| 30-Minute Open | 0.1064 |
| Hourly Open | 0.1418 |
| 4-Hourly Open | 0.1773 |
| Daily Open | 0.2482 |
| Weekly Open | 0.1064 |
| Monthly Open | 0.0355 |
| Previous Week Open | 0.0426 |

### Calculation Method

1. **Signal Generation**: For each reference level:
   - Signal = 1 if Current Price > Reference Level (BULLISH)
   - Signal = 0 if Current Price ≤ Reference Level (BEARISH)

2. **Weighted Score**: `Σ (Signal × Weight)`

3. **Prediction**:
   - BULLISH if Weighted Score ≥ 0.5
   - BEARISH if Weighted Score < 0.5

4. **Confidence**: `|((Score - 0.5) / 0.5)| × 100%`

## Tech Stack

- **Backend**: Flask 3.0.0
- **Data Source**: yfinance 0.2.38
- **Data Processing**: pandas 2.2.0
- **Timezone Handling**: pytz 2024.1
- **Production Server**: gunicorn 21.2.0
- **Frontend**: Bootstrap 5.3.2, Vanilla JavaScript

## Local Setup

### Prerequisites

- Python 3.13.0 or higher
- pip (Python package installer)

### Installation

1. **Clone or navigate to the Predictor directory**:
   ```bash
   cd Predictor
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment file** (optional):
   ```bash
   cp .env.example .env
   ```

5. **Run the application**:
   ```bash
   python app.py
   ```

6. **Access the dashboard**:
   Open your browser and navigate to `http://localhost:5000`

## Deployment to Render.com

### Quick Deploy

1. **Create a new Web Service** on [Render.com](https://render.com)

2. **Connect your repository**

3. **Configure the service**:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Port**: Render will automatically set the PORT environment variable

4. **Deploy**: Click "Create Web Service"

### Environment Variables (Optional)

No environment variables are required for basic operation. The app will use sensible defaults:
- `PORT`: Automatically set by Render (default: 5000)
- `FLASK_ENV`: Set to production
- `FLASK_DEBUG`: Set to False

### Testing the Deployment

Once deployed, your app will be available at:
```
https://your-app-name.onrender.com
```

## Project Structure

**NEW: Modular Architecture** - The application has been refactored into a clean, modular structure for better maintainability and testability.

```
NasdaqPredictor-main/
├── app.py                          # Main Flask application (30 lines!)
├── scripts/                        # Utility scripts
│   ├── README.md                  # Script documentation
│   ├── app_backup.py              # Original monolithic version (legacy)
│   ├── backfill_24h_predictions.py # Prediction backfill utility
│   ├── test_implementation.py     # Implementation tests
│   └── trigger_sync.py            # Manual sync trigger
│
├── templates/
│   └── index.html                 # Dashboard UI
│
├── nasdaq_predictor/               # Main package
│   ├── __init__.py
│   │
│   ├── config/                     # Configuration layer
│   │   ├── __init__.py
│   │   └── settings.py            # Constants, weights, trading sessions
│   │
│   ├── models/                     # Data models layer
│   │   ├── __init__.py
│   │   └── market_data.py         # Dataclasses for type safety
│   │
│   ├── data/                       # Data access layer
│   │   ├── __init__.py
│   │   ├── fetcher.py             # YahooFinanceDataFetcher
│   │   └── processor.py           # Data filtering & transformation
│   │
│   ├── analysis/                   # Business logic layer
│   │   ├── __init__.py
│   │   ├── reference_levels.py    # Calculate 9 reference levels
│   │   ├── signals.py             # Signal generation & prediction
│   │   ├── risk_metrics.py        # Stop loss, flip scenarios
│   │   ├── sessions.py            # ICT killzone analysis
│   │   ├── confidence.py          # Confidence horizons
│   │   └── volatility.py          # Volatility calculations
│   │
│   ├── services/                   # Service layer
│   │   ├── __init__.py
│   │   └── market_service.py      # Orchestrates all analysis
│   │
│   ├── api/                        # API layer
│   │   ├── __init__.py
│   │   └── routes.py              # Flask routes & endpoints
│   │
│   └── utils/                      # Utilities
│       ├── __init__.py
│       ├── cache.py               # ThreadSafeCache
│       ├── timezone.py            # Timezone helpers
│       └── market_status.py       # Market status checking
│
├── tests/                          # Test suite
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures
│   ├── unit/                      # Unit tests
│   │   └── test_signals.py
│   └── integration/               # Integration tests
│
├── requirements.txt               # Python dependencies
├── Procfile                       # Render.com process file
├── runtime.txt                    # Python version specification
├── .env.example                   # Environment variables template
└── README.md                      # This file
```

### Architecture Benefits

1. **Separation of Concerns**: Each module has a single, well-defined responsibility
2. **Testability**: Pure functions can be tested independently without Flask context
3. **Reusability**: Import specific modules without loading the entire application
4. **Maintainability**: Easy to locate and modify specific functionality
5. **Extensibility**: Add new instruments or signals without touching core code
6. **Type Safety**: Dataclasses provide structure and validation

## API Endpoints

### `GET /`
Renders the main dashboard interface.

### `GET /api/data`
Returns JSON data with market analysis for both instruments.

**Response Structure**:
```json
{
  "data": {
    "NQ=F": {
      "current_price": 15234.50,
      "current_time": "2025-01-10 14:30:00 UTC",
      "signals": { ... },
      "weighted_score": 0.6523,
      "prediction": "BULLISH",
      "confidence": 30.46,
      "bullish_count": 7,
      "total_signals": 9
    },
    "^FTSE": { ... }
  },
  "cached": false,
  "timestamp": "2025-01-10 14:30:00"
}
```

## Features in Detail

### Caching System
- 60-second in-memory cache to prevent API rate limiting
- Automatic cache invalidation after expiry
- Cache status visible in API responses

### Error Handling
- Individual instrument failure isolation
- Graceful degradation (one instrument can fail without affecting the other)
- User-friendly error messages in UI

### Timezone Awareness
- All calculations performed in UTC
- Proper timezone conversion for reference level calculations
- Displayed timestamps include timezone information

### Responsive Design
- Mobile-first Bootstrap 5 layout
- Two-column desktop view
- Single-column mobile view
- Touch-friendly interface

## Performance Considerations

- **Data Caching**: Reduces API calls to yfinance
- **Efficient Calculations**: Optimized pandas operations
- **Lazy Loading**: Data fetched only when needed
- **Client-side Refresh**: JavaScript handles auto-refresh without full page reload

## Troubleshooting

### Issue: "Failed to fetch data"

**Possible Causes**:
- yfinance API rate limiting
- Network connectivity issues
- Invalid ticker symbols

**Solutions**:
- Wait 60 seconds for cache to expire
- Check internet connection
- Verify ticker symbols are correct (NQ=F, ^FTSE)

### Issue: Missing reference levels (N/A values)

**Cause**: Insufficient historical data for the time period

**Solution**: This is normal during market closed hours or holidays. The app will calculate predictions with available data.

### Issue: Port already in use

**Solution**:
```bash
# Find and kill the process using port 5000
lsof -ti:5000 | xargs kill -9

# Or use a different port
PORT=5001 python app.py
```

## Development

### Running Tests

The project now includes a test suite using pytest:

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage report
pytest --cov=nasdaq_predictor --cov-report=html

# Run specific test file
pytest tests/unit/test_signals.py
```

### Running in Debug Mode

For development, you can enable debug mode:

```python
# In app.py, change:
app.run(host='0.0.0.0', port=port, debug=True)
```

### Adding New Reference Levels

With the modular structure, adding new reference levels is easier:

1. Add calculation function in `nasdaq_predictor/analysis/reference_levels.py`
2. Update the `ReferenceLevels` dataclass in `nasdaq_predictor/models/market_data.py`
3. Add the weight to `WEIGHTS` dictionary in `nasdaq_predictor/config/settings.py`
4. Update `calculate_all_reference_levels()` to include your new level
5. Update the label in `REFERENCE_LABELS` in `templates/index.html`
6. Ensure weights sum to 1.0
7. Write unit tests for your new calculation

### Module Usage Examples

Import and use specific modules without running the Flask app:

```python
# Example: Calculate reference levels programmatically
from nasdaq_predictor.data.fetcher import YahooFinanceDataFetcher
from nasdaq_predictor.analysis.reference_levels import calculate_all_reference_levels

# Fetch data
fetcher = YahooFinanceDataFetcher()
data = fetcher.fetch_ticker_data('NQ=F')

# Calculate reference levels
ref_levels = calculate_all_reference_levels(
    data['hourly_hist'],
    data['minute_hist'],
    data['daily_hist'],
    data['current_time']
)

print(f"Daily Open: {ref_levels.daily_open}")
```

## License

This project is provided as-is for educational and trading analysis purposes.

## Disclaimer

This application is for informational purposes only. Market predictions are based on historical data and technical analysis. Always conduct your own research and consult with financial advisors before making trading decisions.

---

**Built with Flask and Bootstrap 5**
**Data powered by yfinance**
