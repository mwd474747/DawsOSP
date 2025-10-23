"""
Attribution System - Data Source Attribution Management

Purpose: Ensure proper attribution for data sources in responses
Updated: 2025-10-22
Priority: P0 (Critical for S1-W2 Gate)

Core Responsibilities:
    - Extract data sources from pattern results
    - Generate attribution text
    - Attach attributions to responses
    - Format attributions for display (UI, exports)
    - Track attribution compliance

Flow:
    Pattern Result → Extract Sources → Generate Attributions → Attach to Response

Attribution Formats:
    - UI: Footer text with links
    - Export: Metadata section with full attributions
    - API: __attributions__ field in response
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Set
import logging

from backend.compliance.rights_registry import get_rights_registry, DataSource

logger = logging.getLogger("DawsOS.Compliance.Attribution")


@dataclass
class Attribution:
    """
    Single attribution entry.

    Attributes:
        source: Data source
        text: Attribution text
        url: Terms/attribution URL
        required: Whether attribution is required (vs. optional)
    """
    source: DataSource
    text: str
    url: Optional[str] = None
    required: bool = True


class AttributionManager:
    """
    Manages data source attributions.

    Extracts sources, generates attribution text, attaches to responses.
    """

    def __init__(self):
        """Initialize attribution manager."""
        self._registry = get_rights_registry()
        self._attribution_count = 0
        logger.info("Attribution manager initialized")

    def extract_sources(self, data: Dict[str, Any]) -> List[DataSource]:
        """
        Extract data sources from pattern result.

        Looks for __metadata__ markers that agents attach to their results.

        Args:
            data: Pattern result data

        Returns:
            List of data sources (deduplicated)
        """
        sources: Set[DataSource] = set()

        def _extract_recursive(obj: Any) -> None:
            """Recursively search for __metadata__ markers."""
            if isinstance(obj, dict):
                # Check for __metadata__ marker
                if "__metadata__" in obj:
                    metadata = obj["__metadata__"]
                    if "source" in metadata:
                        source_str = metadata["source"]
                        # Parse source string (format: "source_name" or "source_name:detail")
                        source_name = source_str.split(":")[0] if ":" in source_str else source_str
                        try:
                            source = DataSource(source_name.lower())
                            sources.add(source)
                        except ValueError:
                            logger.warning(f"Unknown data source in metadata: {source_name}")

                # Recurse into dict values
                for value in obj.values():
                    _extract_recursive(value)

            elif isinstance(obj, list):
                # Recurse into list items
                for item in obj:
                    _extract_recursive(item)

        _extract_recursive(data)

        return list(sources)

    def generate_attributions(self, sources: List[DataSource]) -> List[Attribution]:
        """
        Generate attributions for data sources.

        Args:
            sources: List of data sources

        Returns:
            List of Attribution objects
        """
        attributions = []

        for source in sources:
            profile = self._registry.get_profile(source)
            if not profile:
                logger.warning(f"No rights profile for source: {source.value}")
                continue

            if profile.attribution_required and profile.attribution_text:
                attribution = Attribution(
                    source=source,
                    text=profile.attribution_text,
                    url=profile.terms_url,
                    required=profile.attribution_required,
                )
                attributions.append(attribution)

        return attributions

    def attach_attributions(
        self,
        data: Dict[str, Any],
        sources: Optional[List[DataSource]] = None,
    ) -> Dict[str, Any]:
        """
        Attach attributions to response data.

        Args:
            data: Response data
            sources: Data sources (if None, will extract from data)

        Returns:
            Data with __attributions__ field attached
        """
        # Extract sources if not provided
        if sources is None:
            sources = self.extract_sources(data)

        # Generate attributions
        attributions = self.generate_attributions(sources)

        if not attributions:
            # No attributions required
            return data

        # Create copy to avoid mutating original
        result = data.copy()

        # Attach attributions
        result["__attributions__"] = {
            "sources": [attr.source.value for attr in attributions],
            "text": [attr.text for attr in attributions],
            "urls": [attr.url for attr in attributions if attr.url],
            "count": len(attributions),
        }

        self._attribution_count += 1

        logger.info(f"Attached {len(attributions)} attributions to response")

        return result

    def format_attributions(
        self,
        attributions: List[Attribution],
        format: str = "text",
        include_urls: bool = True,
    ) -> str:
        """
        Format attributions for display.

        Args:
            attributions: List of attributions
            format: Output format (text, html, markdown)
            include_urls: Whether to include URLs

        Returns:
            Formatted attribution text
        """
        if not attributions:
            return ""

        if format == "html":
            items = []
            for attr in attributions:
                if include_urls and attr.url:
                    items.append(f"<li><a href='{attr.url}' target='_blank'>{attr.text}</a></li>")
                else:
                    items.append(f"<li>{attr.text}</li>")
            return f"<div class='attributions'><strong>Data Sources:</strong><ul>{''.join(items)}</ul></div>"

        elif format == "markdown":
            items = []
            for attr in attributions:
                if include_urls and attr.url:
                    items.append(f"- [{attr.text}]({attr.url})")
                else:
                    items.append(f"- {attr.text}")
            return f"**Data Sources:**\n\n{''.join(f'{item}\n' for item in items)}"

        else:  # text
            items = []
            for attr in attributions:
                if include_urls and attr.url:
                    items.append(f"{attr.text} ({attr.url})")
                else:
                    items.append(attr.text)
            return "Data Sources:\n" + "\n".join(f"• {item}" for item in items)

    def format_from_data(
        self,
        data: Dict[str, Any],
        format: str = "text",
        include_urls: bool = True,
    ) -> Optional[str]:
        """
        Extract and format attributions from data.

        Args:
            data: Response data with __attributions__ field
            format: Output format (text, html, markdown)
            include_urls: Whether to include URLs

        Returns:
            Formatted attribution text, or None if no attributions
        """
        if "__attributions__" not in data:
            return None

        attr_data = data["__attributions__"]
        sources = attr_data.get("sources", [])

        # Reconstruct Attribution objects
        attributions = []
        for i, source_str in enumerate(sources):
            try:
                source = DataSource(source_str)
                text = attr_data["text"][i]
                url = attr_data["urls"][i] if i < len(attr_data.get("urls", [])) else None

                attribution = Attribution(
                    source=source,
                    text=text,
                    url=url,
                )
                attributions.append(attribution)

            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to reconstruct attribution for {source_str}: {e}")
                continue

        return self.format_attributions(attributions, format=format, include_urls=include_urls)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get attribution manager statistics.

        Returns:
            Dictionary with stats
        """
        return {
            "attributions_attached": self._attribution_count,
        }


