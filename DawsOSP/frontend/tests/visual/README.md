# Visual Regression Tests

**Purpose**: Detect UI regressions in Portfolio Overview using screenshot comparison
**Tool**: Playwright + Custom pixel-perfect comparison
**Updated**: 2025-10-22

---

## Overview

Visual regression tests capture screenshots of the Portfolio Overview UI and compare them against baseline images. Any pixel differences beyond the threshold indicate a visual regression.

**Benefits**:
- ✅ Detect unintended UI changes
- ✅ Validate responsive design
- ✅ Test dark mode variants
- ✅ No external service required (Percy alternative)
- ✅ CI/CD ready

---

## Installation

```bash
# Install Python dependencies
pip install playwright pixelmatch Pillow pytest

# Install Playwright browsers
playwright install chromium
```

---

## Usage

### 1. Start Streamlit App

```bash
# Terminal 1: Start UI with mock client
cd frontend
export USE_MOCK_CLIENT="true"
streamlit run ui/screens/portfolio_overview.py --server.port=8501
```

### 2. Capture Baseline Screenshots (First Run)

```bash
# Terminal 2: Capture baselines
pytest frontend/tests/visual/test_portfolio_overview_screenshots.py \
    --update-baselines \
    -v
```

**Output**:
```
test_portfolio_overview_light_mode ✅ Updated baseline: portfolio_overview_light.png
test_portfolio_overview_dark_mode ✅ Updated baseline: portfolio_overview_dark.png
test_portfolio_overview_kpi_ribbon ✅ Updated baseline: kpi_ribbon.png
test_portfolio_overview_currency_attribution ✅ Updated baseline: currency_attribution.png
test_portfolio_overview_provenance_badges ✅ Updated baseline: provenance_badges.png
test_portfolio_overview_mobile_viewport ✅ Updated baseline: portfolio_overview_mobile.png
```

**Baselines saved to**: `frontend/tests/visual/baselines/`

---

### 3. Run Visual Regression Tests

```bash
# Compare against baselines
pytest frontend/tests/visual/test_portfolio_overview_screenshots.py -v
```

**Output (No Changes)**:
```
test_portfolio_overview_light_mode ✅ Screenshots match: 0.000% pixels differ
test_portfolio_overview_dark_mode ✅ Screenshots match: 0.001% pixels differ
test_portfolio_overview_kpi_ribbon ✅ Screenshots match: 0.000% pixels differ
test_portfolio_overview_currency_attribution ✅ Screenshots match: 0.000% pixels differ
test_portfolio_overview_provenance_badges ✅ Screenshots match: 0.000% pixels differ
test_portfolio_overview_mobile_viewport ✅ Screenshots match: 0.002% pixels differ

==================== 6 passed in 12.45s ====================
```

**Output (Changes Detected)**:
```
test_portfolio_overview_light_mode ❌ Visual regression detected: 2.35% pixels differ (threshold: 0.1%)
   Diff image saved: frontend/tests/visual/diffs/portfolio_overview_light_diff.png

==================== 1 failed, 5 passed in 12.45s ====================
```

---

### 4. Review Diff Images

When a test fails, inspect the diff image:

```bash
# Open diff image
open frontend/tests/visual/diffs/portfolio_overview_light_diff.png
```

**Diff Image Format**:
- 🔴 **Red pixels**: Changed from baseline
- ⚫ **Gray pixels**: Unchanged (dimmed for clarity)

---

### 5. Update Baselines (After Intentional UI Change)

```bash
# After making intentional UI changes, update baselines
pytest frontend/tests/visual/test_portfolio_overview_screenshots.py \
    --update-baselines \
    -v
```

---

## Test Coverage

| Test | Description | Viewport | Baseline File |
|------|-------------|----------|---------------|
| `test_portfolio_overview_light_mode` | Full page (light mode) | 1920x1080 | `portfolio_overview_light.png` |
| `test_portfolio_overview_dark_mode` | Full page (dark mode) | 1920x1080 | `portfolio_overview_dark.png` |
| `test_portfolio_overview_kpi_ribbon` | KPI metrics section | 1920x200 | `kpi_ribbon.png` |
| `test_portfolio_overview_currency_attribution` | Attribution section | 1920x300 | `currency_attribution.png` |
| `test_portfolio_overview_provenance_badges` | Provenance metadata | 1920x180 | `provenance_badges.png` |
| `test_portfolio_overview_mobile_viewport` | Mobile responsive | 375x812 | `portfolio_overview_mobile.png` |

**Total**: 6 visual regression tests

---

## Configuration

### Pixel Diff Threshold

```python
# frontend/tests/visual/test_portfolio_overview_screenshots.py

# Default: 0.1% of pixels can differ
PIXEL_DIFF_THRESHOLD = 0.1
```

**Adjust threshold if**:
- Anti-aliasing causes minor pixel differences
- Dynamic content (timestamps) causes failures
- Font rendering differs across environments

---

### Viewport Sizes

