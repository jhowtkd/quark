# Phase 8 Plan 08-01 Execution Summary

**Phase:** 08-data-provenance-and-labeling  
**Plan:** 08-01 — Data Provenance and Labeling Implementation  
**Executed:** 2026-04-27  
**Status:** ✅ Complete

---

## What Was Built

Implemented defense-in-depth provenance labeling for `economia` profile reports. Every quantitative claim now carries an explicit source-type emoji tag, reports include a Data Sources section, and provenance metadata is logged for observability.

### Architecture: Three-Layer Defense

| Layer | Location | Purpose |
|-------|----------|---------|
| **A — Data Retrieval** | `zep_tools.py` + `report_agent.py` | Wraps tool results with metadata (`source`, `tool_name`, `retrieved_at`) |
| **B — LLM Prompt** | `profile_manager.py` `ECONOMIA_CONFIG` | Instructs LLM to tag claims with 📊/🔮/⚠️ and include "Fontes de Dados" section |
| **C — Post-Processing** | `report_agent.py` `_validate_provenance_tags()` | Validates emoji tag coverage; writes warnings if untagged claims detected |

---

## Files Modified

### `backend/app/services/zep_tools.py`
- Added `provenance: Dict[str, Any]` field to `SearchResult`, `InsightForgeResult`, `PanoramaResult`, `InterviewResult`
- Updated `to_dict()` and `to_text()` to emit provenance metadata

### `backend/app/services/report_agent.py`
- **`ReportAgent.__init__()`**: Added `self.provenance_version = "1.0"`
- **`_execute_tool()`**: Wraps tool outputs with provenance metadata (`connector_name`, `retrieved_at`, `query`)
- **`_trigger_fallback_search()`**: Formats results with `Proveniencia: fonte externa` and logs `provenance_tag`
- **`_validate_provenance_tags()`** (new): Regex-based validator detecting numeric claims without 📊/🔮/⚠️
- **`assemble_full_report()`**: Calls validator; writes `provenance_warnings.txt` if issues found
- **`generate_report()`**: Defensive check aborts if `require_provenance=True` but `provenance_version` missing
- **`ReportLogger.log_tool_call()`**: Added `provenance_tag` parameter
- **`ReportLogger.log_tool_result()`**: Added `provenance_tag` parameter
- **`ReportLogger.log_start()`**: Added `provenance_version: "1.0"`
- **Meta saving**: `meta.json` now includes `provenance_version`, `profile_type`, `provenance_enabled`
- **Observability**: `provenance_coverage` Langfuse score logged after validation

### `backend/app/profiles/profile_manager.py`
- **`ECONOMIA_CONFIG`**: Appended provenance rules to `report_system_prompt` and `report_section_prompt`
- **`ECONOMIA_CONFIG`**: Added `"require_provenance": True`
- **`ProfileConfiguration`**: Added `require_provenance: bool = False`
- **`apply_to_report_agent()`**: Sets `agent.require_provenance`

### `backend/app/api/report.py`
- Task metadata includes `provenance_version: "1.0"` when profile requires provenance

---

## Acceptance Criteria Results

| # | Criterion | Result |
|---|-----------|--------|
| 1 | `provenance` field in 4 dataclasses | ✅ All present |
| 2 | `connector_name` + `retrieved_at` in `_execute_tool` | ✅ Present |
| 3 | `REGRAS DE PROVENIENCIA` in prompts + `require_provenance` wired | ✅ Present |
| 4 | `_validate_provenance_tags` + `provenance_validation` log | ✅ Present |
| 5 | `provenance_tag` in logger + `provenance_version` in log_start | ✅ Present |
| 6 | `provenance_version` in `meta.json` | ✅ Present |
| 7 | Abort logic + in-flight policy comment | ✅ Present |
| 8 | `provenance_tag` wired at all call sites | ✅ Present |
| 9 | Fallback search provenance formatting | ✅ Present |
| 10 | Langfuse `provenance_coverage` score | ✅ Present |

---

## Verification

```bash
cd backend
python -m py_compile app/services/zep_tools.py
python -m py_compile app/services/report_agent.py
python -m py_compile app/profiles/profile_manager.py
python -m py_compile app/api/report.py
# ALL PASS
```

---

## Decisions Honored

| Decision | Implementation |
|----------|---------------|
| D-01 Binary-plus taxonomy | 📊 Fato / 🔮 Hipótese / ⚠️ Dados insuficientes |
| D-02 Zep data labeled cautiously | "📊 Fato — extraído da base de conhecimento" |
| D-03 LLM must cite source or projection | Enforced in prompt + Layer C validation |
| D-04 Fallback search labeled | "📊 Fato — fonte externa" with URL |
| D-05 Insufficient data auto-tagged | ⚠️ tag instruction in prompt |
| D-06 Three-layer defense | Layers A + B + C all implemented |
| D-07 Emoji format | Inline tags at end of sentence/paragraph |
| D-08 Visible in report and logs | Yes — emojis in markdown, tags in agent_log.jsonl |
| D-09 Data Sources section LLM-written | Prompt instructs LLM to write it |
| D-10 economia-only scope | `require_provenance: True` only in `ECONOMIA_CONFIG` |
| D-12 Old reports as-is | `provenance_version` only on new reports; no retroactive processing |
| D-13 Immutable provenance_version | Set at generation time in meta.json |
| D-14 Extend agent_log.jsonl | `provenance_tag` field added to tool entries |
| D-15 No partial-provenance reports | Defensive check in `generate_report()` |

---

## Deferred / Future Work

- Generic provenance toggle for all profiles — future milestone
- Retroactive provenance inference — explicitly rejected
- Separate `provenance.json` file — explicitly rejected
- Auto-generated Data Sources section — explicitly rejected
- Footnote/bracketed citation format — explicitly deferred

---

*Plan 08-01 complete. Phase 8 ready for verification.*
