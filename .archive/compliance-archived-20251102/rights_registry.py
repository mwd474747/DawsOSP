"""
Rights Registry - Data Source Rights & Restrictions

Purpose: Centralized registry of data source usage rights and export restrictions
Updated: 2025-10-22
Priority: P0 (Critical for S1-W2 Gate)

Core Responsibilities:
    - Define rights for each data source (view/export/redistribute)
    - Track attribution requirements
    - Enforce export restrictions
    - Provide rights lookup for compliance checks

Compliance:
    - NewsAPI: View only (no export/redistribution)
    - FMP: Full rights (free tier has attribution requirement)
    - OpenBB: Full rights (open source data)
    - FRED: Full rights (public domain)

Architecture:
    Agent Runtime → Rights Registry → Check rights → Block/Allow → Log violations
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger("DawsOS.Compliance.Rights")


class DataRight(str, Enum):
    """Types of data rights."""
    VIEW = "view"  # Can display in UI
    EXPORT = "export"  # Can export to file
    REDISTRIBUTE = "redistribute"  # Can share with third parties
    COMMERCIAL = "commercial"  # Can use for commercial purposes


class DataSource(str, Enum):
    """Supported data sources."""
    NEWSAPI = "newsapi"
    FMP = "fmp"  # Financial Modeling Prep
    OPENBB = "openbb"
    FRED = "fred"
    POLYGON = "polygon"
    YFINANCE = "yfinance"
    INTERNAL = "internal"  # Our own calculations/data


@dataclass(frozen=True)
class RightsProfile:
    """
    Rights profile for a data source.

    Attributes:
        source: Data source identifier
        rights: List of granted rights
        attribution_required: Whether attribution is required
        attribution_text: Attribution text to display
        watermark_required: Whether watermark is required for exports
        watermark_text: Watermark text
        restrictions: Human-readable restrictions
        terms_url: URL to terms of service
    """
    source: DataSource
    rights: List[DataRight]
    attribution_required: bool
    attribution_text: Optional[str] = None
    watermark_required: bool = False
    watermark_text: Optional[str] = None
    restrictions: Optional[str] = None
    terms_url: Optional[str] = None

    def has_right(self, right: DataRight) -> bool:
        """Check if this profile grants a specific right."""
        return right in self.rights

    def can_export(self) -> bool:
        """Check if export is allowed."""
        return self.has_right(DataRight.EXPORT)

    def can_redistribute(self) -> bool:
        """Check if redistribution is allowed."""
        return self.has_right(DataRight.REDISTRIBUTE)

    def get_attribution(self) -> Optional[str]:
        """Get attribution text if required."""
        if self.attribution_required:
            return self.attribution_text
        return None

    def get_watermark(self) -> Optional[str]:
        """Get watermark text if required."""
        if self.watermark_required:
            return self.watermark_text
        return None


# ============================================================================
# Rights Profiles Registry
# ============================================================================

RIGHTS_PROFILES: Dict[DataSource, RightsProfile] = {
    # NewsAPI: View only (no export/redistribution per TOS)
    DataSource.NEWSAPI: RightsProfile(
        source=DataSource.NEWSAPI,
        rights=[DataRight.VIEW],  # View only
        attribution_required=True,
        attribution_text="News data provided by NewsAPI.org",
        watermark_required=False,
        restrictions="Export and redistribution prohibited per NewsAPI Terms of Service",
        terms_url="https://newsapi.org/terms",
    ),

    # FMP: Full rights with attribution (free tier)
    DataSource.FMP: RightsProfile(
        source=DataSource.FMP,
        rights=[DataRight.VIEW, DataRight.EXPORT, DataRight.REDISTRIBUTE, DataRight.COMMERCIAL],
        attribution_required=True,
        attribution_text="Financial data provided by Financial Modeling Prep (financialmodelingprep.com)",
        watermark_required=True,
        watermark_text="Data: Financial Modeling Prep",
        restrictions=None,
        terms_url="https://financialmodelingprep.com/developer/docs/terms-of-service",
    ),

    # OpenBB: Full rights (open source)
    DataSource.OPENBB: RightsProfile(
        source=DataSource.OPENBB,
        rights=[DataRight.VIEW, DataRight.EXPORT, DataRight.REDISTRIBUTE, DataRight.COMMERCIAL],
        attribution_required=True,
        attribution_text="Market data provided by OpenBB Platform",
        watermark_required=False,
        restrictions=None,
        terms_url="https://openbb.co/legal/terms-of-service",
    ),

    # FRED: Full rights (public domain)
    DataSource.FRED: RightsProfile(
        source=DataSource.FRED,
        rights=[DataRight.VIEW, DataRight.EXPORT, DataRight.REDISTRIBUTE, DataRight.COMMERCIAL],
        attribution_required=True,
        attribution_text="Economic data provided by Federal Reserve Economic Data (FRED)",
        watermark_required=False,
        restrictions=None,
        terms_url="https://fred.stlouisfed.org/docs/api/terms_of_use.html",
    ),

    # Polygon: Full rights with attribution
    DataSource.POLYGON: RightsProfile(
        source=DataSource.POLYGON,
        rights=[DataRight.VIEW, DataRight.EXPORT, DataRight.REDISTRIBUTE, DataRight.COMMERCIAL],
        attribution_required=True,
        attribution_text="Market data provided by Polygon.io",
        watermark_required=True,
        watermark_text="Data: Polygon.io",
        restrictions=None,
        terms_url="https://polygon.io/terms",
    ),

    # yfinance: View only (gray area - Yahoo TOS prohibits automated access)
    DataSource.YFINANCE: RightsProfile(
        source=DataSource.YFINANCE,
        rights=[DataRight.VIEW],
        attribution_required=True,
        attribution_text="Market data from Yahoo Finance",
        watermark_required=False,
        restrictions="Export restricted - Yahoo Finance Terms of Service",
        terms_url="https://policies.yahoo.com/us/en/yahoo/terms/product-atos/apiforydn/index.htm",
    ),

    # Internal: Full rights (our own data)
    DataSource.INTERNAL: RightsProfile(
        source=DataSource.INTERNAL,
        rights=[DataRight.VIEW, DataRight.EXPORT, DataRight.REDISTRIBUTE, DataRight.COMMERCIAL],
        attribution_required=False,
        restrictions=None,
        terms_url=None,
    ),
}


# ============================================================================
# Rights Registry
# ============================================================================

class RightsRegistry:
    """
    Centralized registry for data source rights.

    Provides rights lookup, validation, and violation tracking.
    """

    def __init__(self):
        """Initialize rights registry."""
        self._profiles = RIGHTS_PROFILES
        self._violations: List[Dict[str, Any]] = []
        logger.info(f"Rights registry initialized with {len(self._profiles)} data sources")

    def get_profile(self, source: DataSource) -> Optional[RightsProfile]:
        """
        Get rights profile for a data source.

        Args:
            source: Data source identifier

        Returns:
            RightsProfile if found, None otherwise
        """
        return self._profiles.get(source)

    def has_right(self, source: DataSource, right: DataRight) -> bool:
        """
        Check if a data source grants a specific right.

        Args:
            source: Data source identifier
            right: Right to check

        Returns:
            True if right is granted, False otherwise
        """
        profile = self.get_profile(source)
        if not profile:
            logger.warning(f"Unknown data source: {source}")
            return False

        return profile.has_right(right)

    def can_export(self, source: DataSource) -> bool:
        """
        Check if export is allowed for a data source.

        Args:
            source: Data source identifier

        Returns:
            True if export allowed, False otherwise
        """
        return self.has_right(source, DataRight.EXPORT)

    def can_redistribute(self, source: DataSource) -> bool:
        """
        Check if redistribution is allowed for a data source.

        Args:
            source: Data source identifier

        Returns:
            True if redistribution allowed, False otherwise
        """
        return self.has_right(source, DataRight.REDISTRIBUTE)

    def get_attribution(self, source: DataSource) -> Optional[str]:
        """
        Get attribution text for a data source.

        Args:
            source: Data source identifier

        Returns:
            Attribution text if required, None otherwise
        """
        profile = self.get_profile(source)
        if not profile:
            return None

        return profile.get_attribution()

    def get_watermark(self, source: DataSource) -> Optional[str]:
        """
        Get watermark text for a data source.

        Args:
            source: Data source identifier

        Returns:
            Watermark text if required, None otherwise
        """
        profile = self.get_profile(source)
        if not profile:
            return None

        return profile.get_watermark()

    def get_all_attributions(self, sources: List[DataSource]) -> List[str]:
        """
        Get all required attributions for a list of sources.

        Args:
            sources: List of data sources

        Returns:
            List of attribution texts (deduplicated)
        """
        attributions = []
        seen = set()

        for source in sources:
            attribution = self.get_attribution(source)
            if attribution and attribution not in seen:
                attributions.append(attribution)
                seen.add(attribution)

        return attributions

    def validate_export(self, sources: List[DataSource]) -> tuple[bool, Optional[str]]:
        """
        Validate if export is allowed for a list of sources.

        Args:
            sources: List of data sources

        Returns:
            (allowed, reason) tuple
            - allowed: True if all sources allow export
            - reason: Explanation if blocked, None if allowed
        """
        blocked_sources = []

        for source in sources:
            if not self.can_export(source):
                blocked_sources.append(source.value)

        if blocked_sources:
            reason = f"Export blocked: {', '.join(blocked_sources)} do not permit export"
            return False, reason

        return True, None

    def record_violation(
        self,
        source: DataSource,
        right: DataRight,
        user_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record a rights violation.

        Args:
            source: Data source where violation occurred
            right: Right that was violated
            user_id: User who attempted the action
            context: Additional context (pattern_id, request_id, etc.)
        """
        violation = {
            "timestamp": datetime.now().isoformat(),
            "source": source.value,
            "right": right.value,
            "user_id": user_id,
            "context": context or {},
        }

        self._violations.append(violation)

        logger.warning(
            f"Rights violation: user={user_id}, source={source.value}, "
            f"right={right.value}, context={context}"
        )

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
        violations = self._violations

        # Filter by source
        if source:
            violations = [v for v in violations if v["source"] == source.value]

        # Filter by user
        if user_id:
            violations = [v for v in violations if v["user_id"] == user_id]

        # Apply limit (most recent first)
        return list(reversed(violations[-limit:]))

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of rights registry.

        Returns:
            Dictionary with registry statistics
        """
        export_allowed = sum(1 for p in self._profiles.values() if p.can_export())
        attribution_required = sum(1 for p in self._profiles.values() if p.attribution_required)
        watermark_required = sum(1 for p in self._profiles.values() if p.watermark_required)

        return {
            "total_sources": len(self._profiles),
            "export_allowed": export_allowed,
            "export_restricted": len(self._profiles) - export_allowed,
            "attribution_required": attribution_required,
            "watermark_required": watermark_required,
            "total_violations": len(self._violations),
        }


# ============================================================================
# Singleton Instance
# ============================================================================

_rights_registry: Optional[RightsRegistry] = None


def get_rights_registry() -> RightsRegistry:
    """Get or create singleton rights registry."""
    global _rights_registry
    if _rights_registry is None:
        _rights_registry = RightsRegistry()
    return _rights_registry
