"""
Watermarking System - Apply Watermarks to Exports

Purpose: Apply watermarks to exported data for data source attribution
Updated: 2025-10-22
Priority: P0 (Critical for S1-W2 Gate)

Core Responsibilities:
    - Generate watermark text from data sources
    - Apply watermarks to different export formats (JSON, CSV, PDF)
    - Embed metadata in exports
    - Track watermarked exports

Flow:
    Export Request → Generate Watermark → Apply to Format → Return Watermarked Data

Watermark Formats:
    - JSON: __watermark__ field in metadata
    - CSV: Header comment with watermark
    - PDF: Footer text on each page
    - Excel: Hidden metadata sheet
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging
import json

from backend.compliance.rights_registry import get_rights_registry, DataSource

logger = logging.getLogger("DawsOS.Compliance.Watermark")


@dataclass
class WatermarkConfig:
    """
    Watermark configuration.

    Attributes:
        text: Watermark text
        timestamp: Include timestamp
        user_id: Include user ID
        request_id: Include request ID
        position: Position for visual watermarks (footer, header, overlay)
        opacity: Opacity for visual watermarks (0.0 - 1.0)
    """
    text: str
    timestamp: bool = True
    user_id: bool = True
    request_id: bool = False
    position: str = "footer"
    opacity: float = 0.3


class WatermarkGenerator:
    """
    Generates watermarks for exports.

    Creates watermark text from data sources and export metadata.
    """

    def __init__(self):
        """Initialize watermark generator."""
        self._registry = get_rights_registry()
        self._watermarked_exports = 0
        logger.info("Watermark generator initialized")

    def generate_watermark(
        self,
        sources: List[DataSource],
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        include_timestamp: bool = True,
    ) -> str:
        """
        Generate watermark text from sources.

        Args:
            sources: Data sources used
            user_id: User ID (optional)
            request_id: Request ID (optional)
            include_timestamp: Include timestamp in watermark

        Returns:
            Watermark text
        """
        # Get watermark texts from sources
        watermarks = []
        for source in sources:
            wm = self._registry.get_watermark(source)
            if wm:
                watermarks.append(wm)

        if not watermarks:
            # No watermarks required
            return ""

        # Build watermark text
        parts = []

        # Add source watermarks
        parts.append(" | ".join(watermarks))

        # Add timestamp
        if include_timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
            parts.append(f"Exported: {timestamp}")

        # Add user ID (hashed for privacy)
        if user_id:
            user_hash = self._hash_user_id(user_id)
            parts.append(f"User: {user_hash}")

        # Add request ID (for tracing)
        if request_id:
            parts.append(f"Request: {request_id[:8]}")

        return " | ".join(parts)

    def _hash_user_id(self, user_id: str) -> str:
        """
        Hash user ID for watermark.

        Args:
            user_id: User ID

        Returns:
            Hashed ID (first 8 chars of hash)
        """
        import hashlib
        return hashlib.sha256(user_id.encode()).hexdigest()[:8]

    def apply_watermark_json(
        self,
        data: Dict[str, Any],
        watermark: str,
        config: Optional[WatermarkConfig] = None,
    ) -> Dict[str, Any]:
        """
        Apply watermark to JSON export.

        Args:
            data: Export data
            watermark: Watermark text
            config: Watermark configuration (optional)

        Returns:
            Data with watermark embedded
        """
        if not watermark:
            return data

        # Create copy to avoid mutating original
        result = data.copy()

        # Add watermark to metadata
        if "__export_metadata__" not in result:
            result["__export_metadata__"] = {}

        result["__export_metadata__"]["watermark"] = watermark

        self._watermarked_exports += 1
        logger.debug(f"Applied watermark to JSON: {watermark}")

        return result

    def apply_watermark_csv(
        self,
        csv_data: str,
        watermark: str,
        config: Optional[WatermarkConfig] = None,
    ) -> str:
        """
        Apply watermark to CSV export.

        Args:
            csv_data: CSV data as string
            watermark: Watermark text
            config: Watermark configuration (optional)

        Returns:
            CSV with watermark header
        """
        if not watermark:
            return csv_data

        # Add watermark as comment header
        watermark_header = f"# {watermark}\n"

        self._watermarked_exports += 1
        logger.debug(f"Applied watermark to CSV: {watermark}")

        return watermark_header + csv_data

    def apply_watermark_text(
        self,
        text_data: str,
        watermark: str,
        config: Optional[WatermarkConfig] = None,
    ) -> str:
        """
        Apply watermark to plain text export.

        Args:
            text_data: Text data
            watermark: Watermark text
            config: Watermark configuration (optional)

        Returns:
            Text with watermark footer
        """
        if not watermark:
            return text_data

        # Add watermark as footer
        separator = "\n" + "=" * 80 + "\n"
        watermark_footer = f"{separator}{watermark}\n"

        self._watermarked_exports += 1
        logger.debug(f"Applied watermark to text: {watermark}")

        return text_data + watermark_footer

    def get_watermark_config(
        self,
        sources: List[DataSource],
        format: str = "default",
    ) -> WatermarkConfig:
        """
        Get watermark configuration for sources.

        Args:
            sources: Data sources
            format: Export format

        Returns:
            WatermarkConfig for these sources
        """
        # Generate base watermark text
        watermark_text = self.generate_watermark(sources, include_timestamp=False)

        # Default config
        config = WatermarkConfig(
            text=watermark_text,
            timestamp=True,
            user_id=True,
            request_id=False,
            position="footer",
            opacity=0.3,
        )

        return config

    def get_stats(self) -> Dict[str, Any]:
        """
        Get watermark generator statistics.

        Returns:
            Dictionary with stats
        """
        return {
            "watermarked_exports": self._watermarked_exports,
        }


# ============================================================================
# Singleton Instance
# ============================================================================

_watermark_generator: Optional[WatermarkGenerator] = None


def get_watermark_generator() -> WatermarkGenerator:
    """Get or create singleton watermark generator."""
    global _watermark_generator
    if _watermark_generator is None:
        _watermark_generator = WatermarkGenerator()
    return _watermark_generator


# ============================================================================
# Helper Functions
# ============================================================================


def generate_watermark(
    sources: List[DataSource],
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    include_timestamp: bool = True,
) -> str:
    """
    Convenience function to generate watermark.

    Args:
        sources: Data sources
        user_id: User ID (optional)
        request_id: Request ID (optional)
        include_timestamp: Include timestamp

    Returns:
        Watermark text
    """
    generator = get_watermark_generator()
    return generator.generate_watermark(
        sources=sources,
        user_id=user_id,
        request_id=request_id,
        include_timestamp=include_timestamp,
    )


def apply_watermark(
    data: Any,
    sources: List[DataSource],
    format: str = "json",
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
) -> Any:
    """
    Convenience function to apply watermark to data.

    Args:
        data: Export data (dict for JSON, str for CSV/text)
        sources: Data sources
        format: Export format (json, csv, text)
        user_id: User ID (optional)
        request_id: Request ID (optional)

    Returns:
        Data with watermark applied
    """
    generator = get_watermark_generator()

    # Generate watermark text
    watermark = generator.generate_watermark(
        sources=sources,
        user_id=user_id,
        request_id=request_id,
    )

    # Apply based on format
    if format == "json":
        if not isinstance(data, dict):
            logger.warning(f"Expected dict for JSON watermark, got {type(data)}")
            return data
        return generator.apply_watermark_json(data, watermark)

    elif format == "csv":
        if not isinstance(data, str):
            logger.warning(f"Expected str for CSV watermark, got {type(data)}")
            return data
        return generator.apply_watermark_csv(data, watermark)

    elif format == "text":
        if not isinstance(data, str):
            logger.warning(f"Expected str for text watermark, got {type(data)}")
            return data
        return generator.apply_watermark_text(data, watermark)

    else:
        logger.warning(f"Unsupported watermark format: {format}")
        return data
