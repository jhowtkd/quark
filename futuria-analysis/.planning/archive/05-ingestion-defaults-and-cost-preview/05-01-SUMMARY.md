---
phase: 05
plan: 01
status: complete
completed: 2026-04-20
---

# Plan 05-01 Summary: Ingestion Defaults and Cost Preview

## What Was Built

### Backend
1. **Chunk defaults reduced** to 300/30 in `backend/app/config.py`
2. **Legacy normalization** in `backend/app/models/project.py` — persisted 500/50 values are auto-converted to 300/30 on load
3. **Cost preview endpoint** — `POST /api/graph/build?preview=true` returns chunk count, byte estimate, credit estimate, and warning level without creating tasks or calling Zep
4. **Build gate** — confirmed builds still follow the existing async task lifecycle
5. **Ontology response enrichment** — `generate_ontology` now includes `chunk_size` and `chunk_overlap` in the response

### Frontend
1. **Preview card** in `Step1GraphBuild.vue` shows chunk count, bytes, credits, and warning state
2. **Override controls** for chunk size and overlap
3. **Confirm button** only enables after successful preview and valid ontology guardrails
4. **Stale preview clearing** — changing chunk settings resets the preview
5. **Portuguese labels** added to `locales/pt.json`

### Tests
- `test_graph_chunk_defaults.py` — 3 tests covering defaults and legacy normalization
- `test_graph_cost_preview.py` — 4 tests covering preview math, warning thresholds, overrides, and no-api-key behavior
- `test_graph_safety.py` — 2 tests covering preview non-mutation and confirmed build task creation

## Key Files Changed
- `backend/app/config.py`
- `backend/app/models/project.py`
- `backend/app/api/graph.py`
- `backend/app/services/text_processor.py`
- `frontend/src/views/MainView.vue`
- `frontend/src/components/Step1GraphBuild.vue`
- `locales/pt.json`
- `backend/tests/services/test_graph_chunk_defaults.py`
- `backend/tests/services/test_graph_cost_preview.py`
- `backend/tests/services/test_graph_safety.py`

## Verification
- Backend tests: 9/9 passed
- Frontend build: passed
- Preview does not create tasks or call Zep
- Confirmed builds follow existing lifecycle

## Issues Encountered
None.
