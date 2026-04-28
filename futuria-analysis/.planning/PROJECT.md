# Quark

## What This Is
Quark is a full-stack application consisting of a Vue.js/Vite frontend, a Python FastAPI backend for simulations, and a Convex database.

## Core Value
Execute and manage simulations with an intuitive, reliable user interface.

## Previous Milestone: v1.1 Edge Label Translation

**Goal:** Translate English edge/relation labels in the graph visualization to Portuguese without modifying backend graph data or simulation flows.

**Target features:**
- Map common graph edge types (e.g., RELATED_TO, HAS_ROLE, LOCATED_IN) to Portuguese translations
- Display translated edge labels in the GraphPanel D3 renderer
- Display translated edge labels in the side-panel detail view
- Keep graph data and backend flow unchanged (display-only translation)

**Status:** Completed 2026-04-16

## Current Milestone: v1.2 Zep Cost Optimization

**Goal:** Reduce Zep ingestion cost and unnecessary rebuilds without degrading graph quality, ontology behavior, or the current user flows.

**Target features:**
- Lower default chunk size and overlap to reduce per-episode credit usage
- Estimate Zep credits before ingestion and expose cost-driving chunk metrics
- Deduplicate repeated chunks before sending data to Zep
- Skip rebuilds when source text and ontology have not changed
- Add a safe incremental ingestion path for small content updates

## Requirements

### Validated
- Existing user authentication flows (Convex)
- Simulation runs and reporting (Python backend)
- Graph building functionality
- Blueprint Noir design system applied across frontend UI (v1.0)
- Buttons, inputs, and cards refactored to Analog Brutalism aesthetic (v1.0)
- Graph edge labels translated to Portuguese in UI without backend graph mutations (v1.1)

### Active
- [ ] Reduce Zep credits consumed by default graph ingestion settings
- [ ] Show estimated ingestion cost before data is sent to Zep
- [ ] Avoid sending duplicate or unchanged content to Zep
- [ ] Support incremental ingestion for small graph source updates
- [ ] Preserve current graph quality, ontology setup, and simulation/reporting flows

### Out of Scope
- Replacing Zep in this milestone
- Changing simulation, reporting, or Convex auth flows
- Altering ontology extraction semantics or Zep entity/edge schemas
- Building a standalone billing dashboard or external finance reporting
- Broad UI redesign unrelated to ingestion cost visibility

## Context
Quark uses Zep for vector memory and entity graph persistence/retrieval in the graph build and simulation/report flows. Current defaults split text into 500-character chunks with 50-character overlap before converting each chunk into a Zep episode, which risks multi-credit episodes and duplicate ingestion. The next milestone focuses on reducing ingestion waste first, then adding rebuild-skip and delta-ingestion behavior so small changes do not trigger a full graph resend.

## Constraints
- **Tech stack**: Existing Vue.js frontend plus Python backend and Zep integration must remain in place.
- **Brownfield safety**: Changes must preserve graph correctness and current simulation/report flows.
- **Cost model**: Zep charges by ingested episode volume, so savings must come primarily from ingestion reduction.
- **Observability**: Cost estimates should be visible before sending data, not only after failures.

## Key Decisions
- **Phase 1**: Used Space Grotesk and Work Sans via Google Fonts and defined global CSS variables for typography and colors in `App.vue` to match Blueprint Noir design system. Replaced legacy `--orange` color tokens across main and auth views.
- **Phase 2**: Refactored buttons, inputs, and cards to Analog Brutalism aesthetic using in-place CSS updates. Enforced 0px border-radius, bottom-border inputs, block-shadow hovers, and monochrome tonal layering across all targeted Vue components.
- **Milestone v1.2 direction**: Optimize Zep usage before considering provider replacement, starting with chunk economics, deduplication, rebuild skipping, and delta ingestion.

## Evolution
This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-17 — Milestone v1.2 started*
