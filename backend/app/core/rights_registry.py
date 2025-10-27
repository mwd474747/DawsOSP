"""
Rights Registry

Purpose: Load and enforce data provider rights
Updated: 2025-10-22
Priority: P0 (Critical for legal compliance)

Features:
    - Load provider rights from YAML
    - Check if operation is allowed for providers
    - Generate attribution text for exports
    - Raise RightsViolationError for blocked operations

Usage:
    from backend.app.core.rights_registry import ensure_allowed, get_attribution_text

    # Check if PDF export allowed
    allowed, blocked = ensure_allowed(["FMP", "Polygon"], "export_pdf")
    if not allowed:
        raise RightsViolationError(f"Export blocked: {blocked}")

    # Get attribution text
    attribution = get_attribution_text(["FMP", "FRED"])
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger("DawsOS.RightsRegistry")


# ============================================================================
# Data Models
# ============================================================================


class ProviderRights:
    """Data provider rights and attribution."""

    def __init__(self, provider_id: str, config: Dict):
        self.provider_id = provider_id
        self.name = config.get("name", provider_id)
        self.website = config.get("website")

        # Rights
        self.allows_display = config.get("allows_display", False)
        self.allows_export_pdf = config.get("allows_export_pdf", False)
        self.allows_export_csv = config.get("allows_export_csv", False)
        self.allows_redistribution = config.get("allows_redistribution", False)

        # Attribution
        self.attribution_text = config.get("attribution_text", "")
        self.attribution_required = config.get("attribution_required", True)

    def allows_operation(self, operation: str) -> bool:
        """
        Check if operation is allowed for this provider.

        Args:
            operation: One of: display, export_pdf, export_csv, redistribution

        Returns:
            True if allowed, False otherwise
        """
        operation_map = {
            "display": self.allows_display,
            "export_pdf": self.allows_export_pdf,
            "export_csv": self.allows_export_csv,
            "redistribution": self.allows_redistribution,
        }

        return operation_map.get(operation, False)

    def to_dict(self) -> Dict:
        return {
            "provider_id": self.provider_id,
            "name": self.name,
            "website": self.website,
            "allows_display": self.allows_display,
            "allows_export_pdf": self.allows_export_pdf,
            "allows_export_csv": self.allows_export_csv,
            "allows_redistribution": self.allows_redistribution,
            "attribution_text": self.attribution_text,
            "attribution_required": self.attribution_required,
        }


class RightsViolationError(Exception):
    """Raised when an operation is blocked by provider rights."""

    def __init__(self, message: str, blocked_providers: List[str]):
        super().__init__(message)
        self.blocked_providers = blocked_providers


# ============================================================================
# Rights Registry
# ============================================================================


class RightsRegistry:
    """
    Rights registry for data providers.

    Loads provider rights from YAML and enforces operation permissions.
    """

    def __init__(self, registry_path: str = None):
        """
        Initialize rights registry.

        Args:
            registry_path: Path to RIGHTS_REGISTRY.yaml
                          (default: .ops/RIGHTS_REGISTRY.yaml)
        """
        if registry_path is None:
            # Default path relative to project root
            project_root = Path(__file__).parent.parent.parent.parent
            registry_path = project_root / ".ops" / "RIGHTS_REGISTRY.yaml"

        self.registry_path = Path(registry_path)
        self.providers: Dict[str, ProviderRights] = {}

        self.load_registry()

    def load_registry(self):
        """
        Load provider rights from YAML file.

        Raises:
            FileNotFoundError: If registry file doesn't exist
        """
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Rights registry not found: {self.registry_path}")

        logger.info(f"Loading rights registry from {self.registry_path}")

        with open(self.registry_path, "r") as f:
            config = yaml.safe_load(f)

        providers_config = config.get("providers", {})

        for provider_id, provider_config in providers_config.items():
            self.providers[provider_id] = ProviderRights(provider_id, provider_config)

        logger.info(f"Loaded {len(self.providers)} providers from registry")

    def get_provider(self, provider_id: str) -> Optional[ProviderRights]:
        """
        Get provider rights by ID.

        Args:
            provider_id: Provider ID (e.g., "FMP", "Polygon")

        Returns:
            ProviderRights or None if not found
        """
        return self.providers.get(provider_id)

    def ensure_allowed(
        self,
        provider_ids: List[str],
        operation: str,
    ) -> Tuple[bool, List[str]]:
        """
        Check if operation is allowed for all providers.

        Args:
            provider_ids: List of provider IDs
            operation: Operation to check (display, export_pdf, export_csv, redistribution)

        Returns:
            (allowed, blocked_providers)
            - allowed: True if all providers allow operation
            - blocked_providers: List of provider IDs that block operation
        """
        blocked = []

        for provider_id in provider_ids:
            provider = self.get_provider(provider_id)

            if not provider:
                logger.warning(f"Unknown provider: {provider_id}")
                blocked.append(provider_id)
                continue

            if not provider.allows_operation(operation):
                logger.warning(
                    f"Provider {provider_id} does not allow operation: {operation}"
                )
                blocked.append(provider_id)

        allowed = len(blocked) == 0

        return allowed, blocked

    def get_attribution_text(self, provider_ids: List[str]) -> str:
        """
        Get combined attribution text for providers.

        Args:
            provider_ids: List of provider IDs

        Returns:
            Combined attribution text (one line per provider)
        """
        attribution_lines = []

        for provider_id in provider_ids:
            provider = self.get_provider(provider_id)

            if not provider:
                logger.warning(f"Unknown provider: {provider_id}")
                continue

            if provider.attribution_required and provider.attribution_text:
                attribution_lines.append(f"- {provider.attribution_text}")

        if not attribution_lines:
            return ""

        return "Data Sources:\n" + "\n".join(attribution_lines)

    def list_providers(self) -> List[Dict]:
        """
        List all registered providers.

        Returns:
            List of provider dicts
        """
        return [provider.to_dict() for provider in self.providers.values()]


# ============================================================================
# Singleton
# ============================================================================


_rights_registry_instance = None


def get_rights_registry() -> RightsRegistry:
    """
    Get singleton RightsRegistry instance.

    Returns:
        RightsRegistry singleton
    """
    global _rights_registry_instance

    if _rights_registry_instance is None:
        _rights_registry_instance = RightsRegistry()

    return _rights_registry_instance


# ============================================================================
# Convenience Functions
# ============================================================================


def ensure_allowed(provider_ids: List[str], operation: str) -> Tuple[bool, List[str]]:
    """
    Check if operation is allowed for all providers.

    Args:
        provider_ids: List of provider IDs
        operation: Operation to check (display, export_pdf, export_csv, redistribution)

    Returns:
        (allowed, blocked_providers)
    """
    registry = get_rights_registry()
    return registry.ensure_allowed(provider_ids, operation)


def get_attribution_text(provider_ids: List[str]) -> str:
    """
    Get combined attribution text for providers.

    Args:
        provider_ids: List of provider IDs

    Returns:
        Combined attribution text
    """
    registry = get_rights_registry()
    return registry.get_attribution_text(provider_ids)


def raise_if_blocked(provider_ids: List[str], operation: str):
    """
    Raise RightsViolationError if operation is blocked.

    Args:
        provider_ids: List of provider IDs
        operation: Operation to check

    Raises:
        RightsViolationError: If operation is blocked
    """
    allowed, blocked = ensure_allowed(provider_ids, operation)

    if not allowed:
        raise RightsViolationError(
            f"Operation '{operation}' blocked by providers: {', '.join(blocked)}",
            blocked_providers=blocked,
        )


# ============================================================================
# CLI Entry Point
# ============================================================================


def main():
    """CLI entry point for rights registry."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Rights Registry CLI")

    parser.add_argument(
        "--list",
        action="store_true",
        help="List all providers",
    )

    parser.add_argument(
        "--check",
        type=str,
        nargs="+",
        metavar="PROVIDER",
        help="Check if operation allowed for providers",
    )

    parser.add_argument(
        "--operation",
        type=str,
        choices=["display", "export_pdf", "export_csv", "redistribution"],
        default="export_pdf",
        help="Operation to check (default: export_pdf)",
    )

    parser.add_argument(
        "--attribution",
        type=str,
        nargs="+",
        metavar="PROVIDER",
        help="Get attribution text for providers",
    )

    args = parser.parse_args()

    registry = get_rights_registry()

    if args.list:
        # List all providers
        providers = registry.list_providers()
        print(json.dumps(providers, indent=2))

    elif args.check:
        # Check if operation allowed
        allowed, blocked = registry.ensure_allowed(args.check, args.operation)

        print(f"\nOperation: {args.operation}")
        print(f"Providers: {', '.join(args.check)}")
        print(f"Status: {'✅ ALLOWED' if allowed else '❌ BLOCKED'}")

        if blocked:
            print(f"Blocked by: {', '.join(blocked)}")

    elif args.attribution:
        # Get attribution text
        attribution = registry.get_attribution_text(args.attribution)
        print(attribution)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
