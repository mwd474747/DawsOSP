# Reports Agent Specification

**Role**: PDF/CSV export generation with rights enforcement
**Context**: [PRODUCT_SPEC.md](../../PRODUCT_SPEC.md) | [ORCHESTRATOR.md](./ORCHESTRATOR.md)
**Status**: ⚠️ Partial Implementation (Service Ready, Agent Implemented)
**Priority**: P1
**Last Updated**: October 27, 2025

---

## Mission

Generate professional PDF and CSV exports of portfolio analysis with rights enforcement, watermarks, and attribution footers. This agent ensures compliance with data usage policies while providing high-quality reports.

---

## Current Capabilities

### ⚠️ Implemented but Not Fully Integrated

1. **PDF Generation**
   - `reports.render_pdf` - Generate PDF reports with WeasyPrint
   - `reports.export_csv` - Generate CSV exports
   - `reports.export_excel` - Generate Excel exports (future)

### ⚠️ Service Integration Status
- **Service Class**: `ReportsService` in `backend/app/services/reports.py` ✅ Implemented
- **Agent Class**: `ReportsAgent` in `backend/app/agents/reports_agent.py` ✅ Implemented
- **Pattern Integration**: `export_portfolio_report.json` exists but not fully wired
- **WeasyPrint**: Integration implemented but needs testing

---

## Implementation Status

### ✅ Service Layer Complete
- WeasyPrint integration implemented
- HTML template system implemented
- Rights enforcement implemented
- Watermark and attribution implemented

### ⚠️ Agent Layer Partial
- Agent class implemented
- Capabilities declared
- Method stubs implemented
- Service integration needs completion

### ❌ Pattern Integration Pending
- `export_portfolio_report` pattern exists but not fully functional
- UI integration pending
- End-to-end testing pending

---

## Code Examples

### Agent Method Implementation
```python
async def reports_render_pdf(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    report_type: str = "portfolio_overview",
    template_data: Dict[str, Any] = None,
    **kwargs
) -> Dict[str, Any]:
    """Generate PDF report with rights enforcement."""
    logger.info(f"reports.render_pdf: report_type={report_type}")
    
    try:
        # Get reports service
        reports_service = get_reports_service()
        
        # Check rights
        if not await reports_service.check_export_rights(ctx.user_id, report_type):
            raise PermissionError("Export rights not granted")
        
        # Generate PDF
        pdf_result = await reports_service.render_pdf(
            report_type=report_type,
            template_data=template_data or state,
            user_id=ctx.user_id,
            asof_date=ctx.asof_date
        )
        
        # Attach metadata
        metadata = self._create_metadata(
            source=f"reports_service:{ctx.pricing_pack_id}",
            asof=ctx.asof_date,
            ttl=3600
        )
        
        return self._attach_metadata(pdf_result, metadata)
        
    except PermissionError as e:
        logger.warning(f"Export rights denied: {e}")
        return self._attach_metadata({
            "error": "Export rights not granted",
            "pdf_data": None
        }, metadata)
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        return self._attach_metadata({
            "error": "PDF generation failed",
            "pdf_data": None
        }, metadata)
```

### Service Integration Example
```python
async def render_pdf(
    self,
    report_type: str,
    template_data: Dict[str, Any],
    user_id: UUID,
    asof_date: date
) -> Dict[str, Any]:
    """Generate PDF report with WeasyPrint."""
    
    # Load template
    template = await self._load_template(report_type)
    
    # Apply rights enforcement
    filtered_data = await self._apply_rights_filter(template_data, user_id)
    
    # Render HTML
    html_content = await self._render_html(template, filtered_data)
    
    # Generate PDF
    pdf_data = await self._generate_pdf(html_content)
    
    # Add watermark and attribution
    final_pdf = await self._add_watermark(pdf_data, user_id, asof_date)
    
    return {
        "pdf_data": final_pdf,
        "report_type": report_type,
        "generated_at": datetime.now(),
        "rights_applied": True
    }
```

---

## Integration Points

### Services Used
- **ReportsService**: Core report generation
- **RightsRegistry**: Export rights enforcement
- **TemplateService**: HTML template rendering
- **WatermarkService**: PDF watermarking

### Patterns Using This Agent
- `export_portfolio_report` - Portfolio report export (pending integration)

### Database Tables
- `export_rights` - User export permissions
- `report_templates` - Report templates
- `export_audit` - Export audit trail

---

## Rights Enforcement

### Export Rights Framework
```python
EXPORT_RIGHTS = {
    "portfolio_overview": {
        "required_rights": ["portfolio_read"],
        "watermark_level": "standard",
        "attribution_required": True
    },
    "buffett_checklist": {
        "required_rights": ["ratings_read"],
        "watermark_level": "premium",
        "attribution_required": True
    },
    "macro_analysis": {
        "required_rights": ["macro_read"],
        "watermark_level": "standard",
        "attribution_required": True
    }
}
```

