# API Management Analysis & Recommended Fixes

**Date:** January 14, 2025
**Status:** Analysis from Replit Agent + Recommended Implementation
**Priority:** HIGH - Critical gaps in API key management and provider initialization

---

## Executive Summary

**Replit Agent Assessment:** B+ (Good with Important Gaps)

**Key Strengths:**
- ✅ Excellent provider facade pattern with retry logic
- ✅ Proper rate limiting per provider
- ✅ Circuit breaker implementation
- ✅ Provider rights tracking

**Critical Gaps:**
- 🔴 Inconsistent API key loading (3 different patterns)
- 🔴 No centralized provider registry (new instances everywhere)
- 🔴 No startup validation (fails at runtime)
- 🟡 Scattered provider initialization
- 🟡 No connection pooling

---

## Critical Finding 1: Inconsistent API Key Loading

### Current State (3 Different Patterns)

**Pattern 1: Direct os.getenv() - Most Common ✅**
```python
# backend/app/integrations/fmp_provider.py
api_key = os.getenv("FMP_API_KEY")

# backend/app/integrations/fred_provider.py
api_key = os.getenv("FRED_API_KEY")

# backend/app/integrations/polygon_provider.py
api_key = os.getenv("POLYGON_API_KEY")
```

**Pattern 2: Error dict return (DataHarvester)**
```python
# backend/app/agents/data_harvester.py:2534
api_key = os.getenv("FMP_API_KEY")
if not api_key:
    result = {"error": "FMP_API_KEY not configured"}
    # Returns error dict instead of raising exception
```

**Pattern 3: Empty string default (Claude)**
```python
# backend/app/agents/claude_agent.py:71
self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
# Uses empty string as default instead of None
```

### Impact

**Problems:**
- ⚠️ Silent failures when API keys missing
- ⚠️ Inconsistent error handling (sometimes dict, sometimes exception, sometimes continues)
- ⚠️ Hard to debug in production ("which key is missing?")
- ⚠️ Some code continues with empty string, fails later

**Example Failure Scenario:**
```python
# User tries to fetch dividends
api_key = os.getenv("FMP_API_KEY")  # Returns None
if not api_key:
    return {"error": "FMP_API_KEY not configured"}  # Error dict

# Later code expects exception or valid data, gets error dict
# Causes type errors when trying to process results
```

### Recommended Fix: Standardized API Key Loading

**Create:** `backend/app/core/config.py`

