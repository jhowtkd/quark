---
status: ready
phase: 07-incremental-graph-updates
gathered: 2026-04-20
---

# Phase 7: Incremental Graph Updates - Context

**Gathered:** 2026-04-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Support safe delta ingestion for changed content while preserving existing full rebuild fallback. This phase adds:
1. Diffing changed source content against prior ingestion state
2. Incremental ingestion path that sends only changed chunks
3. Automatic fallback to full rebuild when diff is ambiguous or unsupported

</domain>

<decisions>
## Implementation Decisions

### Chunk Diffing
- Store chunk-level signatures (SHA-256) from the previous ingestion
- Compare chunk signatures between old and new text splits
- Chunks with matching signatures are skipped; only new/modified chunks are sent

### Incremental Ingestion Path
- Use Zep's `add_batch` with only the changed chunks
- Preserve existing graph_id (do not create a new graph)
- Update stored chunk signatures after successful incremental ingestion

### Fallback Conditions
- Fallback to full rebuild when:
  - Chunk count changes by more than 50%
  - Overlap settings changed
  - Force flag is set
  - Any ambiguity in diffing

### Safety
- Graph build, simulation, and reporting flows remain untouched
- Incremental path is opt-in via a new `incremental=true` flag (default false for safety)
- Full rebuild path stays as default behavior

### Claude's Discretion
- Chunk signature storage format (embedded in project vs separate file)
- Diff algorithm (simple signature comparison vs more sophisticated diff)
- Threshold for fallback decision

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `TextProcessor.split_text()` produces chunks
- `TextProcessor.compute_signature()` gives chunk signatures
- `Project` model already stores `text_signature` and `ontology_signature`
- `GraphBuilderService.add_text_batches()` sends chunks to Zep
- `GraphBuilderService._build_graph_worker()` is the build entry point

### Established Patterns
- Build flow: split → deduplicate → add_batch → wait_for_episodes
- Project state transitions: ONTOLOGY_GENERATED → GRAPH_BUILDING → GRAPH_COMPLETED
- Signatures stored in project metadata

### Integration Points
- Chunk signature storage: extend Project model or store alongside extracted text
- Diff logic: after `split_text` and `deduplicate_chunks`, compare with stored signatures
- Incremental path: reuse `add_text_batches` with subset of chunks
- Fallback: route to existing full rebuild worker

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>
