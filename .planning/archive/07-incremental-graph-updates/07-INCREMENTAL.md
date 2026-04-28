# Incremental Graph Updates — Design Document

## Overview

Phase 7 introduces safe delta ingestion for changed content while preserving the existing full rebuild fallback. When source text changes slightly, only the modified chunks are sent to Zep instead of resending the entire graph.

## How Chunk Diffing Works

1. **Text Splitting**: The source text is split into chunks using `TextProcessor.split_text(chunk_size, chunk_overlap)`.
2. **Deduplication**: Exact duplicate chunks are removed via `TextProcessor.deduplicate_chunks()`.
3. **Signature Comparison**: Each chunk is hashed with SHA-256. The resulting signatures are compared against `project.chunk_signatures` from the previous build.
4. **Change Detection**: Chunks whose signatures are not in the stored list are considered "changed" and sent to Zep.

## When Incremental Path Is Used

The incremental path is used when ALL of the following are true:
- `incremental=true` is passed in the build request
- The project has a `graph_id` from a previous build
- `force=false`
- Changed chunks are ≤ 50% of total chunks
- No exceptions occur during diffing

## When Fallback to Full Rebuild Occurs

Fallback happens when ANY of the following is true:
- `incremental=false` (default)
- No stored `chunk_signatures`
- Changed chunks > 50% of total
- `chunk_size` or `chunk_overlap` changed from previous build
- `force=true`
- Any exception during diffing
- Project has no `graph_id`

## API Changes

### POST /api/graph/build

**New parameter:**
- `incremental` (bool, optional, default false) — Enable incremental ingestion

**Responses:**

- **Incremental build started:**
  ```json
  {
    "success": true,
    "data": {
      "project_id": "...",
      "task_id": "...",
      "message": "...",
      "incremental": true
    }
  }
  ```

- **No changes detected (skip):**
  ```json
  {
    "success": true,
    "data": {
      "project_id": "...",
      "message": "No changes detected — skipping rebuild",
      "skipped": true
    }
  }
  ```

- **Full rebuild (fallback):** Same as existing build response

## Safety Guarantees

1. **Default is safe**: Incremental is opt-in (`incremental=false` by default)
2. **Fallback on ambiguity**: Any uncertainty routes to full rebuild
3. **No graph corruption**: Incremental uses the same `add_batch` API as full builds
4. **Existing flows untouched**: Simulation, reporting, and other flows remain functional
5. **Signatures are deterministic**: SHA-256 over UTF-8 bytes ensures consistent comparisons

## Data Storage

- `project.chunk_signatures`: List of SHA-256 hex strings, one per chunk
- Stored in project JSON metadata via `ProjectManager.save_project()`
- Updated after every successful build (full or incremental)

## Future Considerations

- More sophisticated diff algorithms (e.g., fuzzy matching) could reduce false positives
- Chunk signature compression for large documents
- Background reconciliation of stale incremental-ingestion metadata (OPT-03 in v2)