```python
"""
DawsOS Configuration Management
Centralizes API key loading with proper validation
"""

import os
from typing import Optional
from enum import Enum


class APIKeyRequirement(Enum):
    """Classification of API key requirements"""
    REQUIRED = "required"  # App won't start without it
    OPTIONAL = "optional"  # Feature disabled if missing
    DEPRECATED = "deprecated"  # Being phased out


class ConfigurationError(Exception):
    """Raised when required configuration is missing"""
    pass


def get_api_key(
    key_name: str,
    requirement: APIKeyRequirement = APIKeyRequirement.REQUIRED,
    service_name: str = None
) -> Optional[str]:
    """
    Get API key from environment (Replit Secrets).

    Centralizes API key loading with consistent error handling.

    Args:
        key_name: Name of environment variable (e.g., "FMP_API_KEY")
        requirement: Whether key is required, optional, or deprecated
        service_name: Human-readable service name for error messages

    Returns:
        API key value or None (if optional and missing)

    Raises:
        ConfigurationError: If required key not found

    Examples:
        >>> # Required key (raises if missing)
        >>> fmp_key = get_api_key("FMP_API_KEY", APIKeyRequirement.REQUIRED, "Financial Modeling Prep")

        >>> # Optional key (returns None if missing)
        >>> news_key = get_api_key("NEWSAPI_KEY", APIKeyRequirement.OPTIONAL, "NewsAPI")
        >>> if news_key:
        >>>     # Feature available
        >>> else:
        >>>     # Feature disabled gracefully
    """
    value = os.getenv(key_name)
    service_display = service_name or key_name

    if requirement == APIKeyRequirement.REQUIRED and not value:
        raise ConfigurationError(
            f"Required API key '{key_name}' not found in environment.\n"
            f"Service: {service_display}\n"
            f"Action: Add '{key_name}' to Replit Secrets or environment variables."
        )

    if requirement == APIKeyRequirement.DEPRECATED and value:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"API key '{key_name}' is deprecated and will be removed in future version. "
            f"Service: {service_display}"
        )

    return value


# API Key Registry
# Define all API keys used by the application

# Database (REQUIRED)
DATABASE_URL = get_api_key(
    "DATABASE_URL",
    APIKeyRequirement.REQUIRED,
    "PostgreSQL Database"
)

# Authentication (REQUIRED)
AUTH_JWT_SECRET = get_api_key(
    "AUTH_JWT_SECRET",
    APIKeyRequirement.REQUIRED,
    "JWT Authentication"
)

# Financial Data Providers (OPTIONAL - features disabled if missing)
FMP_API_KEY = get_api_key(
    "FMP_API_KEY",
    APIKeyRequirement.OPTIONAL,
    "Financial Modeling Prep"
)

FRED_API_KEY = get_api_key(
    "FRED_API_KEY",
    APIKeyRequirement.OPTIONAL,
    "Federal Reserve Economic Data (FRED)"
)

POLYGON_API_KEY = get_api_key(
    "POLYGON_API_KEY",
    APIKeyRequirement.OPTIONAL,
    "Polygon.io Market Data"
)

NEWSAPI_KEY = get_api_key(
    "NEWSAPI_KEY",
    APIKeyRequirement.OPTIONAL,
    "NewsAPI"
)

# AI Services (OPTIONAL)
ANTHROPIC_API_KEY = get_api_key(
    "ANTHROPIC_API_KEY",
    APIKeyRequirement.OPTIONAL,
    "Anthropic Claude"
)


def get_config_status() -> dict:
    """
    Get status of all configuration keys.

    Useful for health checks and debugging.

    Returns:
        Dict with key status:
        {
            "required": {"DATABASE_URL": True, "AUTH_JWT_SECRET": True},
            "optional": {"FMP_API_KEY": True, "FRED_API_KEY": False, ...},
            "missing": ["FRED_API_KEY", "NEWSAPI_KEY"]
        }
    """
    required_keys = {
        "DATABASE_URL": bool(DATABASE_URL),
        "AUTH_JWT_SECRET": bool(AUTH_JWT_SECRET)
    }

    optional_keys = {
        "FMP_API_KEY": bool(FMP_API_KEY),
        "FRED_API_KEY": bool(FRED_API_KEY),
        "POLYGON_API_KEY": bool(POLYGON_API_KEY),
        "NEWSAPI_KEY": bool(NEWSAPI_KEY),
        "ANTHROPIC_API_KEY": bool(ANTHROPIC_API_KEY)
    }

    missing = [k for k, v in {**required_keys, **optional_keys}.items() if not v]

    return {
        "required": required_keys,
        "optional": optional_keys,
        "missing": missing,
        "all_required_present": all(required_keys.values())
    }


def validate_configuration() -> None:
    """
    Validate all required configuration is present.

    Raises:
        ConfigurationError: If any required keys missing

    Should be called on application startup.
    """
    status = get_config_status()

    if not status["all_required_present"]:
        missing_required = [k for k, v in status["required"].items() if not v]
        raise ConfigurationError(
            f"Missing required configuration keys: {', '.join(missing_required)}\n"
            f"Add these to Replit Secrets or environment variables."
        )

    # Log optional keys status
    import logging
    logger = logging.getLogger(__name__)

    if status["missing"]:
        logger.warning(
            f"Optional API keys not configured (features will be disabled): "
            f"{', '.join(status['missing'])}"
        )

    logger.info("Configuration validation passed")
```

### Migration Guide

**Step 1: Update all providers to use centralized config**

```python
# OLD (in fmp_provider.py)
api_key = os.getenv("FMP_API_KEY")
if not api_key:
    raise ValueError("FMP_API_KEY not configured")

# NEW
from app.core.config import FMP_API_KEY
# That's it! Validation already done at startup
```

