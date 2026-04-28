# Roadmap: Quark

## Proposed Roadmap

**5 phases** | **20 requirements mapped** | All covered ✓

## Phases

- [x] **Phase 13: Dark Mode System** — Implement system-wide dark mode with CSS variables, toggle, and auto preference detection.
- [ ] **Phase 14: Design System Refinements** — Evolve Blueprint Noir v2 tokens, audit components, standardize icons, and build a living style guide.
- [ ] **Phase 15: Animations and Micro-interactions** — Add page transitions, hover/active feedback, skeleton loading, and progress indicators.
- [ ] **Phase 16: Report Viewer Redesign** — Rebuild report layout with cards, interactive tables, mini-charts, and section navigation.
- [ ] **Phase 17: Global UI Polish and Accessibility** — WCAG 2.1 AA audit, responsive refinements, console cleanup, and final consistency pass.

## Phase Details

### Phase 13: Dark Mode System
**Goal**: Every screen renders correctly in light, dark, and auto modes via a token-driven CSS variable system.
**Depends on**: Phase 12 (completed)
**Requirements**: [DARK-01, DARK-02, DARK-03, DARK-04]
**Success Criteria** (what must be TRUE):
  1. User can toggle light/dark/auto and preference persists across sessions.
  2. All screens (auth, dashboard, simulation, graph, report, settings) show no visual regressions in either theme.
  3. Zero hardcoded hex/rgb colors in component styles — all via CSS custom properties.
  4. Auto mode reacts live to OS `prefers-color-scheme` changes.
**Plans**: 1 plan (13-01)

### Phase 14: Design System Refinements
**Goal**: Establish and apply Blueprint Noir v2 design tokens consistently across all reusable components.
**Depends on**: Phase 13
**Requirements**: [DSYS-01, DSYS-02, DSYS-03, DSYS-04]
**Success Criteria** (what must be TRUE):
  1. Token documentation exists and is discoverable in the running app (style guide).
  2. All target components match v2 specs for radius, shadow, focus, and disabled states.
  3. Single icon library is adopted and legacy icons are replaced.
  4. Developers can preview any token/component in both themes from the style guide.
**Plans**: 0 plans

### Phase 15: Animations and Micro-interactions
**Goal**: The UI feels responsive and alive through purposeful motion and clear loading states.
**Depends on**: Phase 14
**Requirements**: [ANIM-01, ANIM-02, ANIM-03, ANIM-04]
**Success Criteria** (what must be TRUE):
  1. Route transitions are smooth and consistent (no flash of unstyled content).
  2. Every interactive element has visible hover, active, and focus states.
  3. Content-heavy loading areas use skeleton placeholders, not generic spinners.
  4. Long-running operations show progress (step labels or time estimates).
**Plans**: 0 plans

### Phase 16: Report Viewer Redesign
**Goal**: Reports are scannable, visually rich, and easy to navigate with interactive data presentation.
**Depends on**: Phase 15
**Requirements**: [RPTV-01, RPTV-02, RPTV-03, RPTV-04]
**Success Criteria** (what must be TRUE):
  1. Report layout follows the 5-section due-diligence structure with clear visual hierarchy.
  2. Tables and mini-charts render inline for key metrics.
  3. Data source tags are accessible and visually distinct.
  4. Users can navigate long reports via anchor links or a floating outline.
**Plans**: 0 plans

### Phase 17: Global UI Polish and Accessibility
**Goal**: The app meets professional accessibility and responsiveness standards with zero known UI drift.
**Depends on**: Phase 16
**Requirements**: [POLY-01, POLY-02, POLY-03, POLY-04]
**Success Criteria** (what must be TRUE):
  1. WCAG 2.1 AA contrast and keyboard requirements pass in both themes.
  2. Layout is usable from 320px to 1440px+ without horizontal scroll or broken grids.
  3. Dev build produces zero console warnings/errors related to UI.
  4. Consistency audit confirms 100% token adoption and no legacy style leakage.
**Plans**: 0 plans

## Progress

**Execution Order:**
Phases execute in numeric order: 13, 14, 15, 16, 17

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 13. Dark Mode System | 1/1 | Complete | 2026-04-28 |
| 14. Design System Refinements | 0/0 | Planned | — |
| 15. Animations and Micro-interactions | 0/0 | Planned | — |
| 16. Report Viewer Redesign | 0/0 | Planned | — |
| 17. Global UI Polish and Accessibility | 0/0 | Planned | — |
