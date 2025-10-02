"""Core Invariants - The physics of DawsOS that never change"""
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, List
from core.confidence_calculator import confidence_calculator

class GraphInvariants:
    """Immutable rules that protect graph integrity"""

    # HARD LIMITS - These prevent system collapse
    MAX_NODES = 100_000  # Prevent memory overflow
    MAX_EDGES_PER_NODE = 100  # Prevent super-nodes
    MAX_EDGE_STRENGTH = 1.0  # Normalized strength
    MIN_EDGE_STRENGTH = 0.0  # No negative relationships
    MAX_GRAPH_DEPTH = 10  # Prevent infinite recursion

    # NODE RULES - These ensure data quality
    REQUIRED_NODE_FIELDS = ['id', 'type', 'created']
    VALID_NODE_TYPES = ['indicator', 'stock', 'sector', 'event', 'pattern', 'news']
    NODE_ID_PATTERN = r'^[a-zA-Z0-9_-]+$'  # No special chars

    # EDGE RULES - These maintain relationship logic
    VALID_RELATIONSHIPS = [
        'causes', 'correlates', 'inverse', 'supports',
        'pressures', 'leads', 'lags', 'contains', 'influences',
        'impacts', 'triggers', 'competes', 'complements'
    ]
    SELF_LOOP_ALLOWED = False  # No node connects to itself
    DUPLICATE_EDGES_ALLOWED = False  # Only one edge between two nodes

    @staticmethod
    def validate_node(node: Dict[str, Any]) -> Tuple[bool, str]:
        """Every node must pass these tests"""
        if not all(field in node for field in GraphInvariants.REQUIRED_NODE_FIELDS):
            return False, "Missing required fields"
        if node['type'] not in GraphInvariants.VALID_NODE_TYPES:
            return False, f"Invalid type: {node['type']}"
        if not re.match(GraphInvariants.NODE_ID_PATTERN, str(node['id'])):
            return False, "Invalid ID format"
        return True, "Valid"

    @staticmethod
    def validate_edge(edge: Dict[str, Any]) -> Tuple[bool, str]:
        """Every edge must pass these tests"""
        if edge['strength'] < 0 or edge['strength'] > 1:
            return False, "Strength out of bounds"
        if edge['type'] not in GraphInvariants.VALID_RELATIONSHIPS:
            return False, "Invalid relationship type"
        if edge['from'] == edge['to'] and not GraphInvariants.SELF_LOOP_ALLOWED:
            return False, "Self-loops not allowed"
        return True, "Valid"


class AgentLimits:
    """Hard limits on what agents can do"""

    # EXECUTION LIMITS - Prevent runaway agents
    MAX_EXECUTION_TIME = 30  # seconds
    MAX_MEMORY_PER_AGENT = 100_000_000  # 100MB
    MAX_RECURSIVE_CALLS = 5  # Prevent infinite loops
    MAX_PARALLEL_AGENTS = 10  # Resource protection

    # CODE GENERATION LIMITS - Keep code simple
    MAX_FUNCTION_LENGTH = 50  # lines
    MAX_FILE_LENGTH = 500  # lines
    MAX_COMPLEXITY_SCORE = 10  # cyclomatic complexity

    # DATA LIMITS - Prevent data explosions
    MAX_NODES_PER_OPERATION = 100  # Batch size
    MAX_API_CALLS_PER_MINUTE = 60  # Rate limiting
    MAX_PATTERN_AGE_DAYS = 90  # Pattern expiry

    # LEARNING LIMITS - Prevent overfitting
    MIN_PATTERN_OCCURRENCES = 3  # Before it's a pattern
    MIN_CONFIDENCE_THRESHOLD = 0.3  # Below this, ignore
    MAX_PATTERNS_STORED = 1000  # Memory limit


