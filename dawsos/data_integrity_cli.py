#!/usr/bin/env python3
"""
Data Integrity CLI - Command-line tools for maintaining DawsOS data integrity
Provides validation, backup, and source control operations
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.data_integrity_manager import get_data_integrity_manager


def cmd_validate(args):
    """Validate patterns and knowledge bases"""
    dim = get_data_integrity_manager()

    print("🔍 Validating Patterns...")
    pattern_report = dim.validate_patterns()

    print(f"\n📊 Pattern Validation Results:")
    print(f"   Total Files: {pattern_report['total_files']}")
    print(f"   Valid Patterns: {pattern_report['valid_patterns']}")
    print(f"   Schema Files: {len(pattern_report['schema_files'])}")

    if pattern_report['duplicate_ids']:
        print(f"\n⚠️  Duplicate Pattern IDs Found:")
        for pattern_id, files in pattern_report['duplicate_ids'].items():
            print(f"   '{pattern_id}': {files}")

    if pattern_report['invalid_files']:
        print(f"\n❌ Invalid Files:")
        for invalid in pattern_report['invalid_files']:
            print(f"   {invalid['file']}: {invalid['error']}")

    if pattern_report['missing_ids']:
        print(f"\n🔤 Files Missing IDs:")
        for file in pattern_report['missing_ids']:
            print(f"   {file}")

    print("\n🔍 Validating Knowledge Bases...")
    knowledge_report = dim.validate_knowledge_bases()

    print(f"\n📊 Knowledge Validation Results:")
    print(f"   Total Files: {knowledge_report['total_files']}")
    print(f"   Valid Files: {knowledge_report['valid_files']}")

    if knowledge_report['invalid_files']:
        print(f"\n❌ Invalid Knowledge Files:")
        for invalid in knowledge_report['invalid_files']:
            print(f"   {invalid['file']}: {invalid['error']}")

    # Schema validation for specific files
    for file, validation in knowledge_report['schema_validation'].items():
        if not validation['valid']:
            print(f"\n⚠️  {file} Missing Required Sections:")
            for section in validation['missing_sections']:
                print(f"   - {section}")

    if args.output:
        # Save detailed report
        full_report = {
            'patterns': pattern_report,
            'knowledge': knowledge_report,
            'timestamp': datetime.now().isoformat()
        }
        with open(args.output, 'w') as f:
            json.dump(full_report, f, indent=2)
        print(f"\n💾 Detailed report saved to: {args.output}")


def cmd_fix_duplicates(args):
    """Fix duplicate pattern IDs"""
    dim = get_data_integrity_manager()

    print("🔧 Fixing Duplicate Pattern IDs...")

    if not args.force:
        # Create backup first
        backup_name = f"before_fix_duplicates_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = dim.create_backup(backup_name)
        print(f"📦 Created backup: {backup_path}")

    fix_report = dim.fix_duplicate_patterns()

    if fix_report['duplicates_resolved'] > 0:
        print(f"\n✅ Resolved {fix_report['duplicates_resolved']} duplicate pattern IDs:")
        for fix in fix_report['fixes_applied']:
            print(f"   {fix['pattern_id']}:")
            print(f"     Kept: {fix['kept_primary']}")
            print(f"     Moved: {fix['moved_from']} → {fix['moved_to']}")
    else:
        print("\n✅ No duplicate pattern IDs found.")


def cmd_health_check(args):
    """Run comprehensive health check"""
    dim = get_data_integrity_manager()

    print("🏥 Running Comprehensive Health Check...")
    health_report = dim.comprehensive_health_check()

    status_emoji = "✅" if health_report['overall_status'] == 'healthy' else "⚠️"
    print(f"\n{status_emoji} Overall Status: {health_report['overall_status'].upper()}")

    print(f"\n📊 Summary:")
    print(f"   Patterns: {health_report['patterns']['valid_patterns']}/{health_report['patterns']['total_files']}")
    print(f"   Knowledge: {health_report['knowledge']['valid_files']}/{health_report['knowledge']['total_files']}")

    if 'issues' in health_report:
        print(f"\n⚠️  Issues Detected:")
        for issue in health_report['issues']:
            print(f"   - {issue.replace('_', ' ').title()}")

    if health_report['recommendations']:
        print(f"\n💡 Recommendations:")
        for rec in health_report['recommendations']:
            print(f"   - {rec}")

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(health_report, f, indent=2)
        print(f"\n💾 Health report saved to: {args.output}")


def cmd_backup(args):
    """Create backup"""
    dim = get_data_integrity_manager()

    backup_name = args.name or f"manual_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"📦 Creating backup: {backup_name}")

    backup_path = dim.create_backup(backup_name)
    print(f"✅ Backup created at: {backup_path}")

    # Show backup contents
    manifest_path = Path(backup_path) / 'manifest.json'
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        print(f"\n📄 Backup Contents:")
        for category, count in manifest['contents'].items():
            print(f"   {category}: {count} files")


def cmd_restore(args):
    """Restore from backup"""
    dim = get_data_integrity_manager()

    backup_dir = Path('storage/backups') / args.backup_name
    if not backup_dir.exists():
        print(f"❌ Backup not found: {args.backup_name}")
        return

    if not args.force:
        response = input(f"⚠️  This will overwrite current data. Continue? (y/N): ")
        if response.lower() != 'y':
            print("❌ Restore cancelled.")
            return

    print(f"🔄 Restoring from backup: {args.backup_name}")
    success = dim.restore_backup(args.backup_name)

    if success:
        print("✅ Restore completed successfully.")
    else:
        print("❌ Restore failed. Check logs for details.")


def cmd_checksums(args):
    """Generate or verify checksums"""
    dim = get_data_integrity_manager()

    if args.verify:
        print("🔍 Verifying checksums...")
        verification_report = dim.verify_checksums()

        if 'error' in verification_report:
            print(f"❌ {verification_report['error']}")
            return

        print(f"\n📊 Verification Results:")
        print(f"   Total Files: {verification_report['total_files']}")
        print(f"   Unchanged: {verification_report['unchanged_files']}")
        print(f"   Modified: {len(verification_report['modified_files'])}")
        print(f"   New: {len(verification_report['new_files'])}")
        print(f"   Deleted: {len(verification_report['deleted_files'])}")

        if verification_report['modified_files']:
            print(f"\n📝 Modified Files:")
            for file in verification_report['modified_files']:
                print(f"   {file}")

        if verification_report['new_files']:
            print(f"\n🆕 New Files:")
            for file in verification_report['new_files']:
                print(f"   {file}")

        if verification_report['deleted_files']:
            print(f"\n🗑️  Deleted Files:")
            for file in verification_report['deleted_files']:
                print(f"   {file}")

    else:
        print("🔐 Generating checksums...")
        checksums = dim.generate_checksums()
        print(f"✅ Generated checksums for {len(checksums)} files")


def cmd_list_backups(args):
    """List available backups"""
    backups_dir = Path('storage/backups')

    if not backups_dir.exists():
        print("📁 No backups directory found.")
        return

    backups = []
    for backup_dir in backups_dir.iterdir():
        if backup_dir.is_dir():
            manifest_path = backup_dir / 'manifest.json'
            if manifest_path.exists():
                try:
                    with open(manifest_path, 'r') as f:
                        manifest = json.load(f)
                    backups.append((backup_dir.name, manifest))
                except:
                    backups.append((backup_dir.name, None))

    if not backups:
        print("📁 No backups found.")
        return

    print("📦 Available Backups:")
    print(f"{'Name':<30} {'Created':<20} {'Patterns':<10} {'Knowledge':<10}")
    print("-" * 70)

    for backup_name, manifest in sorted(backups, key=lambda x: x[0], reverse=True):
        if manifest:
            created = manifest.get('created_at', 'Unknown')[:19].replace('T', ' ')
            patterns = manifest.get('contents', {}).get('patterns', '?')
            knowledge = manifest.get('contents', {}).get('knowledge_files', '?')
        else:
            created = 'Unknown'
            patterns = '?'
            knowledge = '?'

        print(f"{backup_name:<30} {created:<20} {patterns:<10} {knowledge:<10}")


def main():
    parser = argparse.ArgumentParser(
        description="DawsOS Data Integrity Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python data_integrity_cli.py validate                    # Validate all data
  python data_integrity_cli.py fix-duplicates              # Fix duplicate patterns
  python data_integrity_cli.py health-check                # Full health check
  python data_integrity_cli.py backup --name stable-v1     # Create named backup
  python data_integrity_cli.py restore stable-v1           # Restore backup
  python data_integrity_cli.py checksums                   # Generate checksums
  python data_integrity_cli.py checksums --verify          # Verify checksums
  python data_integrity_cli.py list-backups                # List backups
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate patterns and knowledge')
    validate_parser.add_argument('--output', '-o', help='Save detailed report to file')

    # Fix duplicates command
    fix_parser = subparsers.add_parser('fix-duplicates', help='Fix duplicate pattern IDs')
    fix_parser.add_argument('--force', action='store_true', help='Skip backup creation')

    # Health check command
    health_parser = subparsers.add_parser('health-check', help='Run comprehensive health check')
    health_parser.add_argument('--output', '-o', help='Save health report to file')

    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create backup')
    backup_parser.add_argument('--name', '-n', help='Backup name')

    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore from backup')
    restore_parser.add_argument('backup_name', help='Name of backup to restore')
    restore_parser.add_argument('--force', action='store_true', help='Skip confirmation')

    # Checksums command
    checksums_parser = subparsers.add_parser('checksums', help='Generate or verify checksums')
    checksums_parser.add_argument('--verify', action='store_true', help='Verify existing checksums')

    # List backups command
    subparsers.add_parser('list-backups', help='List available backups')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Command routing
    commands = {
        'validate': cmd_validate,
        'fix-duplicates': cmd_fix_duplicates,
        'health-check': cmd_health_check,
        'backup': cmd_backup,
        'restore': cmd_restore,
        'checksums': cmd_checksums,
        'list-backups': cmd_list_backups
    }

    if args.command in commands:
        try:
            commands[args.command](args)
        except KeyboardInterrupt:
            print("\n❌ Operation cancelled by user.")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    else:
        print(f"❌ Unknown command: {args.command}")


if __name__ == '__main__':
    main()