# ============================================================================
# Singleton Instance
# ============================================================================

_attribution_manager: Optional[AttributionManager] = None


def get_attribution_manager() -> AttributionManager:
    """Get or create singleton attribution manager."""
    global _attribution_manager
    if _attribution_manager is None:
        _attribution_manager = AttributionManager()
    return _attribution_manager


# ============================================================================
# Helper Functions
# ============================================================================


def attach_attributions(
    data: Dict[str, Any],
    sources: Optional[List[DataSource]] = None,
) -> Dict[str, Any]:
    """
    Convenience function to attach attributions to response.

    Args:
        data: Response data
        sources: Data sources (optional, will extract if not provided)

    Returns:
        Data with attributions attached
    """
    manager = get_attribution_manager()
    return manager.attach_attributions(data, sources=sources)


def format_attributions(
    data: Dict[str, Any],
    format: str = "text",
    include_urls: bool = True,
) -> Optional[str]:
    """
    Convenience function to format attributions from data.

    Args:
        data: Response data with __attributions__ field
        format: Output format (text, html, markdown)
        include_urls: Whether to include URLs

    Returns:
        Formatted attribution text, or None if no attributions
    """
    manager = get_attribution_manager()
    return manager.format_from_data(data, format=format, include_urls=include_urls)


def extract_sources(data: Dict[str, Any]) -> List[DataSource]:
    """
    Convenience function to extract data sources from response.

    Args:
        data: Response data

    Returns:
        List of data sources
    """
    manager = get_attribution_manager()
    return manager.extract_sources(data)
