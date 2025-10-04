#!/usr/bin/env python3
"""
Pytest tests for pattern JSON validation.
Ensures all patterns have valid JSON syntax and required fields.
"""
import pytest
import json
import os
from pathlib import Path


class TestPatternValidation:
    """Test suite for validating pattern configuration files"""

    @pytest.fixture(scope="class")
    def patterns_dir(self):
        """Get patterns directory path"""
        # Try both possible locations
        test_dir = Path(__file__).parent.parent
        dawsos_patterns = test_dir / 'dawsos' / 'patterns'

        if dawsos_patterns.exists():
            return dawsos_patterns
        else:
            pytest.skip(f"Patterns directory not found at {dawsos_patterns}")

    @pytest.fixture(scope="class")
    def pattern_files(self, patterns_dir):
        """Get all pattern JSON files"""
        return list(patterns_dir.rglob('*.json'))

    def test_patterns_directory_exists(self, patterns_dir):
        """Test that patterns directory exists"""
        assert patterns_dir.exists(), f"Patterns directory should exist at {patterns_dir}"
        assert patterns_dir.is_dir(), "Patterns path should be a directory"

    def test_at_least_one_pattern_exists(self, pattern_files):
        """Test that at least one pattern file exists"""
        assert len(pattern_files) > 0, "Should have at least one pattern file"

    @pytest.mark.parametrize("pattern_file", pytest.lazy_fixture("pattern_files") if hasattr(pytest, "lazy_fixture") else [])
    def test_pattern_valid_json(self, pattern_file):
        """Test that each pattern file contains valid JSON"""
        with open(pattern_file, 'r') as f:
            try:
                data = json.load(f)
                assert isinstance(data, dict), f"{pattern_file.name} should contain a JSON object"
            except json.JSONDecodeError as e:
                pytest.fail(f"{pattern_file.name} contains invalid JSON: {e}")

    def test_all_patterns_valid_json(self, pattern_files):
        """Test that all pattern files contain valid JSON"""
        invalid_files = []

        for pattern_file in pattern_files:
            with open(pattern_file, 'r') as f:
                try:
                    data = json.load(f)
                    assert isinstance(data, dict)
                except (json.JSONDecodeError, AssertionError) as e:
                    invalid_files.append((pattern_file.name, str(e)))

        assert len(invalid_files) == 0, f"Invalid JSON in files: {invalid_files}"

    def test_required_fields_present(self, pattern_files):
        """Test that all patterns have required fields"""
        required_fields = ['id', 'name', 'description']
        missing_fields = []

        for pattern_file in pattern_files:
            with open(pattern_file, 'r') as f:
                try:
                    data = json.load(f)

                    for field in required_fields:
                        if field not in data:
                            missing_fields.append((pattern_file.name, field))
                except json.JSONDecodeError:
                    # Skip files with invalid JSON (covered by other test)
                    continue

        assert len(missing_fields) == 0, f"Missing required fields: {missing_fields}"

    def test_pattern_ids_unique(self, pattern_files):
        """Test that all pattern IDs are unique"""
        pattern_ids = {}

        for pattern_file in pattern_files:
            with open(pattern_file, 'r') as f:
                try:
                    data = json.load(f)
                    pattern_id = data.get('id')

                    if pattern_id:
                        if pattern_id in pattern_ids:
                            pytest.fail(
                                f"Duplicate pattern ID '{pattern_id}' found in:\n"
                                f"  - {pattern_ids[pattern_id]}\n"
                                f"  - {pattern_file}"
                            )
                        pattern_ids[pattern_id] = pattern_file
                except json.JSONDecodeError:
                    continue

        assert len(pattern_ids) > 0, "Should have found at least one pattern with an ID"

    def test_pattern_steps_valid(self, pattern_files):
        """Test that pattern steps are properly formatted"""
        invalid_steps = []

        for pattern_file in pattern_files:
            with open(pattern_file, 'r') as f:
                try:
                    data = json.load(f)

                    if 'steps' in data:
                        steps = data['steps']

                        if not isinstance(steps, list):
                            invalid_steps.append((pattern_file.name, "steps must be a list"))
                            continue

                        for i, step in enumerate(steps):
                            if not isinstance(step, dict):
                                invalid_steps.append((pattern_file.name, f"step {i} must be an object"))
                            elif 'action' not in step:
                                invalid_steps.append((pattern_file.name, f"step {i} missing 'action' field"))
                except json.JSONDecodeError:
                    continue

        assert len(invalid_steps) == 0, f"Invalid steps: {invalid_steps}"

    def test_no_schema_files_in_validation(self, pattern_files):
        """Test that schema files are not included in validation"""
        schema_files = [f for f in pattern_files if 'schema' in f.name.lower()]

        # This is informational - schemas should be skipped but presence is OK
        if schema_files:
            print(f"\nNote: Found {len(schema_files)} schema files (these should be skipped by pattern engine)")

    def test_pattern_count(self, pattern_files):
        """Test that we have expected number of patterns"""
        # Filter out schema files
        actual_patterns = [f for f in pattern_files if 'schema' not in f.name.lower()]

        assert len(actual_patterns) >= 40, f"Should have at least 40 patterns, found {len(actual_patterns)}"
        print(f"\n✓ Found {len(actual_patterns)} valid pattern files")
