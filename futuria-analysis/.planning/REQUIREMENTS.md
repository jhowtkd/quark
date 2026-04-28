# Requirements: Milestone v1.2 Zep Cost Optimization

**Defined:** 2026-04-17
**Core Value:** Execute and manage simulations with an intuitive, reliable user interface.

## v1 Requirements

### Ingestion Economics (INGEST)

- [ ] **INGEST-01**: Default graph-build chunk sizing is reduced to a cost-safer range so typical chunks are less likely to exceed Zep's single-credit episode threshold.
- [ ] **INGEST-02**: Default chunk overlap is reduced to minimize duplicate ingestion while preserving graph extraction quality.
- [ ] **INGEST-03**: Users can still override chunk size and overlap when building a graph.

### Cost Visibility (COST)

- [ ] **COST-01**: Before sending data to Zep, the system computes and exposes estimated chunk count, estimated byte size, and estimated Zep credit usage for the current build settings.
- [ ] **COST-02**: If estimated ingestion size is unusually high, the user-facing flow surfaces a clear warning before full ingestion starts.

### Deduplication and Rebuild Control (BUILD)

- [ ] **BUILD-01**: Exact duplicate chunks are removed before Zep ingestion.
- [ ] **BUILD-02**: The system detects when extracted text and ontology are unchanged and skips unnecessary full rebuild ingestion.
- [ ] **BUILD-03**: Rebuild-skip behavior is visible in logs or task status so users understand why ingestion did not re-run.

### Incremental Updates (DELTA)

- [ ] **DELTA-01**: Small content changes can follow an incremental ingestion path that sends only changed chunks instead of resending the entire graph source.
- [ ] **DELTA-02**: If incremental ingestion cannot be applied safely, the system falls back to the existing full rebuild path without corrupting graph state.

### Safety and Quality (SAFE)

- [ ] **SAFE-01**: Ontology creation and graph schema behavior remain unchanged by cost optimization work.
- [ ] **SAFE-02**: Existing graph build, simulation, and report-generation flows continue to work after the optimization changes.

## v2 Requirements

### Advanced Optimization

- **OPT-01**: Auto-tune chunk settings based on document language/content profile.
- **OPT-02**: Persist historical Zep usage analytics per project.
- **OPT-03**: Support background cleanup/reconciliation of stale incremental-ingestion metadata.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Replace Zep with another provider | This milestone optimizes current spend before any migration decision |
| Change simulation/report agent behavior | Not directly related to Zep ingestion cost |
| Modify ontology semantics or entity schema | Could change graph quality and invalidate existing behavior |
| Full billing dashboard | Useful later, but not required to reduce credits immediately |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INGEST-01 | Phase 5 | Pending |
| INGEST-02 | Phase 5 | Pending |
| INGEST-03 | Phase 5 | Pending |
| COST-01 | Phase 5 | Pending |
| COST-02 | Phase 5 | Pending |
| BUILD-01 | Phase 6 | Pending |
| BUILD-02 | Phase 6 | Pending |
| BUILD-03 | Phase 6 | Pending |
| DELTA-01 | Phase 7 | Pending |
| DELTA-02 | Phase 7 | Pending |
| SAFE-01 | Phase 5 | Pending |
| SAFE-02 | Phase 7 | Pending |

**Coverage:**
- v1 requirements: 12 total
- Mapped to phases: 12
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-17*
*Last updated: 2026-04-17 after milestone v1.2 definition*
