import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Any

class PersistenceManager:
    """Manage saving and loading of system state"""
    
    def __init__(self, base_path: str = 'storage'):
        self.base_path = base_path
        self.ensure_directories()
        
    def ensure_directories(self):
        """Create necessary directories"""
        dirs = [
            self.base_path,
            f"{self.base_path}/backups",
            f"{self.base_path}/sessions",
            f"{self.base_path}/workflows",
            f"{self.base_path}/patterns"
        ]
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
    
    def save_graph(self, graph):
        """Save graph with versioning and backup"""
        # Save main graph
        graph_path = f"{self.base_path}/graph.json"
        graph.save(graph_path)
        
        # Create timestamped backup
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{self.base_path}/backups/graph_{timestamp}.json"
        shutil.copy(graph_path, backup_path)
        
        # Clean old backups (keep last 10)
        self._clean_old_backups()
        
    def save_session(self, session_id: str, interactions: List[Dict]):
        """Save a user session"""
        session_path = f"{self.base_path}/sessions/{session_id}.json"
        
        with open(session_path, 'w') as f:
            json.dump({
                'session_id': session_id,
                'created': datetime.now().isoformat(),
                'interactions': interactions,
                'interaction_count': len(interactions)
            }, f, indent=2)
    
    def save_workflow(self, workflow_id: str, workflow: Dict):
        """Save a workflow"""
        workflow_path = f"{self.base_path}/workflows/{workflow_id}.json"
        
        with open(workflow_path, 'w') as f:
            json.dump({
                'id': workflow_id,
                'workflow': workflow,
                'created': datetime.now().isoformat()
            }, f, indent=2)
    
    def save_pattern(self, pattern_id: str, pattern: Dict):
        """Save a discovered pattern"""
        pattern_path = f"{self.base_path}/patterns/{pattern_id}.json"
        
        with open(pattern_path, 'w') as f:
            json.dump({
                'id': pattern_id,
                'pattern': pattern,
                'created': datetime.now().isoformat()
            }, f, indent=2)
    
    def load_graph(self, graph):
        """Load the graph"""
        graph_path = f"{self.base_path}/graph.json"
        return graph.load(graph_path)
    
    def load_recent_sessions(self, limit: int = 5) -> List[Dict]:
        """Load recent session data"""
        sessions = []
        session_dir = f"{self.base_path}/sessions"
        
        if os.path.exists(session_dir):
            session_files = sorted(
                os.listdir(session_dir),
                key=lambda x: os.path.getmtime(os.path.join(session_dir, x)),
                reverse=True
            )[:limit]
            
            for session_file in session_files:
                with open(os.path.join(session_dir, session_file), 'r') as f:
                    sessions.append(json.load(f))
        
        return sessions
    
    def load_workflows(self) -> Dict[str, Dict]:
        """Load all workflows"""
        workflows = {}
        workflow_dir = f"{self.base_path}/workflows"
        
        if os.path.exists(workflow_dir):
            for workflow_file in os.listdir(workflow_dir):
                with open(os.path.join(workflow_dir, workflow_file), 'r') as f:
                    data = json.load(f)
                    workflows[data['id']] = data['workflow']
        
        return workflows
    
    def load_patterns(self) -> Dict[str, Dict]:
        """Load all patterns"""
        patterns = {}
        pattern_dir = f"{self.base_path}/patterns"
        
        if os.path.exists(pattern_dir):
            for pattern_file in os.listdir(pattern_dir):
                with open(os.path.join(pattern_dir, pattern_file), 'r') as f:
                    data = json.load(f)
                    patterns[data['id']] = data['pattern']
        
        return patterns
    
    def _clean_old_backups(self, keep_count: int = 10):
        """Clean old backup files"""
        backup_dir = f"{self.base_path}/backups"
        
        if os.path.exists(backup_dir):
            backups = sorted(
                [f for f in os.listdir(backup_dir) if f.startswith('graph_')],
                key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)),
                reverse=True
            )
            
            # Remove old backups
            for backup in backups[keep_count:]:
                os.remove(os.path.join(backup_dir, backup))