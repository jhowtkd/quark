# Phase 8 Discussion Log

**Phase:** 08-data-provenance-and-labeling
**Date:** 2026-04-27
**Status:** Complete

---

## Area 1: Label Taxonomy and Detection

**Q1:** For Zep graph data, what default label?
- Options: "realizado" vs "extraído da base de conhecimento" (cautious)
- **Decision:** "extraído da base de conhecimento" — acknowledges extraction fallibility

**Q2:** When LLM generates a number based on received data but not a direct citation, what label?
- Options: "projeção" vs "simulação" vs force exact source citation
- **Decision:** LLM must always cite if it's projection or exact source. Simplified labels: "fato" and "hipótese"

**Q3:** Fallback search data — what label?
- Options: "consenso" vs "fonte externa" with specific citation
- **Decision:** "fonte externa" + must cite the specific source

**Q4:** "Nao possuo informacoes suficientes" — how to handle?
- Options: pass through vs auto-tag
- **Decision:** Auto-tag as "dados insuficientes"

**Key outcome:** Simplified binary-plus taxonomy: 📊 Fato, 🔮 Hipótese, ⚠️ Dados insuficientes

---

## Area 2: Injection Point in the Pipeline

**Q1:** Defense in depth (A+B+C) or single layer?
- **Decision:** Yes, defense in depth — all three layers

**Q2:** Visual format preference?
- Options: emojis / bracketed text / footnotes / separate section
- **Decision:** Emojis (📊, 🔮, ⚠️)

**Q3:** Visible to user, in logs, or both?
- **Decision:** Both

**Q4:** Data Sources section — auto-generated or LLM-written?
- **Decision:** LLM must write it at the end of the report

---

## Area 3: Scope — economia-only or all profiles

**Q1:** Does universal provenance make sense for non-finance profiles?
- **Decision:** Yes, it makes sense

**Q2:** Optional per-profile toggle?
- **Decision:** No

**Q3:** Generic profile inherits from context?
- **Decision:** Yes

**Q4:** Hardcoded in economia or generic architecture?
- **Decision:** Hardcoded in economia for now; architecture should allow future expansion

---

## Area 4: Existing Reports and Backward Compatibility

**Q1:** Old reports without provenance?
- Options: show as-is / banner / retroactive inference
- **Decision:** Show as-is (Option A)

**Q2:** Provenance version evolution?
- Options: fixed / migration / re-processing
- **Decision:** Fixed per report (Option A)

**Q3:** Extend agent_log.jsonl vs separate provenance.json?
- **Decision:** Extend agent_log.jsonl (Option A)

**Q4:** In-flight reports during deployment?
- Options: generate with new code / abort / hybrid
- **Decision:** Abort and ask user to restart (Option B)

---

## Deferred Ideas

- Provenance for non-economia profiles — future milestone
- Retroactive inference for old reports — rejected
- Separate provenance.json file — rejected
- Auto-generated Data Sources — rejected
- Footnote/bracketed citation format — deferred
