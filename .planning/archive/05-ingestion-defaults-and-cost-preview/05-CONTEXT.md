---
status: ready
phase: 05-ingestion-defaults-and-cost-preview
gathered: 2026-04-20
---

# Phase 5: Ingestion Defaults and Cost Preview - Context

**Gathered:** 2026-04-20
**Status:** Ready for planning
**Mode:** Auto-generated (implementation already completed)

<domain>
## Phase Boundary

Tune the graph-build defaults to reduce Zep spend, add a backend preflight cost estimate, and force the user to see that estimate before the real ingestion task starts.

</domain>

<decisions>
## Implementation Decisions

### Chunk Defaults
- Default chunk size: 300 (reduced from 500)
- Default chunk overlap: 30 (reduced from 50)
- Legacy persisted 500/50 values are normalized to 300/30 on project load
- Users can override both settings before build

### Cost Preview
- Preview endpoint: POST /api/graph/build with preview=true
- Estimates: chunk count, total bytes, estimated Zep credits
- Warning threshold: 25 credits
- Preview does not create tasks or call Zep

### Build Gate
- User must request preview before confirming build
- Changing chunk settings clears stale preview
- Confirm button only enables after successful preview and valid ontology guardrails

### Claude's Discretion
- All implementation choices already made and tested — pure infrastructure phase completed before autonomous run.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- TextProcessor.split_text() and estimate_ingestion_cost() already implemented
- Step1GraphBuild.vue already has preview card, warning display, and confirm button
- MainView.vue already handles preview/confirm flow

### Established Patterns
- Backend uses Flask with Config constants
- Frontend uses Vue 3 with props/emits for chunk settings
- Tests use pytest with monkeypatch for isolation

### Integration Points
- Chunk settings flow: Config → Project → API → Frontend
- Preview flow: API → TextProcessor → Frontend display → User confirm → Real build

</code_context>

<specifics>
## Specific Ideas

Implementation completed before autonomous run. Tests pass (9/9), frontend builds successfully.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>
