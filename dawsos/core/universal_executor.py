#!/usr/bin/env python3
"""
Universal Executor for DawsOS Trinity Architecture

This module ensures ALL execution flows through the proper Trinity path:
- Pattern-driven execution
- Automatic compliance enforcement
- Legacy call migration
- Architecture validation

Every agent, pattern, UI action, and API call routes through here.
"""

import json
import logging
from typing import Dict, Any, Optional, TYPE_CHECKING
from pathlib import Path
from datetime import datetime

# Import core components
from core.pattern_engine import PatternEngine
from core.knowledge_graph import KnowledgeGraph
from core.agent_adapter import AgentRegistry  # Fixed: AgentRegistry is in agent_adapter, not agent_registry

if TYPE_CHECKING:
    from core.agent_runtime import AgentRuntime

logger = logging.getLogger(__name__)


class UniversalExecutor:
    """Single entry point for ALL DawsOS execution."""
    
    def __init__(self, graph: KnowledgeGraph, registry: AgentRegistry, runtime: "AgentRuntime" = None):
        """Initialize with Trinity components."""
        self.graph = graph
        self.registry = registry
        self.runtime = runtime
        self.pattern_engine = PatternEngine(runtime=runtime)
        
        # Load meta-patterns
        self._load_meta_patterns()
        
        # Track execution metrics
        self.metrics = {
            'total_executions': 0,
            'pattern_routed': 0,
            'legacy_migrated': 0,
            'compliance_failures': 0,
            'last_execution': None
        }
        
        logger.info("Universal Executor initialized with Trinity Architecture enforcement")
    
    def _load_meta_patterns(self):
        """Load meta-patterns for self-healing architecture."""
        meta_pattern_dir = Path('patterns/system/meta')
        if not meta_pattern_dir.exists():
            logger.warning(f"Meta-pattern directory not found: {meta_pattern_dir}")
            return
        
        loaded = []
        for pattern_file in meta_pattern_dir.glob('*.json'):
            try:
                with open(pattern_file, 'r') as f:
                    pattern = json.load(f)
                    # Meta-patterns are already loaded by PatternEngine
                    # This just validates they exist
                    loaded.append(pattern.get('id', pattern_file.stem))
            except Exception as e:
                logger.error(f"Failed to validate meta-pattern {pattern_file}: {e}")
        
        logger.info(f"Validated {len(loaded)} meta-patterns: {loaded}")
    
    def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Universal execution entry point.
        
        ALL execution requests route through here:
        - Agent calls
        - Pattern executions
        - UI actions
        - API requests
        - Legacy direct calls
        
        The meta_executor pattern determines routing.
        """
        self.metrics['total_executions'] += 1
        self.metrics['last_execution'] = datetime.now().isoformat()
        
        try:
            # Prepare execution context
            context = self._prepare_context(request)

            # ALWAYS route through meta_executor pattern if available
            # This ensures Trinity compliance
            if self.pattern_engine.has_pattern('meta_executor'):
                pattern = self.pattern_engine.get_pattern('meta_executor')

                if pattern:
                    result = self.pattern_engine.execute_pattern(pattern, context)

                    if not isinstance(result, dict):
                        logger.warning("meta_executor pattern returned unexpected result; using fallback execution")
                        result = self._execute_fallback(context)
                    # If pattern engine cannot execute (e.g., no runtime), fall back gracefully
                    elif result.get('error') == 'No runtime configured for pattern execution':
                        logger.warning("meta_executor pattern could not execute (missing runtime); using fallback execution")
                        result = self._execute_fallback(context)
                else:
                    logger.warning("meta_executor pattern metadata missing; using fallback execution")
                    result = self._execute_fallback(context)
            else:
                # Fallback: Direct execution without meta pattern
                logger.warning("meta_executor pattern not found; using fallback execution")
                result = self._execute_fallback(context)

            # Track routing metrics
            if result.get('migrated'):
                self.metrics['legacy_migrated'] += 1
            if result.get('pattern_routed'):
                self.metrics['pattern_routed'] += 1

            # Store in graph (Trinity Knowledge multiplication)
            self._store_execution_result(request, result)

            return result

        except Exception as e:
            logger.error(f"Universal execution failed: {e}")
            self.metrics['compliance_failures'] += 1

            # Attempt recovery through architecture_validator
            return self._attempt_recovery(request, str(e))
    
    def _prepare_context(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare execution context with Trinity components."""
        context = request.copy()
        
        # Inject Trinity components
        context['graph'] = self.graph
        context['registry'] = self.registry
        context['pattern_engine'] = self.pattern_engine
        context['runtime'] = self.runtime
        
        # Add execution metadata
        context['execution_id'] = f"exec_{datetime.now().timestamp()}"
        context['executor'] = 'universal'
        context['timestamp'] = datetime.now().isoformat()
        
        # Preserve original request for migration tracking
        context['original_request'] = request
        
        return context
    
    def _store_execution_result(self, request: Dict[str, Any], result: Dict[str, Any]):
        """Store execution result in knowledge graph."""
        try:
            node_data = {
                'type': 'execution',
                'request': request,
                'result': result,
                'timestamp': datetime.now().isoformat(),
                'executor': 'universal',
                'compliant': result.get('compliant', True)
            }
            
            node_id = self.graph.add_node(**node_data)
            
            # Connect to agent node if applicable
            if result.get('agent'):
                agent_nodes = self.graph.get_nodes_by_type('agent')
                for aid, adata in agent_nodes.items():
                    if adata.get('name') == result['agent']:
                        self.graph.connect(node_id, aid, 'executed_by')
                        break
            
            logger.debug(f"Stored execution result: {node_id}")
            
        except Exception as e:
            logger.error(f"Failed to store execution result: {e}")
    
    def _execute_fallback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback execution when meta_executor pattern is missing.
        Provides basic routing without full Trinity compliance.
        """
        logger.warning("Executing in fallback mode - meta_executor pattern unavailable")

        # Try to route to an agent if specified
        if 'agent' in context:
            agent_name = context['agent']
            if self.registry:
                agent = self.registry.get_agent(agent_name)
                if agent:
                    try:
                        result = agent.execute(context)
                        result['fallback_mode'] = True
                        return result
                    except Exception as e:
                        logger.error(f"Agent execution failed in fallback: {e}")

        # If no agent or agent failed, return basic response
        return {
            'success': False,
            'error': 'Fallback execution - no suitable agent or pattern found',
            'fallback_mode': True,
            'timestamp': datetime.now().isoformat()
        }

    def _attempt_recovery(self, request: Dict[str, Any], error: str) -> Dict[str, Any]:
        """Attempt to recover from execution failure."""
        try:
            # Use architecture_validator pattern for recovery if available
            if self.pattern_engine.has_pattern('architecture_validator'):
                recovery_context = {
                    'request': request,
                    'error': error,
                    'recovery_mode': True
                }

                result = self.pattern_engine.execute_pattern(
                    pattern_name='architecture_validator',
                    context=recovery_context
                )

                if result.get('recovered'):
                    logger.info(f"Successfully recovered from error: {error}")
                    return result
            else:
                logger.warning("architecture_validator pattern not found, cannot attempt recovery")

        except Exception as recovery_error:
            logger.error(f"Recovery failed: {recovery_error}")

        # Return error response if recovery fails
        return {
            'success': False,
            'error': error,
            'recovery_attempted': True,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get execution metrics."""
        return self.metrics.copy()
    
    def validate_architecture(self) -> Dict[str, Any]:
        """Run architecture validation."""
        try:
            result = self.pattern_engine.execute_pattern(
                pattern_name='architecture_validator',
                context={'startup': False}
            )
            return result
        except Exception as e:
            logger.error(f"Architecture validation failed: {e}")
            return {'success': False, 'error': str(e)}


# Singleton instance
_executor_instance = None

def get_executor(graph: KnowledgeGraph = None, registry: AgentRegistry = None, runtime: "AgentRuntime" = None) -> UniversalExecutor:
    """Get or create the universal executor singleton."""
    global _executor_instance
    
    if _executor_instance is None:
        if graph is None or registry is None:
            raise ValueError("Graph and registry required for initial executor creation")
        _executor_instance = UniversalExecutor(graph, registry, runtime)

    return _executor_instance


def execute(request: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function for universal execution."""
    executor = get_executor()
    if executor is None:
        raise RuntimeError("Universal Executor not initialized")
    return executor.execute(request)
