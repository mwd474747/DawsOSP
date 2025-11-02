"""
Export Blocker - Enforce Data Source Export Restrictions

Purpose: Block exports for rights-restricted data sources
Updated: 2025-10-22
Priority: P0 (Critical for S1-W2 Gate)

Core Responsibilities:
    - Validate export requests against rights registry
    - Block exports for restricted sources (NewsAPI, yfinance)
    - Add attributions to allowed exports
    - Apply watermarks to exports
    - Log blocked attempts

Flow:
    Pattern Result → Export Request → Rights Check → Block/Allow + Watermark → Export

Critical Cases:
    - NewsAPI: BLOCK export (TOS violation)
    - FMP: ALLOW with attribution + watermark
    - FRED: ALLOW with attribution
    - Internal: ALLOW (no restrictions)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging
import json

from compliance.rights_registry import (
    get_rights_registry,
    DataSource,
    DataRight,
)

logger = logging.getLogger("DawsOS.Compliance.ExportBlocker")


@dataclass
class ExportRequest:
    """
    Export request with metadata.

    Attributes:
        data: Data to export
        sources: Data sources used in result
        format: Export format (json, csv, excel, pdf)
        user_id: User requesting export
        pattern_id: Pattern that generated the data
        request_id: Request identifier for tracing
    """
    data: Dict[str, Any]
    sources: List[DataSource]
    format: str
    user_id: str
    pattern_id: Optional[str] = None
    request_id: Optional[str] = None


@dataclass
class ExportResult:
    """
    Export result with status.

    Attributes:
        allowed: Whether export was allowed
        data: Exported data (with watermarks/attributions if allowed)
        reason: Explanation if blocked
        attributions: List of attribution texts
        watermarks: List of watermark texts
        blocked_sources: Sources that blocked export
    """
    allowed: bool
    data: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None
    attributions: List[str] = None
    watermarks: List[str] = None
    blocked_sources: List[str] = None

    def __post_init__(self):
        if self.attributions is None:
            self.attributions = []
        if self.watermarks is None:
            self.watermarks = []
        if self.blocked_sources is None:
            self.blocked_sources = []


class ExportBlocker:
    """
    Export blocker for rights enforcement.

    Validates export requests, blocks restricted sources, adds attributions.
    """

    def __init__(self):
        """Initialize export blocker."""
        self._registry = get_rights_registry()
        self._blocked_attempts = 0
        self._allowed_exports = 0
        logger.info("Export blocker initialized")

    def validate_export(self, request: ExportRequest) -> ExportResult:
        """
        Validate export request against rights registry.

        Args:
            request: Export request with data and sources

        Returns:
            ExportResult with allowed status and processed data
        """
        logger.info(
            f"Validating export: user={request.user_id}, sources={[s.value for s in request.sources]}, "
            f"format={request.format}, pattern={request.pattern_id}"
        )

        # Check if all sources allow export
        allowed, reason = self._registry.validate_export(request.sources)

        if not allowed:
            # Export blocked
            blocked_sources = [
                s.value for s in request.sources
                if not self._registry.can_export(s)
            ]

            logger.warning(
                f"Export BLOCKED: user={request.user_id}, blocked_sources={blocked_sources}, "
                f"reason={reason}"
            )

            # Record violation for each blocked source
            for source in request.sources:
                if not self._registry.can_export(source):
                    self._registry.record_violation(
                        source=source,
                        right=DataRight.EXPORT,
                        user_id=request.user_id,
                        context={
                            "pattern_id": request.pattern_id,
                            "request_id": request.request_id,
                            "format": request.format,
                        },
                    )

            self._blocked_attempts += 1

            return ExportResult(
                allowed=False,
                reason=reason,
                blocked_sources=blocked_sources,
            )

        # Export allowed - add attributions and watermarks
        attributions = self._registry.get_all_attributions(request.sources)
        watermarks = [
            wm for wm in (self._registry.get_watermark(s) for s in request.sources)
            if wm is not None
        ]

        # Process data (add metadata)
        processed_data = self._add_export_metadata(
            data=request.data,
            attributions=attributions,
            watermarks=watermarks,
            request=request,
        )

        logger.info(
            f"Export ALLOWED: user={request.user_id}, attributions={len(attributions)}, "
            f"watermarks={len(watermarks)}"
        )

        self._allowed_exports += 1

        return ExportResult(
            allowed=True,
            data=processed_data,
            attributions=attributions,
            watermarks=watermarks,
        )

    def _add_export_metadata(
        self,
        data: Dict[str, Any],
        attributions: List[str],
        watermarks: List[str],
        request: ExportRequest,
    ) -> Dict[str, Any]:
        """
        Add export metadata to data.

        Args:
            data: Original data
            attributions: Attribution texts
            watermarks: Watermark texts
            request: Original export request

        Returns:
            Data with added metadata
        """
        # Create copy to avoid mutating original
        processed = data.copy()

        # Add export metadata
        export_metadata = {
            "exported_at": datetime.now().isoformat(),
            "exported_by": request.user_id,
            "format": request.format,
            "sources": [s.value for s in request.sources],
        }

        # Add attributions
        if attributions:
            export_metadata["attributions"] = attributions

        # Add watermarks
        if watermarks:
            export_metadata["watermarks"] = watermarks

        # Add request context
        if request.pattern_id:
            export_metadata["pattern_id"] = request.pattern_id
        if request.request_id:
            export_metadata["request_id"] = request.request_id

        # Attach metadata to result
        processed["__export_metadata__"] = export_metadata

        return processed

    def format_attributions(self, attributions: List[str], format: str = "text") -> str:
        """
        Format attributions for display.

        Args:
            attributions: List of attribution texts
            format: Output format (text, html, markdown)

        Returns:
            Formatted attribution text
        """
        if not attributions:
            return ""

        if format == "html":
            items = "".join(f"<li>{attr}</li>" for attr in attributions)
            return f"<div class='attributions'><ul>{items}</ul></div>"

        elif format == "markdown":
            items = "\n".join(f"- {attr}" for attr in attributions)
            return f"### Data Attributions\n\n{items}"

        else:  # text
            return "\n".join(f"• {attr}" for attr in attributions)

    def format_watermark(self, watermarks: List[str], format: str = "text") -> str:
        """
        Format watermark for display.

        Args:
            watermarks: List of watermark texts
            format: Output format (text, html, markdown)

        Returns:
            Formatted watermark text
        """
        if not watermarks:
            return ""

        watermark = " | ".join(watermarks)

        if format == "html":
            return f"<div class='watermark'>{watermark}</div>"

        elif format == "markdown":
            return f"*{watermark}*"

        else:  # text
            return watermark

    def check_source(self, source: DataSource) -> Dict[str, Any]:
        """
        Check rights for a specific source.

        Args:
            source: Data source to check

        Returns:
            Dictionary with rights information
        """
        profile = self._registry.get_profile(source)

        if not profile:
            return {
                "source": source.value,
                "known": False,
                "error": "Unknown data source",
            }

        return {
            "source": source.value,
            "known": True,
            "can_view": profile.has_right(DataRight.VIEW),
            "can_export": profile.can_export(),
            "can_redistribute": profile.can_redistribute(),
            "attribution_required": profile.attribution_required,
            "attribution_text": profile.get_attribution(),
            "watermark_required": profile.watermark_required,
            "watermark_text": profile.get_watermark(),
            "restrictions": profile.restrictions,
            "terms_url": profile.terms_url,
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get export blocker statistics.

        Returns:
            Dictionary with stats
        """
        violations = self._registry.get_violations()
        registry_summary = self._registry.get_summary()

        return {
            "blocked_attempts": self._blocked_attempts,
            "allowed_exports": self._allowed_exports,
            "total_requests": self._blocked_attempts + self._allowed_exports,
            "block_rate": (
                self._blocked_attempts / (self._blocked_attempts + self._allowed_exports)
                if (self._blocked_attempts + self._allowed_exports) > 0
                else 0.0
            ),
            "total_violations": len(violations),
            "registry_summary": registry_summary,
        }

    def get_violations(
        self,
        source: Optional[DataSource] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get recorded violations.

        Args:
            source: Filter by data source (optional)
            user_id: Filter by user (optional)
            limit: Maximum number of violations to return

        Returns:
            List of violation records
        """
        return self._registry.get_violations(source=source, user_id=user_id, limit=limit)


# ============================================================================
# Singleton Instance
# ============================================================================

_export_blocker: Optional[ExportBlocker] = None


def get_export_blocker() -> ExportBlocker:
    """Get or create singleton export blocker."""
    global _export_blocker
    if _export_blocker is None:
        _export_blocker = ExportBlocker()
    return _export_blocker


# ============================================================================
# Helper Functions
# ============================================================================


def validate_export(
    data: Dict[str, Any],
    sources: List[DataSource],
    format: str,
    user_id: str,
    pattern_id: Optional[str] = None,
    request_id: Optional[str] = None,
) -> ExportResult:
    """
    Convenience function to validate export.

    Args:
        data: Data to export
        sources: Data sources used
        format: Export format
        user_id: User requesting export
        pattern_id: Pattern ID (optional)
        request_id: Request ID (optional)

    Returns:
        ExportResult with validation status
    """
    blocker = get_export_blocker()

    request = ExportRequest(
        data=data,
        sources=sources,
        format=format,
        user_id=user_id,
        pattern_id=pattern_id,
        request_id=request_id,
    )

    return blocker.validate_export(request)


def check_source_rights(source: DataSource) -> Dict[str, Any]:
    """
    Convenience function to check source rights.

    Args:
        source: Data source to check

    Returns:
        Dictionary with rights information
    """
    blocker = get_export_blocker()
    return blocker.check_source(source)
