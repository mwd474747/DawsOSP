#!/usr/bin/env python3
"""
Data Integrity Manager - Ensures consistent data across DawsOS Trinity architecture
Provides validation, source control, and synchronization for Patterns, Knowledge, and Agents
"""

import json
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
import shutil
import tempfile
from core.logger import get_logger


class DataIntegrityManager:
    """Manages data integrity across the Trinity architecture"""

    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.logger = get_logger('DataIntegrityManager')

        # Define critical paths
        self.paths = {
            'patterns': self.base_path / 'patterns',
            'knowledge': self.base_path / 'storage' / 'knowledge',
            'agents': self.base_path / 'agents',
            'backups': self.base_path / 'storage' / 'backups',
            'checksums': self.base_path / 'storage' / 'checksums.json'
        }

        # Ensure backup directory exists
        self.paths['backups'].mkdir(parents=True, exist_ok=True)

    def validate_patterns(self) -> Dict[str, Any]:
        """Validate all pattern files for integrity and consistency"""
        validation_report = {
            'total_files': 0,
            'valid_patterns': 0,
            'invalid_files': [],
            'duplicate_ids': {},
            'schema_files': [],
            'missing_ids': [],
            'validation_errors': [],
            'recommendations': []
        }

        pattern_ids = {}

        # Scan all pattern files
        for pattern_file in self.paths['patterns'].rglob('*.json'):
            validation_report['total_files'] += 1

            try:
                with open(pattern_file, 'r') as f:
                    pattern = json.load(f)

                # Check if it's a schema file
                if pattern_file.name == 'schema.json' or pattern.get('$schema'):
                    validation_report['schema_files'].append(str(pattern_file))
                    continue

                # Check for pattern ID
                pattern_id = pattern.get('id')
                if not pattern_id:
                    validation_report['missing_ids'].append(str(pattern_file))
                    continue

                # Check for duplicates
                if pattern_id in pattern_ids:
                    if pattern_id not in validation_report['duplicate_ids']:
                        validation_report['duplicate_ids'][pattern_id] = []
                    validation_report['duplicate_ids'][pattern_id].append(str(pattern_file))
                    validation_report['duplicate_ids'][pattern_id].append(pattern_ids[pattern_id])
                else:
                    pattern_ids[pattern_id] = str(pattern_file)
                    validation_report['valid_patterns'] += 1

                # Validate pattern structure
                required_fields = ['id', 'name', 'description']
                for field in required_fields:
                    if field not in pattern:
                        validation_report['validation_errors'].append({
                            'file': str(pattern_file),
                            'error': f'Missing required field: {field}'
                        })

            except json.JSONDecodeError as e:
                validation_report['invalid_files'].append({
                    'file': str(pattern_file),
                    'error': f'Invalid JSON: {str(e)}'
                })
            except Exception as e:
                validation_report['invalid_files'].append({
                    'file': str(pattern_file),
                    'error': f'Read error: {str(e)}'
                })

        # Generate recommendations
        if validation_report['duplicate_ids']:
            validation_report['recommendations'].append(
                "Resolve duplicate pattern IDs to prevent overwrites"
            )

        if validation_report['missing_ids']:
            validation_report['recommendations'].append(
                "Add 'id' field to patterns missing it"
            )

        if validation_report['schema_files']:
            validation_report['recommendations'].append(
                "Exclude schema files from pattern loading"
            )

        return validation_report

    def validate_knowledge_bases(self) -> Dict[str, Any]:
        """Validate knowledge base files for integrity"""
        validation_report = {
            'total_files': 0,
            'valid_files': 0,
            'invalid_files': [],
            'file_sizes': {},
            'last_modified': {},
            'schema_validation': {}
        }

        for knowledge_file in self.paths['knowledge'].glob('*.json'):
            validation_report['total_files'] += 1

            try:
                with open(knowledge_file, 'r') as f:
                    data = json.load(f)

                # File is valid JSON
                validation_report['valid_files'] += 1
                validation_report['file_sizes'][knowledge_file.name] = knowledge_file.stat().st_size
                validation_report['last_modified'][knowledge_file.name] = datetime.fromtimestamp(
                    knowledge_file.stat().st_mtime
                ).isoformat()

                # Basic schema validation
                if knowledge_file.name == 'ui_configurations.json':
                    required_sections = ['dashboard_widgets', 'alert_thresholds', 'ui_themes']
                    missing_sections = [s for s in required_sections if s not in data]
                    validation_report['schema_validation'][knowledge_file.name] = {
                        'required_sections': required_sections,
                        'missing_sections': missing_sections,
                        'valid': len(missing_sections) == 0
                    }

            except json.JSONDecodeError as e:
                validation_report['invalid_files'].append({
                    'file': str(knowledge_file),
                    'error': f'Invalid JSON: {str(e)}'
                })
            except Exception as e:
                validation_report['invalid_files'].append({
                    'file': str(knowledge_file),
                    'error': f'Read error: {str(e)}'
                })

        return validation_report

    def generate_checksums(self) -> Dict[str, str]:
        """Generate checksums for all critical files"""
        checksums = {}

        # Pattern files
        for pattern_file in self.paths['patterns'].rglob('*.json'):
            checksums[str(pattern_file.relative_to(self.base_path))] = self._file_checksum(pattern_file)

        # Knowledge files
        for knowledge_file in self.paths['knowledge'].glob('*.json'):
            checksums[str(knowledge_file.relative_to(self.base_path))] = self._file_checksum(knowledge_file)

        # Agent files
        for agent_file in self.paths['agents'].glob('*.py'):
            checksums[str(agent_file.relative_to(self.base_path))] = self._file_checksum(agent_file)

        # Save checksums
        with open(self.paths['checksums'], 'w') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'checksums': checksums
            }, f, indent=2)

        return checksums

    def verify_checksums(self) -> Dict[str, Any]:
        """Verify current files against stored checksums"""
        if not self.paths['checksums'].exists():
            return {'error': 'No checksums file found. Run generate_checksums() first.'}

        with open(self.paths['checksums'], 'r') as f:
            stored_data = json.load(f)

        stored_checksums = stored_data.get('checksums', {})
        current_checksums = self.generate_checksums()

        verification_report = {
            'generated_at': stored_data.get('generated_at'),
            'verified_at': datetime.now().isoformat(),
            'total_files': len(stored_checksums),
            'unchanged_files': 0,
            'modified_files': [],
            'new_files': [],
            'deleted_files': []
        }

        # Check for modifications and deletions
        for file_path, stored_checksum in stored_checksums.items():
            if file_path in current_checksums:
                if current_checksums[file_path] == stored_checksum:
                    verification_report['unchanged_files'] += 1
                else:
                    verification_report['modified_files'].append(file_path)
            else:
                verification_report['deleted_files'].append(file_path)

        # Check for new files
        for file_path in current_checksums:
            if file_path not in stored_checksums:
                verification_report['new_files'].append(file_path)

        return verification_report

    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """Create a backup of all critical data"""
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        backup_dir = self.paths['backups'] / backup_name
        backup_dir.mkdir(exist_ok=True)

        # Backup patterns
        patterns_backup = backup_dir / 'patterns'
        shutil.copytree(self.paths['patterns'], patterns_backup, dirs_exist_ok=True)

        # Backup knowledge
        knowledge_backup = backup_dir / 'knowledge'
        shutil.copytree(self.paths['knowledge'], knowledge_backup, dirs_exist_ok=True)

        # Backup agents
        agents_backup = backup_dir / 'agents'
        shutil.copytree(self.paths['agents'], agents_backup, dirs_exist_ok=True)

        # Create backup manifest
        manifest = {
            'backup_name': backup_name,
            'created_at': datetime.now().isoformat(),
            'contents': {
                'patterns': len(list(self.paths['patterns'].rglob('*.json'))),
                'knowledge_files': len(list(self.paths['knowledge'].glob('*.json'))),
                'agent_files': len(list(self.paths['agents'].glob('*.py')))
            },
            'checksums': self.generate_checksums()
        }

        with open(backup_dir / 'manifest.json', 'w') as f:
            json.dump(manifest, f, indent=2)

        self.logger.info(f"Backup created: {backup_name}")
        return str(backup_dir)

    def restore_backup(self, backup_name: str) -> bool:
        """Restore from a backup"""
        backup_dir = self.paths['backups'] / backup_name

        if not backup_dir.exists():
            self.logger.error(f"Backup not found: {backup_name}")
            return False

        # Create temporary backup of current state
        temp_backup = self.create_backup("temp_before_restore")

        try:
            # Restore patterns
            if (backup_dir / 'patterns').exists():
                shutil.rmtree(self.paths['patterns'])
                shutil.copytree(backup_dir / 'patterns', self.paths['patterns'])

            # Restore knowledge
            if (backup_dir / 'knowledge').exists():
                shutil.rmtree(self.paths['knowledge'])
                shutil.copytree(backup_dir / 'knowledge', self.paths['knowledge'])

            # Restore agents
            if (backup_dir / 'agents').exists():
                shutil.rmtree(self.paths['agents'])
                shutil.copytree(backup_dir / 'agents', self.paths['agents'])

            self.logger.info(f"Restored from backup: {backup_name}")
            return True

        except Exception as e:
            self.logger.error(f"Restore failed, reverting: {str(e)}")
            # Attempt to restore from temp backup
            self.restore_backup("temp_before_restore")
            return False

    def fix_duplicate_patterns(self) -> Dict[str, Any]:
        """Fix duplicate pattern IDs by moving conflicting files"""
        validation_report = self.validate_patterns()
        fixes_applied = []

        for pattern_id, file_paths in validation_report.get('duplicate_ids', {}).items():
            if len(file_paths) < 2:
                continue

            # Keep the file in the most appropriate directory
            priority_dirs = ['queries', 'analysis', 'workflows', 'actions', 'ui']

            primary_file = None
            files_to_move = []

            for file_path in file_paths:
                path_obj = Path(file_path)
                parent_dir = path_obj.parent.name

                if parent_dir in priority_dirs and not primary_file:
                    primary_file = file_path
                else:
                    files_to_move.append(file_path)

            # If no file in priority dirs, keep the first one
            if not primary_file:
                primary_file = file_paths[0]
                files_to_move = file_paths[1:]

            # Move duplicate files to a duplicates directory
            duplicates_dir = self.paths['patterns'] / 'duplicates'
            duplicates_dir.mkdir(exist_ok=True)

            for file_path in files_to_move:
                src_path = Path(file_path)
                dst_path = duplicates_dir / f"{pattern_id}_{src_path.parent.name}_{src_path.name}"

                shutil.move(src_path, dst_path)
                fixes_applied.append({
                    'pattern_id': pattern_id,
                    'moved_from': file_path,
                    'moved_to': str(dst_path),
                    'kept_primary': primary_file
                })

        return {
            'fixes_applied': fixes_applied,
            'duplicates_resolved': len(fixes_applied)
        }

    def _file_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def comprehensive_health_check(self) -> Dict[str, Any]:
        """Run a comprehensive health check of the Trinity architecture"""
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'patterns': self.validate_patterns(),
            'knowledge': self.validate_knowledge_bases(),
            'checksums': None,
            'recommendations': []
        }

        # Add checksum verification if available
        try:
            health_report['checksums'] = self.verify_checksums()
        except Exception as e:
            health_report['checksums'] = {'error': str(e)}

        # Determine overall status
        issues = []
        if health_report['patterns']['duplicate_ids']:
            issues.append('duplicate_pattern_ids')
        if health_report['patterns']['invalid_files']:
            issues.append('invalid_pattern_files')
        if health_report['knowledge']['invalid_files']:
            issues.append('invalid_knowledge_files')

        if issues:
            health_report['overall_status'] = 'needs_attention'
            health_report['issues'] = issues

        # Generate recommendations
        if 'duplicate_pattern_ids' in issues:
            health_report['recommendations'].append(
                "Run fix_duplicate_patterns() to resolve pattern ID conflicts"
            )

        if health_report['checksums'] and 'error' in health_report['checksums']:
            health_report['recommendations'].append(
                "Run generate_checksums() to establish baseline checksums"
            )

        return health_report


# Factory function for easy access
def get_data_integrity_manager(base_path: str = ".") -> DataIntegrityManager:
    """Get a DataIntegrityManager instance"""
    return DataIntegrityManager(base_path)