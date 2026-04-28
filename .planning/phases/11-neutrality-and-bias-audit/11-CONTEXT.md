# Phase 11: Neutrality and Bias Audit - Context

**Gathered:** 2026-04-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Eliminate confirmation bias and ensure balanced presentation of bull and bear arguments. Detect when the report leans consistently in one direction without balancing evidence, calibrate claim strength to evidence quality, and ensure competitive analysis is quantified.

Requirements: NEUT-01, NEUT-02, NEUT-03, NEUT-04
Depends on: Phase 10 (structured format now provides explicit Fragilidades and Cenarios sections to audit)
</domain>

<decisions>
## Implementation Decisions

### Bias Detection Architecture
- **D-01:** A dedicated `BiasAuditService` module (`backend/app/services/bias_audit.py`) performs post-generation bias analysis using deterministic pattern matching (no LLM calls). This keeps latency low and results reproducible.
- **D-02:** The audit runs after all sections are generated but before final report assembly. It analyzes the full set of section contents.
- **D-03:** Three audit dimensions:
  1. **Sentiment Balance (NEUT-01/NEUT-02):** Count bullish vs bearish keyword density. Flag if ratio exceeds 2:1 in either direction.
  2. **Claim Strength Calibration (NEUT-03):** Detect strong/assertive language ("certamente", "inevitavelmente", "sem duvida") and check if the same sentence contains a provenance tag (📊) or is marked as projection (🔮). Strong claims without 📊 are flagged.
  3. **Competitive Analysis Quantification (NEUT-04):** Detect competitive analysis paragraphs that lack numeric claims. Flag if market share, price, elasticity, or regional mix are discussed without numbers.

### Bias Scoring
- **D-04:** Bias score is computed as a composite:
  - Sentiment balance: 40% weight (ratio closer to 1:1 = higher score)
  - Claim strength calibration: 35% weight (fewer strong unverified claims = higher score)
  - Competitive quantification: 25% weight (more numbers in competitive analysis = higher score)
- **D-05:** Score ranges from 0.0 to 1.0. Thresholds:
  - ≥ 0.80: Balanced (no action)
  - 0.60–0.79: Warning (log discrepancy, reduce narrative confidence)
  - < 0.60: Critical (log as high-priority bias alert)

### Prompt Strengthening
- **D-06:** Update `ECONOMIA_CONFIG.report_system_prompt` with explicit neutrality rules:
  - "A tese deve ser apresentada junto com evidencias contrarias de peso equivalente."
  - "Fragilidades nao devem ser rebatidas imediatamente. Deixe o leitor avaliar."
  - "Afirmacoes fortes exigem fontes fortes (📊). Afirmacoes especulativas devem usar linguagem condicional ("pode", "se", "caso")."
  - "Analise competitiva deve quantificar: market share, elasticidade-preco, mix regional. Evite adjetivos vagos como 'forte' ou 'fraca' sem numeros."

### Integration
- **D-07:** `ReportAgent.generate_report()` calls `BiasAuditService.audit_sections(generated_sections)` after the section loop and before assembly.
- **D-08:** Bias report is logged to `agent_log.jsonl` with action `"bias_audit"`.
- **D-09:** If bias score < 0.80, a "Neutrality Note" is appended to the report meta and a warning is added to the final report (invisible to user but visible in meta).
- **D-10:** The bias audit is profile-scoped: only `economia` activates it via `require_bias_audit` flag in `ProfileConfiguration`.

### Scope
- **D-11:** Economy profile only.
- **D-12:** No frontend changes.
- **D-13:** No automatic rewrite of biased sections — flag only, to avoid introducing new errors.
</decisions>

<specifics>
## Specific Ideas

- The Tesla report was consistently bearish without balancing evidence. The sentiment keyword approach catches this by counting words like "queda", "risco", "preocupacao" vs "crescimento", "oportunidade", "recuperacao".
- Claim strength calibration addresses the "GAAP EPS presented as consensus" issue: if the LLM says "O EPS sera X" without a 📊 tag, it should be flagged as an unverified strong claim.
- Competitive analysis quantification prevents vague statements like "Tesla tem forte presenca na China" — the audit flags this because "forte" has no number attached.
</specifics>

<canonical_refs>
## Canonical References

### Report Generation Pipeline
- `backend/app/services/report_agent.py` — `generate_report()` section loop (lines ~2041-2133) and assembly phase
- `backend/app/profiles/profile_manager.py` — `ECONOMIA_CONFIG` and `ProfileConfiguration`

### Existing Validation Framework
- `backend/app/services/data_validation.py` — ValidationReport pattern (Phase 9)
- `backend/app/utils/language_integrity.py` — Pattern-based validation approach

### Integration Points
- **Hook point:** After section loop, before `assemble_full_report()` in `generate_report()`
- **Prompt updates:** `ECONOMIA_CONFIG.report_system_prompt`
- **Logging:** `ReportLogger.log(action="bias_audit", ...)`
- **Meta output:** `extra_meta["bias_audit_report"]`
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `DataValidationService` and `ValidationReport` (Phase 9) provide the exact pattern for audit services: extract → analyze → return structured report.
- `ReportLogger` already supports arbitrary action types.
- `ProfileConfiguration` already supports profile-specific toggles (`require_provenance`, `require_validation`).

### Established Patterns
- Post-generation validation happens at assembly time (provenance tags in Phase 8).
- Pre-generation validation happens before section loop (data validation in Phase 9).
- Bias audit is a new pattern: mid-generation validation (after sections, before assembly).

### Integration Points
- **Mid-generation hook:** `generate_report()` after `for i, section in enumerate(outline.sections)` loop completes.
- **Profile flag:** Add `require_bias_audit: bool = False` to `ProfileConfiguration`.
- **Prompt injection:** Update `ECONOMIA_CONFIG.report_system_prompt` with neutrality rules.
</code_context>

<deferred>
## Deferred Ideas

- LLM-based bias audit (more nuanced but slower and non-deterministic) — future work
- Automatic rewrite of biased sections — too risky; flag-only approach
- Real-time bias monitoring during section generation (per-section audit) — overkill for v1.3
- Sentiment analysis model integration — out of scope
</deferred>

---

*Phase: 11-neutrality-and-bias-audit*
*Context gathered: 2026-04-27*
