# Phase 11: Neutrality and Bias Audit - Research

**Gathered:** 2026-04-27

## Current Prompt Neutrality State

The `ECONOMIA_CONFIG.report_system_prompt` (after Phase 10) already has some bias prevention:
- "Proibir adjetivos emocionais"
- "Proibir linguagem figurada, metaforas"
- Provenance tags force source attribution

But it lacks explicit:
- Bull/bear balance requirements
- Claim strength calibration rules
- Competitive quantification mandates

## Section Structure Post-Phase 10

The due-diligence structure provides natural audit points:
- **Tese Principal** — should be neutral or present both sides
- **Evidências Verificadas** — should contain both supporting and contradicting facts
- **Fragilidades e Riscos** — dedicated bear case section (already helps balance)
- **Cenários** — Bear/Base/Bull with probabilities (already helps balance)

The audit will verify that these sections are actually used for their intended purpose.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| False positives in sentiment detection (neutral words misclassified) | Medium | Low | Conservative keyword lists; context-aware patterns |
| Bias audit adds significant latency | Low | Low | Pattern-based only, no LLM calls; should be <100ms |
| LLM ignores strengthened neutrality prompts | Medium | Medium | Audit catches it post-hoc; doesn't block but flags |
| Breaking non-economia reports | Low | High | Profile-scoped flag (`require_bias_audit`) |

## Implementation Strategy

1. **New module:** `backend/app/services/bias_audit.py` (~300 lines)
   - Keyword lists for bullish/bearish/strong/conditional language
   - `BiasAuditService` with `audit_sections()` method
   - `BiasReport` dataclass with composite scoring
2. **Profile changes:** `profile_manager.py` — add `require_bias_audit` and neutrality prompt additions
3. **ReportAgent changes:** `report_agent.py` — add bias audit call after section loop, log results, include in meta

## Files to Modify

- `backend/app/services/bias_audit.py` (new)
- `backend/app/profiles/profile_manager.py` (~20 lines)
- `backend/app/services/report_agent.py` (~30 lines)