class DataInvariants:
    """Rules that ensure data consistency"""

    # TIME RULES - Markets have time structure
    MARKET_OPEN = "09:30"
    MARKET_CLOSE = "16:00"
    WEEKENDS_EXCLUDED = True
    HOLIDAYS_EXCLUDED = True

    # PRICE RULES - Sanity checks
    MIN_STOCK_PRICE = 0.01  # Penny stock floor
    MAX_STOCK_PRICE = 1_000_000  # BRK.A ceiling
    MAX_DAILY_CHANGE = 0.50  # 50% circuit breaker

    # INDICATOR RULES - Economic bounds
    INDICATOR_BOUNDS = {
        'UNEMPLOYMENT': (0, 30),  # 0-30%
        'GDP': (-20, 20),  # Growth rate
        'CPI': (-5, 25),  # Inflation
        'FED_RATE': (0, 20),  # Interest rate
    }

    @staticmethod
    def validate_market_data(data: Dict[str, Any]) -> bool:
        """Sanity check market data"""
        if 'price' in data:
            if data['price'] < DataInvariants.MIN_STOCK_PRICE:
                return False
            if data['price'] > DataInvariants.MAX_STOCK_PRICE:
                return False
        if 'change_percent' in data:
            if abs(data['change_percent']) > DataInvariants.MAX_DAILY_CHANGE:
                return False
        return True

    @staticmethod
    def validate_indicator(indicator_type: str, value: float) -> bool:
        """Check if indicator value is realistic"""
        if indicator_type in DataInvariants.INDICATOR_BOUNDS:
            min_val, max_val = DataInvariants.INDICATOR_BOUNDS[indicator_type]
            return min_val <= value <= max_val
        return True


class RelationshipPhysics:
    """Immutable laws of how relationships work"""

    # STRENGTH DECAY - Relationships weaken over distance
    TRANSITIVE_DECAY = 0.7  # A->B->C = 0.7 * strength
    TIME_DECAY_RATE = 0.01  # Per day

    # RELATIONSHIP RULES - How things connect
    RELATIONSHIP_RULES = {
        # (type1, type2): allowed_relationships
        ('indicator', 'indicator'): ['correlates', 'inverse', 'leads', 'lags'],
        ('indicator', 'stock'): ['influences', 'pressures', 'supports'],
        ('stock', 'stock'): ['correlates', 'competes', 'complements'],
        ('sector', 'stock'): ['contains'],
        ('stock', 'sector'): ['belongs_to'],
        ('event', 'stock'): ['impacts', 'triggers'],
        ('event', 'indicator'): ['impacts', 'causes'],
        ('pattern', 'stock'): ['predicts'],
        ('news', 'stock'): ['influences'],
    }

    # CAUSALITY RULES - Some things can't cause others
    FORBIDDEN_CAUSALITY = [
        ('stock', 'indicator'),  # Single stock can't cause macro
        ('news', 'indicator'),  # News doesn't create GDP
    ]

    @staticmethod
    def can_connect(type1: str, type2: str, relationship: str) -> bool:
        """Check if connection is physically possible"""
        key = (type1, type2)
        if key in RelationshipPhysics.RELATIONSHIP_RULES:
            return relationship in RelationshipPhysics.RELATIONSHIP_RULES[key]
        # Check reverse
        key = (type2, type1)
        if key in RelationshipPhysics.RELATIONSHIP_RULES:
            return relationship in RelationshipPhysics.RELATIONSHIP_RULES[key]
        return False

    @staticmethod
    def apply_transitive_decay(strength: float, hops: int) -> float:
        """Calculate strength after multiple hops"""
        return strength * (RelationshipPhysics.TRANSITIVE_DECAY ** hops)

    @staticmethod
    def apply_time_decay(strength: float, days_old: int) -> float:
        """Calculate strength decay over time"""
        return strength * ((1 - RelationshipPhysics.TIME_DECAY_RATE) ** days_old)


