# Phase 9: Data Validation Pipeline - Research

**Gathered:** 2026-04-27

## Current Code Architecture

### ReportAgent.generate_report() Flow
1. Initialize report folder, logger, console logger
2. **Planning phase:** `plan_outline()` → returns `ReportOutline`
3. **Generating phase:** Loop through sections, call `_generate_section_react()` for each
4. **Assembly phase:** `assemble_full_report()` → post-process, validate provenance tags
5. Save final report with `meta.json`

**Hook point identified:** Between step 2 and step 3. After planning, the simulation context has already been fetched. Before generation, the LLM has not yet written any narrative.

### Simulation Context Structure
From `zep_tools.py`:
- `get_simulation_context()` returns graph statistics, related facts, entity counts
- `InsightForgeResult`, `PanoramaResult`, `SearchResult` carry `.provenance` dicts
- Facts are plain text strings that may contain numeric claims

### Profile Configuration
From `profile_manager.py`:
- `ECONOMIA_CONFIG` has `report_system_prompt`, `report_section_prompt`, `simulation_overrides`, `entity_type_weights`
- `ProfileConfiguration` dataclass has `require_provenance: bool`
- `apply_to_report_agent()` sets dynamic attributes on the agent

### Existing Validation Patterns
From `language_integrity.py`:
- `LanguageIntegrityResult` frozen dataclass with `.ok` property
- `assess_text_integrity()` takes text + optional constraints, returns result
- `enforce_controlled_output()` returns `(safe_text, result)` tuple

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| False positives in metric extraction (non-financial numbers flagged) | Medium | Low | Narrow regex patterns; whitelist metric names in Portuguese/English |
| Validation blocks legitimate simulation projections | Low | Medium | Block only on Tier 2 (reference) deviations; Tier 1 (structural) is warning-only |
| LLM ignores validation context in prompt | Medium | Medium | Explicit instruction in section prompt; observability score tracks compliance |
| Performance overhead on large reports | Low | Low | Validation is regex/parsing only — no LLM calls |
| Breaking existing non-economia reports | Low | High | `require_validation` defaults to False; only economia activates it |

## Integration Complexity

- **New module:** `backend/app/services/data_validation.py` (~250 lines)
- **Profile changes:** `profile_manager.py` — add 3 fields (~15 lines)
- **ReportAgent changes:** `report_agent.py` — add validation call and prompt injection (~40 lines)
- **Tests:** Unit tests for `DataValidationService` with mock data (~100 lines)
- **Total estimated:** ~400 lines new code, ~55 lines modified

## Reference Data Strategy

Since live SEC EDGAR is out of scope, the "reference" data comes from:
1. The simulation graph itself (ground truth for the simulated world)
2. External search results already cached in the graph or fetched during planning
3. User-provided simulation requirement (treated as authoritative)

The validation primarily ensures **internal consistency** and **plausibility** rather than matching real-world filings. This is appropriate because the reports describe *simulated futures*, not current reality.
