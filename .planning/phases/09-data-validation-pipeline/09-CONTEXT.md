# Phase 9: Data Validation Pipeline - Context

**Gathered:** 2026-04-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Build pre-generation validation that cross-checks key financial metrics against known public sources or simulation ground truth before report generation. Prevent factual errors in revenue, EPS, margins, capex, and FCF figures.

Requirements: VALID-01, VALID-02, VALID-03, VALID-04
Depends on: Phase 8 (provenance metadata now available)
</domain>

<decisions>
## Implementation Decisions

### Validation Architecture
- **D-01:** A dedicated `DataValidationService` module (`backend/app/services/data_validation.py`) encapsulates all validation logic. It is profile-aware (economia-only for Phase 9).
- **D-02:** Validation runs AFTER outline planning but BEFORE section generation. This is the natural hook point: simulation context is already gathered, but no narrative has been generated yet.
- **D-03:** Two-tier validation:
  - **Tier 1 (Structural):** Validate that extracted metrics are mathematically consistent (e.g., gross margin < operating margin < net margin, revenue > 0, capex < revenue).
  - **Tier 2 (Reference):** Cross-check against curated reference ranges from external search results or known public filings stored in the graph.
- **D-04:** The validation result is a `ValidationReport` dataclass that is passed to the section generation prompts. It contains: `metrics_extracted`, `discrepancies`, `confidence_level` (high/medium/low), `gaap_vs_non_gaap_notes`.

### Metric Extraction Strategy
- **D-05:** Financial metrics are extracted from:
  1. Simulation context (graph statistics, related facts)
  2. Fallback search results (if graph is sparse)
  3. The simulation requirement text itself (user-provided target metrics)
- **D-06:** Extracted metrics are normalized to a canonical form: `{"metric_name": "revenue", "value": 94.8, "unit": "US$ bilhoes", "period": "2025", "source": "simulation"}`.

### Thresholds and Flags
- **D-07:** Default deviation thresholds (configurable per profile):
  - Revenue/EPS/FCF: ±15% from reference triggers warning, ±30% triggers block (requires override).
  - Margins: ±5 percentage points triggers warning, ±10 pp triggers block.
  - Capex: ±20% triggers warning, ±40% triggers block.
- **D-08:** When a metric is blocked, the report generation continues but the `ValidationReport` marks it as `requires_override`. The narrative confidence is downgraded to "low" for that metric.
- **D-09:** GAAP vs non-GAAP: If EPS is mentioned, the validation requires BOTH GAAP and non-GAAP to be present OR explicitly notes which version is being used. If only one is present, the report prompt is instructed to add a disclaimer.

### Integration Points
- **D-10:** `ReportAgent.generate_report()` calls `DataValidationService.validate(simulation_context)` after planning and before the section loop.
- **D-11:** The `ValidationReport` is injected into the `SECTION_SYSTEM_PROMPT_TEMPLATE` as `[Validation Context]` so the LLM knows which metrics are validated, which are flagged, and what confidence level to use.
- **D-12:** `ECONOMIA_CONFIG` gains a `validation_thresholds` dict and `require_validation` flag (default True for economia).
- **D-13:** Validation results are logged to `agent_log.jsonl` with action `"data_validation"`.

### Scope and Deferrals
- **D-14:** Economy profile only. Other profiles skip validation entirely.
- **D-15:** Live SEC EDGAR API integration is explicitly deferred (per PROJECT.md Out of Scope). Validation uses curated reference data from graph/search results.
- **D-16:** No frontend changes. Validation results are invisible to users except through improved report quality and logs.
</decisions>

<specifics>
## Specific Ideas

- The Tesla report error (Q1 2026 EPS using GAAP as consensus proxy) is the canonical example of what this phase prevents.
- The validation module should be unit-testable with mock metrics — no live graph or API required for testing.
- Portuguese variable names and comments must be preserved per AGENTS.md rules.
- The `DataValidationService` should be importable and callable independently of `ReportAgent` for debugging.
</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Report Generation Pipeline
- `backend/app/services/report_agent.py` — `ReportAgent.generate_report()` lines ~1915-2256. Hook validation after planning (line ~2030) and before section loop (line ~2047).
- `backend/app/profiles/profile_manager.py` — `ECONOMIA_CONFIG` lines ~188-275. Add validation configuration here.

### Data Retrieval Layer
- `backend/app/services/zep_tools.py` — `ZepToolsService.get_simulation_context()` and result classes. Simulation context is the primary source for metric extraction.
- `backend/app/services/deep_research_agent.py` — Fallback research may contain curated reference data.

### Existing Validation Framework
- `backend/app/utils/language_integrity.py` — Pattern for validation modules (dataclass result, assess/enforce functions).
- `backend/app/observability/reporting.py` — Langfuse scoring. Add `validation_coverage` score.

### Project Requirements
- `.planning/REQUIREMENTS.md` — VALID-01 through VALID-04.
- `.planning/ROADMAP.md` — Phase 9 goal and success criteria.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ReportLogger` already captures detailed actions. Extending it with validation logs is minimal friction.
- `ProfileConfiguration.apply_to_report_agent()` already injects profile-specific settings. Adding `validation_thresholds` and `require_validation` follows the same pattern.
- `ReportAgent._validate_persisted_output()` and `assess_text_integrity()` show the validation result pattern: return a dataclass with `.ok` or `.warnings`.

### Established Patterns
- Profile-specific rules are applied via `profile.apply_to_report_agent(agent)`.
- The report pipeline has three clear phases: planning → generating → assembling.
- Post-processing validation happens at assembly time (provenance tags). Pre-generation validation is new.
- Reports are saved to `reports/{id}/` with `meta.json`, `section_*.md`, `full_report.md`.

### Integration Points
- **Hook point:** `ReportAgent.generate_report()` after `outline = self.plan_outline(...)` and before `for i, section in enumerate(outline.sections)`.
- **Prompt injection:** `SECTION_SYSTEM_PROMPT_TEMPLATE` or a new section in `_generate_section_react()` messages.
- **Profile config:** `ECONOMIA_CONFIG` dict and `ProfileConfiguration` dataclass.
- **Logging:** `ReportLogger.log()` with action `"data_validation"`.
</code_context>

<deferred>
## Deferred Ideas

- Live SEC EDGAR API integration — explicitly out of scope for v1.3.
- Generic validation for non-economia profiles — future milestone.
- Frontend validation dashboard — not required for this milestone.
- Automatic correction of detected discrepancies (rewrite metrics) — too risky; flag only.
- Multi-period time-series validation — v2 advanced quality (ADVQ-01).
</deferred>

---

*Phase: 09-data-validation-pipeline*
*Context gathered: 2026-04-27*
