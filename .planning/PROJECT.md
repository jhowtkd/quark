# Quark

## What This Is
Quark is a full-stack application consisting of a Vue.js/Vite frontend, a Python FastAPI backend for simulations, and a Convex database.

## Core Value
Execute and manage simulations with an intuitive, reliable user interface.

## Previous Milestone: v1.2 Zep Cost Optimization

**Goal:** Reduce Zep ingestion cost and unnecessary rebuilds without degrading graph quality, ontology behavior, or the current user flows.

**Target features:**
- Lower default chunk size and overlap to reduce per-episode credit usage
- Estimate Zep credits before ingestion and expose cost-driving chunk metrics
- Deduplicate repeated chunks before sending data to Zep
- Skip rebuilds when source text and ontology have not changed
- Add a safe incremental ingestion path for small content updates

**Status:** Completed 2026-04-20

## Current Milestone: v1.3 Report Quality Improvement

**Goal:** Eliminate factual errors, source confusion, and analytical bias from AI-generated economy/finance reports so every report is trustworthy, transparent, and investment-grade.

**Target features:**
- Strict separation of real data, consensus estimates, projections, and simulation artifacts in report output
- Pre-report data validation pipeline that cross-checks key metrics against known public sources
- Structured report format with explicit tese, evidências verificadas, fragilidades, premissas e cenários
- Bias detection and neutrality enforcement in analytical narrative
- Clear GAAP vs non-GAAP distinction and contextualization for financial metrics

## Requirements

### Validated
- Existing user authentication flows (Convex)
- Simulation runs and reporting (Python backend)
- Graph building functionality
- Blueprint Noir design system applied across frontend UI (v1.0)
- Buttons, inputs, and cards refactored to Analog Brutalism aesthetic (v1.0)
- Graph edge labels translated to Portuguese in UI without backend graph mutations (v1.1)
- Zep ingestion cost optimization: chunk defaults, cost preview, deduplication, rebuild skip, incremental updates (v1.2)
- **v1.3 — Report Quality Improvement (Phase 8-12):**
  - Data provenance and labeling: every data point tagged as 📊 (fato), 🔮 (hipotese), or ⚠️ (dados insuficientes) — Phase 8
  - Data validation pipeline: key financial metrics cross-checked before generation with GAAP/non-GAAP distinction — Phase 9
  - Structured report format: due-diligence structure (Tese, Evidencias, Fragilidades, Premissas, Cenarios) — Phase 10
  - Neutrality and bias audit: confirmation bias detection, claim strength calibration, competitive quantification — Phase 11
  - Output quality gates: language consistency, Known Limitations auto-append, numeric sanity, self-contradiction detection — Phase 12

### Active
None. Milestone v1.3 complete.

### Out of Scope
- Replacing the underlying LLM provider in this milestone
- Building a real-time financial data API integration (use curated validation, not live feeds)
- Changing simulation, graph build, or Convex auth flows
- Broad UI redesign unrelated to report quality

## Context
Quark generates AI-powered economy and finance reports via the Python backend (profiles like "economia"). A recent Tesla report exposed systemic quality issues: mixing simulated and real data without clear labels, factual errors in Q1 2026 EPS (using GAAP as consensus proxy), confirmation bias toward a negative thesis, missing GAAP/non-GAAP distinction, and even mid-report language switching. These defects make reports unreliable for investment decisions. This milestone hardens the report generation pipeline with validation, structure, and neutrality enforcement.

## Constraints
- **Tech stack**: Existing Vue.js frontend, Python backend, and LLM integration must remain in place.
- **Brownfield safety**: Changes must preserve current simulation/report flows while improving output quality.
- **Data availability**: Validation relies on publicly available filings and consensus data, not paid data subscriptions.
- **Neutrality**: Reports must present bull/bear/base scenarios with balanced evidence, not advocacy.

## Key Decisions
- **Phase 1**: Used Space Grotesk and Work Sans via Google Fonts and defined global CSS variables for typography and colors in `App.vue` to match Blueprint Noir design system. Replaced legacy `--orange` color tokens across main and auth views.
- **Phase 2**: Refactored buttons, inputs, and cards to Analog Brutalism aesthetic using in-place CSS updates. Enforced 0px border-radius, bottom-border inputs, block-shadow hovers, and monochrome tonal layering across all targeted Vue components.
- **Milestone v1.2 direction**: Optimize Zep usage before considering provider replacement, starting with chunk economics, deduplication, rebuild skipping, and delta ingestion.
- **Milestone v1.3 direction**: Harden report quality through data validation, structured output format, and bias/neutrality enforcement before expanding report domains.

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
*Last updated: 2026-04-27 — Milestone v1.3 started*