**Step 2: Update agents**

```python
# OLD (in data_harvester.py)
api_key = os.getenv("FMP_API_KEY")
if not api_key:
    result = {"error": "FMP_API_KEY not configured"}
    return result

# NEW
from app.core.config import FMP_API_KEY

if not FMP_API_KEY:
    # Feature disabled gracefully
    logger.warning("FMP_API_KEY not configured, dividends feature disabled")
    return {
        "dividends": [],
        "_provenance": {"type": "unavailable", "reason": "API key not configured"}
    }
```

**Step 3: Add startup validation**

```python
# backend/combined_server.py

from app.core.config import validate_configuration, get_config_status

@app.on_event("startup")
async def startup_event():
    """Application startup: validate configuration"""
    try:
        validate_configuration()
        logger.info("✅ Configuration validated successfully")

        # Log status
        status = get_config_status()
        if status["missing"]:
            logger.warning(
                f"Optional features disabled (missing API keys): "
                f"{', '.join(status['missing'])}"
            )
    except ConfigurationError as e:
        logger.error(f"❌ Configuration validation failed: {e}")
        raise  # Fail fast - don't start app with missing required config
```

---

## Critical Finding 2: No Centralized Provider Registry

### Current State: Provider Instances Everywhere

**Problem:** New provider instance created for every request

```python
# backend/app/agents/data_harvester.py:2534
async def corporate_actions_dividends(self, ...):
    api_key = os.getenv("FMP_API_KEY")
    provider = FMPProvider(api_key=api_key)  # ← New instance
    # No connection pooling, no shared rate limiter

# backend/app/agents/data_harvester.py:2658
async def corporate_actions_splits(self, ...):
    api_key = os.getenv("FMP_API_KEY")
    provider = FMPProvider(api_key=api_key)  # ← Another new instance

# backend/app/agents/data_harvester.py:2782
async def corporate_actions_earnings(self, ...):
    api_key = os.getenv("FMP_API_KEY")
    provider = FMPProvider(api_key=api_key)  # ← Yet another instance
```

**Impact:**
- ❌ No connection pooling (new HTTP client per request)
- ❌ Rate limiter state NOT shared (each instance has its own counter)
- ❌ Circuit breaker state NOT shared (provider A fails, provider B keeps trying)
- ❌ Inefficient resource usage (100s of HTTP clients created/destroyed)

**Example Problem:**
```python
# Request 1: Creates FMPProvider instance A, uses 10 rate limit tokens
# Request 2: Creates FMPProvider instance B, doesn't know about A's usage
# Request 3: Creates FMPProvider instance C, doesn't know about A or B
# Result: Rate limiter ineffective, might hit API limit and get blocked
```

### Recommended Fix: Provider Registry Singleton

**Create:** `backend/app/integrations/provider_registry.py`

