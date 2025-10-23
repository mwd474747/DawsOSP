"""
Pattern Loader

Purpose: Load and validate pattern JSON files with schema validation
Updated: 2025-10-22
Priority: P0 (Critical for Phase 2)

Features:
    - Load patterns from JSON files
    - Schema validation (inputs, outputs, steps)
    - Pattern caching (in-memory)
    - Pattern versioning support

Critical Requirements:
    - Patterns immutable after loading
    - Schema validation prevents malformed patterns
    - Caching improves performance (no re-parsing)

Pattern JSON Schema:
    {
      "id": "portfolio_overview",
      "version": "1.0",
      "name": "Portfolio Overview",
      "description": "...",
      "steps": [
        {
          "id": "get_positions",
          "capability": "ledger.positions",
          "agent": "financial_analyst",
          "inputs": {"portfolio_id": "{{inputs.portfolio_id}}"},
          "outputs": ["positions"]
        }
      ]
    }
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger("DawsOS.PatternLoader")


# ============================================================================
# Pattern Schema
# ============================================================================


@dataclass
class PatternStep:
    """
    Pattern execution step.

    Attributes:
        id: Step ID (unique within pattern)
        capability: Capability to execute (e.g., "ledger.positions")
        agent: Agent name (e.g., "financial_analyst")
        inputs: Step inputs (supports template variables like {{inputs.portfolio_id}})
        outputs: Output keys to store in state
        condition: Optional condition for conditional execution
    """

    id: str
    capability: str
    agent: str
    inputs: Dict[str, Any]
    outputs: List[str]
    condition: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PatternStep":
        """Create PatternStep from dictionary."""
        return cls(
            id=data["id"],
            capability=data["capability"],
            agent=data["agent"],
            inputs=data.get("inputs", {}),
            outputs=data.get("outputs", []),
            condition=data.get("condition"),
        )


@dataclass
class Pattern:
    """
    Pattern definition.

    Attributes:
        id: Pattern ID (e.g., "portfolio_overview")
        version: Pattern version (e.g., "1.0")
        name: Human-readable name
        description: Pattern description
        steps: List of execution steps
        inputs_schema: Optional JSON schema for inputs validation
        outputs_schema: Optional JSON schema for outputs validation
    """

    id: str
    version: str
    name: str
    description: str
    steps: List[PatternStep]
    inputs_schema: Optional[Dict[str, Any]] = None
    outputs_schema: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pattern":
        """Create Pattern from dictionary."""
        steps = [PatternStep.from_dict(step) for step in data.get("steps", [])]

        return cls(
            id=data["id"],
            version=data["version"],
            name=data["name"],
            description=data.get("description", ""),
            steps=steps,
            inputs_schema=data.get("inputs_schema"),
            outputs_schema=data.get("outputs_schema"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "version": self.version,
            "name": self.name,
            "description": self.description,
            "steps": [
                {
                    "id": step.id,
                    "capability": step.capability,
                    "agent": step.agent,
                    "inputs": step.inputs,
                    "outputs": step.outputs,
                    "condition": step.condition,
                }
                for step in self.steps
            ],
            "inputs_schema": self.inputs_schema,
            "outputs_schema": self.outputs_schema,
        }


# ============================================================================
# Pattern Loader
# ============================================================================


class PatternLoader:
    """
    Pattern loader with caching.

    Loads patterns from JSON files and caches them in memory.
    Validates pattern schema on load.
    """

    def __init__(self, patterns_dir: str = "backend/patterns"):
        """
        Initialize pattern loader.

        Args:
            patterns_dir: Directory containing pattern JSON files
        """
        self.patterns_dir = Path(patterns_dir)
        self.cache: Dict[str, Pattern] = {}

        logger.info(f"PatternLoader initialized: patterns_dir={self.patterns_dir}")

    async def load(self, pattern_id: str) -> Pattern:
        """
        Load pattern by ID.

        Args:
            pattern_id: Pattern ID (e.g., "portfolio_overview")

        Returns:
            Pattern object

        Raises:
            FileNotFoundError: Pattern file not found
            ValueError: Pattern validation failed
        """
        # Check cache first
        if pattern_id in self.cache:
            logger.debug(f"Pattern loaded from cache: {pattern_id}")
            return self.cache[pattern_id]

        # Load from file
        pattern_file = self.patterns_dir / f"{pattern_id}.json"
        if not pattern_file.exists():
            logger.error(f"Pattern file not found: {pattern_file}")
            raise FileNotFoundError(f"Pattern not found: {pattern_id}")

        logger.info(f"Loading pattern from file: {pattern_file}")

        try:
            with open(pattern_file, "r") as f:
                data = json.load(f)

            # Validate pattern
            self._validate_pattern(data)

            # Create pattern object
            pattern = Pattern.from_dict(data)

            # Cache pattern
            self.cache[pattern_id] = pattern

            logger.info(f"Pattern loaded successfully: {pattern_id} (version {pattern.version})")
            return pattern

        except json.JSONDecodeError as e:
            logger.exception(f"Failed to parse pattern JSON: {pattern_file}")
            raise ValueError(f"Invalid JSON in pattern {pattern_id}: {e}")

        except Exception as e:
            logger.exception(f"Failed to load pattern: {pattern_file}")
            raise ValueError(f"Failed to load pattern {pattern_id}: {e}")

    def _validate_pattern(self, data: Dict[str, Any]) -> None:
        """
        Validate pattern schema.

        Args:
            data: Pattern data dictionary

        Raises:
            ValueError: Validation failed
        """
        # Required fields
        required_fields = ["id", "version", "name", "steps"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Validate steps
        steps = data.get("steps", [])
        if not steps:
            raise ValueError("Pattern must have at least one step")

        for i, step in enumerate(steps):
            # Required step fields
            required_step_fields = ["id", "capability", "agent"]
            for field in required_step_fields:
                if field not in step:
                    raise ValueError(f"Step {i}: Missing required field: {field}")

            # Validate step ID uniqueness
            step_ids = [s["id"] for s in steps]
            if len(step_ids) != len(set(step_ids)):
                raise ValueError("Step IDs must be unique within pattern")

    async def load_all(self) -> List[Pattern]:
        """
        Load all patterns from patterns directory.

        Returns:
            List of Pattern objects
        """
        patterns = []

        # Find all JSON files
        pattern_files = list(self.patterns_dir.glob("*.json"))
        logger.info(f"Found {len(pattern_files)} pattern files")

        for pattern_file in pattern_files:
            try:
                pattern_id = pattern_file.stem
                pattern = await self.load(pattern_id)
                patterns.append(pattern)
            except Exception as e:
                logger.exception(f"Failed to load pattern: {pattern_file}")

        logger.info(f"Loaded {len(patterns)} patterns successfully")
        return patterns

    def clear_cache(self) -> None:
        """Clear pattern cache."""
        self.cache.clear()
        logger.info("Pattern cache cleared")

    def get_cached_patterns(self) -> List[str]:
        """Get list of cached pattern IDs."""
        return list(self.cache.keys())


# ============================================================================
# Global Instance
# ============================================================================


_pattern_loader: Optional[PatternLoader] = None


def get_pattern_loader(patterns_dir: str = "backend/patterns") -> PatternLoader:
    """
    Get singleton PatternLoader instance.

    Args:
        patterns_dir: Directory containing pattern JSON files

    Returns:
        PatternLoader instance
    """
    global _pattern_loader
    if _pattern_loader is None:
        _pattern_loader = PatternLoader(patterns_dir)
    return _pattern_loader
