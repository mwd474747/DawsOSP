# ReportsAgent Methods - Quick Reference Card

## Method Signatures Quick Lookup

### 1. reports_render_pdf()
```
Location:   Lines 54-161
Signature:  async def reports_render_pdf(ctx, state, template_name="portfolio_summary", 
                                          report_data=None, portfolio_id=None, **kwargs)
Returns:    Dict[str, Any] - base64-encoded PDF + metadata
Memory:     5-10MB peak
Timeout:    None (RISK)
File I/O:   None (in-memory)
```

### 2. reports_export_csv()
```
Location:   Lines 163-252
Signature:  async def reports_export_csv(ctx, state, filename="export.csv", 
                                         data=None, providers=None, **kwargs)
Returns:    Dict[str, Any] - base64-encoded CSV + metadata
Memory:     1-5MB peak
Timeout:    None (RISK)
File I/O:   None (in-memory)
```

### 3. reports_export_excel()
```
Location:   Lines 254-282
Signature:  async def reports_export_excel(ctx, state, filename="export.xlsx", **kwargs)
Returns:    Dict[str, Any] - {"status": "not_implemented", ...}
Memory:     N/A (stub)
Timeout:    N/A (stub)
File I/O:   N/A (stub)
Status:     Future implementation (Week 5)
```

---

## Return Keys by Method

### PDF Success
```python
{
    "pdf_base64": str,           # Base64 PDF bytes
    "size_bytes": int,           # Original size
    "attributions": [str],       # Provider attributions
    "watermark_applied": bool,   # Watermark flag
    "template_name": str,        # Template used
    "providers": [str],          # Detected providers
    "download_filename": str,    # Suggested filename
    "status": "success",
    "generated_at": str,         # ISO timestamp
    "_metadata": {...}           # Agent metadata
}
```

### CSV Success
```python
{
    "csv_base64": str,           # Base64 CSV bytes
    "size_bytes": int,
    "attributions": [str],
    "filename": str,
    "providers": [str],
    "download_filename": str,
    "status": "success",
    "generated_at": str,
    "_metadata": {...}
}
```

### Any Error
```python
{
    "status": "error",
    "error": str,                # Exception message
    "pdf_base64" or "csv_base64": None,
    # Note: No _metadata in error case
}
```

---

## Service Dependency Chain

```
ReportsAgent.reports_render_pdf()
    ↓
ReportService.render_pdf()
    ├── RightsRegistry.ensure_allowed()       [may raise RightsViolationError]
    ├── Jinja2.render(template_name)         [may raise FileNotFoundError]
    ├── WeasyPrint.HTML(string=...).write_pdf()  [in-memory PDF generation]
    └── Returns: bytes (PDF or HTML fallback)

ReportsAgent.reports_export_csv()
    ↓
ReportService.generate_csv()
    ├── RightsRegistry.check_export()        [returns result, doesn't raise]
    ├── csv.writer(io.StringIO)              [in-memory buffer]
    ├── flatten_dict() recursively           [May cause stack overflow]
    └── Returns: bytes (UTF-8 CSV)
```

---

## Input Validation Checklist

### PDF Method
- [ ] template_name: No validation (fallback HTML used if missing)
- [ ] report_data: No field validation
- [ ] portfolio_id: No validation
- [ ] ctx: Assumed valid RequestCtx
- [ ] Risk: Invalid template silently uses fallback HTML

### CSV Method
- [ ] filename: No sanitization (RISK for disk writes)
- [ ] data: No structure validation (circular refs not caught)
- [ ] providers: Optional (auto-detected if None)
- [ ] Risk: Filename injection if later written to disk

### Excel Method
- [ ] filename: Not validated (N/A - stub)

---

## Memory Impact Estimation

### PDF Generation Example: 1MB Portfolio Report
```
State dict:          500KB
Metadata additions:  50KB
Jinja2 expansion:    1.5MB (3x data size)
Final PDF:           400KB
Base64 encoded:      533KB (1.33x original)
Total peak:          2.5MB
```

