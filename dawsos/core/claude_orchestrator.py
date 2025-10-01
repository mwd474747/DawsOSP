from anthropic import Anthropic
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

class ClaudeOrchestrator:
    """Claude's brain - interprets, decides, and orchestrates"""
    
    def __init__(self, graph, agents: Dict = None):
        self.claude = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.graph = graph
        self.agents = agents or {}
        self.session_memory = []
        self.max_memory = 20
        
    def think(self, user_input: str) -> Dict:
        """Main thinking process"""
        # Build context
        context = self._build_context(user_input)
        
        # Create prompt for Claude
        prompt = self._create_prompt(user_input, context)
        
        try:
            # Get Claude's response
            response = self.claude.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=2000,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse and execute
            result = self._parse_and_execute(response.content[0].text)
            
            # Update memory
            self._update_memory(user_input, result)
            
            return result
            
        except Exception as e:
            return {
                'error': str(e),
                'suggestion': 'Please ensure ANTHROPIC_API_KEY is set'
            }
    
    def _build_context(self, user_input: str) -> Dict:
        """Build context from graph and memory"""
        # Find relevant nodes based on input
        keywords = user_input.lower().split()
        relevant_nodes = []
        
        for node_id, node in self.graph.nodes.items():
            node_text = f"{node_id} {node['type']} {str(node.get('data', {}))}".lower()
            if any(keyword in node_text for keyword in keywords):
                relevant_nodes.append(node_id)
        
        return {
            'graph_stats': self.graph.get_stats(),
            'relevant_nodes': relevant_nodes[:10],
            'recent_patterns': list(self.graph.patterns.keys())[-5:],
            'recent_memory': self.session_memory[-5:],
            'available_agents': list(self.agents.keys())
        }
    
    def _create_prompt(self, user_input: str, context: Dict) -> str:
        """Create the prompt for Claude"""
        return f"""You are DawsOS, a knowledge graph intelligence system.

Current Graph State:
- Nodes: {context['graph_stats']['total_nodes']} ({', '.join(f"{k}:{v}" for k,v in context['graph_stats']['node_types'].items())})
- Edges: {context['graph_stats']['total_edges']}
- Patterns discovered: {len(context['recent_patterns'])}

Relevant nodes: {context['relevant_nodes']}
Available agents: {context['available_agents']}

User said: {user_input}

Recent context: {context['recent_memory']}

You can respond with a JSON array of actions:
1. {{"action": "add_node", "type": "node_type", "id": "node_id", "data": {{...}}}}
2. {{"action": "connect", "from": "node_id", "to": "node_id", "relationship": "type", "strength": 0.8}}
3. {{"action": "forecast", "target": "node_id"}}
4. {{"action": "trace", "from": "node_id", "depth": 3}}
5. {{"action": "query", "pattern": {{"type": "...", "data": {{...}}}}}}
6. {{"action": "use_agent", "agent": "agent_name", "command": "..."}}
7. {{"action": "explain", "text": "explanation"}}

Respond with a JSON array of actions to take. Focus on building connections and understanding relationships.
"""
    
    def _parse_and_execute(self, response_text: str) -> Dict:
        """Parse Claude's response and execute actions"""
        results = []
        
        try:
            # Extract JSON from response
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                actions = json.loads(response_text[json_start:json_end])
            else:
                # Try to parse as single action
                actions = [json.loads(response_text)]
                
        except json.JSONDecodeError:
            # If not JSON, treat as explanation
            return {'response': response_text}
        
        # Execute each action
        for action in actions:
            result = self._execute_action(action)
            results.append(result)
        
        # Save graph after changes
        if any('success' in r for r in results):
            self.graph.save()
        
        return {
            'results': results,
            'graph_stats': self.graph.get_stats()
        }
    
    def _execute_action(self, action: Dict) -> Dict:
        """Execute a single action"""
        action_type = action.get('action')
        
        if action_type == 'add_node':
            node_id = self.graph.add_node(
                node_type=action.get('type'),
                data=action.get('data', {}),
                node_id=action.get('id')
            )
            return {'action': 'add_node', 'node_id': node_id, 'success': True}
            
        elif action_type == 'connect':
            success = self.graph.connect(
                from_id=action.get('from'),
                to_id=action.get('to'),
                relationship=action.get('relationship'),
                strength=action.get('strength', 1.0),
                metadata=action.get('metadata', {})
            )
            return {
                'action': 'connect',
                'from': action.get('from'),
                'to': action.get('to'),
                'success': success
            }
            
        elif action_type == 'forecast':
            forecast = self.graph.forecast(
                target_node=action.get('target'),
                horizon=action.get('horizon', '1d')
            )
            return {'action': 'forecast', 'result': forecast}
            
        elif action_type == 'trace':
            paths = self.graph.trace_connections(
                start_node=action.get('from'),
                max_depth=action.get('depth', 3)
            )
            return {
                'action': 'trace',
                'from': action.get('from'),
                'paths_found': len(paths),
                'paths': paths[:10]  # Limit to 10 paths
            }
            
        elif action_type == 'query':
            results = self.graph.query(action.get('pattern', {}))
            return {
                'action': 'query',
                'pattern': action.get('pattern'),
                'results': results
            }
            
        elif action_type == 'use_agent':
            agent_name = action.get('agent')
            if agent_name in self.agents:
                agent_result = self.agents[agent_name].analyze(
                    action.get('command', '')
                )
                return {'action': 'use_agent', 'agent': agent_name, 'result': agent_result}
            else:
                return {'action': 'use_agent', 'error': f'Agent {agent_name} not found'}
                
        elif action_type == 'explain':
            return {'action': 'explain', 'text': action.get('text', '')}
            
        else:
            return {'action': action_type, 'error': 'Unknown action type'}
    
    def _update_memory(self, user_input: str, result: Dict):
        """Update session memory"""
        memory_entry = {
            'timestamp': datetime.now().isoformat(),
            'input': user_input,
            'actions': result.get('results', [])
        }
        
        self.session_memory.append(memory_entry)
        
        # Trim memory if too long
        if len(self.session_memory) > self.max_memory:
            self.session_memory = self.session_memory[-self.max_memory:]