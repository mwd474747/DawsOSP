# Trinity 3.0 - Deployment Guide

**Status**: Production Ready ✅
**Platform**: Streamlit
**Port**: 8501

---

## 🚀 Quick Start

### Option 1: Automated Deployment (Recommended)

```bash
cd trinity3/
./deploy.sh
```

This script will:
1. Create/activate virtual environment
2. Install all dependencies
3. Check API keys
4. Launch Streamlit server at http://localhost:8501

### Option 2: Manual Deployment

```bash
cd trinity3/

# Create virtual environment (first time only)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Launch Streamlit
streamlit run main.py --server.port=8501
```

---

## 🔑 API Keys (Optional)

Trinity 3.0 works without API keys using mock data, but for full functionality:

### Required for Intelligence Layer
```bash
export ANTHROPIC_API_KEY="your_anthropic_key_here"
```
- Enables entity extraction
- Enables conversation memory
- Enables natural language understanding

### Required for Real Market Data
```bash
export OPENBB_API_KEY="your_openbb_key_here"
```
- Enables real-time market data
- Enables historical price data
- Enables fundamental data

### Optional API Keys
```bash
export FRED_API_KEY="your_fred_key_here"          # Economic data
export FMP_API_KEY="your_fmp_key_here"            # Financial data
export NEWSAPI_KEY="your_newsapi_key_here"        # News data
export POLYGON_API_KEY="your_polygon_key_here"    # Market data
```

---

## 📦 Dependencies

### Core (Required)
- `streamlit>=1.30.0` - Web framework
- `pandas>=2.0.0` - Data manipulation
- `numpy>=1.24.0` - Numerical computing
- `plotly>=5.18.0` - Visualizations
- `networkx>=3.1` - Knowledge graph

### Intelligence Layer (Optional)
- `instructor>=1.0.0` - Structured extraction
- `pydantic>=2.0.0` - Data validation
- `anthropic>=0.25.0` - Claude API

### Data Integration (Optional)
- `openbb>=4.0.0` - Market data
- `psycopg2-binary>=2.9.0` - Database

---

## 🌐 Accessing the UI

Once deployed, access Trinity 3.0 at:

**Local**: http://localhost:8501

**Network**: http://[your-ip]:8501 (if server.address set to 0.0.0.0)

---

## 🎨 UI Features

### Main Dashboard
- Market overview with live quotes (SPY, QQQ, DIA, VIX)
- Economic cycle analysis (Dalio framework)
- Recession risk gauges
- Sector rotation analysis

### Query Interface
- Natural language queries
- Entity extraction (symbols, timeframes, metrics)
- Conversation memory (multi-turn)
- Reference resolution ("it", "that stock")

### Visualizations (22 types)
- Gauge charts (recession risk, confidence)
- Time series (price history, economic indicators)
- Candlestick charts (OHLC data)
- Heatmaps (correlations, sector performance)
- Dalio framework charts (debt cycle, empire cycle)
- Monte Carlo simulations
- Risk dashboards
- Portfolio analysis

### Quick Actions
- Dalio Cycles Analysis
- Recession Risk Assessment
- Housing Cycle Analysis
- Fed Policy Impact
- Empire Cycle Position
- Market Breadth
- Sector Rotation
- Economic Outlook

---

## 🧪 Testing the Deployment

### Test 1: Basic Load
```
1. Navigate to http://localhost:8501
2. Verify dashboard loads
3. Check market overview displays
```

### Test 2: Query Execution
```
1. Enter query: "What's the recession risk?"
2. Verify analysis displays
3. Check gauge chart renders
```

### Test 3: Conversation Flow
```
1. Enter query: "Analyze AAPL"
2. Verify stock analysis displays
3. Enter follow-up: "How does it compare to MSFT?"
4. Verify context is maintained
```

### Test 4: Visualization
```
1. Click "Dalio Cycles" quick action
2. Verify debt cycle charts display
3. Check empire cycle visualization
4. Verify All Weather allocation chart
```

---

## 🔧 Configuration

### Streamlit Config
Location: `trinity3/.streamlit/config.toml`

```toml
[server]
port = 8501
enableCORS = false

[theme]
primaryColor = "#4A9EFF"        # Sky blue
backgroundColor = "#0A0E27"      # Deep space blue
secondaryBackgroundColor = "#0F1629"
textColor = "#E8E9F3"           # Bright white-blue

[client]
toolbarMode = "minimal"
```

### Environment Variables
Create `.env` file in `trinity3/`:

```bash
# API Keys
ANTHROPIC_API_KEY=your_key_here
OPENBB_API_KEY=your_key_here

# Database (optional)
DATABASE_URL=postgresql://user:pass@localhost/trinity

# Cache (optional)
REDIS_URL=redis://localhost:6379
```

---

## 🐛 Troubleshooting

### Issue: Import Errors
**Solution**: Install missing dependencies
```bash
pip install -r requirements.txt
```

### Issue: Port Already in Use
**Solution**: Use different port
```bash
streamlit run main.py --server.port=8502
```

### Issue: No Market Data
**Solution**: Set OPENBB_API_KEY or use mock data mode

### Issue: Entity Extraction Not Working
**Solution**: Set ANTHROPIC_API_KEY for intelligence layer

### Issue: Slow Performance
**Solution**:
1. Check network connection
2. Verify API keys are valid
3. Consider enabling Redis cache

---

## 📊 Performance Optimization

### Enable Caching
```bash
# Install Redis
brew install redis  # macOS
sudo apt-get install redis  # Linux

# Start Redis
redis-server

# Set environment variable
export REDIS_URL=redis://localhost:6379
```

### Reduce API Calls
- Use mock data mode for development
- Enable KnowledgeLoader cache (30-min TTL)
- Limit pattern execution depth

---

## 🚀 Production Deployment

### Streamlit Cloud
1. Push code to GitHub
2. Connect repository to Streamlit Cloud
3. Set environment variables in Streamlit Cloud dashboard
4. Deploy

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY trinity3/ /app/

RUN pip install -r requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### AWS/GCP/Azure
1. Deploy Docker container
2. Configure load balancer
3. Set environment variables
4. Enable SSL/TLS

---

## 📞 Support

### Documentation
- Main docs: [TRINITY3_MIGRATION_COMPLETE.md](../TRINITY3_MIGRATION_COMPLETE.md)
- UI details: [VISUALIZATION_PRESERVATION_PLAN.md](VISUALIZATION_PRESERVATION_PLAN.md)
- Project memory: [CLAUDE.md](../CLAUDE.md)

### Common Queries
- "What's the recession risk?" - Recession analysis
- "Analyze AAPL stock" - Stock analysis
- "Show economic cycles" - Dalio framework
- "Compare AAPL and MSFT" - Comparative analysis
- "Review portfolio: 60% stocks, 40% bonds" - Portfolio analysis

---

## ✅ Deployment Checklist

- [ ] Python 3.11+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] API keys configured (optional)
- [ ] Streamlit config created (`.streamlit/config.toml`)
- [ ] Port 8501 available
- [ ] Firewall allows port 8501 (if remote access needed)
- [ ] Browser tested (Chrome/Firefox/Safari)
- [ ] Sample queries tested
- [ ] Visualizations verified

---

**Deployment Status**: Ready for production ✅
**Last Updated**: October 20, 2025
**Version**: Trinity 3.0
