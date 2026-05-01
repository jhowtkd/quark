<!-- generated-by: gsd-doc-writer -->

# Testing Guide

This document covers how to run and write tests for the FUTUR.IA codebase.

## Overview

The project uses a split testing stack:

- **Frontend** — [Vitest](https://vitest.dev/) with `jsdom` for unit and component tests
- **Backend** — [pytest](https://docs.pytest.org/) with `pytest-asyncio` for Python service and API tests

Tests are organized by subsystem and mirrored across the main project (`/`) and the analysis module (`futuria-analysis/`).

---

## Test Framework and Setup

### Frontend

| Dependency | Version | Purpose |
|------------|---------|---------|
| `vitest` | `^4.1.5` | Test runner |
| `@vue/test-utils` | `^2.4.9` | Vue component mounting and interaction |
| `jsdom` | `^29.1.0` | DOM environment for headless component tests |

**Configuration:** `frontend/vitest.config.js`

```js
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    globals: true,
  },
})
```

Globals are enabled, so `describe`, `it`, `expect`, and `vi` are available without importing them in test files (although many files still import explicitly for clarity).

### Backend

| Dependency | Version | Purpose |
|------------|---------|---------|
| `pytest` | `>=8.0.0` | Test runner and framework |
| `pytest-asyncio` | `>=0.23.0` | Async test support |

**Configuration:** Declared in `backend/pyproject.toml` under `[project.optional-dependencies] dev` and `[dependency-groups] dev`.

Backend tests are run with `pytest` inside the backend virtual environment managed by `uv`.

---

## Running Tests

### Frontend

From the repository root:

```bash
# Run the full frontend test suite once
cd frontend && npm test

# Watch mode (re-runs on file changes)
cd frontend && npm run test:watch

# Run a single test file
cd frontend && npx vitest run tests/composables/useSimulationMonitor.test.js

# Run tests matching a pattern
cd frontend && npx vitest run --reporter=verbose "simulation"
```

### Backend

From the repository root:

```bash
# Full backend test suite
cd backend && uv run pytest

# Run with verbose output
cd backend && uv run pytest -v

# Run a single test file
cd backend && uv run pytest tests/connectors/test_fallback_router.py -v

# Run a single test class or method
cd backend && uv run pytest tests/connectors/test_fallback_router.py::TestFallbackRouterBehavior -v
cd backend && uv run pytest tests/connectors/test_fallback_router.py::TestFallbackRouterBehavior::test_skips_brave_when_key_unset -v

# Run tests by directory
cd backend && uv run pytest tests/services/ -v
cd backend && uv run pytest tests/observability/ -v

# Root-level backend tests (outside the backend/ directory)
cd tests/backend && uv run pytest
```

### Analysis Module

The `futuria-analysis/` directory contains a parallel copy of the backend and its tests. Run them the same way:

```bash
cd futuria-analysis/backend && uv run pytest
cd futuria-analysis/tests && uv run pytest
```

### Language Contamination Checks

The project includes custom Python scripts that act as policy-level tests for output language consistency:

```bash
# Check backend/reporting code for language contamination
npm run check:language-backend

# Check report artifacts for contamination
npm run check:language-artifacts

# Run all preflight checks
npm run preflight
```

---

## Writing New Tests

### Frontend

**File naming:** `*.test.js`

**Location conventions:**

| What you're testing | Where to put the test |
|---------------------|-----------------------|
| Vue composables | `frontend/tests/composables/` |
| Vue components | `frontend/tests/components/<Subsystem>/` |
| Shared mocks | `frontend/tests/mocks/` |

**Example pattern (composable test):**

```js
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref, toRef, defineComponent, h, nextTick } from 'vue'

vi.mock('../../src/api/someModule.js', () => ({
  someApiCall: vi.fn(),
}))

const TestComponent = defineComponent({
  props: ['someId'],
  setup(props) {
    const result = useSomeComposable(toRef(props, 'someId'))
    return { result }
  },
  render() { return h('div') },
})

describe('useSomeComposable', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should behave correctly', async () => {
    // arrange
    // act
    // assert
  })
})
```

**Key patterns used:**
- `vi.mock()` for module-level API mocking
- `vi.useFakeTimers()` / `vi.useRealTimers()` for timer control
- `mount()` from `@vue/test-utils` to instantiate composables inside test components
- `nextTick()` to flush Vue reactivity updates before assertions

### Backend

**File naming:** `test_*.py`

**Location conventions:**

| What you're testing | Where to put the test |
|---------------------|-----------------------|
| App-level observability | `backend/tests/test_app_observability.py` |
| Connectors | `backend/tests/connectors/` |
| Configuration | `backend/tests/config/` |
| Observability / Langfuse | `backend/tests/observability/` |
| Services | `backend/tests/services/` |
| Utilities | `backend/tests/utils/` |

**Example pattern (service test with patching):**

```python
import pytest
from unittest.mock import patch, MagicMock

from app.connectors.base import Connector, ConnectorResult
from app.connectors.fallback_router import ConnectorFallbackRouter


class TestMyServiceBehavior:
    def test_does_something_when_condition(self):
        with patch("app.services.my_service.Config") as mock_config:
            mock_config.SOME_KEY = "value"
            result = my_service.do_work()
            assert result.success is True
```

**Key patterns used:**
- `unittest.mock.patch` for config and external service mocking
- Class-based test grouping (`class TestXxx:`) for related behavior
- Explicit docstrings on test methods describing the scenario

---

## Coverage Requirements

No explicit coverage thresholds are currently configured. There is no `.nycrc`, `c8`, or `.coveragerc` file in the repository.

If you want to generate coverage reports locally:

**Frontend:**
```bash
cd frontend && npx vitest run --coverage
```

**Backend:**
```bash
cd backend && uv run pytest --cov=app --cov-report=term-missing
```

> Note: You may need to install `pytest-cov` first (`uv add --dev pytest-cov`).

---

## CI Integration

There are no GitHub Actions workflows in this repository (`.github/workflows/` does not exist). Tests are run manually or via local scripts during development.

The closest automated quality gate is the `preflight` npm script, which runs language contamination checks before commits:

```bash
npm run preflight
```

This executes:
- `check:language-backend`
- `check:language-artifacts`

---

## Test Directories at a Glance

```
backend/tests/
├── test_app_observability.py
├── config/
├── connectors/
├── e2e/                    # Currently empty; manual E2E doc at MANUAL_E2E_TEST.md
├── observability/
├── services/
└── utils/

frontend/tests/
├── mocks/
├── composposables/
└── components/
    └── simulation/

tests/
├── backend/
├── reporting/
└── services/

futuria-analysis/tests/
├── backend/
├── reporting/
└── services/
```
