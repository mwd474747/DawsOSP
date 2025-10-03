import json
import os
import shutil
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Configure logging
logger = logging.getLogger(__name__)

class PersistenceManager:
    """Manage saving and loading of system state with backup rotation and integrity validation"""

    def __init__(self, base_path: str = 'storage'):
        self.base_path = base_path
        self.backup_dir = f"{self.base_path}/backups"
        self.graph_version = "1.0"
        self.ensure_directories()

    def ensure_directories(self):
        """Create necessary directories"""
        dirs = [
            self.base_path,
            self.backup_dir,
            f"{self.base_path}/sessions",
            f"{self.base_path}/workflows",
            f"{self.base_path}/patterns"
        ]
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)

    # ====================================================================
    # BACKUP MANAGEMENT
    # ====================================================================

    def save_graph_with_backup(self, graph) -> Dict[str, Any]:
        """
        Save graph with automatic timestamped backup and checksum validation

        Returns:
            Dict with save statistics including checksum and backup path
        """
        logger.info("Starting graph save with backup...")

        # Save main graph
        graph_path = f"{self.base_path}/graph.json"
        graph.save(graph_path)

        # Calculate checksum for the saved graph
        checksum = self._calculate_checksum_file(graph_path)

        # Create metadata
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'checksum': checksum,
            'node_count': len(graph.nodes) if hasattr(graph, 'nodes') else 0,
            'edge_count': len(graph.edges) if hasattr(graph, 'edges') else 0,
            'graph_version': self.graph_version,
            'saved_by': 'DawsOS PersistenceManager'
        }

        # Save with metadata
        self._save_with_metadata(graph_path, metadata)

        # Create timestamped backup
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{self.backup_dir}/graph_{timestamp}.json"
        backup_meta_path = f"{self.backup_dir}/graph_{timestamp}.meta"

        shutil.copy(graph_path, backup_path)
        shutil.copy(f"{graph_path}.meta", backup_meta_path)

        logger.info(f"Backup created: {backup_path}")
        logger.info(f"Checksum: {checksum}")

        # Rotate old backups
        removed_count = self._rotate_backups()

        return {
            'success': True,
            'graph_path': graph_path,
            'backup_path': backup_path,
            'checksum': checksum,
            'metadata': metadata,
            'backups_removed': removed_count
        }

    def _rotate_backups(self, retention_days: int = 30) -> int:
        """
        Remove old backups beyond retention period

        Args:
            retention_days: Number of days to keep backups (default: 30)

        Returns:
            Number of backups removed
        """
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        removed_count = 0

        if os.path.exists(self.backup_dir):
            backups = [f for f in os.listdir(self.backup_dir) if f.startswith('graph_')]

            for backup in backups:
                backup_path = os.path.join(self.backup_dir, backup)
                file_time = datetime.fromtimestamp(os.path.getmtime(backup_path))

                if file_time < cutoff_date:
                    os.remove(backup_path)
                    removed_count += 1
                    logger.info(f"Removed old backup: {backup}")

                    # Also remove metadata file if exists
                    meta_path = f"{backup_path}.meta"
                    if os.path.exists(meta_path):
                        os.remove(meta_path)

        logger.info(f"Backup rotation complete: {removed_count} backups removed")
        return removed_count

    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List available backups with metadata

        Returns:
            List of backup info dicts sorted by timestamp (newest first)
        """
        backups = []

        if os.path.exists(self.backup_dir):
            backup_files = [f for f in os.listdir(self.backup_dir)
                           if f.startswith('graph_') and f.endswith('.json')]

            for backup_file in backup_files:
                backup_path = os.path.join(self.backup_dir, backup_file)
                meta_path = f"{backup_path}.meta"

                backup_info = {
                    'filename': backup_file,
                    'path': backup_path,
                    'size': os.path.getsize(backup_path),
                    'modified': datetime.fromtimestamp(os.path.getmtime(backup_path)).isoformat()
                }

                # Load metadata if available
                if os.path.exists(meta_path):
                    try:
                        with open(meta_path, 'r') as f:
                            backup_info['metadata'] = json.load(f)
                    except Exception as e:
                        logger.warning(f"Could not load metadata for {backup_file}: {e}")

                backups.append(backup_info)

        # Sort by modified time, newest first
        backups.sort(key=lambda x: x['modified'], reverse=True)
        return backups

    def restore_from_backup(self, backup_path: str, graph) -> Dict[str, Any]:
        """
        Restore graph from a backup file

        Args:
            backup_path: Path to backup file
            graph: Graph instance to restore into

        Returns:
            Dict with restoration statistics
        """
        logger.info(f"Restoring from backup: {backup_path}")

        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup not found: {backup_path}")

        # Verify integrity if metadata exists
        meta_path = f"{backup_path}.meta"
        if os.path.exists(meta_path):
            try:
                integrity_check = self.verify_integrity(backup_path)
                if not integrity_check['valid']:
                    logger.error(f"Backup integrity check failed: {integrity_check['error']}")
                    raise ValueError(f"Corrupted backup: {integrity_check['error']}")
            except Exception as e:
                logger.warning(f"Could not verify backup integrity: {e}")

        # Load the backup
        original_node_count = len(graph.nodes) if hasattr(graph, 'nodes') else 0
        original_edge_count = len(graph.edges) if hasattr(graph, 'edges') else 0

        graph.load(backup_path)

        new_node_count = len(graph.nodes) if hasattr(graph, 'nodes') else 0
        new_edge_count = len(graph.edges) if hasattr(graph, 'edges') else 0

        stats = {
            'success': True,
            'backup_path': backup_path,
            'nodes_restored': new_node_count,
            'edges_restored': new_edge_count,
            'nodes_changed': new_node_count - original_node_count,
            'edges_changed': new_edge_count - original_edge_count
        }

        logger.info(f"Restore complete: {stats['nodes_restored']} nodes, {stats['edges_restored']} edges")
        return stats

    # ====================================================================
    # INTEGRITY VALIDATION
    # ====================================================================

    def _calculate_checksum(self, graph) -> str:
        """
        Calculate SHA-256 checksum of graph data

        Args:
            graph: Graph instance

        Returns:
            SHA-256 hash as hex string
        """
        # Serialize graph to consistent JSON format
        graph_data = {
            'nodes': graph.nodes if hasattr(graph, 'nodes') else {},
            'edges': graph.edges if hasattr(graph, 'edges') else [],
            'patterns': graph.patterns if hasattr(graph, 'patterns') else {}
        }

        # Convert to JSON string with sorted keys for consistency
        json_str = json.dumps(graph_data, sort_keys=True, separators=(',', ':'))

        # Calculate SHA-256
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()

    def _calculate_checksum_file(self, filepath: str) -> str:
        """
        Calculate SHA-256 checksum of a file

        Args:
            filepath: Path to file

        Returns:
            SHA-256 hash as hex string
        """
        sha256_hash = hashlib.sha256()

        with open(filepath, 'rb') as f:
            # Read file in chunks for memory efficiency
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()

    def _save_with_metadata(self, filepath: str, metadata: Dict[str, Any]) -> None:
        """
        Save metadata file alongside data file

        Args:
            filepath: Path to data file
            metadata: Metadata dictionary
        """
        meta_path = f"{filepath}.meta"

        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.debug(f"Metadata saved: {meta_path}")

    def verify_integrity(self, filepath: str) -> Dict[str, Any]:
        """
        Verify graph file against checksum

        Args:
            filepath: Path to graph file

        Returns:
            Dict with validation results
        """
        meta_path = f"{filepath}.meta"

        if not os.path.exists(filepath):
            return {'valid': False, 'error': 'File not found'}

        if not os.path.exists(meta_path):
            return {'valid': False, 'error': 'Metadata file not found'}

        try:
            # Load metadata
            with open(meta_path, 'r') as f:
                metadata = json.load(f)

            stored_checksum = metadata.get('checksum')
            if not stored_checksum:
                return {'valid': False, 'error': 'No checksum in metadata'}

            # Calculate current checksum
            current_checksum = self._calculate_checksum_file(filepath)

            # Compare
            if current_checksum == stored_checksum:
                return {
                    'valid': True,
                    'checksum': current_checksum,
                    'metadata': metadata
                }
            else:
                return {
                    'valid': False,
                    'error': 'Checksum mismatch',
                    'expected': stored_checksum,
                    'actual': current_checksum
                }

        except Exception as e:
            return {'valid': False, 'error': f'Verification failed: {str(e)}'}

    # ====================================================================
    # RECOVERY PROCEDURES
    # ====================================================================

    def load_graph_with_recovery(self, graph) -> Dict[str, Any]:
        """
        Load graph with automatic integrity check and recovery from backup if corrupted

        Args:
            graph: Graph instance to load into

        Returns:
            Dict with load statistics and recovery info
        """
        graph_path = f"{self.base_path}/graph.json"

        # First, try to load the main graph with integrity check
        if os.path.exists(graph_path):
            integrity = self.verify_integrity(graph_path)

            if integrity['valid']:
                logger.info("Graph integrity verified, loading...")
                graph.load(graph_path)
                return {
                    'success': True,
                    'source': 'primary',
                    'integrity_verified': True,
                    'nodes': len(graph.nodes) if hasattr(graph, 'nodes') else 0,
                    'edges': len(graph.edges) if hasattr(graph, 'edges') else 0
                }
            else:
                logger.warning(f"Graph integrity check failed: {integrity['error']}")
                logger.info("Attempting recovery from backup...")

                # Try to recover from most recent valid backup
                return self._recover_from_backup(graph, integrity)
        else:
            logger.warning(f"Graph file not found: {graph_path}")
            return {'success': False, 'error': 'Graph file not found'}

    def _recover_from_backup(self, graph, failed_integrity: Dict) -> Dict[str, Any]:
        """
        Recover graph from most recent valid backup

        Args:
            graph: Graph instance to restore into
            failed_integrity: Failed integrity check results

        Returns:
            Dict with recovery statistics
        """
        backups = self.list_backups()

        if not backups:
            return {
                'success': False,
                'error': 'No backups available for recovery',
                'failed_integrity': failed_integrity
            }

        # Try backups from newest to oldest
        for backup_info in backups:
            backup_path = backup_info['path']
            logger.info(f"Trying backup: {backup_info['filename']}")

            # Verify backup integrity
            integrity = self.verify_integrity(backup_path)

            if integrity['valid']:
                # This backup is good, use it
                try:
                    restore_stats = self.restore_from_backup(backup_path, graph)

                    # Copy restored backup to main graph location
                    graph_path = f"{self.base_path}/graph.json"
                    shutil.copy(backup_path, graph_path)
                    shutil.copy(f"{backup_path}.meta", f"{graph_path}.meta")

                    logger.info(f"Successfully recovered from backup: {backup_info['filename']}")

                    return {
                        'success': True,
                        'source': 'backup_recovery',
                        'backup_used': backup_info['filename'],
                        'recovery_stats': restore_stats,
                        'failed_integrity': failed_integrity
                    }

                except Exception as e:
                    logger.error(f"Failed to restore from {backup_info['filename']}: {e}")
                    continue
            else:
                logger.warning(f"Backup {backup_info['filename']} also corrupted, trying next...")

        # No valid backups found
        return {
            'success': False,
            'error': 'No valid backups found',
            'failed_integrity': failed_integrity,
            'backups_checked': len(backups)
        }

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