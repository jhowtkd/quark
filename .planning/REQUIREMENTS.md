# Requirements: Milestone v1.3 Report Quality Improvement

**Defined:** 2026-04-27
**Core Value:** Execute and manage simulations with an intuitive, reliable user interface.

## v1 Requirements

### Data Provenance and Labeling (PROV)

- [x] **PROV-01**: Every quantitative claim in a report is tagged with its source type: realizado (public filing), consenso (analyst consensus), projeção (model projection), or simulação (simulated/estimated data).
- [x] **PROV-02**: Reports include a "Data Sources" section listing every external source referenced, with URLs or identifiers where applicable.
- [x] **PROV-03**: When simulated or projected data is used, the report explicitly states the methodology and confidence level.
- [x] **PROV-04**: No data point is presented as fact without a verifiable source or explicit simulation label.

### Data Validation Pipeline (VALID)

- [x] **VALID-01**: Before report generation, key financial metrics (revenue, EPS, gross/operating/net margins, capex, FCF) are cross-checked against known public filings or consensus databases.
- [x] **VALID-02**: When a metric deviates from the expected public range by more than a configurable threshold, the system flags the discrepancy and requires human review or explicit override.
- [x] **VALID-03**: GAAP and non-GAAP versions of EPS and other dual-metric figures are both captured and distinguished.
- [x] **VALID-04**: The validation result is surfaced to the report generation pipeline so it can adjust narrative confidence accordingly.

### Structured Report Format (FORMAT)

- [x] **FORMAT-01**: Reports follow a due-diligence structure: Tese Principal, Evidências Verificadas, Fragilidades e Riscos, Premissas Explícitas, Cenários (Bear/Base/Bull).
- [x] **FORMAT-02**: Each section contains only content relevant to its heading — no mixing of tese and evidência within the same unstructured block.
- [x] **FORMAT-03**: Quantified tables accompany narrative sections where appropriate (revenue, margins, capex, FCF, deliveries).
- [x] **FORMAT-04**: Scenarios include explicit probability weights and trigger conditions, not just optimistic/pessimistic narratives.

### Neutrality and Bias Audit (NEUT)

- [x] **NEUT-01**: Generated narrative is audited for confirmation bias — if the report leans consistently bullish or bearish without balancing evidence, it is flagged.
- [x] **NEUT-02**: Bull and bear cases are presented with comparable depth and specificity — no shallow dismissal of the contrarian view.
- [x] **NEUT-03**: Language strength is calibrated to evidence quality — strong claims require strong evidence; speculative claims use conditional language.
- [x] **NEUT-04**: Competitive analysis quantifies market share, price elasticity, or regional mix impact where data exists, rather than relying on vague qualitative statements.

### Output Quality Gates (QUAL)

- [x] **QUAL-01**: Generated reports are verified to be in a single language (Portuguese or English, per profile setting) — no mid-document language switching.
- [x] **QUAL-02**: Reports include a "Known Limitations" section documenting gaps in available data or unresolved uncertainties.
- [x] **QUAL-03**: Numeric inconsistencies within the same report are detected and flagged before final output.
- [x] **QUAL-04**: Reports pass a post-generation sanity check: no self-contradictory claims, no unsupported valuation conclusions.

## v2 Requirements

### Advanced Quality

- **ADVQ-01**: Automated fact-checking against live SEC EDGAR filings or equivalent primary sources.
- **ADVQ-02**: Sentiment and tone scoring with automatic rewrite suggestions for biased passages.
- **ADVQ-03**: Peer-report benchmarking — compare generated report quality against industry-standard research notes.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Replace LLM provider | Quality improvement is achievable through prompts, validation, and structure first |
| Real-time market data API | Use curated validation against known sources; live feeds are future work |
| Full interactive report builder | Focus on report quality, not report UI customization |
| Multi-language simultaneous output | Single-language per report is the requirement for v1.3 |
| Automated investment recommendation engine | Reports present analysis; decision-making stays with the user |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PROV-01 | Phase 8 | Complete |
| PROV-02 | Phase 8 | Complete |
| PROV-03 | Phase 8 | Complete |
| PROV-04 | Phase 8 | Complete |
| VALID-01 | Phase 9 | Complete |
| VALID-02 | Phase 9 | Complete |
| VALID-03 | Phase 9 | Complete |
| VALID-04 | Phase 9 | Complete |
| FORMAT-01 | Phase 10 | Complete |
| FORMAT-02 | Phase 10 | Complete |
| FORMAT-03 | Phase 10 | Complete |
| FORMAT-04 | Phase 10 | Complete |
| NEUT-01 | Phase 11 | Complete |
| NEUT-02 | Phase 11 | Complete |
| NEUT-03 | Phase 11 | Complete |
| NEUT-04 | Phase 11 | Complete |
| QUAL-01 | Phase 12 | Complete |
| QUAL-02 | Phase 12 | Complete |
| QUAL-03 | Phase 12 | Complete |
| QUAL-04 | Phase 12 | Complete |

**Coverage:**
- v1 requirements: 20 total
- Mapped to phases: 20
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-27*
*Last updated: 2026-04-27 after milestone v1.3 definition*
