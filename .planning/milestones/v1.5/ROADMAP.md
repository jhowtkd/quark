# Roadmap: Quark — Milestone v1.5

## Proposed Roadmap

**5 phases** | **20 requirements mapped** | All covered ✓

## Phases

- [ ] **Phase 18: Bundle Optimization & Code Splitting** — Reduce main JS chunk, lazy-load heavy components, split vendor chunks.
- [ ] **Phase 19: Report Export & Deep Linking** — PDF export, section anchor URLs, shareable links.
- [ ] **Phase 20: Advanced Report Visualization** — Integrate mini-charts, table sorting, tag tooltips, smooth animations.
- [ ] **Phase 21: PWA Foundation** — Web App Manifest, service worker, offline caching, install prompt.
- [ ] **Phase 22: Quality & Polish** — E2E tests, Lighthouse audit, docs update, final consistency pass.

## Phase Details

### Phase 18: Bundle Optimization & Code Splitting
**Goal**: The app loads fast on all connections by splitting code intelligently and reducing the main bundle.
**Depends on**: Phase 17 (completed)
**Requirements**: [PERF-01, PERF-02, PERF-03, PERF-04]
**Success Criteria**:
  1. Main JS chunk < 800KB gzipped.
  2. Step4Report.vue loads as a separate chunk.
  3. D3 is only loaded when graph viewer is active.
  4. Lighthouse performance ≥ 70 mobile, ≥ 85 desktop.
**Plans**: 1 plan (18-01)

### Phase 19: Report Export & Deep Linking
**Goal**: Reports are shareable and exportable, extending their utility beyond the app.
**Depends on**: Phase 18
**Requirements**: [REXP-01, REXP-02, REXP-03, REXP-04]
**Success Criteria**:
  1. One-click PDF export preserves all report styling.
  2. URL anchors scroll to correct sections on page load.
  3. Shareable links include report ID and optional section anchor.
  4. PDF includes metadata header/footer.
**Plans**: 1 plan (19-01)

### Phase 20: Advanced Report Visualization
**Goal**: Reports are more informative and interactive with inline charts and enhanced data presentation.
**Depends on**: Phase 19
**Requirements**: [RVIZ-01, RVIZ-02, RVIZ-03, RVIZ-04]
**Success Criteria**:
  1. Mini-charts render automatically when numeric tables are detected.
  2. Tables support client-side sorting.
  3. Data source tags have rich tooltips with methodology.
  4. Section collapse/expand animates smoothly.
**Plans**: 1 plan (20-01)

### Phase 21: PWA Foundation
**Goal**: The app is installable and works offline for static assets.
**Depends on**: Phase 20
**Requirements**: [PWA-01, PWA-02, PWA-03, PWA-04]
**Success Criteria**:
  1. Valid manifest passes Lighthouse PWA audit.
  2. Static assets are cached and served offline.
  3. Install prompt appears on supported browsers.
  4. Offline fallback page is shown when API is unreachable.
**Plans**: 1 plan (21-01)

### Phase 22: Quality & Polish
**Goal**: The milestone ships with confidence through testing, auditing, and documentation.
**Depends on**: Phase 21
**Requirements**: [QUAL-01, QUAL-02, QUAL-03, QUAL-04]
**Success Criteria**:
  1. E2E tests cover login → project → simulation → report flow.
  2. Zero console warnings in production.
  3. All new components follow v2 design system.
  4. ARCHITECTURE.md reflects current codebase structure.
**Plans**: 1 plan (22-01)

---

## Progress

**Execution Order:**
Phases execute in numeric order: 18, 19, 20, 21, 22

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 18. Bundle Optimization | 0/0 | Planned | — |
| 19. Report Export | 0/0 | Planned | — |
| 20. Advanced Visualization | 0/0 | Planned | — |
| 21. PWA Foundation | 0/0 | Planned | — |
| 22. Quality & Polish | 0/0 | Planned | — |

---
*Roadmap created: 2026-04-28*
*Milestone: v1.5 Performance & Report Experience*