### Rights Checking
```python
async def check_export_rights(self, user_id: UUID, report_type: str) -> bool:
    """Check if user has rights to export report type."""
    
    # Get user rights
    user_rights = await self._get_user_rights(user_id)
    
    # Check required rights
    required_rights = EXPORT_RIGHTS[report_type]["required_rights"]
    
    return all(right in user_rights for right in required_rights)
```

---

## Template System

### HTML Templates
- `portfolio_summary.html` - Portfolio overview
- `buffett_checklist.html` - Quality ratings
- `macro_analysis.html` - Macro analysis
- `base.html` - Base template with styling

### Template Variables
```python
TEMPLATE_VARIABLES = {
    "portfolio_data": "Portfolio positions and metrics",
    "ratings_data": "Quality ratings and explanations",
    "macro_data": "Macro regime and cycle data",
    "user_info": "User information for attribution",
    "asof_date": "Report generation date",
    "watermark": "Watermark information"
}
```

### CSS Styling
- `dawsos_pdf.css` - PDF-specific styling
- Print-optimized layouts
- Professional color scheme
- Responsive design elements

---

## WeasyPrint Integration

### PDF Generation
```python
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

async def _generate_pdf(self, html_content: str) -> bytes:
    """Generate PDF using WeasyPrint."""
    
    # Configure fonts
    font_config = FontConfiguration()
    
    # Create HTML object
    html_doc = HTML(string=html_content)
    
    # Generate PDF
    pdf_bytes = html_doc.write_pdf(
        stylesheets=[CSS('backend/templates/dawsos_pdf.css')],
        font_config=font_config
    )
    
    return pdf_bytes
```

### PDF Features
- Professional styling
- Page breaks and headers
- Watermarks
- Attribution footers
- Table formatting
- Chart integration

---

## Performance Characteristics

### Response Times
- `reports.render_pdf`: ~3-10 seconds (template dependent)
- `reports.export_csv`: ~1-3 seconds
- `reports.export_excel`: ~2-5 seconds (future)

### PDF Generation Complexity
- Simple reports: ~3 seconds
- Complex reports with charts: ~10 seconds
- Large portfolios: ~15+ seconds

### Caching Strategy
- Generated PDFs: 1 hour TTL
- Template rendering: 30 minutes TTL
- Rights checks: 15 minutes TTL

---

## Error Handling

### PDF Generation Failures
```python
try:
    pdf_data = await self._generate_pdf(html_content)
except WeasyPrintError as e:
    logger.error(f"WeasyPrint error: {e}")
    return {
        "error": "PDF generation failed",
        "fallback": "CSV export available"
    }
except TemplateError as e:
    logger.error(f"Template error: {e}")
    return {
        "error": "Report template error",
        "suggestion": "Contact support"
    }
```

### Common Error Scenarios
- Template rendering errors
- WeasyPrint failures
- Rights permission denied
- Large file generation timeout

---

## Security and Compliance

### Data Protection
- Rights-based data filtering
- Watermarking for traceability
- Attribution requirements
- Audit logging

### Watermarking
```python
async def _add_watermark(self, pdf_data: bytes, user_id: UUID, asof_date: date) -> bytes:
    """Add watermark and attribution to PDF."""
    
    watermark_info = {
        "user_id": str(user_id),
        "generated_at": asof_date.isoformat(),
        "system": "DawsOS Portfolio Intelligence",
        "rights": "Confidential - Internal Use Only"
    }
    
    # Add watermark to PDF
    watermarked_pdf = await self._apply_watermark(pdf_data, watermark_info)
    
    return watermarked_pdf
```

---

## Future Enhancements

### Planned Capabilities
- Interactive PDF reports
- Custom report templates
- Scheduled report generation
- Multi-format exports

### Performance Improvements
- Parallel PDF generation
- Advanced caching
- Template optimization
- Batch processing

---

## Testing

### Test Coverage Needed
- Unit tests for PDF generation
- Integration tests with WeasyPrint
- Rights enforcement tests
- Template rendering tests

### Test Files to Create
- `backend/tests/unit/test_reports_agent.py`
- `backend/tests/integration/test_pdf_generation.py`
- `backend/tests/golden/test_report_outputs.py`

---

## Configuration

### Environment Variables
- `WEASYPRINT_CACHE_SIZE` - PDF cache size
- `PDF_GENERATION_TIMEOUT` - Maximum generation time
- `WATERMARK_ENABLED` - Enable watermarking

### WeasyPrint Configuration
```python
WEASYPRINT_CONFIG = {
    "base_url": "backend/templates/",
    "encoding": "utf-8",
    "optimize_images": True,
    "jpeg_quality": 95
}
```

---

## Monitoring and Observability

### Key Metrics
- PDF generation success rate
- Average generation time
- Rights check success rate
- Template rendering performance

### Logging
- PDF generation logs
- Rights check logs
- Template rendering logs
- Error logs with context

### Health Checks
- WeasyPrint availability
- Template system health
- Rights system health
- Service response times
