"""ForecastDreamer - Makes predictions based on the graph"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List
from datetime import datetime, timedelta

class ForecastDreamer(BaseAgent):
    """Dreams up forecasts based on graph knowledge"""

    def __init__(self, graph, llm_client=None):
        super().__init__(graph=graph, name="ForecastDreamer", llm_client=llm_client)
        self.vibe = "prophetic"
        self.predictions = []

    def get_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
        You are ForecastDreamer, seeing possible futures.

        Target: {context.get('target', 'unknown')}
        Current influences: {context.get('influences', [])}
        Historical patterns: {context.get('patterns', [])}
        Time horizon: {context.get('horizon', '1 day')}

        What will happen? Consider:
        - Direction (up/down/sideways)
        - Magnitude (small/medium/large move)
        - Confidence (how sure are you)
        - Key drivers (what's causing this)

        Return your prophecy.
        """

    def dream(self, target: str, horizon: str = "1d") -> Dict[str, Any]:
        """Main forecast method"""
        if not self.graph or target not in self.graph.nodes:
            return {"error": f"Cannot forecast {target} - not in graph"}

        # Use graph's built-in forecast
        forecast = self.graph.forecast(target, horizon)

        # Enhance with pattern-based insights
        patterns = self._find_relevant_patterns(target)
        forecast['patterns'] = patterns

        # Add narrative
        forecast['narrative'] = self._create_narrative(forecast)

        # Store prediction
        self._remember_prediction(target, forecast)

        return forecast

    def dream_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Forecast based on a scenario"""
        results = {}

        # Apply scenario changes
        for node, change in scenario.items():
            if node in self.graph.nodes:
                # Trace effects through graph
                effects = self._trace_scenario_effects(node, change)
                results[node] = effects

        return {
            "scenario": scenario,
            "effects": results,
            "summary": self._summarize_scenario(results)
        }

    def _find_relevant_patterns(self, target: str) -> List[Dict[str, Any]]:
        """Find patterns relevant to forecast"""
        relevant = []

        if not self.graph:
            return relevant

        # Check stored patterns
        for pattern_id, pattern in self.graph.patterns.items():
            if target in str(pattern):
                relevant.append(pattern)

        return relevant[:5]

    def _create_narrative(self, forecast: Dict[str, Any]) -> str:
        """Create a narrative explanation"""
        direction = forecast.get('forecast', 'neutral')
        confidence = forecast.get('confidence', 0)
        drivers = forecast.get('key_drivers', [])

        if confidence < 0.3:
            return f"Uncertain outlook for {forecast.get('target')}. Not enough data."
        elif direction == 'bullish':
            return f"Positive outlook driven by {len(drivers)} supporting factors. Confidence: {confidence:.0%}"
        elif direction == 'bearish':
            return f"Negative pressure from {len(drivers)} factors. Confidence: {confidence:.0%}"
        else:
            return f"Mixed signals suggest sideways movement. Watching {len(drivers)} factors."

    def _trace_scenario_effects(self, start_node: str, change: float) -> Dict[str, Any]:
        """Trace how a change propagates through the graph"""
        effects = {start_node: change}

        if not self.graph:
            return effects

        # Find all nodes this affects
        paths = self.graph.trace_connections(start_node, max_depth=2)

        for path in paths:
            if path:
                cumulative_effect = change
                for edge in path:
                    cumulative_effect *= edge.get('strength', 0.5)
                    target = edge.get('to')
                    if target:
                        effects[target] = effects.get(target, 0) + cumulative_effect

        return effects

    def _summarize_scenario(self, results: Dict[str, Any]) -> str:
        """Summarize scenario analysis"""
        total_nodes = sum(len(effects) for effects in results.values())
        max_effect = max(
            [abs(e) for effects in results.values() for e in effects.values()],
            default=0
        )

        if max_effect > 0.5:
            return f"Significant cascade effects across {total_nodes} nodes"
        elif max_effect > 0.2:
            return f"Moderate ripple effects on {total_nodes} nodes"
        else:
            return f"Limited impact, affecting {total_nodes} nodes"

    def _remember_prediction(self, target: str, forecast: Dict[str, Any]):
        """Store prediction for later validation"""
        prediction = {
            "target": target,
            "forecast": forecast,
            "made_at": datetime.now().isoformat(),
            "validate_at": (datetime.now() + timedelta(days=1)).isoformat(),
            "validated": False,
            "accuracy": None
        }
        self.predictions.append(prediction)

        # Keep last 100 predictions
        if len(self.predictions) > 100:
            self.predictions = self.predictions[-100:]

class PathTracer(BaseAgent):
    """Sub-agent that traces influence paths"""

    def __init__(self, graph, llm_client=None):
        super().__init__("PathTracer", graph, llm_client)
        self.vibe = "thorough"

class SignalAggregator(BaseAgent):
    """Sub-agent that combines multiple signals"""

    def __init__(self, graph, llm_client=None):
        super().__init__("SignalAggregator", graph, llm_client)
        self.vibe = "balanced"

class ConfidenceCalculator(BaseAgent):
    """Sub-agent that calculates forecast confidence"""

    def __init__(self, graph, llm_client=None):
        super().__init__("ConfidenceCalculator", graph, llm_client)
        self.vibe = "cautious"