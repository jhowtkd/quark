# 34-02: Estados de Erro e Vazio — Summary

## What Was Done

Implemented comprehensive empty/error states and a quality indicator for the report viewer, ensuring users always understand the report status and have actionable recovery paths.

## Files Modified

| File | Change |
|------|--------|
| `frontend/src/components/Step4Report.vue` | Added empty state (404), section error state with retry, quality indicator, new state refs, `fetchReportProgress`, `handleRetrySection` |
| `frontend/src/api/report.js` | Added `getReportProgress` and `retrySection` API functions |
| `frontend/tests/components/Step4Report.spec.js` | Added 7 new tests (15 total) for empty state, section error, retry, quality indicator |
| `backend/app/api/report.py` | Added `POST /<report_id>/retry-section` endpoint, `status: "failed"` in `get_report_sections`, `failed_sections` in progress |
| `backend/app/services/report_agent.py` | `update_progress` now accepts `failed_sections`; `_generate_all_sections` tracks and persists failed sections |
| `backend/tests/api/test_report_retry_api.py` | New test file with 5 tests for retry endpoint |
| `locales/pt.json` | Added API and progress strings for retry flow |

## Key Implementation Details

- **Empty state (404):** `getReport` is called on load; if 404, `reportNotFound` shows a document icon, title, description, and "Voltar para o Workbench" button
- **Section error state:** Progress polling populates `failedSections` Map; failed sections show an error card with retry button
- **Retry flow:** `handleRetrySection` calls `POST /retry-section`, removes from `failedSections` immediately, and polls agent logs for regenerated content
- **Quality indicator:** Inline bar below report header showing completion %, contamination count, failed count, and "thinking process filtrado" badge
- **Backend retry endpoint:** Validates `section_index`, checks `failed_sections`, removes entry before starting background thread with `SectionGenerator`

## Tests

- **Frontend:** 15/15 passing (8 focus mode + 7 new for empty/error/quality)
- **Backend:** 5/5 new retry API tests + 419 existing tests passing

## Build Status

✅ Frontend build passes (`npm run build`)
✅ Backend tests pass (`uv run pytest -q`)