```python
"""
DawsOS Provider Registry
Centralized singleton for managing external API providers
"""

import logging
from typing import Optional, Dict
from app.integrations.fmp_provider import FMPProvider
from app.integrations.fred_provider import FREDProvider
from app.integrations.polygon_provider import PolygonProvider
from app.integrations.newsapi_provider import NewsAPIProvider
from app.core.config import (
    FMP_API_KEY,
    FRED_API_KEY,
    POLYGON_API_KEY,
    NEWSAPI_KEY
)

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """
    Singleton registry for external API providers.

    Ensures:
    - Single provider instance per API (connection pooling)
    - Shared rate limiter state
    - Shared circuit breaker state
    - Efficient resource usage

    Usage:
        >>> registry = ProviderRegistry.get_instance()
        >>> fmp = registry.get_fmp_provider()
        >>> if fmp:
        >>>     dividends = await fmp.fetch_dividends(symbol)
    """

    _instance: Optional['ProviderRegistry'] = None

    def __init__(self):
        """Private constructor - use get_instance() instead"""
        if ProviderRegistry._instance is not None:
            raise RuntimeError("Use ProviderRegistry.get_instance() instead")

        # Provider instances (lazily initialized)
        self._fmp_provider: Optional[FMPProvider] = None
        self._fred_provider: Optional[FREDProvider] = None
        self._polygon_provider: Optional[PolygonProvider] = None
        self._newsapi_provider: Optional[NewsAPIProvider] = None

        logger.info("ProviderRegistry initialized")

    @classmethod
    def get_instance(cls) -> 'ProviderRegistry':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Reset singleton (useful for testing)"""
        cls._instance = None

    def get_fmp_provider(self) -> Optional[FMPProvider]:
        """
        Get FMP provider instance.

        Returns:
            FMPProvider if API key configured, None otherwise
        """
        if not FMP_API_KEY:
            logger.debug("FMP_API_KEY not configured, provider unavailable")
            return None

        if self._fmp_provider is None:
            logger.info("Initializing FMPProvider (first use)")
            self._fmp_provider = FMPProvider(api_key=FMP_API_KEY)

        return self._fmp_provider

    def get_fred_provider(self) -> Optional[FREDProvider]:
        """
        Get FRED provider instance.

        Returns:
            FREDProvider if API key configured, None otherwise
        """
        if not FRED_API_KEY:
            logger.debug("FRED_API_KEY not configured, provider unavailable")
            return None

        if self._fred_provider is None:
            logger.info("Initializing FREDProvider (first use)")
            self._fred_provider = FREDProvider(api_key=FRED_API_KEY)

        return self._fred_provider

    def get_polygon_provider(self) -> Optional[PolygonProvider]:
        """Get Polygon provider instance"""
        if not POLYGON_API_KEY:
            return None

        if self._polygon_provider is None:
            logger.info("Initializing PolygonProvider (first use)")
            self._polygon_provider = PolygonProvider(api_key=POLYGON_API_KEY)

        return self._polygon_provider

    def get_newsapi_provider(self) -> Optional[NewsAPIProvider]:
        """Get NewsAPI provider instance"""
        if not NEWSAPI_KEY:
            return None

        if self._newsapi_provider is None:
            logger.info("Initializing NewsAPIProvider (first use)")
            self._newsapi_provider = NewsAPIProvider(api_key=NEWSAPI_KEY)

        return self._newsapi_provider

    def get_provider_status(self) -> Dict[str, bool]:
        """
        Get status of all providers.

        Returns:
            Dict mapping provider name to availability:
            {"fmp": True, "fred": False, "polygon": True, "newsapi": False}
        """
        return {
            "fmp": self.get_fmp_provider() is not None,
            "fred": self.get_fred_provider() is not None,
            "polygon": self.get_polygon_provider() is not None,
            "newsapi": self.get_newsapi_provider() is not None
        }

    async def health_check(self) -> Dict[str, Dict[str, any]]:
        """
        Check health of all available providers.

        Returns:
            Dict with provider health status:
            {
                "fmp": {"available": True, "healthy": True, "rate_limit": "80/120"},
                "fred": {"available": False, "reason": "API key not configured"}
            }
        """
        results = {}

        # FMP health check
        fmp = self.get_fmp_provider()
        if fmp:
            try:
                # Simple health check - fetch a known symbol
                await fmp.fetch_quote("AAPL")
                results["fmp"] = {
                    "available": True,
                    "healthy": True,
                    "rate_limit": f"{fmp.rate_limiter.tokens}/{fmp.rate_limiter.capacity}"
                }
            except Exception as e:
                results["fmp"] = {
                    "available": True,
                    "healthy": False,
                    "error": str(e)
                }
        else:
            results["fmp"] = {"available": False, "reason": "API key not configured"}

        # FRED health check
        fred = self.get_fred_provider()
        if fred:
            # Similar health check logic
            results["fred"] = {"available": True, "healthy": True}
        else:
            results["fred"] = {"available": False, "reason": "API key not configured"}

        # Similar for other providers...

        return results


# Convenience functions for backwards compatibility
def get_fmp_provider() -> Optional[FMPProvider]:
    """Get FMP provider from registry"""
    return ProviderRegistry.get_instance().get_fmp_provider()


def get_fred_provider() -> Optional[FREDProvider]:
    """Get FRED provider from registry"""
    return ProviderRegistry.get_instance().get_fred_provider()


def get_polygon_provider() -> Optional[PolygonProvider]:
    """Get Polygon provider from registry"""
    return ProviderRegistry.get_instance().get_polygon_provider()


def get_newsapi_provider() -> Optional[NewsAPIProvider]:
    """Get NewsAPI provider from registry"""
    return ProviderRegistry.get_instance().get_newsapi_provider()
```

