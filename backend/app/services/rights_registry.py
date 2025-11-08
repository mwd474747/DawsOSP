"""
DawsOS Rights Registry

Purpose: Load and enforce data provider export rights
Updated: 2025-10-21
Priority: P0 (Critical for legal compliance)

Features:
    - Load rights from .ops/RIGHTS_REGISTRY.yaml
    - Check export permissions per provider
    - Staging vs production enforcement
    - Collect required attributions
    - Watermark requirements
    - Audit logging

Usage:
    registry = RightsRegistry.load_from_yaml(".ops/RIGHTS_REGISTRY.yaml")
    result = registry.check_export(["FMP", "Polygon"], "pdf", "staging")
    if result["allowed"]:
        # Generate export with attributions
        print(result["attributions"])
"""

import logging
import os
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class ExportRights:
    """Export rights for a provider."""

    allows_export_pdf: bool
    allows_export_csv: bool
    allows_redistribution: bool
    requires_attribution: bool
    watermark_required: bool


@dataclass
class Attribution:
    """Attribution requirements for a provider."""

    required_text: str
    placement: str = "footer"
    font_size: str = "8pt"


@dataclass
class Watermark:
    """Watermark requirements for a provider."""

    text: str
    opacity: float = 0.3
    position: str = "diagonal"


@dataclass
class ProviderRights:
    """Complete rights package for a provider."""

    name: str
    tier: str
    data_types: List[str]
    export_rights: ExportRights
    attribution: Attribution
    requires_license: bool
    watermark: Optional[Watermark] = None


@dataclass
class ExportCheckResult:
    """Result of export permission check."""

    allowed: bool
    providers: List[str]
    export_type: str
    environment: str
    attributions: List[str]
    watermark: Optional[Watermark]
    blocked_providers: List[str]
    reason: Optional[str]
    timestamp: datetime


# ============================================================================
# Rights Registry
# ============================================================================


