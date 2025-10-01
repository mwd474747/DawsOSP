# DawsOS - Phase 1 Setup

## Quick Start

### 1. Set up Python environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Then edit `.env` and add your API keys:
```
ANTHROPIC_API_KEY=sk-ant-api03-...
FMP_API_KEY=your-fmp-key
NEWSAPI_KEY=your-news-key
```

### 3. Test the setup
```bash
python test_api.py
```

You should see:
- ✅ Claude API: Set
- ✅ Claude API working
- ✅ Agent system working

### 4. Run DawsOS
```bash
streamlit run main.py
```

Open http://localhost:8501 in your browser

## API Keys

### Required:
- **ANTHROPIC_API_KEY**: Powers agent intelligence
  - Get it at: https://console.anthropic.com/account/keys
  - Cost: ~$0.30 per session with Haiku model

### Optional but recommended:
- **FMP_API_KEY**: Real-time market data
  - Get it at: https://site.financialmodelingprep.com/developer/docs/
  - Free tier available (250 requests/day)

- **NEWSAPI_KEY**: News sentiment
  - Get it at: https://newsapi.org/register
  - Free tier: 100 requests/day

## Features Now Working

With API keys configured:

1. **Natural Language Chat**
   - "What's Apple's stock price?"
   - "How will inflation affect tech stocks?"
   - "Add Tesla to the graph"

2. **Real Intelligence**
   - Claude understands intent
   - Agents make real decisions
   - Graph learns from interactions

3. **Live Data**
   - Stock quotes (FMP)
   - Economic indicators (FRED - free)
   - News sentiment (NewsAPI)

## Testing the System

Try these commands in the chat:

```
"Add Apple stock to the graph"
"What's the GDP growth rate?"
"How are tech stocks doing today?"
"Find patterns in the market"
```

## Troubleshooting

If you see "Mock mode" responses:
1. Check your API keys are set: `echo $ANTHROPIC_API_KEY`
2. Restart the app after setting keys
3. Check test_api.py output for errors

## Cost Management

Using Claude 3 Haiku (cheapest):
- ~$0.001 per agent call
- ~$0.30 per hour of use
- Switch to mock mode to develop without costs

## Next Steps

The system is now de-mocked! You can:
1. Chat naturally and see real responses
2. Add real market data to the graph
3. Watch patterns emerge
4. See agents make actual decisions

The knowledge graph will grow with each interaction!