#!/usr/bin/env python3
"""
DawsOS Application Completeness Validator
Checks all UI functions, patterns, and data dependencies
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, 'dawsos')

class AppValidator:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.successes = []

    def validate_all(self):
        """Run all validation checks"""
        print("=" * 80)
        print("  DawsOS Application Completeness Validation")
        print("=" * 80)
        print()

        # Run all checks
        self.check_ui_components()
        self.check_patterns()
        self.check_core_functions()
        self.check_data_dependencies()
        self.check_storage_structure()
        self.check_imports()

        # Print summary
        self.print_summary()

    def check_ui_components(self):
        """Check all UI components are complete"""
        print("\n📱 Checking UI Components...")
        print("-" * 80)

        ui_files = {
            'pattern_browser.py': ['render_pattern_browser'],
            'alert_panel.py': ['AlertPanel', 'render_alert_panel'],
            'intelligence_display.py': ['IntelligenceDisplay', 'create_intelligence_display'],
            'trinity_dashboard_tabs.py': ['TrinityDashboardTabs', 'get_trinity_dashboard_tabs'],
            'governance_tab.py': ['render_governance_tab'],
            'data_integrity_tab.py': ['render_data_integrity_tab'],
            'workflows_tab.py': ['render_workflows_tab'],
        }

        for filename, required_items in ui_files.items():
            filepath = Path(f'dawsos/ui/{filename}')

            if not filepath.exists():
                self.issues.append(f"UI file missing: {filename}")
                print(f"  ❌ {filename} - FILE MISSING")
                continue

            content = filepath.read_text()

            missing = []
            for item in required_items:
                if item not in content:
                    missing.append(item)

            if missing:
                self.issues.append(f"{filename} missing: {', '.join(missing)}")
                print(f"  ❌ {filename} - Missing: {', '.join(missing)}")
            else:
                self.successes.append(f"{filename} complete")
                print(f"  ✅ {filename} - All required items present")

    def check_patterns(self):
        """Check all patterns are complete and valid"""
        print("\n📋 Checking Patterns...")
        print("-" * 80)

        pattern_dir = Path('dawsos/patterns')

        if not pattern_dir.exists():
            self.issues.append("Pattern directory missing")
            print("  ❌ Pattern directory not found")
            return

        patterns = list(pattern_dir.rglob('*.json'))
        print(f"  Found {len(patterns)} pattern files")

        incomplete_patterns = []
        valid_patterns = []

        for pattern_file in patterns:
            try:
                with open(pattern_file) as f:
                    pattern = json.load(f)

                # Check required fields
                required = ['id', 'name', 'description']
                missing = [f for f in required if f not in pattern]

                # Check for steps or triggers
                has_steps = 'steps' in pattern or 'extends' in pattern
                has_triggers = 'triggers' in pattern or 'extends' in pattern

                if missing:
                    incomplete_patterns.append((pattern_file.name, f"Missing: {', '.join(missing)}"))
                elif not has_steps:
                    incomplete_patterns.append((pattern_file.name, "Missing 'steps' or 'extends'"))
                elif not has_triggers and pattern.get('id') != 'governance_template':
                    self.warnings.append(f"{pattern_file.name} has no triggers")
                    valid_patterns.append(pattern_file.name)
                else:
                    valid_patterns.append(pattern_file.name)

            except json.JSONDecodeError as e:
                incomplete_patterns.append((pattern_file.name, f"Invalid JSON: {e}"))
            except Exception as e:
                incomplete_patterns.append((pattern_file.name, f"Error: {e}"))

        print(f"  ✅ Valid patterns: {len(valid_patterns)}")

        if incomplete_patterns:
            print(f"  ⚠️  Incomplete patterns: {len(incomplete_patterns)}")
            for name, reason in incomplete_patterns[:5]:
                print(f"     - {name}: {reason}")
                self.warnings.append(f"Pattern {name}: {reason}")

    def check_core_functions(self):
        """Check core Trinity functions are present"""
        print("\n⚙️  Checking Core Functions...")
        print("-" * 80)

        core_files = {
            'agent_runtime.py': ['AgentRuntime', 'exec_via_registry'],
            'pattern_engine.py': ['PatternEngine', 'execute_pattern'],
            'universal_executor.py': ['UniversalExecutor', 'execute'],
            'knowledge_graph.py': ['KnowledgeGraph', 'add_node'],
            'agent_adapter.py': ['AgentRegistry', 'AgentAdapter'],  # Fixed: AgentRegistry is in agent_adapter.py
            'alert_manager.py': ['AlertManager', 'create_alert'],
            'compliance_checker.py': ['ComplianceChecker', 'check_pattern'],
        }

        for filename, required_items in core_files.items():
            filepath = Path(f'dawsos/core/{filename}')

            if not filepath.exists():
                self.issues.append(f"Core file missing: {filename}")
                print(f"  ❌ {filename} - FILE MISSING")
                continue

            content = filepath.read_text()

            missing = []
            for item in required_items:
                # Check for class or function definition
                if f"class {item}" not in content and f"def {item}" not in content:
                    missing.append(item)

            if missing:
                self.issues.append(f"{filename} missing: {', '.join(missing)}")
                print(f"  ❌ {filename} - Missing: {', '.join(missing)}")
            else:
                self.successes.append(f"{filename} complete")
                print(f"  ✅ {filename} - All required items present")

    def check_data_dependencies(self):
        """Check required data files exist"""
        print("\n📊 Checking Data Dependencies...")
        print("-" * 80)

        required_data = [
            'storage/knowledge/sector_performance.json',
            'storage/knowledge/economic_cycles.json',
            'storage/knowledge/buffett_checklist.json',
            'storage/knowledge/dalio_cycles.json',
        ]

        for data_path in required_data:
            filepath = Path(f'dawsos/{data_path}')

            if filepath.exists():
                size = filepath.stat().st_size
                print(f"  ✅ {data_path} ({size} bytes)")
                self.successes.append(f"Data file present: {data_path}")
            else:
                print(f"  ⚠️  {data_path} - Missing (will use defaults)")
                self.warnings.append(f"Optional data file missing: {data_path}")

    def check_storage_structure(self):
        """Check storage directories exist"""
        print("\n💾 Checking Storage Structure...")
        print("-" * 80)

        required_dirs = [
            'storage',
            'storage/knowledge',
            'storage/backups',
            'storage/alerts',
            'storage/agent_memory',
        ]

        for dir_path in required_dirs:
            dirpath = Path(f'dawsos/{dir_path}')

            if dirpath.exists():
                file_count = len(list(dirpath.glob('*')))
                print(f"  ✅ {dir_path}/ ({file_count} files)")
                self.successes.append(f"Directory exists: {dir_path}")
            else:
                print(f"  ⚠️  {dir_path}/ - Missing (will be created)")
                self.warnings.append(f"Storage directory missing: {dir_path}")

                # Try to create it
                try:
                    dirpath.mkdir(parents=True, exist_ok=True)
                    print(f"     ✓ Created {dir_path}/")
                except Exception as e:
                    self.issues.append(f"Cannot create {dir_path}: {e}")

    def check_imports(self):
        """Check critical imports work"""
        print("\n📦 Checking Critical Imports...")
        print("-" * 80)

        imports_to_check = [
            ('streamlit', 'Streamlit UI framework'),
            ('pandas', 'Data manipulation'),
            ('anthropic', 'Claude API (optional)'),
            ('plotly', 'Visualizations (optional)'),
        ]

        for module_name, description in imports_to_check:
            try:
                __import__(module_name)
                print(f"  ✅ {module_name} - {description}")
                self.successes.append(f"Import working: {module_name}")
            except ImportError:
                if module_name in ['anthropic', 'plotly']:
                    print(f"  ⚠️  {module_name} - {description} (optional, not installed)")
                    self.warnings.append(f"Optional import missing: {module_name}")
                else:
                    print(f"  ❌ {module_name} - {description} (REQUIRED)")
                    self.issues.append(f"Required import missing: {module_name}")

    def check_main_integration(self):
        """Check main.py has all integrations"""
        print("\n🔗 Checking Main Integration...")
        print("-" * 80)

        main_file = Path('dawsos/main.py')

        if not main_file.exists():
            self.issues.append("main.py not found")
            print("  ❌ main.py not found")
            return

        content = main_file.read_text()

        required_imports = [
            'render_pattern_browser',
            'AlertPanel',
            'AlertManager',
        ]

        missing_imports = [imp for imp in required_imports if imp not in content]

        if missing_imports:
            self.issues.append(f"main.py missing imports: {', '.join(missing_imports)}")
            print(f"  ❌ Missing imports: {', '.join(missing_imports)}")
        else:
            print("  ✅ All required imports present")

        # Check tabs
        if 'Pattern Browser' in content and 'Alerts' in content:
            print("  ✅ New tabs integrated")
        else:
            self.issues.append("New tabs not integrated in main.py")
            print("  ❌ New tabs not integrated")

    def print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 80)
        print("  VALIDATION SUMMARY")
        print("=" * 80)
        print()

        total_checks = len(self.successes) + len(self.warnings) + len(self.issues)

        print(f"✅ Successes: {len(self.successes)}")
        print(f"⚠️  Warnings:  {len(self.warnings)}")
        print(f"❌ Issues:    {len(self.issues)}")
        print(f"📊 Total:     {total_checks}")
        print()

        if self.issues:
            print("🚨 CRITICAL ISSUES (Must Fix):")
            print("-" * 80)
            for issue in self.issues:
                print(f"  ❌ {issue}")
            print()

        if self.warnings:
            print("⚠️  WARNINGS (Optional):")
            print("-" * 80)
            for warning in self.warnings[:10]:
                print(f"  ⚠️  {warning}")
            if len(self.warnings) > 10:
                print(f"  ... and {len(self.warnings) - 10} more warnings")
            print()

        # Overall status
        print("=" * 80)
        if not self.issues:
            print("✅ APPLICATION IS READY TO RUN")
            print()
            print("Start with: streamlit run dawsos/main.py")
            return 0
        else:
            print("❌ APPLICATION HAS CRITICAL ISSUES")
            print()
            print(f"Please fix {len(self.issues)} critical issue(s) before running.")
            return 1

def main():
    validator = AppValidator()
    validator.validate_all()

    # Also check main integration
    validator.check_main_integration()

    return validator.print_summary()

if __name__ == "__main__":
    exit(main())