```python
# Desktop
VIEWPORT = {"width": 1920, "height": 1080}

# Mobile (iPhone 11 Pro)
page.set_viewport_size({"width": 375, "height": 812})
```

---

### Base URL

```python
# Default: localhost:8501
BASE_URL = os.getenv("STREAMLIT_BASE_URL", "http://localhost:8501")
```

**CI/CD**: Set `STREAMLIT_BASE_URL` environment variable to staging URL.

---

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/visual-regression.yml
name: Visual Regression Tests

on: [pull_request]

jobs:
  visual-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r frontend/requirements.txt
          pip install playwright pixelmatch Pillow pytest
          playwright install chromium

      - name: Start Streamlit (background)
        run: |
          export USE_MOCK_CLIENT="true"
          streamlit run frontend/ui/screens/portfolio_overview.py \
            --server.port=8501 \
            --server.headless=true &
          sleep 10  # Wait for app to start

      - name: Run visual regression tests
        run: |
          pytest frontend/tests/visual/test_portfolio_overview_screenshots.py -v

      - name: Upload diff images (on failure)
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: visual-diffs
          path: frontend/tests/visual/diffs/
```

---

## Troubleshooting

### Issue: Playwright not found

**Error**:
```
ModuleNotFoundError: No module named 'playwright'
```

**Solution**:
```bash
pip install playwright
playwright install chromium
```

---

### Issue: Streamlit not running

**Error**:
```
playwright._impl._api_types.TimeoutError: Timeout 30000ms exceeded.
```

**Solution**:
Ensure Streamlit is running on http://localhost:8501:
```bash
streamlit run frontend/ui/screens/portfolio_overview.py --server.port=8501
```

---

### Issue: Tests always fail with "pixels differ"

**Possible Causes**:
1. **Font rendering differences** (macOS vs Linux)
2. **Anti-aliasing** (browser rendering)
3. **Dynamic content** (timestamps, random data)

**Solutions**:

1. **Increase threshold**:
   ```python
   PIXEL_DIFF_THRESHOLD = 0.5  # 0.5% tolerance
   ```

2. **Mock dynamic content**:
   ```python
   # Ensure mock client returns consistent data
   client = MockDawsOSClient()
   client.fixed_timestamp = True  # Use fixed timestamp
   ```

3. **Normalize fonts** (CI/CD):
   ```yaml
   # Install fonts in CI
   - name: Install fonts
     run: |
       sudo apt-get install fonts-liberation
   ```

---

### Issue: Baselines missing

**Error**:
```
FileNotFoundError: baseline not found
```

**Solution**:
Run with `--update-baselines` to create baselines:
```bash
pytest frontend/tests/visual/test_portfolio_overview_screenshots.py --update-baselines
```

---

## Best Practices

### 1. Consistent Test Data

Always use mock client with fixed data:
```bash
export USE_MOCK_CLIENT="true"
```

### 2. Update Baselines After UI Changes

After intentional UI changes, update baselines and commit to git:
```bash
pytest frontend/tests/visual/test_portfolio_overview_screenshots.py --update-baselines
git add frontend/tests/visual/baselines/
git commit -m "Update visual regression baselines"
```

### 3. Review Diff Images Before Updating

Always inspect diff images to ensure changes are intentional:
```bash
open frontend/tests/visual/diffs/*.png
```

### 4. Run Visual Tests Before PRs

Include visual regression tests in pre-commit/pre-push hooks:
```bash
# .git/hooks/pre-push
pytest frontend/tests/visual/test_portfolio_overview_screenshots.py -v
```

---

## Directory Structure

```
frontend/tests/visual/
├── README.md                           # This file
├── test_portfolio_overview_screenshots.py  # Test suite
├── baselines/                          # Baseline screenshots
│   ├── portfolio_overview_light.png
│   ├── portfolio_overview_dark.png
│   ├── kpi_ribbon.png
│   ├── currency_attribution.png
│   ├── provenance_badges.png
│   └── portfolio_overview_mobile.png
└── diffs/                              # Diff images (on failure)
    └── portfolio_overview_light_diff.png
```

---

## Comparison with Percy

| Feature | Percy (SaaS) | Playwright + Pixelmatch (Local) |
|---------|-------------|----------------------------------|
| **External Service** | Required | None |
| **Cost** | $$$ (per screenshot) | Free |
| **Setup** | Complex (API tokens) | Simple (pip install) |
| **CI/CD** | Percy integration | Standard pytest |
| **Baselines** | Cloud storage | Git repository |
| **Diff UI** | Web dashboard | Local PNG files |
| **Privacy** | Data sent to Percy | Data stays local |

**Recommendation**: Use Playwright + Pixelmatch for simplicity and cost savings.

---

## References

- [Playwright Documentation](https://playwright.dev/python/)
- [Pillow (PIL) Documentation](https://pillow.readthedocs.io/)
- [pytest Documentation](https://docs.pytest.org/)

---

**Last Updated**: 2025-10-22
**Status**: ✅ Production Ready