### Migration Guide for Provider Registry

**Step 1: Update DataHarvester agent**

```python
# OLD (backend/app/agents/data_harvester.py:2534)
async def corporate_actions_dividends(self, ctx, state, symbol, ...):
    api_key = os.getenv("FMP_API_KEY")
    if not api_key:
        return {"error": "FMP_API_KEY not configured"}

    provider = FMPProvider(api_key=api_key)  # ← New instance every call
    dividends = await provider.fetch_dividends(symbol)

# NEW
from app.integrations.provider_registry import get_fmp_provider

async def corporate_actions_dividends(self, ctx, state, symbol, ...):
    provider = get_fmp_provider()
    if not provider:
        # Graceful degradation
        return {
            "dividends": [],
            "_provenance": {"type": "unavailable", "reason": "FMP API not configured"}
        }

    dividends = await provider.fetch_dividends(symbol)  # ← Reuses singleton instance
```

**Step 2: Update all services**

```python
# OLD (backend/app/services/corporate_actions_sync.py:155)
api_key = os.getenv("FMP_API_KEY")
provider = FMPProvider(api_key=api_key)

# NEW
from app.integrations.provider_registry import get_fmp_provider

provider = get_fmp_provider()
if not provider:
    logger.warning("FMP provider unavailable, skipping sync")
    return
```

**Step 3: Add health check endpoint**

```python
# backend/app/api/health.py

from fastapi import APIRouter
from app.integrations.provider_registry import ProviderRegistry

router = APIRouter()

@router.get("/health/providers")
async def check_provider_health():
    """
    Check health of all external API providers.

    Returns:
        {
            "fmp": {"available": True, "healthy": True, "rate_limit": "80/120"},
            "fred": {"available": False, "reason": "API key not configured"},
            ...
        }
    """
    registry = ProviderRegistry.get_instance()
    return await registry.health_check()

@router.get("/health/config")
def check_config():
    """
    Check configuration status.

    Returns:
        {
            "required": {"DATABASE_URL": True, "AUTH_JWT_SECRET": True},
            "optional": {"FMP_API_KEY": True, "FRED_API_KEY": False},
            "missing": ["FRED_API_KEY"]
        }
    """
    from app.core.config import get_config_status
    return get_config_status()
```

---

## Implementation Priority

### P0 (Critical - Do Immediately)

**1. Create config.py with standardized API key loading**
- **File:** `backend/app/core/config.py`
- **Effort:** 2 hours
- **Impact:** Prevents silent failures, improves debuggability
- **Risk:** Low (backwards compatible if done right)

