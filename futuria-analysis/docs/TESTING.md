# Testing

## Current test setup

The committed automated test suite is backend-focused and uses `pytest` from `backend/tests/`.

There is **no root `npm test` script** in the current `package.json`.

## Automated checks

### Backend pytest

Run from `backend/`:

```bash
uv run pytest
```

If your environment does not already have the optional dev dependencies synced, install them first:

```bash
uv sync --extra dev
```

### Frontend build check

From the repo root:

```bash
npm run build
```

This builds the frontend production bundle through Vite.

### Reporting contamination checks

From the repo root:

```bash
npm run preflight
```

That runs:

- `npm run check:language-backend`
- `npm run check:language-artifacts`

These checks matter if you touch reporting, persisted report artifacts, or language-integrity tooling.

## Backend test coverage areas

The backend test tree currently covers:

- app/health + observability wiring
- Langfuse config/client behavior
- fallback connector routing
- graph cost preview, chunk defaults, guardrails, rebuild skip, safety, deduplication, incremental behavior
- deep research start/status/result flows
- research approval / rejection / rerun / promote / create-project flows
- simulation manager / runner / IPC observability
- report-agent observability
- LLM client observability

Representative files include:

- `backend/tests/test_app_observability.py`
- `backend/tests/services/test_deep_research_api.py`
- `backend/tests/services/test_research_approval.py`
- `backend/tests/services/test_graph_cost_preview.py`
- `backend/tests/services/test_graph_incremental.py`
- `backend/tests/services/test_report_agent_observability.py`

## Suggested verification by change type

### Frontend-only changes

Run:

```bash
npm run build
```

Then manually verify the affected route in the browser.

### Backend API or service changes

Run:

```bash
cd backend && uv run pytest
```

Add or update tests close to the changed behavior when practical.

### Reporting / contamination / persisted artifact changes

Run:

```bash
npm run preflight
```

### Docker or deploy-shape changes

At minimum, verify:

```bash
npm run build
cd backend && uv run pytest
```

## Manual smoke checklist

Use this when the change affects runtime behavior across the stack:

- [ ] frontend loads at `http://localhost:4000`
- [ ] backend health responds at `http://localhost:5001/health`
- [ ] route guards still behave as expected for login/register/home/workflow routes
- [ ] project load and graph workbench open without frontend crashes
- [ ] graph preview/build workflow still works for the touched scenario
- [ ] simulation preparation still returns status updates
- [ ] report generation/retrieval still works if report code changed
- [ ] interaction view still loads if report/simulation graph context changed

## Notes on auth verification

Because the committed auth client is a localStorage stub, auth testing currently means verifying frontend guard behavior rather than a real backend auth exchange.
