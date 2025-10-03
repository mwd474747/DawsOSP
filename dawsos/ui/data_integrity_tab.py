#!/usr/bin/env python3
"""
Data Integrity Tab - Real-time data integrity monitoring and management UI
Provides visual monitoring of pattern consistency, knowledge base integrity, and system health
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from core.data_integrity_manager import get_data_integrity_manager


def render_data_integrity_tab():
    """Render the data integrity monitoring tab"""
    st.markdown("# 🔐 Data Integrity Dashboard")
    st.markdown("*Real-time monitoring of Trinity architecture data consistency*")

    # Initialize Data Integrity Manager
    try:
        dim = get_data_integrity_manager()
    except Exception as e:
        st.error(f"Failed to initialize Data Integrity Manager: {str(e)}")
        return

    # Top-level metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        try:
            pattern_validation = dim.validate_patterns()
            total_patterns = pattern_validation['valid_patterns']
            total_files = pattern_validation['total_files']
            st.metric(
                "Pattern Health",
                f"{total_patterns}/{total_files}",
                delta=f"-{len(pattern_validation['duplicate_ids'])} dupes" if pattern_validation['duplicate_ids'] else "✓ Clean"
            )
        except Exception as e:
            st.metric("Pattern Health", "Error", delta=str(e))

    with col2:
        try:
            knowledge_validation = dim.validate_knowledge_bases()
            valid_knowledge = knowledge_validation['valid_files']
            total_knowledge = knowledge_validation['total_files']
            st.metric(
                "Knowledge Health",
                f"{valid_knowledge}/{total_knowledge}",
                delta="✓ Valid" if valid_knowledge == total_knowledge else "⚠ Issues"
            )
        except Exception as e:
            st.metric("Knowledge Health", "Error", delta=str(e))

    with col3:
        try:
            health_report = dim.comprehensive_health_check()
            status = health_report['overall_status']
            status_emoji = "✅" if status == 'healthy' else "⚠️"
            st.metric(
                "System Status",
                f"{status_emoji} {status.title()}",
                delta=f"{len(health_report.get('issues', []))} issues"
            )
        except Exception as e:
            st.metric("System Status", "Error", delta=str(e))

    with col4:
        try:
            backup_dir = Path('storage/backups')
            backup_count = len([d for d in backup_dir.iterdir() if d.is_dir()]) if backup_dir.exists() else 0
            st.metric(
                "Backup Count",
                backup_count,
                delta="💾 Available"
            )
        except Exception as e:
            st.metric("Backup Count", "Error", delta=str(e))

    st.markdown("---")

    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔍 Validation",
        "📊 Health Check",
        "🛠️ Management",
        "📦 Backups",
        "🔐 Checksums"
    ])

    with tab1:
        render_validation_tab(dim)

    with tab2:
        render_health_check_tab(dim)

    with tab3:
        render_management_tab(dim)

    with tab4:
        render_backups_tab(dim)

    with tab5:
        render_checksums_tab(dim)


def render_validation_tab(dim):
    """Render pattern and knowledge validation interface"""
    st.markdown("### 🔍 Data Validation")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Pattern Validation")
        if st.button("🔄 Validate Patterns", key="validate_patterns"):
            with st.spinner("Validating patterns..."):
                try:
                    pattern_report = dim.validate_patterns()

                    # Display results
                    st.success(f"✅ Validated {pattern_report['total_files']} pattern files")

                    if pattern_report['duplicate_ids']:
                        st.warning("⚠️ Duplicate IDs Found:")
                        for pattern_id, files in pattern_report['duplicate_ids'].items():
                            with st.expander(f"Duplicate: {pattern_id}"):
                                for file in files:
                                    st.code(file)

                    if pattern_report['invalid_files']:
                        st.error("❌ Invalid Files:")
                        for invalid in pattern_report['invalid_files']:
                            st.error(f"{invalid['file']}: {invalid['error']}")

                    if pattern_report['schema_files']:
                        st.info(f"ℹ️ Skipped {len(pattern_report['schema_files'])} schema files")

                    # Store in session state for other tabs
                    st.session_state['pattern_validation'] = pattern_report

                except Exception as e:
                    st.error(f"Validation failed: {str(e)}")

    with col2:
        st.markdown("#### Knowledge Validation")
        if st.button("🔄 Validate Knowledge", key="validate_knowledge"):
            with st.spinner("Validating knowledge bases..."):
                try:
                    knowledge_report = dim.validate_knowledge_bases()

                    st.success(f"✅ Validated {knowledge_report['total_files']} knowledge files")

                    if knowledge_report['invalid_files']:
                        st.error("❌ Invalid Files:")
                        for invalid in knowledge_report['invalid_files']:
                            st.error(f"{invalid['file']}: {invalid['error']}")

                    # Show file sizes
                    if knowledge_report['file_sizes']:
                        st.markdown("📊 **File Sizes:**")
                        for file, size in knowledge_report['file_sizes'].items():
                            st.text(f"{file}: {size:,} bytes")

                    st.session_state['knowledge_validation'] = knowledge_report

                except Exception as e:
                    st.error(f"Validation failed: {str(e)}")

    # Pattern distribution chart
    if 'pattern_validation' in st.session_state:
        pattern_report = st.session_state['pattern_validation']
        if pattern_report['total_files'] > 0:
            st.markdown("#### 📊 Pattern Distribution")

            # Count patterns by directory
            pattern_dirs = {}
            for pattern_file in Path('patterns').rglob('*.json'):
                if pattern_file.name != 'schema.json':
                    dir_name = pattern_file.parent.name
                    pattern_dirs[dir_name] = pattern_dirs.get(dir_name, 0) + 1

            if pattern_dirs:
                df = pd.DataFrame(
                    list(pattern_dirs.items()),
                    columns=['Directory', 'Count']
                )

                fig = px.pie(df, values='Count', names='Directory',
                           title="Pattern Files by Directory")
                st.plotly_chart(fig, use_container_width=True)


def render_health_check_tab(dim):
    """Render comprehensive health check interface"""
    st.markdown("### 🏥 System Health Check")

    if st.button("🔄 Run Health Check", key="health_check"):
        with st.spinner("Running comprehensive health check..."):
            try:
                health_report = dim.comprehensive_health_check()

                # Overall status
                status = health_report['overall_status']
                if status == 'healthy':
                    st.success(f"✅ System Status: {status.upper()}")
                else:
                    st.warning(f"⚠️ System Status: {status.upper()}")

                # Issues
                if 'issues' in health_report:
                    st.markdown("#### ⚠️ Issues Detected")
                    for issue in health_report['issues']:
                        st.error(f"• {issue.replace('_', ' ').title()}")

                # Recommendations
                if health_report['recommendations']:
                    st.markdown("#### 💡 Recommendations")
                    for rec in health_report['recommendations']:
                        st.info(f"• {rec}")

                # Detailed metrics
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("#### 📊 Pattern Metrics")
                    pattern_data = health_report['patterns']
                    st.json({
                        'Total Files': pattern_data['total_files'],
                        'Valid Patterns': pattern_data['valid_patterns'],
                        'Duplicates': len(pattern_data['duplicate_ids']),
                        'Invalid Files': len(pattern_data['invalid_files'])
                    })

                with col2:
                    st.markdown("#### 📊 Knowledge Metrics")
                    knowledge_data = health_report['knowledge']
                    st.json({
                        'Total Files': knowledge_data['total_files'],
                        'Valid Files': knowledge_data['valid_files'],
                        'Invalid Files': len(knowledge_data['invalid_files'])
                    })

                # Store in session state
                st.session_state['health_report'] = health_report

            except Exception as e:
                st.error(f"Health check failed: {str(e)}")


def render_management_tab(dim):
    """Render data management operations"""
    st.markdown("### 🛠️ Data Management")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🔧 Fix Operations")

        if st.button("🔧 Fix Duplicate Patterns", key="fix_duplicates"):
            if 'pattern_validation' not in st.session_state:
                st.warning("⚠️ Run pattern validation first to identify duplicates")
            else:
                with st.spinner("Fixing duplicate patterns..."):
                    try:
                        fix_report = dim.fix_duplicate_patterns()

                        if fix_report['duplicates_resolved'] > 0:
                            st.success(f"✅ Fixed {fix_report['duplicates_resolved']} duplicate patterns")

                            for fix in fix_report['fixes_applied']:
                                with st.expander(f"Fixed: {fix['pattern_id']}"):
                                    st.text(f"Kept: {fix['kept_primary']}")
                                    st.text(f"Moved: {fix['moved_from']} → {fix['moved_to']}")
                        else:
                            st.info("ℹ️ No duplicate patterns found")

                    except Exception as e:
                        st.error(f"Fix operation failed: {str(e)}")

        if st.button("📊 Generate Checksums", key="generate_checksums"):
            with st.spinner("Generating checksums..."):
                try:
                    checksums = dim.generate_checksums()
                    st.success(f"✅ Generated checksums for {len(checksums)} files")
                    st.info("💾 Checksums saved to storage/checksums.json")
                except Exception as e:
                    st.error(f"Checksum generation failed: {str(e)}")

    with col2:
        st.markdown("#### 🗂️ File Operations")

        # Pattern file browser
        st.markdown("**Pattern Files:**")
        pattern_files = list(Path('patterns').rglob('*.json'))
        if pattern_files:
            selected_pattern = st.selectbox(
                "Select pattern file:",
                pattern_files,
                format_func=lambda x: str(x.relative_to(Path('patterns')))
            )

            if selected_pattern and st.button("👁️ View Pattern", key="view_pattern"):
                try:
                    with open(selected_pattern, 'r') as f:
                        pattern_content = json.load(f)

                    st.json(pattern_content)
                except Exception as e:
                    st.error(f"Failed to read pattern: {str(e)}")

        # Knowledge file browser
        st.markdown("**Knowledge Files:**")
        knowledge_files = list(Path('storage/knowledge').glob('*.json'))
        if knowledge_files:
            selected_knowledge = st.selectbox(
                "Select knowledge file:",
                knowledge_files,
                format_func=lambda x: x.name
            )

            if selected_knowledge and st.button("👁️ View Knowledge", key="view_knowledge"):
                try:
                    with open(selected_knowledge, 'r') as f:
                        knowledge_content = json.load(f)

                    # Show limited preview for large files
                    if isinstance(knowledge_content, dict) and len(str(knowledge_content)) > 10000:
                        st.info("📄 Large file - showing structure only")
                        preview = {k: f"<{type(v).__name__}>" for k, v in knowledge_content.items()}
                        st.json(preview)
                    else:
                        st.json(knowledge_content)
                except Exception as e:
                    st.error(f"Failed to read knowledge file: {str(e)}")


def render_backups_tab(dim):
    """Render backup management interface"""
    st.markdown("### 📦 Backup Management")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### 💾 Create Backup")

        backup_name = st.text_input(
            "Backup name (optional):",
            placeholder="e.g., stable-v1, before-experiment"
        )

        if st.button("📦 Create Backup", key="create_backup"):
            with st.spinner("Creating backup..."):
                try:
                    backup_path = dim.create_backup(backup_name or None)
                    st.success(f"✅ Backup created: {backup_path}")

                    # Show backup contents
                    manifest_path = Path(backup_path) / 'manifest.json'
                    if manifest_path.exists():
                        with open(manifest_path, 'r') as f:
                            manifest = json.load(f)

                        st.info("📄 Backup Contents:")
                        for category, count in manifest['contents'].items():
                            st.text(f"• {category}: {count} files")

                except Exception as e:
                    st.error(f"Backup creation failed: {str(e)}")

    with col2:
        st.markdown("#### 📋 Available Backups")

        backups_dir = Path('storage/backups')
        if backups_dir.exists():
            backup_dirs = [d for d in backups_dir.iterdir() if d.is_dir()]
            backup_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            if backup_dirs:
                for backup_dir in backup_dirs[:5]:  # Show last 5 backups
                    manifest_path = backup_dir / 'manifest.json'
                    if manifest_path.exists():
                        try:
                            with open(manifest_path, 'r') as f:
                                manifest = json.load(f)

                            created = manifest.get('created_at', 'Unknown')[:19].replace('T', ' ')
                            st.text(f"📦 {backup_dir.name}")
                            st.text(f"   {created}")

                        except:
                            st.text(f"📦 {backup_dir.name} (no manifest)")
            else:
                st.info("No backups found")
        else:
            st.info("Backups directory not found")


def render_checksums_tab(dim):
    """Render checksum verification interface"""
    st.markdown("### 🔐 Checksum Management")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🔍 Verify Checksums")

        if st.button("🔍 Verify File Integrity", key="verify_checksums"):
            with st.spinner("Verifying checksums..."):
                try:
                    verification_report = dim.verify_checksums()

                    if 'error' in verification_report:
                        st.error(f"❌ {verification_report['error']}")
                        st.info("💡 Generate checksums first")
                    else:
                        # Show verification results
                        st.success("✅ Checksum verification completed")

                        col_a, col_b, col_c, col_d = st.columns(4)
                        with col_a:
                            st.metric("Unchanged", verification_report['unchanged_files'])
                        with col_b:
                            st.metric("Modified", len(verification_report['modified_files']))
                        with col_c:
                            st.metric("New", len(verification_report['new_files']))
                        with col_d:
                            st.metric("Deleted", len(verification_report['deleted_files']))

                        # Show details
                        if verification_report['modified_files']:
                            st.warning("⚠️ Modified Files:")
                            for file in verification_report['modified_files']:
                                st.text(f"• {file}")

                        if verification_report['new_files']:
                            st.info("🆕 New Files:")
                            for file in verification_report['new_files']:
                                st.text(f"• {file}")

                        if verification_report['deleted_files']:
                            st.error("🗑️ Deleted Files:")
                            for file in verification_report['deleted_files']:
                                st.text(f"• {file}")

                except Exception as e:
                    st.error(f"Verification failed: {str(e)}")

    with col2:
        st.markdown("#### 📊 Checksum Statistics")

        # Show checksum file info if it exists
        checksums_file = Path('storage/checksums.json')
        if checksums_file.exists():
            try:
                with open(checksums_file, 'r') as f:
                    checksum_data = json.load(f)

                generated_at = checksum_data.get('generated_at', 'Unknown')
                checksum_count = len(checksum_data.get('checksums', {}))

                st.info("📄 Checksums File:")
                st.text(f"Generated: {generated_at[:19].replace('T', ' ')}")
                st.text(f"Files tracked: {checksum_count}")

                # File type breakdown
                checksums = checksum_data.get('checksums', {})
                file_types = {}
                for file_path in checksums.keys():
                    ext = Path(file_path).suffix or 'no extension'
                    file_types[ext] = file_types.get(ext, 0) + 1

                if file_types:
                    st.markdown("**File Types:**")
                    for ext, count in sorted(file_types.items()):
                        st.text(f"• {ext}: {count}")

            except Exception as e:
                st.error(f"Failed to read checksums: {str(e)}")
        else:
            st.warning("⚠️ No checksums file found")
            st.info("💡 Generate checksums to track file integrity")