"""
DawsOS Compliance Module

Purpose: Data source rights enforcement, attribution, and export controls
Updated: 2025-10-22
Priority: P0 (Critical for S1-W2 Gate)

Components:
    - rights_registry.py: Data source rights definitions
    - export_blocker.py: Export validation and blocking
    - attribution.py: Attribution generation and attachment
    - watermark.py: Watermark generation and application

Usage:
    from compliance import (
        get_rights_registry,
        validate_export,
        attach_attributions,
        apply_watermark,
    )

    # Check rights
    registry = get_rights_registry()
    can_export = registry.can_export(DataSource.NEWSAPI)  # False

    # Validate export
    result = validate_export(
        data=data,
        sources=[DataSource.FMP, DataSource.FRED],
        format="json",
        user_id="U1",
    )

    # Add attributions
    data_with_attrs = attach_attributions(data)

    # Apply watermark
    watermarked = apply_watermark(data, sources=[DataSource.FMP], format="json")
"""

from .rights_registry import (
    RightsRegistry,
    RightsProfile,
    DataSource,
    DataRight,
    get_rights_registry,
    RIGHTS_PROFILES,
)

from .export_blocker import (
    ExportBlocker,
    ExportRequest,
    ExportResult,
    get_export_blocker,
    validate_export,
    check_source_rights,
)

from .attribution import (
    AttributionManager,
    Attribution,
    get_attribution_manager,
    attach_attributions,
    format_attributions,
    extract_sources,
)

from .watermark import (
    WatermarkGenerator,
    WatermarkConfig,
    get_watermark_generator,
    generate_watermark,
    apply_watermark,
)

__all__ = [
    # Rights Registry
    "RightsRegistry",
    "RightsProfile",
    "DataSource",
    "DataRight",
    "get_rights_registry",
    "RIGHTS_PROFILES",
    # Export Blocker
    "ExportBlocker",
    "ExportRequest",
    "ExportResult",
    "get_export_blocker",
    "validate_export",
    "check_source_rights",
    # Attribution
    "AttributionManager",
    "Attribution",
    "get_attribution_manager",
    "attach_attributions",
    "format_attributions",
    "extract_sources",
    # Watermark
    "WatermarkGenerator",
    "WatermarkConfig",
    "get_watermark_generator",
    "generate_watermark",
    "apply_watermark",
]
