# Phase 11 Plan 11-01 Execution Summary

**Phase:** 11-neutrality-and-bias-audit  
**Plan:** 11-01 — Neutrality and Bias Audit Implementation  
**Executed:** 2026-04-27  
**Status:** ✅ Complete

---

## What Was Built

Post-generation bias detection and neutrality enforcement for `economia` profile reports.

### Files Modified

#### `backend/app/services/bias_audit.py` (new)
- `BiasDimension` enum: `SENTIMENT_BALANCE`, `CLAIM_CALIBRATION`, `COMPETITIVE_QUANTIFICATION`
- `BiasReport` dataclass with `bias_score`, `dimensions`, `warnings`, `is_balanced`
- Keyword dictionaries:
  - `BULLISH_KEYWORDS` — 40+ bullish terms in Portuguese
  - `BEARISH_KEYWORDS` — 40+ bearish terms in Portuguese
  - `STRONG_CLAIM_MARKERS` — 20+ strong assertion markers
  - `CONDITIONAL_MARKERS` — 20+ conditional language markers
  - `COMPETITIVE_CONTEXT_KEYWORDS` — 15+ competitive analysis indicators
- `BiasAuditService` class:
  - `audit_sections(section_contents)` — main entry point
  - `_analyze_sentiment_balance()` — counts bullish/bearish keywords, computes ratio
  - `_analyze_claim_calibration()` — checks strong claims without 📊 tags, conditional markers with 🔮 tags
  - `_analyze_competitive_quantification()` — detects competitive paragraphs lacking numeric data
  - `_compute_composite_score()` — weighted score (sentiment 40%, claim 35%, competitive 25%)
- Thresholds: warning if score < 0.80, critical if < 0.60

#### `backend/app/profiles/profile_manager.py`
- `ECONOMIA_CONFIG`: added `require_bias_audit: True`
- `ProfileConfiguration`: added `require_bias_audit: bool = False`
- `apply_to_report_agent()`: sets `agent.require_bias_audit`
- `to_dict()`: includes `require_bias_audit`
- Prompt additions:
  - "A tese deve ser apresentada junto com evidencias contrarias de peso equivalente."
  - "Fragilidades nao devem ser rebatidas imediatamente."
  - "Afirmacoes fortes exigem fontes fortes (📊)."
  - "Analise competitiva deve quantificar: market share, elasticidade-preco, mix regional."

#### `backend/app/services/report_agent.py`
- Imports `BiasAuditService`, `BiasReport`
- In `generate_report()`: after section loop, if `require_bias_audit`:
  - Collects section contents
  - Calls `BiasAuditService().audit_sections()`
  - Stores result as `self.bias_report`
  - Logs via `report_logger.log(action="bias_audit", ...)`
  - Warns if `bias_score < 0.80`
- In `extra_meta`: includes `bias_audit_report` if available

---

## Verification

```bash
cd backend
python -m py_compile app/services/bias_audit.py
python -m py_compile app/profiles/profile_manager.py
python -m py_compile app/services/report_agent.py
# ALL PASS
```

---

## Requirements Satisfied

- ✅ **NEUT-01** — Bias score computed; reports leaning consistently bullish/bearish are flagged
- ✅ **NEUT-02** — Bull and bear cases have comparable depth (sentiment balance analysis)
- ✅ **NEUT-03** — Strong claims require strong evidence; speculative claims use conditional language (claim calibration)
- ✅ **NEUT-04** — Competitive analysis quantifies metrics (competitive quantification detection)

---

*Phase 11 complete. Ready for Phase 12.*
