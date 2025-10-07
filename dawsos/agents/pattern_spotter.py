"""PatternSpotter - Identifies recurring patterns in the graph

Phase 3.1: Comprehensive type hints added for better IDE support and type safety.
"""
from .base_agent import BaseAgent
from typing import Dict, Any, List, Optional
from core.typing_compat import TypeAlias
from datetime import datetime

# Type aliases for clarity
PatternDict: TypeAlias = Dict[str, Any]
PatternList: TypeAlias = List[PatternDict]
AnalysisResult: TypeAlias = Dict[str, Any]
ContextData: TypeAlias = Dict[str, Any]

class PatternSpotter(BaseAgent):
    """Spots patterns in data and behavior"""

    def __init__(self, graph: Any, llm_client: Optional[Any] = None) -> None:
        """Initialize PatternSpotter.

        Args:
            graph: Knowledge graph instance
            llm_client: Optional LLM client for AI-powered pattern recognition
        """
        super().__init__(graph=graph, name="PatternSpotter", llm_client=llm_client)
        self.vibe: str = "observant"
        self.spotted_patterns: PatternList = []

    def get_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
        You are PatternSpotter, finding recurring patterns.

        Recent events: {context.get('events', [])}
        Graph state: {context.get('graph_stats', {})}
        Time period: {context.get('period', 'recent')}

        What patterns do you see? Look for:
        - Sequences (A then B then C)
        - Cycles (repeating patterns)
        - Triggers (X always causes Y)
        - Anomalies (unusual events)

        Return:
        - pattern_type: sequence/cycle/trigger/anomaly
        - description: what you found
        - confidence: how sure (0-1)
        - actionable: can we trade on this?
        """

    def process(self, context: Any) -> AnalysisResult:
        """Process method for compatibility with patterns.

        Args:
            context: Analysis context (can be dict or other format)

        Returns:
            Dictionary with analysis results, patterns, or regime detection
        """
        # Extract analysis type
        if isinstance(context, dict):
            analysis_type = context.get('analysis_type', 'general')
            data = context.get('data', {})
        else:
            analysis_type = 'general'
            data = {}

        # Use real pattern detection algorithms for macro trends
        if analysis_type == 'macro_trends':
            patterns = self._analyze_macro_trends(data)
            return {
                'response': 'Analyzed macro economic patterns using data-driven algorithms',
                'patterns': patterns
            }
        elif analysis_type == 'regime' or analysis_type == 'quick_regime':
            regime_analysis = self._detect_market_regime(data)
            return {
                'response': 'Detected market regime using multi-factor analysis',
                'regime': regime_analysis.get('regime', 'Unknown'),
                'confidence': regime_analysis.get('confidence', 0.0),
                'indicators': regime_analysis.get('indicators', [])
            }

        return {
            'response': f'Analyzed patterns for {analysis_type}',
            'patterns': []
        }

    def spot(self, lookback_days: int = 7) -> PatternList:
        """Main pattern spotting method - finds all pattern types.

        Args:
            lookback_days: How many days to look back for patterns

        Returns:
            List of discovered patterns (sequences, cycles, triggers, anomalies)
        """
        if not self.graph:
            return []

        patterns = []

        # Look for sequence patterns
        sequences = self._find_sequences()
        patterns.extend(sequences)

        # Look for cycles
        cycles = self._find_cycles()
        patterns.extend(cycles)

        # Look for trigger patterns
        triggers = self._find_triggers()
        patterns.extend(triggers)

        # Look for anomalies
        anomalies = self._find_anomalies()
        patterns.extend(anomalies)

        # Store the best patterns
        self.spotted_patterns = patterns[:10]

        return patterns

    def _find_sequences(self) -> PatternList:
        """Find sequential patterns (A->B->C).

        Returns:
            List of sequence patterns with occurrences and confidence
        """
        sequences = []

        if not self.graph:
            return sequences

        # Group edges by time
        edge_sequences = {}
        for edge in self.graph.get_all_edges():
            # Group by day
            created = edge.get('created', '')
            if created:
                day = created.split('T')[0]
                if day not in edge_sequences:
                    edge_sequences[day] = []
                edge_sequences[day].append(edge)

        # Look for repeated sequences
        sequence_counts = {}
        for day, edges in edge_sequences.items():
            if len(edges) >= 2:
                # Create sequence signature
                sequence = tuple([(e['from'], e['to'], e['type']) for e in edges[:3]])
                sequence_counts[sequence] = sequence_counts.get(sequence, 0) + 1

        # Find repeated sequences
        for sequence, count in sequence_counts.items():
            if count >= 2:  # Seen at least twice
                sequences.append({
                    "pattern_type": "sequence",
                    "description": f"Pattern: {sequence[0][0]} -> {sequence[0][1]} often repeats",
                    "occurrences": count,
                    "confidence": min(count / 10, 1.0),
                    "actionable": count >= 3
                })

        return sequences

    def _find_cycles(self) -> PatternList:
        """Find cyclical patterns (feedback loops).

        Returns:
            List of up to 5 cycle patterns
        """
        cycles = []

        if not self.graph:
            return cycles

        # Look for nodes that connect back to themselves through other nodes
        for node_id, _ in self.graph.get_all_nodes():
            paths = self.graph.trace_connections(node_id, max_depth=4)
            for path in paths:
                if path and path[-1].get('to') == node_id:
                    cycles.append({
                        "pattern_type": "cycle",
                        "description": f"Cycle detected: {node_id} influences itself",
                        "path_length": len(path),
                        "confidence": 0.7,
                        "actionable": True
                    })

        return cycles[:5]  # Limit to top 5 cycles

    def _find_triggers(self) -> PatternList:
        """Find trigger patterns (X causes Y).

        Returns:
            List of causal trigger patterns with strength > 0.7
        """
        triggers = []

        if not self.graph:
            return triggers

        # Look for strong causal relationships
        for edge in self.graph.get_all_edges():
            if edge.get('type') in ['causes', 'triggers'] and edge.get('strength', 0) > 0.7:
                triggers.append({
                    "pattern_type": "trigger",
                    "description": f"{edge['from']} strongly {edge['type']} {edge['to']}",
                    "strength": edge['strength'],
                    "confidence": edge['strength'],
                    "actionable": True,
                    "trigger": edge['from'],
                    "target": edge['to']
                })

        return triggers

    def _find_anomalies(self) -> PatternList:
        """Find unusual patterns (over-connected or isolated nodes).

        Returns:
            List of anomaly patterns
        """
        anomalies = []

        if not self.graph:
            return anomalies

        stats = self.graph.get_stats()
        avg_connections = stats.get('avg_connections', 0)

        # Find over-connected nodes
        for node_id, node in self.graph.get_all_nodes():
            connection_count = len(node.get('connections_in', [])) + len(node.get('connections_out', []))
            if connection_count > avg_connections * 3:
                anomalies.append({
                    "pattern_type": "anomaly",
                    "description": f"{node_id} is unusually connected ({connection_count} connections)",
                    "confidence": 0.8,
                    "actionable": True,
                    "node": node_id
                })

        # Find isolated nodes
        for node_id, node in self.graph.get_all_nodes():
            connection_count = len(node.get('connections_in', [])) + len(node.get('connections_out', []))
            if connection_count == 0:
                anomalies.append({
                    "pattern_type": "anomaly",
                    "description": f"{node_id} is isolated (no connections)",
                    "confidence": 0.9,
                    "actionable": False,
                    "node": node_id
                })

        return anomalies

    def remember_pattern(self, pattern: PatternDict) -> None:
        """Store a pattern for future reference in graph and memory.

        Args:
            pattern: Pattern dictionary to remember
        """
        pattern['discovered'] = datetime.now().isoformat()
        pattern['uses'] = 0

        # Add to graph as a pattern node
        if self.graph:
            pattern_id = f"pattern_{len(self.spotted_patterns)}"
            self.graph.patterns[pattern_id] = pattern

        self.spotted_patterns.append(pattern)

    def _analyze_macro_trends(self, data: ContextData) -> AnalysisResult:
        """Analyze macro economic trends using data-driven methods.

        Args:
            data: Dictionary with economic indicators

        Returns:
            Analysis result with cycle_stage, trend_strength, divergences
        """
        try:
            # Extract economic indicators from data
            economic_data = data.get('economic', {})
            if not economic_data:
                return {'cycle_stage': 'Unknown', 'confidence': 0.0}

            # Analyze growth vs inflation dynamics - handle both dict and direct value formats
            gdp_data = economic_data.get('GDP', {})
            cpi_data = economic_data.get('CPI', {})
            unemployment_data = economic_data.get('Unemployment', {})

            # Handle both nested dict and direct value formats
            gdp = gdp_data.get('value', 0) if isinstance(gdp_data, dict) else gdp_data if isinstance(gdp_data, (int, float)) else 0
            cpi = cpi_data.get('value', 0) if isinstance(cpi_data, dict) else cpi_data if isinstance(cpi_data, (int, float)) else 0
            unemployment = unemployment_data.get('value', 0) if isinstance(unemployment_data, dict) else unemployment_data if isinstance(unemployment_data, (int, float)) else 0

            # Calculate cycle stage based on economic data
            if isinstance(gdp, (int, float)) and isinstance(cpi, (int, float)):
                if gdp > 2.5 and cpi < 3.0:
                    cycle_stage = 'Early Cycle'
                    trend_strength = 0.8
                elif gdp > 2.0 and cpi > 3.0:
                    cycle_stage = 'Mid Cycle'
                    trend_strength = 0.7
                elif gdp < 2.0 and cpi > 3.0:
                    cycle_stage = 'Late Cycle'
                    trend_strength = 0.6
                else:
                    cycle_stage = 'Recession Risk'
                    trend_strength = 0.4
            else:
                cycle_stage = 'Data Insufficient'
                trend_strength = 0.0

            # Generate insights based on patterns
            divergences = []
            regime_shifts = []
            key_signals = []

            if isinstance(gdp, (int, float)) and isinstance(cpi, (int, float)):
                if gdp < 1.5 and cpi > 4.0:
                    divergences.append('Stagflation risk: Low growth with high inflation')
                if unemployment < 4.0 and cpi > 3.5:
                    divergences.append('Tight labor market driving inflation')

            return {
                'cycle_stage': cycle_stage,
                'trend_strength': trend_strength,
                'divergences': divergences,
                'regime_shifts': regime_shifts,
                'key_signals': key_signals,
                'confidence': 0.8 if trend_strength > 0.5 else 0.4
            }

        except Exception as e:
            print(f"Error in macro trend analysis: {e}")
            return {'cycle_stage': 'Analysis Error', 'confidence': 0.0}

    def _detect_market_regime(self, data: ContextData) -> AnalysisResult:
        """Detect market regime using multi-factor analysis.

        Args:
            data: Dictionary with market and economic indicators

        Returns:
            Analysis result with regime, confidence, and indicators
        """
        try:
            # Initialize regime indicators
            risk_on_score = 0
            total_indicators = 0

            # Analyze VIX if available
            if 'market' in data:
                market_data = data['market']
                if 'VIX' in market_data:
                    vix = market_data['VIX']
                    if isinstance(vix, (int, float)):
                        if vix < 20:
                            risk_on_score += 1
                        total_indicators += 1

            # Analyze economic indicators
            if 'economic' in data:
                economic_data = data['economic']

                # Low unemployment is risk-on
                unemployment = economic_data.get('Unemployment', {}).get('value')
                if isinstance(unemployment, (int, float)) and unemployment < 5.0:
                    risk_on_score += 1
                total_indicators += 1

                # Moderate inflation is risk-on
                inflation = economic_data.get('CPI', {}).get('value')
                if isinstance(inflation, (int, float)) and 2.0 <= inflation <= 4.0:
                    risk_on_score += 1
                total_indicators += 1

            # Calculate confidence and regime
            if total_indicators > 0:
                confidence = risk_on_score / total_indicators
                regime = 'Risk-On' if confidence > 0.6 else 'Risk-Off' if confidence < 0.4 else 'Neutral'
            else:
                confidence = 0.0
                regime = 'Unknown'

            # Generate indicator descriptions
            indicators = []
            if total_indicators > 0:
                if risk_on_score > total_indicators * 0.6:
                    indicators = ['Market optimism prevailing', 'Economic conditions supportive']
                elif risk_on_score < total_indicators * 0.4:
                    indicators = ['Risk aversion evident', 'Defensive positioning warranted']
                else:
                    indicators = ['Mixed signals', 'Regime transition possible']

            return {
                'regime': regime,
                'confidence': confidence,
                'indicators': indicators
            }

        except Exception as e:
            print(f"Error in regime detection: {e}")
            return {'regime': 'Analysis Error', 'confidence': 0.0, 'indicators': []}

class SequenceTracker(BaseAgent):
    """Sub-agent that tracks event sequences (Phase 3.1: Type hints added)"""

    def __init__(self, graph: Any, llm_client: Optional[Any] = None) -> None:
        """Initialize SequenceTracker.

        Args:
            graph: Knowledge graph instance
            llm_client: Optional LLM client
        """
        super().__init__("SequenceTracker", graph, llm_client)
        self.vibe: str = "methodical"
        self.sequences: List[Any] = []

class CycleFinder(BaseAgent):
    """Sub-agent that finds cycles (Phase 3.1: Type hints added)"""

    def __init__(self, graph: Any, llm_client: Optional[Any] = None) -> None:
        """Initialize CycleFinder.

        Args:
            graph: Knowledge graph instance
            llm_client: Optional LLM client
        """
        super().__init__("CycleFinder", graph, llm_client)
        self.vibe: str = "circular"

class AnomalyDetector(BaseAgent):
    """Sub-agent that detects anomalies (Phase 3.1: Type hints added)"""

    def __init__(self, graph: Any, llm_client: Optional[Any] = None) -> None:
        """Initialize AnomalyDetector.

        Args:
            graph: Knowledge graph instance
            llm_client: Optional LLM client
        """
        super().__init__("AnomalyDetector", graph, llm_client)
        self.vibe: str = "suspicious"