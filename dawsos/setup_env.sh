#!/bin/bash
# Setup environment for DawsOS

echo "Setting up DawsOS environment..."

# Activate virtual environment
source venv/bin/activate

# Set API keys (replace with your actual keys)
export ANTHROPIC_API_KEY='your-anthropic-api-key-here'
export FMP_API_KEY='your-fmp-api-key-here'
export NEWSAPI_KEY='your-newsapi-key-here'

# Optional: Save to .env file for persistence
cat > .env << EOF
ANTHROPIC_API_KEY='$ANTHROPIC_API_KEY'
FMP_API_KEY='$FMP_API_KEY'
NEWSAPI_KEY='$NEWSAPI_KEY'
EOF

echo "Environment variables set!"
echo ""
echo "To test the setup, run:"
echo "  python test_api.py"
echo ""
echo "To start DawsOS, run:"
echo "  streamlit run main.py"
echo ""
echo "Remember to replace the placeholder API keys with your actual keys!"