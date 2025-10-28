# PDF Reports Agent - Implementation Specification

**Agent Type**: PDF_REPORTS_AGENT  
**Priority**: P0 (Critical)  
**Estimated Time**: 16 hours  
**Status**: 🚧 Ready for Implementation  

---

## Mission

Complete the PDF reports implementation by integrating WeasyPrint with the existing reports service, implementing rights-enforced exports with proper attribution footers, and ensuring compliance with provider licensing requirements.

---

## Current State Analysis

### ✅ What's Already Implemented
- **Reports Service**: `backend/app/services/reports.py` exists with placeholder implementation
- **Rights Registry**: `backend/app/core/rights_registry.py` implemented with enforcement hooks
- **WeasyPrint**: Already installed in requirements.txt
- **Template Structure**: Basic HTML template framework exists

### ⚠️ What Needs Implementation
- **WeasyPrint Integration**: Replace placeholder text with actual PDF generation
- **HTML Templates**: Create professional portfolio report templates
- **Rights Enforcement**: Wire rights registry to block restricted exports
- **Attribution Footers**: Add provider attribution requirements
- **Error Handling**: Graceful degradation for missing dependencies

---

## Implementation Tasks

### Task 1: Complete WeasyPrint Integration (6 hours)

**File**: `backend/app/services/reports.py`

**Current State**:
```python
async def render_pdf(self, template_name: str, data: Dict[str, Any]) -> bytes:
    """Render PDF from template and data."""
    # TODO: Implement WeasyPrint integration
    return b"PDF placeholder - WeasyPrint integration pending"
```

**Target Implementation**:
```python
async def render_pdf(self, template_name: str, data: Dict[str, Any]) -> bytes:
    """Render PDF from template and data."""
    try:
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
        
        # Load template
        template_path = f"backend/templates/{template_name}.html"
        with open(template_path, 'r') as f:
            html_content = f.read()
        
        # Render with Jinja2
        template = self.jinja_env.from_string(html_content)
        rendered_html = template.render(**data)
        
        # Generate PDF
        font_config = FontConfiguration()
        html_doc = HTML(string=rendered_html)
        pdf_bytes = html_doc.write_pdf(font_config=font_config)
        
        return pdf_bytes
        
    except ImportError:
        raise ServiceError("WeasyPrint not available. Install with: pip install weasyprint")
    except Exception as e:
        raise ServiceError(f"PDF generation failed: {str(e)}")
```

### Task 2: Create HTML Templates (4 hours)

**Files to Create**:
- `backend/templates/portfolio_report.html`
- `backend/templates/holding_report.html`
- `backend/templates/macro_report.html`
- `backend/static/css/report_styles.css`

**Template Requirements**:
- Professional DawsOS dark theme
- Responsive design for print
- Provider attribution footers
- Pricing pack provenance
- Ledger commit hash
- Rights compliance notices

**Example Structure**:
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>DawsOS Portfolio Report</title>
    <link rel="stylesheet" href="static/css/report_styles.css">
</head>
<body>
    <header class="report-header">
        <h1>DawsOS Portfolio Intelligence Report</h1>
        <div class="provenance">
            <span>Pack: {{ pricing_pack_id }}</span>
            <span>Ledger: {{ ledger_commit_hash }}</span>
            <span>Generated: {{ generated_at }}</span>
        </div>
    </header>
    
    <main class="report-content">
        <!-- Portfolio overview -->
        <!-- Holdings table -->
        <!-- Performance metrics -->
        <!-- Risk analysis -->
    </main>
    
    <footer class="report-footer">
        <div class="attributions">
            {% for provider in data_sources %}
            <p>{{ provider.attribution }}</p>
            {% endfor %}
        </div>
        <div class="rights-notice">
            <p>This report contains data subject to licensing restrictions. 
               Redistribution prohibited without proper authorization.</p>
        </div>
    </footer>
</body>
</html>
```

### Task 3: Wire Rights Enforcement (3 hours)

**File**: `backend/app/services/reports.py`

**Integration Points**:
1. **Pre-export Check**: Validate provider permissions before PDF generation
2. **Attribution Injection**: Add required attribution footers
3. **Watermarking**: Add watermarks for restricted content
4. **Blocking**: Prevent export if rights not satisfied

**Implementation**:
```python
async def generate_portfolio_report(
    self, 
    portfolio_id: UUID, 
    pricing_pack_id: str,
    user_context: RequestCtx
) -> bytes:
    """Generate portfolio PDF report with rights enforcement."""
    
    # 1. Gather data and identify providers
    portfolio_data = await self._gather_portfolio_data(portfolio_id, pricing_pack_id)
    providers_used = self._identify_providers(portfolio_data)
    
    # 2. Check rights
    rights_registry = get_rights_registry()
    export_allowed = await rights_registry.check_export_permission(
        providers=providers_used,
        export_type="pdf",
        user_context=user_context
    )
    
    if not export_allowed:
        raise RightsViolationError(
            "Export blocked: Insufficient rights for providers used in this report"
        )
    
    # 3. Add attributions
    portfolio_data["attributions"] = [
        rights_registry.get_attribution(provider) 
        for provider in providers_used
    ]
    
    # 4. Generate PDF
    pdf_bytes = await self.render_pdf("portfolio_report", portfolio_data)
    
    # 5. Log export for audit
    await self._log_export_audit(portfolio_id, providers_used, user_context)
    
    return pdf_bytes
