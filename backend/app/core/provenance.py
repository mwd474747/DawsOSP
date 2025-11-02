"""
DawsOS Data Provenance System

Purpose: Track and display where data comes from (real, cached, computed, or stub)
Created: 2025-11-01
Priority: P0 (Critical for data transparency)

Features:
    - DataProvenance enum for source types
    - ProvenanceWrapper to wrap data with metadata
    - Automatic tracking of data sources
    - Support for warnings and confidence levels

Architecture:
    Agent → ProvenanceWrapper → Pattern Orchestrator → API Response

Usage:
    from app.core.provenance import ProvenanceWrapper, DataProvenance
    
    # Wrap data with provenance
    result = ProvenanceWrapper(
        data={"positions": [...]},
        provenance=DataProvenance.REAL,
        source="database:portfolio_metrics",
        confidence=0.95
    )
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("DawsOS.Provenance")


class DataProvenance(Enum):
    """Data source types for provenance tracking."""
    
    REAL = "real"          # From database/API (live data)
    CACHED = "cached"      # From Redis/memory cache
    COMPUTED = "computed"  # Calculated from real data
    STUB = "stub"          # Hardcoded/fake/demo data
    MIXED = "mixed"        # Mix of real and stub data
    UNKNOWN = "unknown"    # Source cannot be determined


class ProvenanceWrapper:
    """
    Wraps data with provenance metadata.
    
    This wrapper provides transparency about where data comes from,
    when it was retrieved, and any warnings about data quality.
    """
    
    def __init__(
        self,
        data: Any,
        provenance: DataProvenance,
        source: Optional[str] = None,
        warnings: Optional[List[str]] = None,
        confidence: Optional[float] = None,
        ttl: Optional[int] = None,
        asof: Optional[datetime] = None,
    ):
        """
        Initialize provenance wrapper.
        
        Args:
            data: The actual data being wrapped
            provenance: Type of data source (REAL, CACHED, COMPUTED, STUB)
            source: Specific source identifier (e.g., "database:portfolio_metrics")
            warnings: List of warnings about data quality or completeness
            confidence: Confidence score (0-1) for data quality
            ttl: Time-to-live in seconds for caching
            asof: As-of date for the data
        """
        self.data = data
        self.provenance = provenance
        self.source = source or "unknown"
        self.timestamp = datetime.utcnow()
        self.warnings = warnings or []
        self.confidence = confidence
        self.ttl = ttl
        self.asof = asof
        
        # Add automatic warnings for stub data
        if provenance == DataProvenance.STUB and not any("demo" in w.lower() or "stub" in w.lower() for w in self.warnings):
            self.warnings.append("This is demo/stub data for development purposes")
        
        # Log provenance for debugging
        logger.debug(
            f"ProvenanceWrapper created: provenance={provenance.value}, "
            f"source={source}, confidence={confidence}, warnings={len(self.warnings)}"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert wrapper to dictionary for JSON serialization.
        
        Returns:
            Dict with data and metadata
        """
        metadata = {
            "provenance": self.provenance.value,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "warnings": self.warnings,
        }
        
        # Add optional fields if present
        if self.confidence is not None:
            metadata["confidence"] = self.confidence
        if self.ttl is not None:
            metadata["ttl"] = self.ttl
        if self.asof is not None:
            metadata["asof"] = self.asof.isoformat() if isinstance(self.asof, datetime) else str(self.asof)
        
        return {
            "data": self.data,
            "_provenance": metadata
        }
    
    def extract_data(self) -> Any:
        """
        Extract just the data without provenance metadata.
        
        Returns:
            The unwrapped data
        """
        return self.data
    
    def is_real_data(self) -> bool:
        """Check if this is real (not stub) data."""
        return self.provenance in [DataProvenance.REAL, DataProvenance.CACHED, DataProvenance.COMPUTED]
    
    def is_stub_data(self) -> bool:
        """Check if this is stub/demo data."""
        return self.provenance == DataProvenance.STUB
    
    def add_warning(self, warning: str):
        """Add a warning to the provenance."""
        if warning not in self.warnings:
            self.warnings.append(warning)
            logger.warning(f"Provenance warning added: {warning}")
    
    @classmethod
    def from_agent_result(
        cls,
        result: Any,
        default_provenance: DataProvenance = DataProvenance.UNKNOWN,
        source: Optional[str] = None,
    ) -> "ProvenanceWrapper":
        """
        Create a ProvenanceWrapper from an agent result.
        
        If the result already has metadata, extract it.
        Otherwise, wrap with default provenance.
        
        Args:
            result: Agent execution result
            default_provenance: Default provenance if not specified
            source: Source identifier
        
        Returns:
            ProvenanceWrapper instance
        """
        # Check if result already has metadata attached
        if isinstance(result, dict) and "_metadata" in result:
            metadata = result["_metadata"]
            
            # Determine provenance from metadata
            if metadata.get("source", "").startswith("database"):
                provenance = DataProvenance.REAL
            elif metadata.get("source", "").startswith("cache"):
                provenance = DataProvenance.CACHED
            elif metadata.get("source", "").startswith("computed"):
                provenance = DataProvenance.COMPUTED
            elif "stub" in metadata.get("source", "").lower():
                provenance = DataProvenance.STUB
            else:
                provenance = default_provenance
            
            # Create wrapper with extracted metadata
            return cls(
                data=result,
                provenance=provenance,
                source=metadata.get("source", source),
                confidence=metadata.get("confidence"),
                ttl=metadata.get("ttl"),
                asof=metadata.get("asof"),
            )
        
        # No metadata, use defaults
        return cls(
            data=result,
            provenance=default_provenance,
            source=source,
        )
    
    @classmethod
    def merge_provenance(cls, wrappers: List["ProvenanceWrapper"]) -> DataProvenance:
        """
        Determine merged provenance from multiple wrappers.
        
        Rules:
        - If any is STUB, result is MIXED (unless all are STUB)
        - If all are same type, use that type
        - Otherwise, MIXED
        
        Args:
            wrappers: List of ProvenanceWrapper instances
        
        Returns:
            Merged DataProvenance value
        """
        if not wrappers:
            return DataProvenance.UNKNOWN
        
        provenances = [w.provenance for w in wrappers]
        unique_provenances = set(provenances)
        
        # All same provenance
        if len(unique_provenances) == 1:
            return provenances[0]
        
        # Mix of stub and real data
        if DataProvenance.STUB in unique_provenances:
            return DataProvenance.MIXED
        
        # Mix of real data types (real, cached, computed)
        real_types = {DataProvenance.REAL, DataProvenance.CACHED, DataProvenance.COMPUTED}
        if unique_provenances.issubset(real_types):
            # Prefer REAL > CACHED > COMPUTED
            if DataProvenance.REAL in unique_provenances:
                return DataProvenance.REAL
            elif DataProvenance.CACHED in unique_provenances:
                return DataProvenance.CACHED
            else:
                return DataProvenance.COMPUTED
        
        return DataProvenance.MIXED