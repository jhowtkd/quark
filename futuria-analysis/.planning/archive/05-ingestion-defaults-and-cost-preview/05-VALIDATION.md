---
phase: 5
slug: ingestion-defaults-and-cost-preview
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-17
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest 8.2.0` for backend checks, `npm run build` for frontend compile validation, browser smoke for preview gate behavior |
| **Config file** | none |
| **Quick run command** | `cd backend && uv run pytest -q tests/services/test_graph_chunk_defaults.py tests/services/test_graph_cost_preview.py tests/services/test_graph_safety.py` |
| **Full suite command** | `cd backend && uv run pytest -q tests/services/test_graph_chunk_defaults.py tests/services/test_graph_cost_preview.py tests/services/test_graph_safety.py && cd ../frontend && npm run build` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && uv run pytest -q tests/services/test_graph_chunk_defaults.py tests/services/test_graph_cost_preview.py tests/services/test_graph_safety.py`
- **After every plan wave:** Run `cd backend && uv run pytest -q tests/services/test_graph_chunk_defaults.py tests/services/test_graph_cost_preview.py tests/services/test_graph_safety.py && cd ../frontend && npm run build`
- **Before `$gsd-verify-work`:** Full suite must be green and browser smoke must pass
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 5-01-01 | 01 | 1 | INGEST-01, INGEST-02, INGEST-03, COST-01, COST-02, SAFE-01 | T-05-01 / T-05-03 | Preview uses validated chunk settings, echoes normalized chunk values, counts UTF-8 bytes, and does not create tasks or trigger Zep writes | unit/integration | `cd backend && uv run pytest -q tests/services/test_graph_chunk_defaults.py tests/services/test_graph_cost_preview.py tests/services/test_graph_safety.py` | ❌ W0 | ⬜ pending |
| 5-01-02 | 01 | 1 | INGEST-03, COST-01, COST-02, SAFE-01 | T-05-02 / T-05-03 | UI shows preview before build, clears stale preview after settings changes, and starts real build only after explicit confirmation | build + manual smoke | `cd frontend && npm run build` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/services/test_graph_chunk_defaults.py` — default and normalization coverage for chunk settings
- [ ] `backend/tests/services/test_graph_cost_preview.py` — preview chunk/byte/credit math and warning level coverage
- [ ] `backend/tests/services/test_graph_safety.py` — preview non-mutation and build lifecycle safety coverage

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Preview appears before build task creation | COST-01, COST-02 | No frontend interaction test harness exists in the repo today | Open the `Process` route, generate ontology, confirm Step 1 shows preview state and no build task starts automatically |
| Expensive preview shows warning and still requires confirmation | COST-02 | Warning-card UX is user-facing behavior | Use a large document or settings that trigger the warning and verify the warning appears before build confirmation |
| Settings change invalidates stale preview | INGEST-03, COST-01 | Requires browser interaction across local state transitions | Generate a preview, change `chunk_size` or `chunk_overlap`, verify preview clears and must be regenerated |
| Real build still follows existing polling flow after confirmation | SAFE-01 | End-to-end behavior spans preview gate and existing async task lifecycle | Confirm build after preview, then verify progress polling and graph refresh behave as before |
| Lower overlap preserves graph extraction quality on representative docs | INGEST-02, SAFE-01 | Requires side-by-side qualitative comparison of graph outputs | Build one representative document set with legacy `500/50` settings and one with the new `300/30` baseline; compare node/edge counts and inspect whether the resulting graph still captures the expected entities and relationships without obvious degradation |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
