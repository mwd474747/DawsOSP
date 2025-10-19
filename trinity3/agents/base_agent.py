"""
Base Agent class for Trinity 3.0
"""

from typing import Dict, Any, List, Optional, Tuple
from abc import ABC, abstractmethod
import json
from datetime import datetime

class BaseAgent(ABC):
    """Base class for all Trinity agents"""
    
    def __init__(self, name: str, capabilities: List[str]):
        self.name = name
        self.capabilities = capabilities
        self.last_analysis = None
        self.confidence_scores = {}
        
    @abstractmethod
    def analyze(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Main analysis method - must be implemented by each agent"""
        pass
    
    @abstractmethod
    def predict(self, target: str, horizon: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Make predictions - must be implemented by each agent"""
        pass
    
    def can_handle(self, query: str) -> Tuple[bool, float]:
        """
        Check if this agent can handle the query
        Returns (can_handle, confidence_score)
        """
        query_lower = query.lower()
        
        # Check for capability keywords
        for capability in self.capabilities:
            keywords = capability.replace('_', ' ').split()
            if any(keyword in query_lower for keyword in keywords):
                return True, 0.8
        
        return False, 0.0
    
    def format_response(
        self,
        analysis_type: str,
        data: Dict[str, Any],
        confidence: float,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Format agent response in standard structure"""
        return {
            'agent': self.name,
            'analysis_type': analysis_type,
            'timestamp': datetime.now().isoformat(),
            'confidence': confidence,
            'data': data,
            'metadata': metadata or {},
            'status': 'success'
        }