**2. Add startup validation**
- **File:** `backend/combined_server.py`
- **Effort:** 30 minutes
- **Impact:** Fail fast on missing required config
- **Risk:** None (only validates, doesn't change behavior)

### P1 (High Priority - This Week)

**3. Create provider_registry.py**
- **File:** `backend/app/integrations/provider_registry.py`
- **Effort:** 3 hours
- **Impact:** Connection pooling, shared rate limiting, efficiency
- **Risk:** Medium (requires testing all provider usage)

**4. Migrate DataHarvester agent to use registry**
- **File:** `backend/app/agents/data_harvester.py`
- **Effort:** 2 hours
- **Impact:** Most frequent provider usage
- **Risk:** Medium (high-traffic code path)

**5. Add health check endpoint**
- **File:** `backend/app/api/health.py`
- **Effort:** 1 hour
- **Impact:** Operational visibility
- **Risk:** None (new endpoint)

### P2 (Medium Priority - Next Sprint)

**6. Migrate all services to use registry**
- **Files:** `backend/app/services/*.py`
- **Effort:** 4 hours
- **Impact:** Complete provider consolidation
- **Risk:** Low (less frequent usage)

**7. Update tests to use registry**
- **Files:** `backend/tests/*.py`
- **Effort:** 2 hours
- **Impact:** Test consistency
- **Risk:** None (test-only)

---

## Testing Strategy

### Unit Tests

**Test config.py:**
```python
# backend/tests/test_config.py

import pytest
from app.core.config import get_api_key, APIKeyRequirement, ConfigurationError

def test_required_key_missing(monkeypatch):
    """Test that required key raises exception when missing"""
    monkeypatch.delenv("TEST_KEY", raising=False)

    with pytest.raises(ConfigurationError) as exc_info:
        get_api_key("TEST_KEY", APIKeyRequirement.REQUIRED, "Test Service")

    assert "TEST_KEY" in str(exc_info.value)
    assert "Test Service" in str(exc_info.value)

def test_optional_key_missing(monkeypatch):
    """Test that optional key returns None when missing"""
    monkeypatch.delenv("TEST_KEY", raising=False)

    result = get_api_key("TEST_KEY", APIKeyRequirement.OPTIONAL)
    assert result is None

def test_required_key_present(monkeypatch):
    """Test that required key returns value when present"""
    monkeypatch.setenv("TEST_KEY", "test-value-123")

    result = get_api_key("TEST_KEY", APIKeyRequirement.REQUIRED)
    assert result == "test-value-123"
```

**Test provider_registry.py:**
```python
# backend/tests/test_provider_registry.py

import pytest
from app.integrations.provider_registry import ProviderRegistry, get_fmp_provider

def test_singleton_pattern():
    """Test that get_instance() returns same instance"""
    registry1 = ProviderRegistry.get_instance()
    registry2 = ProviderRegistry.get_instance()

    assert registry1 is registry2

def test_get_fmp_provider_with_key(monkeypatch):
    """Test FMP provider created when key present"""
    monkeypatch.setenv("FMP_API_KEY", "test-key")
    ProviderRegistry.reset_instance()  # Reset for clean test

    provider = get_fmp_provider()
    assert provider is not None
    assert provider.api_key == "test-key"

def test_get_fmp_provider_without_key(monkeypatch):
    """Test FMP provider returns None when key missing"""
    monkeypatch.delenv("FMP_API_KEY", raising=False)
    ProviderRegistry.reset_instance()

    provider = get_fmp_provider()
    assert provider is None

def test_provider_reuse():
    """Test that same provider instance returned on multiple calls"""
    registry = ProviderRegistry.get_instance()

    provider1 = registry.get_fmp_provider()
    provider2 = registry.get_fmp_provider()

    if provider1:  # Only test if key configured
        assert provider1 is provider2
```

### Integration Tests

**Test agent with registry:**
```python
# backend/tests/test_data_harvester_integration.py

import pytest
from app.agents.data_harvester import DataHarvester
from app.integrations.provider_registry import ProviderRegistry

@pytest.mark.asyncio
async def test_dividends_with_fmp_configured(monkeypatch):
    """Test dividends fetch when FMP configured"""
    monkeypatch.setenv("FMP_API_KEY", "test-key")
    ProviderRegistry.reset_instance()

    agent = DataHarvester(services={})
    result = await agent.corporate_actions_dividends(ctx, state, symbol="AAPL")

    # Should attempt fetch (may fail if test key invalid, but shouldn't error on missing key)
    assert "dividends" in result or "error" in result

@pytest.mark.asyncio
async def test_dividends_without_fmp_configured(monkeypatch):
    """Test dividends gracefully degrades when FMP not configured"""
    monkeypatch.delenv("FMP_API_KEY", raising=False)
    ProviderRegistry.reset_instance()

    agent = DataHarvester(services={})
    result = await agent.corporate_actions_dividends(ctx, state, symbol="AAPL")

    # Should return empty list with provenance, not error
    assert result["dividends"] == []
    assert result["_provenance"]["type"] == "unavailable"
```

---

## Rollout Plan

### Week 1: Foundation

**Day 1-2: Core Infrastructure**
- Create `backend/app/core/config.py`
- Add unit tests
- Create `backend/app/integrations/provider_registry.py`
- Add unit tests

**Day 3: Startup Validation**
- Add validation to `combined_server.py`
- Test locally with missing keys
- Test on Replit with configured keys

**Day 4: Health Checks**
- Create `backend/app/api/health.py`
- Add `/health/providers` endpoint
- Add `/health/config` endpoint
- Test health checks

**Day 5: Documentation**
- Document Replit Secrets setup
- Document provider registry usage
- Create migration guide

### Week 2: Migration

**Day 1: DataHarvester Agent**
- Update all corporate_actions_* methods
- Test thoroughly (high-traffic code)
- Deploy to staging

**Day 2: Other Agents**
- Update remaining agents
- Test integration

**Day 3-4: Services**
- Update all service files
- Test corporate actions sync
- Test other background tasks

**Day 5: Cleanup**
- Remove old patterns (direct os.getenv in agents/services)
- Update tests
- Final validation

---

## Monitoring & Alerts

### Metrics to Track

**1. Provider Health:**
```python
# Emit metrics on each provider call
@provider_call_metric
async def fetch_dividends(...):
    # Track: success rate, latency, rate limit usage
```

**2. Rate Limit Usage:**
```python
# Alert when approaching limits
if rate_limiter.tokens < rate_limiter.capacity * 0.2:
    logger.warning(f"FMP rate limit usage high: {rate_limiter.tokens}/{rate_limiter.capacity}")
```

**3. Circuit Breaker Trips:**
```python
# Alert when circuit breaker opens
if circuit_breaker.is_open():
    logger.error(f"FMP circuit breaker opened after {failure_count} failures")
```

### Dashboards

**Provider Health Dashboard:**
- Availability: % time each provider available
- Latency: P50, P95, P99 per provider
- Error Rate: % calls failing per provider
- Rate Limit: Current usage vs capacity

---

## Replit Secrets Configuration

### Required Secrets (App won't start)

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Authentication
AUTH_JWT_SECRET=<generate-random-256-bit-key>
```

### Optional Secrets (Features disabled if missing)

```bash
# Financial data providers
FMP_API_KEY=<your-fmp-api-key>           # Financial Modeling Prep
FRED_API_KEY=<your-fred-api-key>         # Federal Reserve Economic Data
POLYGON_API_KEY=<your-polygon-api-key>   # Polygon.io

# News & AI
NEWSAPI_KEY=<your-newsapi-key>           # NewsAPI
ANTHROPIC_API_KEY=<your-anthropic-key>   # Claude AI
```

### How to Add Secrets on Replit

1. Open Replit project
2. Click "Secrets" icon (🔒) in left sidebar
3. Add key-value pairs:
   - Key: `FMP_API_KEY`
   - Value: `your-actual-api-key`
4. Secrets automatically loaded as environment variables
5. Access via `os.getenv("FMP_API_KEY")`

---

## Success Criteria

✅ **Configuration Management:**
- All API keys loaded through centralized `config.py`
- Startup validation prevents app from starting with missing required keys
- Clear error messages when optional keys missing

✅ **Provider Registry:**
- Single provider instance per API (connection pooling working)
- Rate limiter state shared across all requests
- Circuit breaker state shared across all requests

✅ **Health Monitoring:**
- `/health/providers` endpoint shows provider status
- `/health/config` endpoint shows configuration status
- Metrics tracked for all provider calls

✅ **Code Quality:**
- No more scattered `os.getenv()` calls
- No more inconsistent error handling
- Provider usage patterns consistent across codebase

---

**Status:** ✅ **ANALYSIS COMPLETE** - Implementation plan ready
**Estimated Effort:** 16 hours total
**Risk Level:** LOW-MEDIUM (well-defined changes, good test coverage)
**ROI:** HIGH (prevents silent failures, improves efficiency, better monitoring)

---

**Next Steps:**
1. Review this plan with team
2. Create implementation tasks in project tracker
3. Start with P0 items (config.py + startup validation)
4. Progress through P1 and P2 in order
5. Monitor metrics after deployment