### CSV Generation Example: 500KB Holdings Data
```
State dict:          500KB
Flattening (nested): 1.2MB (2.4x original - many rows)
Final CSV:           800KB
Base64 encoded:      1.06MB
Total peak:          2.3MB
```

---

## Error Scenarios & Handling

### PDF Generation
| Scenario | Exception | Caught As | Result |
|----------|-----------|-----------|--------|
| Missing template | FileNotFoundError | Exception | Returns fallback HTML |
| Blocked by rights | RightsViolationError | Exception | Generic "PDF generation failed" |
| WeasyPrint error | RuntimeError | Exception | Generic error message |
| Large PDF | MemoryError | Exception | Service crashes (NO LIMIT) |
| HTML rendering | TemplateError | Exception | Generic error message |

### CSV Generation
| Scenario | Exception | Caught As | Result |
|----------|-----------|-----------|--------|
| Circular reference | RecursionError | Exception | "CSV generation failed" |
| Blocked by rights | RightsViolationError | Exception | Generic error message |
| Malformed data | AttributeError | Exception | Generic error message |
| Large CSV | MemoryError | Exception | Service crashes (NO LIMIT) |

---

## Critical Risks Summary

### HIGH (Need Immediate Fix)
1. **No timeout protection** - PDF generation can hang indefinitely
2. **No file size limits** - 100MB+ PDFs can exhaust memory
3. **Inconsistent error handling** - Rights violations not clearly distinguished

### MEDIUM (Consolidation Opportunity)
4. **Code duplication** - PDF/CSV have nearly identical structure
5. **Weak input validation** - filename not sanitized, data not validated
6. **Single ReportService per call** - No connection pooling/singleton pattern

### LOW (Monitor)
7. **Base64 overhead** - 33% size increase acceptable
8. **Template fallback** - Silent fallback may hide issues
9. **Provider auto-detection** - Heuristic-based, may miss providers

---

## Week 5 Migration Checklist

- [ ] Create DataHarvester class with unified interface
- [ ] Add size limits (PDF 50MB, CSV 10MB, Excel 20MB)
- [ ] Add asyncio.wait_for() timeout wrapper (30s)
- [ ] Implement ResourceGuard for memory monitoring
- [ ] Convert to return raw bytes (not base64) - let HTTP layer encode
- [ ] Use singleton ReportService instance
- [ ] Add observability metrics (duration, memory, size)
- [ ] Update all API endpoints to use DataHarvester
- [ ] Deprecate ReportsAgent methods
- [ ] Run A/B tests for week 1
- [ ] Full cutover by end of week 5

---

## File Locations Reference

```
reports_agent.py         /backend/app/agents/reports_agent.py
reports.py              /backend/app/services/reports.py
rights_registry.py      /backend/app/services/rights_registry.py
base_agent.py          /backend/app/agents/base_agent.py
RequestCtx             /backend/app/core/types.py
RightsRegistry         /backend/app/services/rights_registry.py
```

---

## Key Code Patterns to Preserve

### Metadata Attachment (lines 144-150 in PDF)
```python
metadata = self._create_metadata(
    source=f"report_service:{ctx.pricing_pack_id}",
    asof=ctx.asof_date,
    ttl=0,  # Point-in-time reports
)
return self._attach_metadata(result, metadata)
```

### Provider Extraction Pattern
```python
providers = report_service._extract_providers(report_data)
# Looks for: _metadata.source, _sources.prices, etc.
```

### Rights Check Pattern
```python
rights_check = report_service.registry.check_export(
    providers=providers,
    export_type="pdf",  # or "csv"
    environment=report_service.environment,
)
result["attributions"] = rights_check.attributions
```

---

Generated: 2025-11-03
Analysis Level: MEDIUM (breadth-focused, resource management emphasis)
Report Location: /REPORTS_AGENT_ANALYSIS.md
