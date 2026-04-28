# Roadmap: Quark

## Proposed Roadmap

**3 phases** | **12 requirements mapped** | All covered ✓

## Phases

- [x] **Phase 5: Ingestion Defaults and Cost Preview** - Reduce baseline Zep ingestion cost by tuning chunk defaults and surfacing preflight cost estimates. (completed 2026-04-20)
- [x] **Phase 6: Deduplication and Rebuild Skip** - Avoid sending repeated or unchanged content to Zep during graph rebuilds. (completed 2026-04-20)
- [x] **Phase 7: Incremental Graph Updates** - Add a safe delta-ingestion path so small source changes do not trigger a full resend. (completed 2026-04-20)

## Phase Details

### Phase 5: Ingestion Defaults and Cost Preview
**Goal**: Tune chunking economics and give users visibility into estimated Zep cost before ingestion begins.
**Depends on**: Phase 4 (completed)
**Requirements**: [INGEST-01, INGEST-02, INGEST-03, COST-01, COST-02, SAFE-01]
**Success Criteria** (what must be TRUE):
  1. Default chunk size is reduced from the current 500-character setting to a safer cost-oriented default.
  2. Default chunk overlap is reduced from the current 50-character setting while remaining configurable.
  3. Preflight build flow reports estimated chunk count, byte volume, and estimated Zep credits before ingestion.
  4. High-cost builds surface a warning before full ingestion starts.
  5. Existing graph creation and ontology setup behavior remain intact.
**Plans**: 1 plan

- [x] 05-01-PLAN.md — Reduce chunk defaults, add preview gate, and surface cost warning

### Phase 6: Deduplication and Rebuild Skip
**Goal**: Prevent duplicate and unchanged content from being sent to Zep during rebuild workflows.
**Depends on**: Phase 5
**Requirements**: [BUILD-01, BUILD-02, BUILD-03]
**Success Criteria** (what must be TRUE):
  1. Exact duplicate chunks are removed before `add_batch` ingestion.
  2. Rebuild requests compare current extracted text and ontology against stored signatures.
  3. Unchanged builds skip unnecessary Zep ingestion instead of resending all chunks.
  4. Skip behavior is visible through logs or task messages.
  5. Forced rebuild paths still work when users explicitly need a full resend.
**Plans**: 0 plans

### Phase 7: Incremental Graph Updates
**Goal**: Support safe delta ingestion for changed content while preserving existing full rebuild fallback.
**Depends on**: Phase 6
**Requirements**: [DELTA-01, DELTA-02, SAFE-02]
**Success Criteria** (what must be TRUE):
  1. Changed source content can be diffed against prior ingestion state.
  2. Only changed chunks are sent through the incremental ingestion path when safe.
  3. Unsupported or ambiguous diffs fall back automatically to the existing full rebuild path.
  4. Graph build, simulation, and reporting flows remain functional after incremental-update support lands.
  5. Incremental-update behavior is documented well enough for future phase planning and verification.
**Plans**: 0 plans

## Progress

**Execution Order:**
Phases execute in numeric order: 5, 6, 7

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 5. Ingestion Defaults and Cost Preview | 1/1 | Complete    | 2026-04-20 |
| 6. Deduplication and Rebuild Skip | 1/1 | Complete    | 2026-04-20 |
| 7. Incremental Graph Updates | 1/1 | Complete    | 2026-04-20 |
