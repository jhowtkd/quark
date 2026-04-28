# Roadmap: Quark

## Proposed Roadmap

**5 phases** | **20 requirements mapped** | All covered ✓

## Phases

- [x] **Phase 8: Data Provenance and Labeling** — Enforce strict source tagging and transparency for every data point in generated reports.
- [x] **Phase 9: Data Validation Pipeline** — Build pre-generation validation that cross-checks key financial metrics against public sources.
- [x] **Phase 10: Structured Report Format** — Implement due-diligence report structure with explicit sections for tese, evidências, fragilidades, premissas e cenários.
- [x] **Phase 11: Neutrality and Bias Audit** — Add bias detection and neutrality enforcement to analytical narrative generation.
- [x] **Phase 12: Output Quality Gates** — Implement post-generation checks for language consistency, numeric sanity, and self-contradiction.

## Phase Details

### Phase 8: Data Provenance and Labeling
**Goal**: Every data point in a report must carry an explicit source-type label, and simulated/projected data must never be presented as verified fact.
**Depends on**: Phase 7 (completed)
**Requirements**: [PROV-01, PROV-02, PROV-03, PROV-04]
**Success Criteria** (what must be TRUE):
  1. Every quantitative claim in a generated report is tagged with one of: realizado, consenso, projeção, simulação.
  2. A "Data Sources" section is automatically appended to every report.
  3. Simulated data points include a brief methodology note.
  4. No untagged or ambiguously sourced data points appear in report output.
**Plans**: 1 plan (08-01)

### Phase 9: Data Validation Pipeline
**Goal**: Prevent factual errors in key financial metrics by cross-checking them against known public sources before report generation.
**Depends on**: Phase 8
**Requirements**: [VALID-01, VALID-02, VALID-03, VALID-04]
**Success Criteria** (what must be TRUE):
  1. Revenue, EPS, margins, capex, and FCF figures are validated against a curated reference before narrative generation.
  2. Deviations beyond a threshold trigger a warning or block generation until reviewed.
  3. GAAP and non-GAAP EPS are both available to the report generator and correctly labeled.
  4. Validation results influence narrative confidence levels.
**Plans**: 0 plans

### Phase 10: Structured Report Format
**Goal**: Replace free-form narrative with a disciplined due-diligence structure that separates tese from evidência and quantifies scenarios.
**Depends on**: Phase 9
**Requirements**: [FORMAT-01, FORMAT-02, FORMAT-03, FORMAT-04]
**Success Criteria** (what must be TRUE):
  1. Reports follow a fixed section order: Tese, Evidências, Fragilidades, Premissas, Cenários.
  2. Each section contains only content relevant to its heading.
  3. Key metrics are presented in tables alongside narrative.
  4. Bear/Base/Bull scenarios include explicit probability weights and triggers.
**Plans**: 0 plans

### Phase 11: Neutrality and Bias Audit
**Goal**: Eliminate confirmation bias and ensure balanced presentation of bull and bear arguments.
**Depends on**: Phase 10
**Requirements**: [NEUT-01, NEUT-02, NEUT-03, NEUT-04]
**Success Criteria** (what must be TRUE):
  1. A bias score is computed for each report; scores beyond a threshold trigger rewrite.
  2. Bull and bear cases are presented with comparable depth.
  3. Claim strength is calibrated to evidence quality.
  4. Competitive analysis includes quantified metrics where available.
**Plans**: 0 plans

### Phase 12: Output Quality Gates
**Goal**: Catch language mixing, numeric inconsistencies, and self-contradictions before the report reaches the user.
**Depends on**: Phase 11
**Requirements**: [QUAL-01, QUAL-02, QUAL-03, QUAL-04]
**Success Criteria** (what must be TRUE):
  1. Reports are verified to be in a single language throughout.
  2. A "Known Limitations" section is automatically included.
  3. Internal numeric contradictions are detected and flagged.
  4. No unsupported valuation conclusions or self-contradictory claims appear in final output.
**Plans**: 0 plans

## Progress

**Execution Order:**
Phases execute in numeric order: 8, 9, 10, 11, 12

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 8. Data Provenance and Labeling | 1/1 | Complete | 2026-04-27 |
| 9. Data Validation Pipeline | 1/1 | Complete | 2026-04-27 |
| 10. Structured Report Format | 1/1 | Complete | 2026-04-27 |
| 11. Neutrality and Bias Audit | 1/1 | Complete | 2026-04-27 |
| 12. Output Quality Gates | 1/1 | Complete | 2026-04-27 |