```

### Task 4: Error Handling & Graceful Degradation (2 hours)

**Scenarios to Handle**:
- WeasyPrint not installed
- Template files missing
- Font loading failures
- Memory constraints
- Rights violations

**Implementation**:
```python
class ReportsService:
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.weasyprint_available = self._check_weasyprint()
        self.jinja_env = self._setup_jinja()
    
    def _check_weasyprint(self) -> bool:
        """Check if WeasyPrint is available."""
        try:
            import weasyprint
            return True
        except ImportError:
            logger.warning("WeasyPrint not available. PDF exports will return placeholder.")
            return False
    
    async def render_pdf(self, template_name: str, data: Dict[str, Any]) -> bytes:
        """Render PDF with graceful degradation."""
        if not self.weasyprint_available:
            return self._generate_placeholder_pdf(template_name, data)
        
        try:
            return await self._render_with_weasyprint(template_name, data)
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            return self._generate_error_pdf(str(e))
```

### Task 5: Integration Testing (1 hour)

**Test Cases**:
- PDF generation with valid data
- Rights enforcement blocking
- Graceful degradation without WeasyPrint
- Template rendering with various data types
- Attribution footer generation
- Error handling scenarios

---

## Integration Points

### Agent Registration
**File**: `backend/app/api/executor.py`

Add to agent registration:
```python
from backend.app.agents.reports_agent import ReportsAgent

reports_agent = ReportsAgent("reports", services)
_agent_runtime.register_agent(reports_agent)
```

### Pattern Integration
**File**: `patterns/export_portfolio_report.json`

Update pattern to use new PDF generation:
```json
{
  "id": "export_portfolio_report",
  "name": "Export Portfolio Report",
  "category": "reports",
  "steps": [
    {"capability": "reports.generate_portfolio_pdf", "as": "pdf_report"}
  ],
  "outputs": ["pdf_report"]
}
```

### API Endpoint
**File**: `backend/app/api/routes/reports.py`

Create endpoint for PDF downloads:
```python
@app.post("/api/reports/portfolio/{portfolio_id}/pdf")
async def download_portfolio_report(
    portfolio_id: UUID,
    user: User = Depends(get_current_user)
):
    """Download portfolio report as PDF."""
    reports_service = get_reports_service()
    pdf_bytes = await reports_service.generate_portfolio_report(
        portfolio_id=portfolio_id,
        pricing_pack_id=user.pricing_pack_id,
        user_context=user
    )
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=portfolio_{portfolio_id}.pdf"}
    )
```

---

## Success Criteria

### Functional Requirements
- [ ] PDF generation works with WeasyPrint
- [ ] Rights enforcement blocks restricted exports
- [ ] Attribution footers appear correctly
- [ ] Templates render professional reports
- [ ] Graceful degradation without WeasyPrint

### Technical Requirements
- [ ] Error handling covers all failure modes
- [ ] Memory usage stays within limits
- [ ] PDF generation completes in <5 seconds
- [ ] Templates are maintainable and extensible
- [ ] Integration tests pass

### Compliance Requirements
- [ ] Provider attributions match licensing terms
- [ ] Rights violations are properly logged
- [ ] Export audit trail is complete
- [ ] Watermarking works for restricted content

---

## Dependencies

### External Libraries
- **WeasyPrint**: Already installed
- **Jinja2**: Already installed
- **Pillow**: Already installed

### Internal Services
- **Rights Registry**: Already implemented
- **Pricing Service**: For pack data
- **Ledger Service**: For audit trail
- **Auth Service**: For user context

---

## Risk Mitigation

### Technical Risks
- **WeasyPrint Installation**: Provide clear installation instructions
- **Font Issues**: Use web-safe fonts as fallbacks
- **Memory Usage**: Implement streaming for large reports
- **Template Complexity**: Start simple, iterate

### Compliance Risks
- **Rights Violations**: Comprehensive testing of enforcement
- **Attribution Errors**: Validate against provider requirements
- **Audit Gaps**: Ensure complete logging

---

## Next Steps

1. **Start with WeasyPrint Integration**: Get basic PDF generation working
2. **Create Simple Template**: Portfolio overview with basic styling
3. **Add Rights Enforcement**: Wire existing rights registry
4. **Expand Templates**: Add more report types
5. **Comprehensive Testing**: Cover all scenarios

---

**Estimated Completion**: 16 hours  
**Priority**: P0 (Critical for production)  
**Dependencies**: None (all services available)  
**Risk Level**: Low (well-defined scope, existing infrastructure)
