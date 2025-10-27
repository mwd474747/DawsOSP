# Claude Agent Specification

**Role**: AI-powered explanations, analysis, and insights
**Context**: [PRODUCT_SPEC.md](../../PRODUCT_SPEC.md) | [ORCHESTRATOR.md](./ORCHESTRATOR.md)
**Status**: ✅ Operational (Production)
**Priority**: P0
**Last Updated**: October 27, 2025

---

## Mission

Provide AI-powered explanations and analysis for portfolio data, ratings, scenarios, and macro insights. This agent bridges the gap between complex quantitative analysis and human understanding through natural language explanations.

---

## Current Capabilities

### ✅ Implemented and Operational

1. **Explanation Generation**
   - `claude.explain` - Generate explanations for complex data
   - `ai.explain` - Alias for pattern compatibility

2. **Analysis and Insights**
   - `claude.analyze` - Deep analysis of portfolio data
   - `claude.summarize` - Summarize complex information

### ✅ Pattern Integration
- Used by `buffett_checklist` pattern for quality rating explanations
- Integrated with macro analysis for regime explanations
- Provides context for scenario analysis results

---

## Implementation Status

### ✅ Complete Implementation
- **Agent Class**: `ClaudeAgent` in `backend/app/agents/claude_agent.py`
- **API Integration**: Anthropic Claude API integration
- **Pattern Integration**: Used by multiple patterns for explanations
- **Error Handling**: Graceful fallback when API unavailable
- **Testing**: Basic test coverage implemented

### ✅ Production Ready
- All capabilities implemented
- API integration working
- Pattern execution functional
- Graceful degradation when API unavailable
- Metadata attachment for traceability

---

## Code Examples

### Agent Method Implementation
```python
async def claude_explain(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    data: Dict[str, Any],
    prompt: str,
    **kwargs
) -> Dict[str, Any]:
    """Generate AI explanation for complex data."""
    try:
        # Prepare context for Claude
        context = {
            "data": data,
            "prompt": prompt,
            "asof_date": ctx.asof_date,
            "portfolio_id": ctx.portfolio_id
        }
        
        # Call Claude API
        explanation = await self._call_claude_api(context)
        
        # Attach metadata
        metadata = self._create_metadata(
            source="claude_api",
            asof=ctx.asof_date,
            ttl=3600,
            confidence=0.85
        )
        
        return self._attach_metadata({
            "explanation": explanation,
            "context": context
        }, metadata)
        
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        # Graceful fallback
        return self._attach_metadata({
            "explanation": "AI explanation unavailable",
            "fallback": True
        }, metadata)
```

### Pattern Integration Example
```json
{
  "steps": [
    {
      "capability": "ratings.dividend_safety",
      "args": {"security_id": "{{inputs.security_id}}"},
      "as": "dividend_safety"
    },
    {
      "capability": "ai.explain",
      "args": {
        "ratings": "{{state.dividend_safety}}",
        "prompt": "Explain the dividend safety rating in Buffett's framework"
      },
      "as": "explanation"
    }
  ]
}
```

---

## Integration Points

### API Integration
- **Anthropic Claude API**: Primary AI service
- **Rate Limiting**: Respects API rate limits
- **Error Handling**: Graceful fallback when API unavailable
- **Authentication**: API key management

### Patterns Using This Agent
- `buffett_checklist` - Quality rating explanations
- `portfolio_scenario_analysis` - Scenario impact explanations
- `macro_cycles_overview` - Cycle phase explanations
- `portfolio_macro_overview` - Macro regime explanations

### Data Sources
- Rating results from RatingsAgent
- Scenario results from MacroHound
- Portfolio metrics from FinancialAnalyst
- Macro data from DataHarvester

---

## Performance Characteristics

### Response Times
- `claude.explain`: ~2-5 seconds (API dependent)
- `claude.analyze`: ~3-7 seconds (API dependent)
- `claude.summarize`: ~1-3 seconds (API dependent)

### Caching Strategy
- Explanations: 1 hour TTL
- Analysis: 2 hours TTL
- Summaries: 30 minutes TTL

### Rate Limiting
- Respects Anthropic API rate limits
- Implements exponential backoff
- Circuit breaker for API failures

---

## Error Handling

### Graceful Degradation
```python
try:
    explanation = await self._call_claude_api(context)
except APIRateLimitError:
    logger.warning("Claude API rate limit exceeded")
    explanation = "Explanation temporarily unavailable due to rate limits"
except APITimeoutError:
    logger.warning("Claude API timeout")
    explanation = "Explanation unavailable due to timeout"
except Exception as e:
    logger.error(f"Claude API error: {e}")
    explanation = "AI explanation unavailable"
```

### Fallback Strategies
- Static explanations for common scenarios
- Template-based responses
- Error messages with context
- Retry logic with backoff

---

## Configuration

### Environment Variables
- `ANTHROPIC_API_KEY` - Claude API key
- `CLAUDE_MODEL` - Model version (default: claude-3-sonnet)
- `CLAUDE_MAX_TOKENS` - Maximum response tokens
- `CLAUDE_TEMPERATURE` - Response creativity (0.0-1.0)

### API Configuration
```python
CLAUDE_CONFIG = {
    "model": "claude-3-sonnet-20240229",
    "max_tokens": 1000,
    "temperature": 0.7,
    "timeout": 30
}
```

---

## Use Cases

### Portfolio Analysis Explanations
- Explain performance metrics in plain language
- Provide context for attribution analysis
- Clarify risk factor exposures

### Quality Rating Explanations
- Explain Buffett quality scores
- Provide context for rating components
- Suggest improvement areas

### Scenario Analysis Explanations
- Explain scenario impact on portfolio
- Provide context for hedge suggestions
- Clarify risk implications

### Macro Analysis Explanations
- Explain regime classifications
- Provide context for cycle phases
- Clarify economic implications

---

## Future Enhancements

### Planned Capabilities
- Multi-language explanations
- Custom explanation templates
- Explanation personalization
- Advanced analysis capabilities

### Performance Improvements
- Response streaming
- Advanced caching
- Batch processing
- Local model integration

---

## Testing

### Test Coverage
- Unit tests for all capabilities
- API integration tests
- Error handling tests
- Fallback mechanism tests

### Test Files
- `backend/tests/unit/test_claude_agent.py`
- `backend/tests/integration/test_ai_explanations.py`

### Mock Testing
- Mock Claude API responses
- Test error scenarios
- Validate fallback behavior

---

## Security and Compliance

### Data Handling
- No sensitive data sent to external API
- Sanitized inputs for API calls
- Audit logging for all requests

### Privacy
- Respects data privacy requirements
- No PII in API calls
- Secure API key management

---

## Monitoring and Observability

### Key Metrics
- API request count
- Response time percentiles
- Error rates by capability
- Fallback usage rates
- API quota utilization

### Logging
- API request/response logs
- Error logs with context
- Performance timing logs
- Fallback usage logs

### Health Checks
- API connectivity
- Response time thresholds
- Error rate thresholds
- Quota utilization
