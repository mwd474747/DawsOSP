#!/usr/bin/env python3
"""Test script for API connections"""
import os
import sys

# Load environment variables
from load_env import load_env
load_env()

# Set API keys (you'll need to replace with your actual keys)
print("Testing API connections for DawsOS...")
print("-" * 50)

# Check environment variables
apis = {
    "ANTHROPIC_API_KEY": "Claude API",
    "FMP_API_KEY": "Financial Modeling Prep",
    "NEWSAPI_KEY": "News API"
}

print("Checking API keys:")
for key, name in apis.items():
    if os.getenv(key):
        print(f"✅ {name}: Set")
    else:
        print(f"❌ {name}: Not set")

print("\n" + "-" * 50)
print("Testing Claude connection...")

# Test Claude
from core.llm_client import LLMClient

client = LLMClient()
test_prompt = "Respond with a simple JSON object containing one field 'status' with value 'working'"
response = client.complete(test_prompt, parse_json=True)

if isinstance(response, dict) and 'error' not in response:
    print(f"✅ Claude API working: {response}")
else:
    print(f"❌ Claude API failed: {response}")

print("\n" + "-" * 50)
print("Testing agent system...")

# Test an agent
from agents.claude import Claude
from core.knowledge_graph import KnowledgeGraph

graph = KnowledgeGraph()
claude = Claude(graph)

test_input = "What is Apple's stock price?"
result = claude.process(test_input)

print(f"User input: {test_input}")
print(f"Claude response: {result}")

if result.get('intent'):
    print(f"✅ Agent system working!")
    print(f"  - Intent: {result.get('intent')}")
    print(f"  - Entities: {result.get('entities')}")
    print(f"  - Response: {result.get('friendly_response')}")
else:
    print(f"❌ Agent system not fully functional")

print("\n" + "-" * 50)
print("Testing data capabilities...")

# Test FRED
from capabilities.fred import FREDCapability

fred = FREDCapability()
gdp = fred.get_latest('GDP')
if gdp and 'error' not in gdp:
    print(f"✅ FRED API working: Latest GDP = {gdp.get('value')}")
else:
    print(f"❌ FRED API failed")

print("\n" + "-" * 50)
print("\nTo set API keys, run:")
print("export ANTHROPIC_API_KEY='your-key-here'")
print("export FMP_API_KEY='your-key-here'")
print("export NEWSAPI_KEY='your-key-here'")
print("\nThen run: python test_api.py")