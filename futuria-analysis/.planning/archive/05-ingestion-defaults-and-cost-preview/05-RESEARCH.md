<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INGEST-01 | Default graph-build chunk sizing is reduced to a cost-safer range so typical chunks are less likely to exceed Zep's single-credit episode threshold. | Use the same local splitter as production, then pick a default below the 350-byte billing step and verify it with exact UTF-8 byte counts per chunk [CITED: https://www.getzep.com/pricing/][CITED: https://help.getzep.com/v2/adding-data-to-the-graph][VERIFIED: /Users/jhonatan/Repos/Quark/backend/app/utils/file_parser.py]. |
| INGEST-02 | Default chunk overlap is reduced to minimize duplicate ingestion while preserving graph extraction quality. | Keep overlap modest, compute it from the same splitter, and validate graph quality on representative docs because Zep recommends small chunks for better entity/relationship capture [CITED: https://help.getzep.com/chunking-large-documents][VERIFIED: /Users/jhonatan/Repos/Quark/backend/app/utils/file_parser.py]. |
| INGEST-03 | Users can still override chunk size and overlap when building a graph. | The backend already accepts `chunk_size` and `chunk_overlap`, but the live frontend auto-starts build without any override UI, so the phase needs an explicit settings surface [VERIFIED: /Users/jhonatan/Repos/Quark/backend/app/api/graph.py][VERIFIED: /Users/jhonatan/Repos/Quark/frontend/src/views/MainView.vue]. |
| COST-01 | Before sending data to Zep, the system computes and exposes estimated chunk count, estimated byte size, and estimated Zep credit usage for the current build settings. | Reuse the saved extracted text plus the production splitter, then sum UTF-8 bytes and bill credits by `ceil(bytes / 350)` because Zep bills episodes above 350 bytes in multiples [CITED: https://www.getzep.com/pricing/][VERIFIED: /Users/jhonatan/Repos/Quark/backend/app/models/project.py][VERIFIED: /Users/jhonatan/Repos/Quark/backend/app/services/text_processor.py]. |
| COST-02 | If estimated ingestion size is unusually high, the user-facing flow surfaces a clear warning before full ingestion starts. | The current flow auto-starts build immediately after ontology generation, so phase 5 must insert a preview/confirm gate before ingestion begins [VERIFIED: /Users/jhonatan/Repos/Quark/frontend/src/views/MainView.vue]. |
| SAFE-01 | Ontology creation and graph schema behavior remain unchanged by cost optimization work. | Ontology generation happens before graph chunking; phase 5 should not touch `set_ontology` or the ontology generator [VERIFIED: /Users/jhonatan/Repos/Quark/backend/app/api/graph.py][VERIFIED: /Users/jhonatan/Repos/Quark/backend/app/services/graph_builder.py]. |
</phase_requirements>

# Phase 5: Ingestion Defaults and Cost Preview - Research

**Researched:** 2026-04-17
**Domain:** Zep ingestion economics, chunking, and preview UX
**Confidence:** HIGH

## Summary

Current ingestion defaults are still `500/50` in `Config`, `Project`, `TextProcessor`, and the `/graph/build` fallback path [VERIFIED: /Users/jhonatan/Repos/Quark/backend/app/config.py][VERIFIED: /Users/jhonatan/Repos/Quark/backend/app/models/project.py][VERIFIED: /Users/jhonatan/Repos/Quark/backend/app/services/text_processor.py][VERIFIED: /Users/jhonatan/Repos/Quark/backend/app/api/graph.py]. Zep's current pricing docs say each Episode costs 1 credit and episodes larger than 350 bytes are billed in multiples, while the ingestion docs cap each episode at 10,000 characters and recommend small chunks for better entity capture [CITED: https://www.getzep.com/pricing/][CITED: https://help.getzep.com/v2/adding-data-to-the-graph][CITED: https://help.getzep.com/chunking-large-documents]. The current UI does not expose chunk controls or a cost preview; `MainView.vue` auto-starts build immediately after ontology generation, so users cannot review or override spend before ingestion begins [VERIFIED: /Users/jhonatan/Repos/Quark/frontend/src/views/MainView.vue][VERIFIED: /Users/jhonatan/Repos/Quark/frontend/src/components/Step1GraphBuild.vue].

Primary recommendation: switch to a server-side preflight preview, compute it from the saved extracted text with the same splitter and UTF-8 byte counts, and gate build start behind an explicit user confirmation. The phase proceeds with `300/30` as the baseline because it keeps chunks under Zep's 350-byte billing step for typical Latin-text corpora while preserving the current ~10% overlap ratio and staying within Zep's "small chunk" guidance [CITED: https://help.getzep.com/chunking-large-documents][CITED: https://www.getzep.com/pricing/]. The remaining default and threshold choices are resolved below.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| File upload and text extraction | API / Backend | Database / Storage | The server already extracts text, preprocesses it, and persists the saved snapshot that preview should read [VERIFIED: /Users/jhonatan/Repos/Quark/backend/app/api/graph.py][VERIFIED: /Users/jhonatan/Repos/Quark/backend/app/models/project.py]. |
| Cost estimation | API / Backend | Browser / Client | Preview must run from the saved extracted text so the estimate matches the live build path instead of a stale client copy [VERIFIED: /Users/jhonatan/Repos/Quark/backend/app/models/project.py][VERIFIED: /Users/jhonatan/Repos/Quark/backend/app/services/text_processor.py]. |
| Chunk setting controls and confirmation | Browser / Client | API / Backend | The UI needs to let users override `chunk_size` and `chunk_overlap`, but the backend must validate them again before build [VERIFIED: /Users/jhonatan/Repos/Quark/frontend/src/views/MainView.vue][VERIFIED: /Users/jhonatan/Repos/Quark/backend/app/api/graph.py]. |
| Ontology generation | API / Backend | - | Ontology is produced before graph chunking and should remain untouched in this phase [VERIFIED: /Users/jhonatan/Repos/Quark/backend/app/api/graph.py]. |
| Zep ingestion | API / Backend | External Zep Cloud | The backend owns `graph.add_batch` and the task/progress lifecycle; Zep remains an external boundary [VERIFIED: /Users/jhonatan/Repos/Quark/backend/app/services/graph_builder.py][CITED: https://help.getzep.com/adding-batch-data]. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard | Source |
|---------|---------|---------|--------------|--------|
| Flask | `>=3.0.0` | API surface for graph routes | Already the backend HTTP framework in the repo [VERIFIED: /Users/jhonatan/Repos/Quark/backend/pyproject.toml]. | Repo pin |
| zep-cloud | `3.13.0` | Zep Graph ingestion client | Current repo pin; keep the existing SDK for this phase [VERIFIED: /Users/jhonatan/Repos/Quark/backend/pyproject.toml][VERIFIED: https://pypi.org/project/zep-cloud/]. | Repo pin + PyPI |
| Vue | `3.5.24` | Frontend UI | Existing frontend framework and component model [VERIFIED: /Users/jhonatan/Repos/Quark/frontend/package.json]. | Repo pin |
| Vite | `7.2.4` | Frontend build tool | Existing build pipeline for the Vue app [VERIFIED: /Users/jhonatan/Repos/Quark/frontend/package.json]. | Repo pin |

### Supporting
| Library | Version | Purpose | When to Use | Source |
|---------|---------|---------|-------------|--------|
| vue-router | `4.6.3` | Route-level UI flow | Needed because `Process` route resolves to `MainView.vue` [VERIFIED: /Users/jhonatan/Repos/Quark/frontend/src/router/index.js]. | Repo pin |
| axios | `1.14.0` | API calls | Existing HTTP client for the frontend API layer [VERIFIED: /Users/jhonatan/Repos/Quark/frontend/package.json]. | Repo pin |
| pytest | `8.2.0` | Backend validation | Available through `uv run pytest` on this host [VERIFIED: local command output]. | Host + backend lock |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Exact local preview | Character-count-only estimate | Faster, but it underestimates billing because Zep charges by bytes, not characters [CITED: https://www.getzep.com/pricing/]. |
| Server-side preview | Client-side preview in Vue only | Easier to wire up, but it drifts from the saved extracted text and can become stale [VERIFIED: /Users/jhonatan/Repos/Quark/backend/app/models/project.py]. |
| Auto-start build on ontology success | Explicit build confirmation | One more click, but it prevents accidental credit burn and makes warnings actionable [VERIFIED: /Users/jhonatan/Repos/Quark/frontend/src/views/MainView.vue][CITED: https://help.getzep.com/cookbook/check-data-ingestion-status]. |

**Installation:**
No new package is required for this phase. Keep the existing `uv sync` backend workflow and `npm install` / `npm run build` frontend workflow [VERIFIED: /Users/jhonatan/Repos/Quark/backend/pyproject.toml][VERIFIED: /Users/jhonatan/Repos/Quark/frontend/package.json].

## Architecture Patterns

### System Architecture Diagram

```text
Upload files
  -> /graph/ontology/generate
  -> extract + preprocess text
  -> save extracted_text.txt and ontology
  -> preview endpoint computes:
       split_text(text, chunk_size, overlap)
       -> UTF-8 byte count per chunk
       -> ceil(bytes / 350) credits
       -> warning level + reason
  -> user confirms / overrides chunk settings
  -> /graph/build
  -> create graph
  -> set ontology
  -> split_text(text, chunk_size, overlap)
  -> graph.add_batch(episodes)
  -> task/episode progress
  -> graph data fetch
```

Requirements for the diagram:
- The preview step must be a real gate between ontology success and ingestion start [VERIFIED: /Users/jhonatan/Repos/Quark/frontend/src/views/MainView.vue].
- The preview must use the same splitter as production, not a separate client-side approximation [VERIFIED: /Users/jhonatan/Repos/Quark/backend/app/services/text_processor.py][VERIFIED: /Users/jhonatan/Repos/Quark/backend/app/utils/file_parser.py].
- The ingest path should remain backend-owned; the browser only renders settings, warnings, and confirmation [VERIFIED: /Users/jhonatan/Repos/Quark/frontend/src/components/Step1GraphBuild.vue].

### Recommended Project Structure
```text
backend/
  app/
    services/
      ingest_cost_estimator.py   # pure preview math: bytes, chunks, credits, warnings
    api/
      graph.py                   # preview endpoint + build gate
frontend/
  src/
    components/
      Step1GraphBuild.vue        # preview card, override controls, warning state
    views/
      MainView.vue               # no auto-start; confirm before build
```

### Pattern 1: Exact Local Preview
**What:** Run the same preprocessing and splitter used by the live build, then sum UTF-8 bytes and compute credits from the 350-byte billing step [CITED: https://www.getzep.com/pricing/][VERIFIED: /Users/jhonatan/Repos/Quark/backend/app/services/text_processor.py].

**When to use:** Any time the UI needs a pre-ingestion cost estimate that should match the eventual backend build as closely as possible.

**Example:**
```python
# Source: repo splitter + Zep pricing docs
chunks = TextProcessor.split_text(text, chunk_size, overlap)
byte_sizes = [len(chunk.encode("utf-8")) for chunk in chunks]
estimated_credits = sum(math.ceil(size / 350) for size in byte_sizes)
estimated_bytes = sum(byte_sizes)
warning = estimated_credits >= 25 or len(chunks) >= 25  # resolved phase-5 warning heuristic
```

### Pattern 2: Explicit Build Gate
**What:** Do not auto-start ingestion after ontology generation; show a preview summary and require a deliberate confirmation action before calling `/graph/build` [VERIFIED: /Users/jhonatan/Repos/Quark/frontend/src/views/MainView.vue].

**When to use:** Always for phase 5, because the user must be able to inspect cost and override chunk settings before spending credits.

**Example:**
```json
{
  "project_id": "proj_123",
  "chunk_size": 300,
  "chunk_overlap": 30,
  "confirm_preview": true
}
```

### Anti-Patterns to Avoid
- **Character-only cost math:** Do not estimate by `len(text)` alone; Zep bills by bytes and the docs explicitly call out the 350-byte step [CITED: https://www.getzep.com/pricing/].
- **Auto-starting the build:** Do not keep the current immediate `startBuildGraph()` behavior if the user has not seen the estimate yet [VERIFIED: /Users/jhonatan/Repos/Quark/frontend/src/views/MainView.vue].
- **Duplicate splitter logic:** Do not copy the chunking algorithm into the frontend; keep one backend splitter as the source of truth [VERIFIED: /Users/jhonatan/Repos/Quark/backend/app/utils/file_parser.py].
- **Persisting stale previews:** Do not store the estimate as authoritative state; compute it on demand from the saved extracted text snapshot [VERIFIED: /Users/jhonatan/Repos/Quark/backend/app/models/project.py].

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Credit estimation | A separate client-only heuristic | Backend preview helper that reuses the production splitter | Keeps preview aligned with the actual build path and billing step [CITED: https://www.getzep.com/pricing/][VERIFIED: /Users/jhonatan/Repos/Quark/backend/app/services/text_processor.py]. |
| Chunk boundary logic | A second split algorithm in the UI | `TextProcessor.split_text` / `split_text_into_chunks` | One source of truth avoids drift and makes preview tests straightforward [VERIFIED: /Users/jhonatan/Repos/Quark/backend/app/services/text_processor.py][VERIFIED: /Users/jhonatan/Repos/Quark/backend/app/utils/file_parser.py]. |
| Cost warning thresholds | Scattered hard-coded constants in Vue | One backend response shape with `warning_level` + `warning_reason` | Keeps the UI thin and makes threshold tuning testable. |
| Build gating | Ad hoc modal logic in multiple components | One explicit confirm step in the routed build view | Prevents the current auto-start flow from spending credits before review [VERIFIED: /Users/jhonatan/Repos/Quark/frontend/src/views/MainView.vue]. |

**Key insight:** phase 5 is not a billing dashboard; it is a preflight safety gate. The cheapest reliable implementation is to compute a single authoritative preview on the server and let the browser render it [VERIFIED: /Users/jhonatan/Repos/Quark/backend/app/models/project.py][CITED: https://help.getzep.com/cookbook/check-data-ingestion-status].

## Common Pitfalls

### Pitfall 1: Counting characters instead of bytes
**What goes wrong:** The preview looks cheap, but the build still burns multiple credits because Zep bills episodes larger than 350 bytes in multiples [CITED: https://www.getzep.com/pricing/].
**Why it happens:** The existing splitter is character-based, while billing is byte-based.
**How to avoid:** Compute `len(chunk.encode("utf-8"))` for every chunk before showing the preview [VERIFIED: /Users/jhonatan/Repos/Quark/backend/app/utils/file_parser.py].
**Warning signs:** High-cost builds whose preview says "1 credit per chunk" even when chunks are near the threshold.

### Pitfall 2: Leaving the auto-start flow intact
**What goes wrong:** The system starts ingestion immediately after ontology generation, so the user never sees the estimate.
**Why it happens:** `MainView.vue` calls `startBuildGraph()` right after ontology success and on reload when the project is in `ontology_generated` state [VERIFIED: /Users/jhonatan/Repos/Quark/frontend/src/views/MainView.vue].
**How to avoid:** Replace auto-start with a preview step and a confirm button.
**Warning signs:** Builds begin before the user touches the chunk controls.

### Pitfall 3: Editing the wrong Vue file
**What goes wrong:** A change lands in `Process.vue` but the live route still uses `MainView.vue`.
**Why it happens:** The router maps `Process` to `MainView.vue`, not to `Process.vue` [VERIFIED: /Users/jhonatan/Repos/Quark/frontend/src/router/index.js].
**How to avoid:** Update the routed component and treat `Process.vue` as a stale duplicate unless the router changes.
**Warning signs:** Code review shows the wrong file changed, but the UI behavior does not move.

### Pitfall 4: Overlap too low for boundary context
**What goes wrong:** Credit usage drops, but entity/relationship extraction loses cross-chunk continuity.
**Why it happens:** Smaller overlap reduces duplication, but it also removes repeated context at chunk boundaries; Zep docs explicitly say small chunks help graph quality, so the phase should not over-correct [CITED: https://help.getzep.com/chunking-large-documents].
**How to avoid:** Keep overlap modest, validate on representative docs, and compare graph quality before/after.
**Warning signs:** Fewer edges, weaker summaries, or more orphaned entities after lowering overlap.

## Code Examples

Verified patterns from official sources and the current repo:

### Preview Estimation
```python
# Source: repo splitter + Zep pricing docs
chunks = TextProcessor.split_text(text, chunk_size, overlap)
estimated_bytes = sum(len(chunk.encode("utf-8")) for chunk in chunks)
estimated_credits = sum(math.ceil(len(chunk.encode("utf-8")) / 350) for chunk in chunks)
```

### Batch Ingestion Status
```python
# Source: Zep docs
result = client.graph.add_batch(graph_id=graph_id, episodes=episodes)
task_id = result[0].task_id
status = client.task.get(task_id=task_id)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Fixed `500/50` chunk defaults | `300/30` chunk defaults with legacy normalization | Phase 5 | Fewer multi-credit episodes for typical text, while persisted legacy records do not keep the old baseline. |
| Character-only preview | Exact UTF-8 byte preview per chunk | Phase 5 | Preview tracks Zep billing instead of papering over it. |
| Auto-start ingestion after ontology | Explicit preview and confirmation | Phase 5 | Users can override chunk settings before spending credits. |
| Batch status via per-episode polling | `client.task.get()` for batch operations | Zep current docs [CITED: https://help.getzep.com/cookbook/check-data-ingestion-status] | One task-level status check is simpler and less noisy. |

**Deprecated/outdated:**
- `500/50` as the default tuning target for this milestone [VERIFIED: /Users/jhonatan/Repos/Quark/backend/app/config.py].
- Client-side cost guesses based only on characters [CITED: https://www.getzep.com/pricing/].
- Immediate `startBuildGraph()` after ontology success [VERIFIED: /Users/jhonatan/Repos/Quark/frontend/src/views/MainView.vue].

## Resolved Decisions

| # | Decision | Sections | Why it was resolved this way |
|---|----------|----------|------------------------------|
| D1 | Use `300/30` as the phase-5 baseline, and normalize persisted `500/50` records to the new baseline on load/build. | Summary / State of the Art / Must-Haves | It stays below Zep's 350-byte billing step for typical Latin-text corpora while preventing legacy records from preserving the old defaults. |
| D2 | Keep the preview on the build route as a `preview` branch rather than a separate endpoint. | Summary / Architecture Patterns | The same backend validation and normalization path should serve both preview and real build so the estimate cannot drift from the actual ingestion settings. |
| D3 | Warn on high-cost previews and require explicit user confirmation for every real build, rather than auto-blocking on preview cost alone. | Pattern 2 / Common Pitfalls / State of the Art | The confirmation gate already prevents accidental spend; the warning explains why the build is expensive without adding another blocking state. |

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python | Backend preview helpers and pytest | Yes | 3.14.3 | - |
| Node | Frontend build and browser UI checks | Yes | v24.3.0 | - |
| npm | Frontend build | Yes | 11.4.2 | - |
| uv | Backend test runner | Yes | 0.11.6 | - |
| pytest | Backend validation | Yes | 8.2.0 | - |

**Missing dependencies with no fallback:**
- None.

**Missing dependencies with fallback:**
- None.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `pytest 8.2.0` for backend checks, `npm run build` for frontend compile validation, browser smoke on the Process route for the preview gate |
| Config file | none - see Wave 0 [VERIFIED: /Users/jhonatan/Repos/Quark/.planning/config.json absent] |
| Quick run command | `uv run pytest -q backend/tests/services/test_graph_cost_preview.py` |
| Full suite command | `uv run pytest -q backend/tests/services/test_graph_chunk_defaults.py backend/tests/services/test_graph_cost_preview.py backend/tests/services/test_graph_safety.py && cd frontend && npm run build` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INGEST-01 | Reduced default chunk size | unit | `uv run pytest -q backend/tests/services/test_graph_chunk_defaults.py::test_default_chunk_size` | No [VERIFIED: /Users/jhonatan/Repos/Quark repo] - Wave 0 |
| INGEST-02 | Reduced overlap without losing boundary context | unit | `uv run pytest -q backend/tests/services/test_graph_chunk_defaults.py::test_default_overlap_and_split_behavior` | No [VERIFIED: /Users/jhonatan/Repos/Quark repo] - Wave 0 |
| INGEST-03 | Override chunk size/overlap through build request and UI | integration | `uv run pytest -q backend/tests/services/test_graph_safety.py::test_build_accepts_chunk_overrides` | No [VERIFIED: /Users/jhonatan/Repos/Quark repo] - Wave 0 |
| COST-01 | Preview bytes/chunks/credits before ingestion | unit | `uv run pytest -q backend/tests/services/test_graph_cost_preview.py::test_preview_counts_bytes_and_credits` | No [VERIFIED: /Users/jhonatan/Repos/Quark repo] - Wave 0 |
| COST-02 | Warning for expensive builds | unit | `uv run pytest -q backend/tests/services/test_graph_cost_preview.py::test_preview_warning_level` | No [VERIFIED: /Users/jhonatan/Repos/Quark repo] - Wave 0 |
| SAFE-01 | Ontology behavior unchanged | integration | `uv run pytest -q backend/tests/services/test_graph_safety.py::test_preview_does_not_mutate_ontology` | No [VERIFIED: /Users/jhonatan/Repos/Quark repo] - Wave 0 |

### Sampling Rate
- Per task commit: `uv run pytest -q backend/tests/services/test_graph_cost_preview.py`
- Per wave merge: `uv run pytest -q backend/tests/services/test_graph_chunk_defaults.py backend/tests/services/test_graph_cost_preview.py backend/tests/services/test_graph_safety.py && cd frontend && npm run build`
- Phase gate: backend tests green, frontend build green, and a browser smoke check confirms preview rendering and no auto-start before `/gsd-verify-work`

### Wave 0 Gaps
- `backend/tests/services/test_graph_chunk_defaults.py` - reduced defaults and legacy normalization.
- `backend/tests/services/test_graph_cost_preview.py` - pure preview math, bytes/chunks/credits, warning threshold coverage.
- `backend/tests/services/test_graph_safety.py` - ontology isolation, preview/build separation, and no mutation during preview.
- Frontend has no browser test harness in `frontend/package.json`, so preview/banner UX needs a documented browser smoke check during execution unless a UI test harness is added [VERIFIED: /Users/jhonatan/Repos/Quark/frontend/package.json].

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | No new auth mechanism is introduced in this phase. |
| V3 Session Management | no | No new session state is introduced in this phase. |
| V4 Access Control | yes | Reuse the current authenticated project flow and validate project ownership again on the backend before preview/build. |
| V5 Input Validation | yes | Validate/clamp `chunk_size`, `chunk_overlap`, and confirm flags with a shared Pydantic or explicit validator path [VERIFIED: /Users/jhonatan/Repos/Quark/backend/pyproject.toml]. |
| V6 Cryptography | no | No new crypto or secret handling is needed. |

### Known Threat Patterns for Flask/Vue + Zep

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Oversized `chunk_size` / negative `overlap` | DoS / Tampering | Clamp values server-side, reject invalid ranges, and recompute preview at build start. |
| Stale preview vs actual build settings | Tampering | Include the selected chunk settings in the preview response and revalidate the same values before build. |
| Cost blowup from accidental auto-start | DoS | Insert the confirmation gate and keep the build start backend-owned. |

## Sources

### Primary (HIGH confidence)
- `/Users/jhonatan/Repos/Quark/backend/app/config.py` - current default chunk settings [VERIFIED: repo].
- `/Users/jhonatan/Repos/Quark/backend/app/models/project.py` - persisted chunk defaults and extracted text snapshot [VERIFIED: repo].
- `/Users/jhonatan/Repos/Quark/backend/app/api/graph.py` - ontology generation, build fallback defaults, and auto-start flow [VERIFIED: repo].
- `/Users/jhonatan/Repos/Quark/backend/app/services/text_processor.py` - splitter entry point [VERIFIED: repo].
- `/Users/jhonatan/Repos/Quark/backend/app/utils/file_parser.py` - sentence-aware chunking implementation [VERIFIED: repo].
- `/Users/jhonatan/Repos/Quark/backend/app/services/graph_builder.py` - batch ingestion and ontology setup [VERIFIED: repo].
- `/Users/jhonatan/Repos/Quark/frontend/src/router/index.js` - active route points `Process` to `MainView.vue` [VERIFIED: repo].
- `/Users/jhonatan/Repos/Quark/frontend/src/views/MainView.vue` - live build auto-start flow [VERIFIED: repo].
- `/Users/jhonatan/Repos/Quark/frontend/src/components/Step1GraphBuild.vue` - current UI has stats/logs but no chunk override controls [VERIFIED: repo].
- `/Users/jhonatan/Repos/Quark/backend/pyproject.toml` - backend dependencies and pytest availability [VERIFIED: repo].
- `/Users/jhonatan/Repos/Quark/frontend/package.json` - frontend dependencies and lack of test script [VERIFIED: repo].
- `https://www.getzep.com/pricing/` - credit billing and 350-byte episode step [CITED].
- `https://help.getzep.com/v2/adding-data-to-the-graph` - 10,000 character limit and small-chunk guidance [CITED].
- `https://help.getzep.com/adding-batch-data` - batch limits and experimental behavior [CITED].
- `https://help.getzep.com/chunking-large-documents` - chunking best practices and contextualized retrieval [CITED].
- `https://help.getzep.com/cookbook/check-data-ingestion-status` - task polling recommendation for batch ops [CITED].
- `https://pypi.org/project/zep-cloud/` - current release history and latest SDK version [VERIFIED].

### Secondary (MEDIUM confidence)
- None.

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - current repo pins and current official docs were checked.
- Architecture: HIGH - live route ownership, auto-start behavior, and saved-text snapshot path were verified in the repo.
- Pitfalls: HIGH - pitfalls are directly grounded in the code and the current Zep docs.

**Research date:** 2026-04-17
**Valid until:** 2026-05-17
