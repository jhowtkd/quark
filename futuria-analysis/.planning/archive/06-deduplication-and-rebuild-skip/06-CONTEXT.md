---
status: ready
phase: 06-deduplication-and-rebuild-skip
gathered: 2026-04-20
---

# Phase 6: Deduplication and Rebuild Skip - Context

**Gathered:** 2026-04-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Prevent duplicate and unchanged content from being sent to Zep during rebuild workflows. This phase adds:
1. Exact duplicate chunk removal before `add_batch` ingestion
2. Signature-based comparison to detect unchanged text/ontology
3. Skip behavior when no changes detected (with forced rebuild override)

</domain>

<decisions>
## Implementation Decisions

### Deduplication
- Remove exact duplicate chunks before sending to Zep via `add_batch`
- Use a set-based deduplication on the chunk strings
- Preserve chunk order for the first occurrence of each unique chunk

### Rebuild Skip
- Store SHA-256 signatures of extracted text and ontology JSON on successful build
- Compare signatures on rebuild requests
- If signatures match, skip Zep ingestion and return success immediately
- If signatures differ, proceed with normal build

### Visibility
- Skip behavior logged via TaskManager messages
- Frontend shows "No changes detected — skipping rebuild" message

### Forced Rebuild
- `force=true` bypasses signature comparison and always rebuilds
- Force flag resets project state as currently implemented

### Claude's Discretion
- Signature storage format (file vs project metadata) at Claude's discretion
- Deduplication can be done in `TextProcessor.split_text` or in `GraphBuilderService.add_text_batches`

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Project` model already stores `chunk_size`, `chunk_overlap`, `graph_id`, `graph_build_task_id`
- `ProjectManager.save_project()` persists project metadata as JSON
- `ProjectManager.save_extracted_text()` saves raw text to file
- `TextProcessor.split_text()` produces chunk list
- `GraphBuilderService.add_text_batches()` sends chunks to Zep

### Established Patterns
- Project state transitions: CREATED → ONTOLOGY_GENERATED → GRAPH_BUILDING → GRAPH_COMPLETED
- `force` flag in build endpoint resets state for rebuilds
- TaskManager updates provide progress visibility

### Integration Points
- Text signature: compute after `save_extracted_text`, store in project metadata
- Ontology signature: compute after ontology generation, store in project metadata
- Deduplication: best done right after `split_text` in build worker
- Skip detection: in build endpoint before creating task

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>
