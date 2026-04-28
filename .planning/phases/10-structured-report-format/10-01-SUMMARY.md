# Phase 10 Summary: Structured Report Format

**Completed:** 2026-04-27
**Plan:** 10-01
**Requirements:** FORMAT-01, FORMAT-02, FORMAT-03, FORMAT-04

## What Was Built

### Updated: `backend/app/profiles/profile_manager.py`

**New field:** `outline_system_prompt` added to `ProfileConfiguration` dataclass and propagated through `apply_to_report_agent()` and `to_dict()`.

**Updated `ECONOMIA_CONFIG`:**

1. **`report_system_prompt`** — Replaced the generic 6-section structure with a strict 5-section due-diligence format:
   - Tese Principal (1-2 sentences, no data)
   - Evidências Verificadas (facts with sources, mandatory table)
   - Fragilidades e Riscos (risks only, no rebuttals)
   - Premissas Explícitas (assumptions with "if false then..." consequences)
   - Cenários (Bear/Base/Bull with probability, observable trigger, quantified result)

2. **Scenario rules added:**
   - Probability ranges for each scenario (Bear 20-30%, Base 45-55%, Bull 20-30%)
   - Triggers must be observable events (concrete thresholds, not sentiments)
   - Mandatory comparative table: Cenario | Probabilidade | Gatilho | Resultado
   - Probabilities must sum to 100%

3. **`report_section_prompt`** — Now section-aware with `{section_title}` placeholder:
   - Dynamically enforces content boundaries per section type
   - "Tese Principal": only thesis, no data
   - "Evidências Verificadas": only verified facts, mandatory table, no opinion
   - "Fragilidades e Riscos": only risks, no rebuttals, no positive arguments
   - "Premissas Explícitas": only assumptions with explicit consequences
   - "Cenários": only quantified projections with probability/trigger/table

4. **`outline_system_prompt`** — New field that instructs the LLM to generate exactly 5 sections with the due-diligence titles in order. Forbids generic titles like "Resumo Executivo".

### Updated: `backend/app/services/report_agent.py`

1. **`_get_profile_section_prompt()`** — Now supports dynamic formatting with `{section_title}`. If the profile's `section_prompt` contains this placeholder, it is replaced with the actual section title before injection.

2. **`plan_outline()`** — Injects `outline_system_prompt` into the planning system prompt when configured. This ensures the LLM generates the due-diligence structure during outline planning.

3. **Fallback outline** — When `outline_system_prompt` is set (economia profile), the fallback outline (used when LLM fails) returns the 5 due-diligence sections instead of the generic 3-section fallback. Non-economia profiles continue to use the generic fallback.

## Success Criteria Verification

| Criterion | Status | Evidence |
|-----------|--------|----------|
| FORMAT-01: Fixed section order (Tese, Evidencias, Fragilidades, Premissas, Cenarios) | ✅ | `outline_system_prompt` enforces exact titles and order; fallback outline uses same structure |
| FORMAT-02: Each section contains only relevant content | ✅ | `report_section_prompt` has section-specific rules with explicit negative examples ("NAO rebata", "NENHUM argumento positivo") |
| FORMAT-03: Quantified tables in appropriate sections | ✅ | `report_system_prompt` mandates tables in Evidencias and Cenarios; `report_section_prompt` reinforces with "OBRIGATORIO: tabela" |
| FORMAT-04: Scenarios with probability weights and triggers | ✅ | `report_system_prompt` defines scenario format with probability, observable trigger, quantified result; mandates comparative table; probabilities must sum to 100% |

## Files Modified

- `backend/app/profiles/profile_manager.py` (~80 lines modified)
- `backend/app/services/report_agent.py` (~25 lines modified)

## Deferred

- Automatic probability-sum validator (100% check) — can be added as lightweight post-processor in future
- Interactive report builder UI — out of scope
- Custom section structures per user request — future milestone

## Notes

- All syntax checks passed
- Profile config loads correctly with new fields
- `_get_profile_section_prompt()` remains backward-compatible: prompts without `{section_title}` work unchanged
- Non-economia profiles unaffected (no `outline_system_prompt` configured)
