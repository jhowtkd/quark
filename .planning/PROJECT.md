# Quark

## What This Is
Quark is a full-stack application consisting of a Vue.js/Vite frontend, a Python FastAPI backend for simulations, and a Convex database.

## Core Value
Execute and manage simulations with an intuitive, reliable user interface.

## Previous Milestone: v1.3 Report Quality Improvement

**Goal:** Eliminate factual errors, source confusion, and analytical bias from AI-generated economy/finance reports so every report is trustworthy, transparent, and investment-grade.

**Target features:**
- Strict separation of real data, consensus estimates, projections, and simulation artifacts in report output
- Pre-report data validation pipeline that cross-checks key metrics against known public sources
- Structured report format with explicit tese, evidências verificadas, fragilidades, premissas e cenários
- Bias detection and neutrality enforcement in analytical narrative
- Clear GAAP vs non-GAAP distinction and contextualization for financial metrics

**Status:** Completed 2026-04-27

## Current Milestone: v1.4 Blueprint Noir v2

**Goal:** Evolve the user interface across all screens with a refined design system, dark mode, purposeful animations, and a redesigned report viewer for a professional, accessible, and delightful experience.

**Target features:**
- System-wide dark mode (light/dark/auto) with CSS variable-driven theming
- Blueprint Noir v2 design tokens: expanded palette, refined typography, consistent spacing
- Animations and micro-interactions: route transitions, hover/active feedback, skeleton loading, progress indicators
- Report viewer redesign: card-based layout, interactive tables, mini-charts, anchor navigation
- Accessibility and responsiveness: WCAG 2.1 AA, 320px–1440px+ coverage, zero console warnings

## Requirements

### Validated
- Existing user authentication flows (Convex)
- Simulation runs and reporting (Python backend)
- Graph building functionality
- Blueprint Noir design system applied across frontend UI (v1.0)
- Buttons, inputs, and cards refactored to Analog Brutalism aesthetic (v1.0)
- Graph edge labels translated to Portuguese in UI without backend graph mutations (v1.1)
- Zep ingestion cost optimization: chunk defaults, cost preview, deduplication, rebuild skip, incremental updates (v1.2)
- **v1.3 — Report Quality Improvement (Phases 8-12):**
  - Data provenance and labeling: every data point tagged as realizado, consenso, projeção, or simulação — Phase 8
  - Data validation pipeline: key financial metrics cross-checked before generation with GAAP/non-GAAP distinction — Phase 9
  - Structured report format: due-diligence structure (Tese, Evidencias, Fragilidades, Premissas, Cenarios) — Phase 10
  - Neutrality and bias audit: confirmation bias detection, claim strength calibration, competitive quantification — Phase 11
  - Output quality gates: language consistency, Known Limitations auto-append, numeric sanity, self-contradiction detection — Phase 12

### Active
- **v1.4 — Blueprint Noir v2 (Phases 13-17):**
  - Dark mode system: toggle, auto preference, CSS variables, full-screen coverage — Phase 13
  - Design system refinements: v2 tokens, component audit, icon standardization, living style guide — Phase 14
  - Animations and micro-interactions: transitions, hover states, skeletons, progress indicators — Phase 15
  - Report viewer redesign: cards, tables, mini-charts, data source tags, anchor nav — Phase 16
  - Global UI polish and accessibility: WCAG AA, responsive, console cleanup, consistency audit — Phase 17

### Out of Scope
- Replacing the underlying LLM provider in this milestone
- Building a real-time financial data API integration (use curated validation, not live feeds)
- Changing simulation, graph build, or Convex auth flows
- Framework migration (Nuxt/Next) — remain on Vue 3 + Vite
- Real-time collaborative editing
- Mobile native app
- Multi-language UI (i18n)

## Context
Quark generates AI-powered economy and finance reports via the Python backend. After hardening report quality in v1.3, the next priority is the user experience: the app must look and feel professional, accessible, and modern. Blueprint Noir v2 evolves the existing design system rather than replacing it, adding dark mode support, purposeful motion, and a significantly improved report reading experience. All changes stay within the Vue 3 + Vite stack to limit risk.

## Constraints
- **Tech stack**: Existing Vue.js frontend, Python backend, and LLM integration must remain in place.
- **Brownfield safety**: Changes must preserve current simulation/report flows while improving the UI.
- **Accessibility**: All new UI work must meet WCAG 2.1 AA standards.
- **Responsive**: Must work from 320px mobile to 1440px+ desktop.

## Key Decisions
- **Phase 1**: Used Space Grotesk and Work Sans via Google Fonts and defined global CSS variables for typography and colors in `App.vue` to match Blueprint Noir design system. Replaced legacy `--orange` color tokens across main and auth views.
- **Phase 2**: Refactored buttons, inputs, and cards to Analog Brutalism aesthetic using in-place CSS updates. Enforced 0px border-radius, bottom-border inputs, block-shadow hovers, and monochrome tonal layering across all targeted Vue components.
- **Milestone v1.2 direction**: Optimize Zep usage before considering provider replacement, starting with chunk economics, deduplication, rebuild skipping, and delta ingestion.
- **Milestone v1.3 direction**: Harden report quality through data validation, structured output format, and bias/neutrality enforcement before expanding report domains.
- **Milestone v1.4 direction**: Evolve the entire UI with dark mode, design system v2, animations, and report viewer redesign while staying on Vue 3 + Vite.

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
*Last updated: 2026-04-28 — Milestone v1.4 started*
