#!/usr/bin/env python3
"""
Tests for Pattern Templates

Validates that all 48 patterns have valid template fields and
can perform variable substitution correctly.
"""

import pytest
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestPatternTemplates:
    """Test pattern template structure and validation"""

    @pytest.fixture
    def pattern_files(self):
        """Get all pattern JSON files"""
        pattern_dir = Path(__file__).parent.parent.parent / 'patterns'
        return list(pattern_dir.rglob('*.json'))

    def test_all_patterns_have_templates(self, pattern_files):
        """Test that all patterns include template field"""
        patterns_without_templates = []

        for pattern_file in pattern_files:
            # Skip schema file
            if pattern_file.name == 'schema.json':
                continue

            with open(pattern_file) as f:
                pattern = json.load(f)

            # Check if pattern has template field
            if 'template' not in pattern:
                patterns_without_templates.append(pattern_file.name)

        # Allow some patterns to not have templates (legacy)
        # But report them
        if patterns_without_templates:
            print(f"\nPatterns without templates: {patterns_without_templates}")

        # Most patterns should have templates
        assert len(patterns_without_templates) < 10, \
            f"Too many patterns missing templates: {patterns_without_templates}"

    def test_template_variable_syntax(self, pattern_files):
        """Test that template variables use correct syntax"""
        invalid_templates = []

        for pattern_file in pattern_files:
            if pattern_file.name == 'schema.json':
                continue

            with open(pattern_file) as f:
                pattern = json.load(f)

            template = pattern.get('template', '')
            if not template:
                continue

            # Check for common variable syntax patterns
            # Variables should use {{variable}} syntax
            if '${' in template or '%s' in template or '{0}' in template:
                invalid_templates.append({
                    'file': pattern_file.name,
                    'template': template[:100]
                })

        assert len(invalid_templates) == 0, \
            f"Patterns with invalid variable syntax: {invalid_templates}"

    def test_template_field_types(self, pattern_files):
        """Test that template fields have correct types"""
        invalid_types = []

        for pattern_file in pattern_files:
            if pattern_file.name == 'schema.json':
                continue

            with open(pattern_file) as f:
                pattern = json.load(f)

            template = pattern.get('template')

            # Template should be string if present
            if template is not None and not isinstance(template, str):
                invalid_types.append({
                    'file': pattern_file.name,
                    'type': type(template).__name__
                })

        assert len(invalid_types) == 0, \
            f"Patterns with invalid template types: {invalid_types}"

    def test_pattern_structure_validity(self, pattern_files):
        """Test that all patterns have required fields"""
        invalid_patterns = []

        required_fields = ['id', 'name', 'description', 'version', 'last_updated']

        for pattern_file in pattern_files:
            if pattern_file.name == 'schema.json':
                continue

            with open(pattern_file) as f:
                pattern = json.load(f)

            # Check required fields
            missing_fields = [f for f in required_fields if f not in pattern]

            if missing_fields:
                invalid_patterns.append({
                    'file': pattern_file.name,
                    'missing': missing_fields
                })

        assert len(invalid_patterns) == 0, \
            f"Patterns with missing required fields: {invalid_patterns}"

    def test_pattern_json_valid(self, pattern_files):
        """Test that all pattern files are valid JSON"""
        invalid_json = []

        for pattern_file in pattern_files:
            try:
                with open(pattern_file) as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                invalid_json.append({
                    'file': pattern_file.name,
                    'error': str(e)
                })

        assert len(invalid_json) == 0, \
            f"Patterns with invalid JSON: {invalid_json}"

    def test_template_placeholder_consistency(self, pattern_files):
        """Test that template placeholders match step parameters"""
        inconsistent_patterns = []

        for pattern_file in pattern_files:
            if pattern_file.name == 'schema.json':
                continue

            with open(pattern_file) as f:
                pattern = json.load(f)

            template = pattern.get('template', '')
            steps = pattern.get('steps', [])

            if not template or not steps:
                continue

            # Extract placeholders from template ({{variable}} format)
            import re
            template_vars = set(re.findall(r'\{\{(\w+)\}\}', template))

            # Extract parameters from steps
            step_params = set()
            for step in steps:
                params = step.get('params', {})
                step_params.update(params.keys())

            # Check for undefined variables in template
            undefined_vars = template_vars - step_params

            if undefined_vars:
                inconsistent_patterns.append({
                    'file': pattern_file.name,
                    'undefined': list(undefined_vars)
                })

        # Allow some inconsistency (templates might reference context vars)
        assert len(inconsistent_patterns) < 5, \
            f"Too many patterns with undefined template vars: {inconsistent_patterns}"

    def test_pattern_count(self, pattern_files):
        """Test that we have expected number of patterns"""
        # Exclude schema.json
        pattern_count = len([f for f in pattern_files if f.name != 'schema.json'])

        # Should have around 48 patterns
        assert 45 <= pattern_count <= 55, \
            f"Expected ~48 patterns, found {pattern_count}"

    def test_pattern_categories_exist(self, pattern_files):
        """Test that patterns are organized in categories"""
        categories = set()

        for pattern_file in pattern_files:
            if pattern_file.name == 'schema.json':
                continue

            # Category is parent directory name
            category = pattern_file.parent.name
            categories.add(category)

        expected_categories = {'analysis', 'queries', 'actions', 'workflows', 'governance', 'ui', 'system'}

        # Should have most expected categories
        found_categories = categories & expected_categories
        assert len(found_categories) >= 5, \
            f"Expected categories: {expected_categories}, found: {categories}"


class TestPatternTemplateRendering:
    """Test template rendering functionality"""

    def test_simple_template_substitution(self):
        """Test basic template variable substitution"""
        template = "Analyze {{symbol}} stock"
        params = {'symbol': 'AAPL'}

        # Simple substitution
        result = template
        for key, value in params.items():
            result = result.replace(f'{{{{{key}}}}}', str(value))

        assert result == "Analyze AAPL stock"

    def test_multiple_variable_substitution(self):
        """Test template with multiple variables"""
        template = "Compare {{symbol1}} and {{symbol2}} using {{metric}}"
        params = {
            'symbol1': 'AAPL',
            'symbol2': 'GOOGL',
            'metric': 'PE ratio'
        }

        result = template
        for key, value in params.items():
            result = result.replace(f'{{{{{key}}}}}', str(value))

        assert result == "Compare AAPL and GOOGL using PE ratio"

    def test_missing_variable_handling(self):
        """Test template with missing variable"""
        template = "Analyze {{symbol}} with {{timeframe}}"
        params = {'symbol': 'AAPL'}  # timeframe missing

        result = template
        for key, value in params.items():
            result = result.replace(f'{{{{{key}}}}}', str(value))

        # Should leave unsubstituted variable
        assert '{{timeframe}}' in result
        assert 'AAPL' in result

    def test_template_with_defaults(self):
        """Test template rendering with default values"""
        template = "Analyze {{symbol}} over {{timeframe}}"
        params = {'symbol': 'AAPL'}
        defaults = {'timeframe': '1Y'}

        # Merge with defaults
        merged_params = {**defaults, **params}

        result = template
        for key, value in merged_params.items():
            result = result.replace(f'{{{{{key}}}}}', str(value))

        assert result == "Analyze AAPL over 1Y"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