class ErrorCorrection:
    """Self-healing mechanisms"""

    @staticmethod
    def heal_graph(graph) -> List[str]:
        """Fix common graph problems, return fixes made"""
        fixes = []

        # Remove orphan nodes (no connections after 7 days)
        for node_id, node in list(graph.nodes.items()):
            connections = len(node.get('connections_in', [])) + len(node.get('connections_out', []))
            if connections == 0:
                created = node.get('created', datetime.now().isoformat())
                age = (datetime.now() - datetime.fromisoformat(created)).days
                if age > 7:
                    del graph.nodes[node_id]
                    fixes.append(f"Removed orphan node: {node_id}")

        # Fix strength overflow
        for edge in graph.edges:
            if edge['strength'] > 1.0:
                edge['strength'] = 1.0
                fixes.append(f"Clamped edge strength: {edge['from']}->{edge['to']}")
            if edge['strength'] < 0.1:  # Too weak
                graph.edges.remove(edge)
                fixes.append(f"Removed weak edge: {edge['from']}->{edge['to']}")

        # Remove duplicate edges
        seen = set()
        for edge in list(graph.edges):
            key = (edge['from'], edge['to'], edge['type'])
            if key in seen:
                graph.edges.remove(edge)
                fixes.append(f"Removed duplicate edge: {key}")
            seen.add(key)

        # Validate all nodes
        for node_id, node in list(graph.nodes.items()):
            valid, reason = GraphInvariants.validate_node(node)
            if not valid:
                del graph.nodes[node_id]
                fixes.append(f"Removed invalid node {node_id}: {reason}")

        return fixes

    @staticmethod
    def validate_forecast(forecast: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure forecasts make sense using dynamic confidence validation"""
        # Calculate or validate confidence using dynamic system
        influences = forecast.get('influences', 0)
        data_quality = forecast.get('data_quality', 0.6)
        signal_strength = forecast.get('signal_strength', 0.0)

        # Use dynamic confidence calculator if confidence not provided or seems unrealistic
        current_confidence = forecast.get('confidence', 0)
        if current_confidence == 0 or current_confidence > 0.95:  # Too high is suspicious
            # Calculate dynamic confidence
            confidence_result = confidence_calculator.calculate_confidence(
                data_quality=data_quality,
                correlation_strength=signal_strength,
                num_data_points=max(influences, 1),
                analysis_type='forecast'
            )
            forecast['confidence'] = confidence_result['confidence']
        else:
            # Validate existing confidence against data quality
            max_allowed_confidence = min(0.9, data_quality + 0.2)
            if current_confidence > max_allowed_confidence:
                forecast['confidence'] = max_allowed_confidence

            # Need minimum influences for high confidence
            if influences < 3 and current_confidence > 0.6:
                forecast['confidence'] = min(current_confidence, 0.6)

        # Ensure required fields with dynamic defaults
        forecast.setdefault('forecast', 'neutral')
        forecast.setdefault('signal_strength', 0.0)

        return forecast

    @staticmethod
    def sanitize_user_input(text: str) -> str:
        """Clean user input to prevent injection"""
        # Remove any potential code
        text = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL)
        text = re.sub(r'<.*?>', '', text)  # Remove HTML

        # Limit length
        if len(text) > 1000:
            text = text[:1000]

        return text.strip()


class CoreAgentBehaviors:
    """Immutable agent behaviors"""

    # Every agent MUST follow this contract
    AGENT_CONTRACT = {
        'timeout': 30,
        'return_type': dict,
        'error_key': 'error',
        'success_key': 'result',
        'must_log': True,
        'can_delete': False,
        'can_modify_others': False
    }

    @staticmethod
    def validate_agent_response(response: Any) -> bool:
        """Check if agent response follows contract"""
        if not isinstance(response, dict):
            return False

        # Must have either error or result
        has_error = 'error' in response
        has_result = 'result' in response or 'status' in response

        return has_error or has_result

    @staticmethod
    def enforce_timeout(func, timeout: int = 30):
        """Decorator to enforce timeout on agent operations"""
        import signal

        def handler(signum, frame):
            raise TimeoutError(f"Agent exceeded {timeout}s timeout")

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(timeout)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wrapper