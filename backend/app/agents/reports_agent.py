"""
DawsOS Reports Agent

Purpose: PDF/CSV export generation with rights enforcement
Updated: 2025-11-02
Capabilities:
    - reports.render_pdf: Generate PDF from pattern result
    - reports.export_csv: Export data to CSV format
    - reports.export_excel: Export data to Excel format (future)

Architecture:
    - Delegates to ReportService for actual generation
    - Enforces rights via RightsRegistry
    - Attaches metadata for traceability
    - Returns base64-encoded bytes for transport

Usage:
    agent = ReportsAgent("reports_agent", services)
    result = await agent.reports_render_pdf(
        ctx,
        state,
        template_name="portfolio_summary",
        report_data={...}
    )
"""

import base64
import logging
from typing import Any, Dict, List, Optional

from app.agents.base_agent import BaseAgent
from app.core.types import RequestCtx
from app.services.reports import ReportService

logger = logging.getLogger(__name__)
class ReportsAgent(BaseAgent):
    """
    Reports Agent: Generate PDF/CSV exports with rights enforcement.

    Capabilities:
        - reports.render_pdf: Generate PDF report
        - reports.export_csv: Generate CSV export
        - reports.export_excel: Generate Excel export (future)
    """

    def get_capabilities(self) -> List[str]:
        """Return list of export capabilities."""
        return [
            "reports.render_pdf",
            "reports.export_csv",
            "reports.export_excel",  # Future capability
        ]

    async def reports_render_pdf(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        template_name: str = "portfolio_summary",
        report_data: Optional[Dict[str, Any]] = None,
        portfolio_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate PDF report from pattern result.

        Capability: reports.render_pdf

        Args:
            ctx: Request context (contains user_id, pricing_pack_id, etc.)
            state: Pattern execution state (contains accumulated results)
            template_name: Template to use (e.g., "portfolio_summary", "buffett_checklist")
            report_data: Explicit report data (if not using state)
            portfolio_id: Portfolio UUID for audit logging
            **kwargs: Additional template variables

        Returns:
            Dict with:
                - pdf_base64: Base64-encoded PDF bytes
                - size_bytes: PDF file size
                - attributions: List of attribution strings
                - watermark_applied: Boolean
                - template_name: Template used
                - providers: List of data providers
        """
        logger.info(
            f"reports.render_pdf: template={template_name}, "
            f"portfolio_id={portfolio_id}, user_id={ctx.user_id}"
        )

        # Get report data from state or explicit parameter
        if report_data is None:
            # Merge all state variables into report_data
            report_data = {
                k: v for k, v in state.items()
                if not k.startswith("_")  # Exclude internal state
            }

        # Add context metadata
        report_data["_metadata"] = {
            "pricing_pack_id": ctx.pricing_pack_id,
            "ledger_commit_hash": ctx.ledger_commit_hash,
            "asof_date": str(ctx.asof_date) if ctx.asof_date else None,
            "user_id": ctx.user_id,
        }

        # Add any additional kwargs to report_data
        report_data.update(kwargs)

        # Initialize report service
        report_service = ReportService(environment=self._get_environment())

        # Generate PDF
        try:
            pdf_bytes = await report_service.render_pdf(
                report_data=report_data,
                template_name=template_name,
                user_id=ctx.user_id,
                portfolio_id=portfolio_id,
            )

            # Extract providers from report data
            providers = report_service._extract_providers(report_data)

            # Get attributions
            rights_check = report_service.registry.check_export(
                providers=providers,
                export_type="pdf",
                environment=report_service.environment,
            )

            result = {
                "pdf_base64": base64.b64encode(pdf_bytes).decode('utf-8'),
                "size_bytes": len(pdf_bytes),
                "attributions": rights_check.attributions,
                "watermark_applied": rights_check.watermark is not None,
                "template_name": template_name,
                "providers": providers,
                "download_filename": f"{template_name}_{portfolio_id or 'report'}.pdf",
                "status": "success",
                "generated_at": str(rights_check.timestamp),
            }

            # Attach metadata
            metadata = self._create_metadata(
                source=f"report_service:{ctx.pricing_pack_id}",
                asof=ctx.asof_date,
                ttl=self.CACHE_TTL_NONE,  # PDF is point-in-time, no caching
            )

            return self._attach_metadata(result, metadata)

        except Exception as e:
            logger.error(f"PDF generation failed: {e}", exc_info=True)

            # Return error result
            return {
                "status": "error",
                "error": str(e),
                "template_name": template_name,
                "pdf_base64": None,
            }

    async def reports_export_csv(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        filename: str = "export.csv",
        data: Optional[Dict[str, Any]] = None,
        providers: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate CSV export with rights enforcement.

        Capability: reports.export_csv

        Args:
            ctx: Request context
            state: Pattern execution state
            filename: CSV filename
            data: Explicit data to export (if not using state)
            providers: List of provider IDs (if known)
            **kwargs: Additional options

        Returns:
            Dict with:
                - csv_base64: Base64-encoded CSV bytes
                - size_bytes: CSV file size
                - attributions: List of attribution strings
                - filename: CSV filename
                - providers: List of data providers
        """
        logger.info(f"reports.export_csv: filename={filename}, user_id={ctx.user_id}")

        # Get data from state or explicit parameter
        if data is None:
            data = {
                k: v for k, v in state.items()
                if not k.startswith("_")
            }

        # Initialize report service
        report_service = ReportService(environment=self._get_environment())

        # Extract providers if not provided
        if providers is None:
            providers = report_service._extract_providers(data)

        # Generate CSV
        try:
            csv_bytes = await report_service.generate_csv(
                data=data,
                providers=providers,
                filename=filename,
            )

            # Get attributions
            rights_check = report_service.registry.check_export(
                providers=providers,
                export_type="csv",
                environment=report_service.environment,
            )

            result = {
                "csv_base64": base64.b64encode(csv_bytes).decode('utf-8'),
                "size_bytes": len(csv_bytes),
                "attributions": rights_check.attributions,
                "filename": filename,
                "providers": providers,
                "download_filename": filename,
                "status": "success",
                "generated_at": str(rights_check.timestamp),
            }

            # Attach metadata
            metadata = self._create_metadata(
                source=f"report_service:csv",
                asof=ctx.asof_date,
                ttl=self.CACHE_TTL_NONE,
            )

            return self._attach_metadata(result, metadata)

        except Exception as e:
            logger.error(f"CSV generation failed: {e}", exc_info=True)

            return {
                "status": "error",
                "error": str(e),
                "filename": filename,
                "csv_base64": None,
            }

    async def reports_export_excel(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        filename: str = "export.xlsx",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate Excel export (future capability).

        Capability: reports.export_excel

        Args:
            ctx: Request context
            state: Pattern execution state
            filename: Excel filename
            **kwargs: Additional options

        Returns:
            Dict with status and error message (not yet implemented)
        """
        logger.warning("reports.export_excel: Not yet implemented")

        return {
            "status": "not_implemented",
            "error": "Excel export not yet implemented",
            "filename": filename,
            "excel_base64": None,
        }

    def _get_environment(self) -> str:
        """
        Determine environment for rights enforcement.

        Returns:
            "staging" or "production"
        """
        # Check environment variable or service config
        import os
        env = os.getenv("ENVIRONMENT", "staging")

        # Map common environment names
        if env in ["prod", "production"]:
            return "production"
        else:
            return "staging"