class RightsRegistry:
    """
    Rights registry: load and enforce provider export rights.

    Enforcement timeline:
        - S1-W2 (staging): Block exports with restricted providers
        - S4-W8 (production): Full enforcement with alerts
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize rights registry.

        Args:
            config: Parsed YAML config
        """
        self.config = config
        self.providers: Dict[str, ProviderRights] = {}
        self._load_providers()
        logger.info(f"RightsRegistry initialized with {len(self.providers)} providers")

    @classmethod
    def load_from_yaml(cls, yaml_path: str) -> "RightsRegistry":
        """
        Load rights registry from YAML file.

        Args:
            yaml_path: Path to RIGHTS_REGISTRY.yaml

        Returns:
            RightsRegistry instance

        Raises:
            FileNotFoundError: If YAML file not found
            yaml.YAMLError: If YAML parsing fails
        """
        path = Path(yaml_path)
        if not path.exists():
            raise FileNotFoundError(f"Rights registry not found: {yaml_path}")

        with open(path) as f:
            config = yaml.safe_load(f)

        logger.info(f"Loaded rights registry from {yaml_path} (version {config.get('version')})")
        return cls(config)

    def _load_providers(self):
        """Load provider rights from config."""
        providers_config = self.config.get("providers", {})

        for provider_id, provider_data in providers_config.items():
            # Parse export rights
            export_cfg = provider_data.get("export_rights", {})
            export_rights = ExportRights(
                allows_export_pdf=export_cfg.get("allows_export_pdf", False),
                allows_export_csv=export_cfg.get("allows_export_csv", False),
                allows_redistribution=export_cfg.get("allows_redistribution", False),
                requires_attribution=export_cfg.get("requires_attribution", True),
                watermark_required=export_cfg.get("watermark_required", False),
            )

            # Parse attribution
            attr_cfg = provider_data.get("attribution", {})
            attribution = Attribution(
                required_text=attr_cfg.get("required_text", f"Data © {provider_id}"),
                placement=attr_cfg.get("placement", "footer"),
                font_size=attr_cfg.get("font_size", "8pt"),
            )

            # Parse watermark (if required)
            watermark = None
            if export_rights.watermark_required and "watermark" in provider_data:
                wm_cfg = provider_data["watermark"]
                watermark = Watermark(
                    text=wm_cfg.get("text", f"Data from {provider_id}"),
                    opacity=wm_cfg.get("opacity", 0.3),
                    position=wm_cfg.get("position", "diagonal"),
                )

            # Parse licensing
            license_cfg = provider_data.get("licensing", {})
            requires_license = license_cfg.get("requires_license", True)

            # Create ProviderRights
            self.providers[provider_id] = ProviderRights(
                name=provider_data.get("name", provider_id),
                tier=provider_data.get("tier", "unknown"),
                data_types=provider_data.get("data_types", []),
                export_rights=export_rights,
                attribution=attribution,
                requires_license=requires_license,
                watermark=watermark,
            )

    def check_export(
        self,
        providers: List[str],
        export_type: str,
        environment: str = "staging",
    ) -> ExportCheckResult:
        """
        Check if export is allowed for given providers.

        Args:
            providers: List of provider IDs (e.g., ["FMP", "Polygon"])
            export_type: Export type ("pdf", "csv", "api")
            environment: "staging" or "production"

        Returns:
            ExportCheckResult with allowed status, attributions, and reason
        """
        # Get enforcement config
        enforcement = self.config.get("enforcement", {}).get(environment, {})
        enforcement_enabled = enforcement.get("enabled", False)

        # Collect blocked providers
        blocked_providers = []
        attributions = []
        watermarks = []

        for provider_id in providers:
            provider = self.providers.get(provider_id)

            if not provider:
                logger.warning(f"Unknown provider: {provider_id}, applying default restrictions")
                blocked_providers.append(provider_id)
                continue

            # Check export permission
            if export_type == "pdf" and not provider.export_rights.allows_export_pdf:
                blocked_providers.append(provider_id)

            if export_type == "csv" and not provider.export_rights.allows_export_csv:
                blocked_providers.append(provider_id)

            # Collect attribution
            if provider.export_rights.requires_attribution:
                attributions.append(provider.attribution.required_text)

            # Collect watermark
            if provider.export_rights.watermark_required and provider.watermark:
                watermarks.append(provider.watermark)

        # Determine result
        allowed = len(blocked_providers) == 0
        reason = None

        if not allowed and enforcement_enabled:
            blocked_names = [
                self.providers.get(p, ProviderRights(name=p, tier="unknown", data_types=[], export_rights=ExportRights(False, False, False, True, False), attribution=Attribution(""))).name
                for p in blocked_providers
            ]
            reason = (
                f"Export blocked: {', '.join(blocked_names)} "
                f"{'does not' if len(blocked_providers) == 1 else 'do not'} "
                f"allow {export_type.upper()} export. "
                f"Remove restricted analysis or upgrade license."
            )

        # Use first watermark if any (in production, might overlay multiple)
        watermark = watermarks[0] if watermarks else None

        result = ExportCheckResult(
            allowed=allowed,
            providers=providers,
            export_type=export_type,
            environment=environment,
            attributions=attributions,
            watermark=watermark,
            blocked_providers=blocked_providers,
            reason=reason,
            timestamp=datetime.utcnow(),
        )

        # Log result
        if not allowed:
            logger.warning(
                f"Export BLOCKED: {export_type} export with providers {providers} "
                f"in {environment} - {reason}"
            )
        else:
            logger.info(
                f"Export ALLOWED: {export_type} export with providers {providers} "
                f"in {environment}"
            )

        return result

    def ensure_allowed(
        self,
        providers: List[str],
        export_type: str,
        environment: str = "staging",
    ) -> ExportCheckResult:
        """
        Check export permission and raise exception if blocked.

        Args:
            providers: List of provider IDs
            export_type: Export type ("pdf", "csv", "api")
            environment: "staging" or "production"

        Returns:
            ExportCheckResult if allowed

        Raises:
            RightsViolationError: If export not allowed in current environment
        """
        result = self.check_export(providers, export_type, environment)

        if not result.allowed:
            from app.core.types import RightsViolationError
            raise RightsViolationError(
                action=f"{export_type}_export",
                rights_profile=environment,
            )

        return result

    def get_provider_info(self, provider_id: str) -> Optional[ProviderRights]:
        """
        Get rights info for a provider.

        Args:
            provider_id: Provider identifier

        Returns:
            ProviderRights or None if not found
        """
        return self.providers.get(provider_id)

    def list_providers(self) -> List[Dict[str, Any]]:
        """
        List all registered providers with rights summary.

        Returns:
            List of provider info dicts
        """
        return [
            {
                "id": provider_id,
                "name": rights.name,
                "tier": rights.tier,
                "allows_pdf_export": rights.export_rights.allows_export_pdf,
                "allows_csv_export": rights.export_rights.allows_export_csv,
                "requires_attribution": rights.export_rights.requires_attribution,
                "watermark_required": rights.export_rights.watermark_required,
            }
            for provider_id, rights in self.providers.items()
        ]


# ============================================================================
# Module-Level Singleton
# ============================================================================

_registry: Optional[RightsRegistry] = None


def get_registry() -> RightsRegistry:
    """
    Get rights registry singleton.

    Lazily loads from .ops/RIGHTS_REGISTRY.yaml.

    Returns:
        RightsRegistry instance
    """
    global _registry
    if _registry is None:
        yaml_path = os.getenv("RIGHTS_REGISTRY_PATH", ".ops/RIGHTS_REGISTRY.yaml")
        _registry = RightsRegistry.load_from_yaml(yaml_path)
    return _registry
