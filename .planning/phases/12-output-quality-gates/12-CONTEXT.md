# Phase 12: Output Quality Gates — Context

**Phase:** 12 (FINAL)  
**Milestone:** v1.3 Report Quality Improvement  
**Requirements:** QUAL-01, QUAL-02, QUAL-03, QUAL-04  
**Goal:** Catch language mixing, numeric inconsistencies, and self-contradictions before the report reaches the user.

---

## Phase Boundary

### Inputs (from Phase 11)
- BiasAuditService with three dimensions: sentiment balance, claim calibration, competitive quantification
- `report_agent.py` runs bias audit after sections, before assembly
- Profile system supports `require_bias_audit` flag
- `ECONOMIA_CONFIG` has structured report format with 5 sections

### Outputs (this phase)
- `QualityGateService` in `backend/app/services/quality_gates.py`
- Extended `language_integrity.py` with language-switching detection
- Profile prompts updated to require Known Limitations section
- Quality gates hooked into report generation pipeline after bias audit

### Decisions
1. **Where to hook:** Quality gates run after bias audit, before `assemble_full_report()` — same pattern as Phase 11.
2. **Architecture:** Single `QualityGateService` class with inner gate classes, following `BiasAuditService` pattern.
3. **Language detection:** Use simple regex-based detection (Portuguese vs English stopwords) rather than external libraries to avoid dependencies.
4. **Numeric consistency:** Extract numeric claims with context and detect same-metric-different-value patterns.
5. **Self-contradiction:** Reuse keyword-pair approach from bias audit (bullish/bearish patterns) but for logical opposites (growing/declining, strong/weak).
6. **Known Limitations:** Both prompt-level instruction AND post-generation auto-append if missing.

---

## Canonical References

| File | Purpose |
|------|---------|
| `backend/app/services/quality_gates.py` | New service — all quality gates |
| `backend/app/utils/language_integrity.py` | Extended with `detect_language_switches()` |
| `backend/app/profiles/profile_manager.py` | ECONOMIA_CONFIG prompt updated for limitations section |
| `backend/app/services/report_agent.py` | Hook quality gates in `generate_report()` |
| `backend/app/services/bias_audit.py` | Pattern reference for audit service structure |
