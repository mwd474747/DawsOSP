"""
DawsOS Reports Service

Purpose: Generate PDF/CSV exports with rights enforcement
Updated: 2025-10-27
Priority: P0 (Critical for export functionality)

Features:
    - PDF report generation with WeasyPrint
    - CSV export
    - Rights enforcement via RightsRegistry
    - Attribution footer inclusion
    - Watermark overlay (if required)
    - Audit logging
    - HTML template rendering with Jinja2

Usage:
    report = ReportService(environment="staging")
    pdf_bytes = await report.render_pdf(
        report_data=result_data,
        template_name="portfolio_summary",
        user_id="user-123",
        portfolio_id="portfolio-456"
    )
"""

import base64
import io
import logging
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from backend.app.services.rights_registry import get_registry, ExportCheckResult

logger = logging.getLogger(__name__)

# WeasyPrint imported conditionally (may not be available in all environments)
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    logger.warning("WeasyPrint not available - PDF export will use fallback mode")
    WEASYPRINT_AVAILABLE = False


# ============================================================================
# Report Service
# ============================================================================


class ReportService:
    """
    Report service: generate exports with rights enforcement.

    Integrates with RightsRegistry to ensure compliance with provider
    export restrictions and attribution requirements.
    """

    def __init__(self, environment: str = "staging", templates_dir: Optional[str] = None):
        """
        Initialize report service.

        Args:
            environment: "staging" or "production" (affects enforcement)
            templates_dir: Path to templates directory (default: backend/templates)
        """
        self.environment = environment
        self.registry = get_registry()

        # Setup Jinja2 environment
        if templates_dir is None:
            # Default to backend/templates
            templates_dir = Path(__file__).parent.parent.parent / "templates"

        self.templates_dir = Path(templates_dir)
        if not self.templates_dir.exists():
            logger.warning(f"Templates directory not found: {self.templates_dir}")
            self.templates_dir.mkdir(parents=True, exist_ok=True)

        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        logger.info(f"ReportService initialized (environment={environment}, templates={self.templates_dir})")

    async def render_pdf(
        self,
        report_data: Dict[str, Any],
        template_name: str,
        user_id: Optional[str] = None,
        portfolio_id: Optional[str] = None,
    ) -> bytes:
        """
        Generate PDF report from HTML template with rights enforcement.

        Args:
            report_data: Report data (pattern execution result)
            template_name: Template name (e.g., "portfolio_summary", "buffett_checklist")
            user_id: User ID for audit logging
            portfolio_id: Portfolio ID for audit logging

        Returns:
            PDF bytes

        Raises:
            RightsViolationError: If export not allowed
        """
        # Extract providers from report data
        providers = self._extract_providers(report_data)

        # Check rights
        rights_check = self.registry.ensure_allowed(
            providers=providers,
            export_type="pdf",
            environment=self.environment,
        )

        logger.info(
            f"Rendering PDF: template={template_name}, providers={providers}, "
            f"user_id={user_id}, portfolio_id={portfolio_id}"
        )

        # Enforce rights - filter data based on permissions
        filtered_data = self.enforce_rights(report_data, rights_check)

        # Generate attributions
        attributions = self.generate_attribution(filtered_data, rights_check)

        # Render HTML from template
        html_content = self._render_html(
            template_name=template_name,
            report_data=filtered_data,
            attributions=attributions,
            watermark=rights_check.watermark,
        )

        # Generate PDF
        if WEASYPRINT_AVAILABLE:
            pdf_bytes = self._generate_pdf_weasyprint(html_content)
        else:
            # Fallback: return HTML as bytes
            logger.warning("WeasyPrint not available - returning HTML instead of PDF")
            pdf_bytes = html_content.encode('utf-8')

        # Audit log
        await self._audit_log_export(
            export_type="pdf",
            providers=providers,
            title=f"{template_name}.pdf",
            user_id=user_id,
            portfolio_id=portfolio_id,
            allowed=True,
            rights_check=rights_check,
        )

        return pdf_bytes

    def enforce_rights(
        self,
        report_data: Dict[str, Any],
        rights_check: ExportCheckResult
    ) -> Dict[str, Any]:
        """
        Filter report data based on provider rights.

        Args:
            report_data: Full report data
            rights_check: Rights check result with blocked providers

        Returns:
            Filtered report data with warnings for excluded sections
        """
        filtered_data = report_data.copy()
        warnings = []

        # Check for blocked providers
        if rights_check.blocked_providers:
            blocked_set = set(rights_check.blocked_providers)

            # Remove sections based on blocked providers
            if "NewsAPI" in blocked_set:
                if "news" in filtered_data:
                    del filtered_data["news"]
                    warnings.append("News analysis excluded (NewsAPI export restricted)")
                if "news_impact" in filtered_data:
                    del filtered_data["news_impact"]

            if "AlphaVantage" in blocked_set:
                if "alphavantage_data" in filtered_data:
                    del filtered_data["alphavantage_data"]
                    warnings.append("AlphaVantage data excluded (export restricted)")

            if "YahooFinance" in blocked_set:
                if "yahoo_data" in filtered_data:
                    del filtered_data["yahoo_data"]
                    warnings.append("Yahoo Finance data excluded (export restricted)")

        # Add warnings to data
        if warnings:
            filtered_data["_warnings"] = warnings
            logger.info(f"Rights enforcement: {len(warnings)} sections excluded")

        return filtered_data

    def generate_attribution(
        self,
        report_data: Dict[str, Any],
        rights_check: ExportCheckResult
    ) -> List[str]:
        """
        Generate attribution notices for PDF footer.

        Args:
            report_data: Report data (after rights filtering)
            rights_check: Rights check result

        Returns:
            List of attribution strings
        """
        attributions = []

        # Add provider attributions from rights check
        if rights_check.attributions:
            attributions.extend(rights_check.attributions)

        # Add DawsOS attribution
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        attributions.append(f"Generated by DawsOS Portfolio Intelligence - {timestamp}")

        # Add warnings as attributions
        if "_warnings" in report_data:
            for warning in report_data["_warnings"]:
                attributions.append(f"⚠️ {warning}")

        return attributions

    async def generate_csv(
        self,
        data: Dict[str, Any],
        providers: List[str],
        filename: str,
    ) -> bytes:
        """
        Generate CSV export with rights enforcement.

        Args:
            data: Report data (pattern execution result)
            providers: List of provider IDs used in analysis
            filename: CSV filename

        Returns:
            CSV bytes

        Raises:
            RightsViolationError: If export not allowed
        """
        # Check rights
        rights_check = self.registry.ensure_allowed(
            providers=providers,
            export_type="csv",
            environment=self.environment,
        )

        logger.info(
            f"Generating CSV export: '{filename}' with providers {providers} "
            f"(environment={self.environment})"
        )

        # Generate CSV
        csv_bytes = self._generate_csv_content(
            data=data,
            filename=filename,
            rights_check=rights_check,
        )

        # Audit log
        await self._audit_log_export(
            export_type="csv",
            providers=providers,
            title=filename,
            user_id=None,
            portfolio_id=None,
            allowed=True,
            rights_check=rights_check,
        )

        return csv_bytes

    def _extract_providers(self, report_data: Dict[str, Any]) -> List[str]:
        """
        Extract list of providers from report data sources.

        Args:
            report_data: Report data with _metadata or _sources

        Returns:
            List of provider IDs
        """
        providers = set()

        # Check _metadata for sources
        metadata = report_data.get("_metadata", {})
        if isinstance(metadata, dict):
            source = metadata.get("source", "")
            if "fmp" in source.lower():
                providers.add("FMP")
            if "polygon" in source.lower():
                providers.add("Polygon")
            if "fred" in source.lower():
                providers.add("FRED")
            if "newsapi" in source.lower():
                providers.add("NewsAPI")

        # Check _sources field
        sources = report_data.get("_sources", {})
        if isinstance(sources, dict):
            if sources.get("prices") == "FMP" or sources.get("fundamentals"):
                providers.add("FMP")
            if sources.get("corporate_actions") or sources.get("prices") == "Polygon":
                providers.add("Polygon")
            if sources.get("fx_rates") or sources.get("macro_indicators"):
                providers.add("FRED")
            if sources.get("news"):
                providers.add("NewsAPI")

        # Default to Manual if no providers detected
        if not providers:
            providers.add("Manual")

        return list(providers)

    def _render_html(
        self,
        template_name: str,
        report_data: Dict[str, Any],
        attributions: List[str],
        watermark: Optional[Any] = None,
    ) -> str:
        """
        Render HTML from Jinja2 template.

        Args:
            template_name: Template name (without .html extension)
            report_data: Report data for template
            attributions: Attribution strings for footer
            watermark: Optional watermark config

        Returns:
            Rendered HTML string
        """
        # Ensure template name has .html extension
        if not template_name.endswith(".html"):
            template_name = f"{template_name}.html"

        try:
            template = self.jinja_env.get_template(template_name)
        except Exception as e:
            logger.error(f"Template not found: {template_name} - {e}")
            # Return simple HTML fallback
            return self._generate_fallback_html(report_data, attributions, watermark)

        # Render template
        html = template.render(
            report_data=report_data,
            attributions=attributions,
            watermark=watermark,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        return html

    def _generate_pdf_weasyprint(self, html_content: str) -> bytes:
        """
        Generate PDF from HTML using WeasyPrint.

        Args:
            html_content: HTML string

        Returns:
            PDF bytes
        """
        # Check for custom CSS
        css_path = self.templates_dir / "dawsos_pdf.css"

        if css_path.exists():
            css = CSS(filename=str(css_path))
            pdf_bytes = HTML(string=html_content).write_pdf(stylesheets=[css])
        else:
            # Use default styling
            pdf_bytes = HTML(string=html_content).write_pdf()

        logger.info(f"Generated PDF: {len(pdf_bytes)} bytes")
        return pdf_bytes

    def _generate_fallback_html(
        self,
        report_data: Dict[str, Any],
        attributions: List[str],
        watermark: Optional[Any] = None,
    ) -> str:
        """
        Generate simple HTML when template not found.

        Args:
            report_data: Report data
            attributions: Attribution strings
            watermark: Optional watermark

        Returns:
            HTML string
        """
        import json

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>DawsOS Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #00ACC1; }}
        .attribution {{ font-size: 10px; color: #666; margin-top: 20px; border-top: 1px solid #ccc; padding-top: 10px; }}
        .watermark {{ opacity: 0.3; font-size: 48px; text-align: center; color: #ccc; }}
        pre {{ background: #f5f5f5; padding: 10px; overflow: auto; }}
    </style>
</head>
<body>
    <h1>DawsOS Portfolio Report</h1>

    {f'<div class="watermark">{watermark.text}</div>' if watermark else ''}

    <h2>Report Data</h2>
    <pre>{json.dumps(report_data, indent=2, default=str)}</pre>

    <div class="attribution">
        {'<br>'.join(attributions)}
    </div>
</body>
</html>
        """

        return html

    def _generate_csv_content(
        self,
        data: Dict[str, Any],
        filename: str,
        rights_check: ExportCheckResult,
    ) -> bytes:
        """
        Generate CSV content.

        Args:
            data: Report data
            filename: CSV filename
            rights_check: Rights check result with attributions

        Returns:
            CSV bytes
        """
        import csv

        output = io.StringIO()
        writer = csv.writer(output)

        # Attribution header
        for attr in rights_check.attributions:
            writer.writerow([f"# {attr}"])
        writer.writerow([])

        # Data headers
        writer.writerow(["key", "value"])

        # Data rows
        def flatten_dict(d: Dict[str, Any], prefix: str = ""):
            """Flatten nested dict for CSV."""
            for key, value in d.items():
                full_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict):
                    yield from flatten_dict(value, full_key)
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            yield from flatten_dict(item, f"{full_key}[{i}]")
                        else:
                            writer.writerow([f"{full_key}[{i}]", str(item)])
                else:
                    yield (full_key, value)

        for key, value in flatten_dict(data):
            writer.writerow([key, str(value)])

        csv_bytes = output.getvalue().encode("utf-8")
        return csv_bytes

    async def _audit_log_export(
        self,
        export_type: str,
        providers: List[str],
        title: str,
        user_id: Optional[str],
        portfolio_id: Optional[str],
        allowed: bool,
        rights_check: ExportCheckResult,
    ):
        """
        Log export attempt to audit table.

        Args:
            export_type: "pdf" or "csv"
            providers: List of provider IDs
            title: Report title
            user_id: User ID
            portfolio_id: Portfolio ID
            allowed: Whether export was allowed
            rights_check: Rights check result
        """
        # TODO: Write to audit_log table in database
        # For now, just log to file
        logger.info(
            f"AUDIT: {export_type.upper()} export "
            f"{'ALLOWED' if allowed else 'BLOCKED'} - "
            f"title='{title}', providers={providers}, "
            f"user_id={user_id}, portfolio_id={portfolio_id}, "
            f"environment={self.environment}, "
            f"timestamp={rights_check.timestamp.isoformat()}"
        )


# ============================================================================
# Example Usage
# ============================================================================


async def example_usage():
    """Example of using ReportService."""
    service = ReportService(environment="staging")

    # Example 1: PDF with allowed providers
    try:
        pdf = await service.generate_pdf(
            data={"portfolio_value": 100000, "return_pct": 0.15},
            providers=["FMP", "Polygon"],
            title="Portfolio Performance Report",
            subtitle="Q4 2024",
        )
        print(f"PDF generated: {len(pdf)} bytes")
    except Exception as e:
        print(f"PDF failed: {e}")

    # Example 2: PDF with blocked provider (NewsAPI Developer)
    try:
        pdf = await service.generate_pdf(
            data={"sentiment_score": 0.7},
            providers=["NewsAPI"],
            title="Sentiment Analysis",
        )
        print(f"PDF generated: {len(pdf)} bytes")
    except Exception as e:
        print(f"PDF blocked (expected): {e}")

    # Example 3: CSV export
    try:
        csv = await service.generate_csv(
            data={"AAPL": 150.25, "MSFT": 380.50, "GOOGL": 140.75},
            providers=["FMP"],
            filename="positions.csv",
        )
        print(f"CSV generated: {len(csv)} bytes")
    except Exception as e:
        print(f"CSV failed: {e}")


# ============================================================================
# Service Singleton
# ============================================================================

_reports_service = None


def get_reports_service() -> ReportService:
    """Get singleton reports service instance."""
    global _reports_service

    if _reports_service is None:
        _reports_service = ReportService()

    return _reports_service


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
