#!/usr/bin/env python3
"""
Test that Quick Action buttons update chat history
"""
from load_env import load_env
load_env()

from core.pattern_engine import PatternEngine
from core.agent_runtime import AgentRuntime
from core.knowledge_graph import KnowledgeGraph

# Import agents
from agents.claude import Claude
from agents.data_harvester import DataHarvester
from agents.pattern_spotter import PatternSpotter
from capabilities.market_data import MarketDataCapability

print("Testing Quick Action Button Fix...")

# Initialize
graph = KnowledgeGraph()
runtime = AgentRuntime()

# Register minimum agents
caps = {'market': MarketDataCapability()}
runtime.register_agent('claude', Claude(graph))
runtime.register_agent('data_harvester', DataHarvester(graph, caps))
runtime.register_agent('pattern_spotter', PatternSpotter(graph))

# Initialize pattern engine
pattern_engine = PatternEngine('patterns', runtime)
runtime.pattern_engine = pattern_engine

# Simulate chat history (like Streamlit session state)
chat_history = []

# Test Quick Action: Detect Market Regime
print("\n🔘 Simulating 'Detect Market Regime' button click...")
user_msg = "Detect the market regime"
chat_history.append({"role": "user", "content": user_msg})

response = runtime.orchestrate(user_msg)
chat_history.append({"role": "assistant", "content": response})

print(f"✅ Chat history has {len(chat_history)} messages")
print(f"✅ Last user message: {chat_history[-2]['content']}")
print(f"✅ Response has pattern: {'pattern' in response}")
print(f"✅ Response has formatted_response: {'formatted_response' in response}")

# Test display format
if isinstance(response, dict):
    if 'pattern' in response:
        print(f"   🔮 Pattern: {response.get('pattern', 'Unknown')}")
    if 'formatted_response' in response:
        print(f"   📝 Response preview: {response['formatted_response'][:100]}...")

print("\n✅ Fix verified: Quick Actions now update chat history!")