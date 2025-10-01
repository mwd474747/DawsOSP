"""PatternSpotter - Identifies recurring patterns in the graph"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List
from datetime import datetime, timedelta

class PatternSpotter(BaseAgent):
    """Spots patterns in data and behavior"""

    def __init__(self, graph, llm_client=None):
        super().__init__("PatternSpotter", graph, llm_client)
        self.vibe = "observant"
        self.spotted_patterns = []

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

    def spot(self, lookback_days: int = 7) -> List[Dict[str, Any]]:
        """Main pattern spotting method"""
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

    def _find_sequences(self) -> List[Dict[str, Any]]:
        """Find sequential patterns (A->B->C)"""
        sequences = []

        if not self.graph or not self.graph.edges:
            return sequences

        # Group edges by time
        edge_sequences = {}
        for edge in self.graph.edges:
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

    def _find_cycles(self) -> List[Dict[str, Any]]:
        """Find cyclical patterns"""
        cycles = []

        if not self.graph:
            return cycles

        # Look for nodes that connect back to themselves through other nodes
        for node_id in self.graph.nodes:
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

    def _find_triggers(self) -> List[Dict[str, Any]]:
        """Find trigger patterns (X causes Y)"""
        triggers = []

        if not self.graph or not self.graph.edges:
            return triggers

        # Look for strong causal relationships
        for edge in self.graph.edges:
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

    def _find_anomalies(self) -> List[Dict[str, Any]]:
        """Find unusual patterns"""
        anomalies = []

        if not self.graph:
            return anomalies

        stats = self.graph.get_stats()
        avg_connections = stats.get('avg_connections', 0)

        # Find over-connected nodes
        for node_id, node in self.graph.nodes.items():
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
        for node_id, node in self.graph.nodes.items():
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

    def remember_pattern(self, pattern: Dict[str, Any]):
        """Store a pattern for future reference"""
        pattern['discovered'] = datetime.now().isoformat()
        pattern['uses'] = 0

        # Add to graph as a pattern node
        if self.graph:
            pattern_id = f"pattern_{len(self.spotted_patterns)}"
            self.graph.patterns[pattern_id] = pattern

        self.spotted_patterns.append(pattern)

class SequenceTracker(BaseAgent):
    """Sub-agent that tracks event sequences"""

    def __init__(self, graph, llm_client=None):
        super().__init__("SequenceTracker", graph, llm_client)
        self.vibe = "methodical"
        self.sequences = []

class CycleFinder(BaseAgent):
    """Sub-agent that finds cycles"""

    def __init__(self, graph, llm_client=None):
        super().__init__("CycleFinder", graph, llm_client)
        self.vibe = "circular"

class AnomalyDetector(BaseAgent):
    """Sub-agent that detects anomalies"""

    def __init__(self, graph, llm_client=None):
        super().__init__("AnomalyDetector", graph, llm_client)
        self.vibe = "suspicious"