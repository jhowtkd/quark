# Requirements: Milestone v1.5 Performance & Report Experience

**Defined:** 2026-04-28
**Core Value:** Execute and manage simulations with an intuitive, reliable user interface.
**Previous:** v1.4 Blueprint Noir v2 (complete)

---

## v1.5 Requirements

### Performance & Bundle Optimization (PERF)

- [ ] **PERF-01**: The main JS bundle is under 800KB (gzipped) through code-splitting and lazy loading of heavy components.
- [ ] **PERF-02**: Step4Report.vue (5,400+ lines) is lazy-loaded as a separate chunk, not bundled in the main entry.
- [ ] **PERF-03**: D3 and other heavy dependencies are split into vendor chunks loaded on demand.
- [ ] **PERF-04**: Lighthouse performance score is ≥ 70 on mobile and ≥ 85 on desktop.

### Report Export & Deep Linking (REXP)

- [ ] **REXP-01**: Users can export a completed report as PDF with proper styling, page breaks, and preserved formatting.
- [ ] **REXP-02**: Report URLs include section anchors (e.g., `/report/123#evidencias`) that scroll to the correct section on load.
- [ ] **REXP-03**: A "Copy Link" button generates a shareable URL for the current report view (including active section).
- [ ] **REXP-04**: Exported PDFs include report metadata (title, date, ID) in the header/footer.

### Advanced Report Visualization (RVIZ)

- [ ] **RVIZ-01**: MiniBarChart and MiniSparkline components render inline within report sections when numeric data is detected.
- [ ] **RVIZ-02**: Report tables support column sorting and row hover highlighting.
- [ ] **RVIZ-03**: Data source tags show an interactive tooltip with methodology explanation on hover/focus.
- [ ] **RVIZ-04**: Collapsible sections animate smoothly with height transition (respecting prefers-reduced-motion).

### PWA Foundation (PWA)

- [ ] **PWA-01**: A valid Web App Manifest exists with app name, icons, theme colors, and display mode.
- [ ] **PWA-02**: A service worker caches static assets (JS, CSS, fonts) for offline access.
- [ ] **PWA-03**: The app is installable on mobile/desktop with a custom install prompt.
- [ ] **PWA-04**: Offline fallback page shown when the user has no connectivity.

### Quality & Polish (QUAL)

- [ ] **QUAL-01**: End-to-end tests cover critical user paths: login → create project → run simulation → view report.
- [ ] **QUAL-02**: No console warnings or errors in production build after all v1.5 changes.
- [ ] **QUAL-03**: All new code follows the established component patterns (BaseButton, BaseCard, etc.).
- [ ] **QUAL-04**: Technical documentation (ARCHITECTURE.md) is updated to reflect current frontend structure.

---

## Out of Scope

| Feature | Reason |
|---------|--------|
| Backend API changes | Frontend-only milestone; backend changes deferred to v1.6 |
| Real-time data feeds | Requires backend infrastructure not planned for this cycle |
| Multi-user collaboration | Complex auth/permissions work deferred |
| Native mobile app | PWA is the mobile strategy for now |
| LLM provider swap | Backend decision, not frontend UI |

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PERF-01 | Phase 18 | Planned |
| PERF-02 | Phase 18 | Planned |
| PERF-03 | Phase 18 | Planned |
| PERF-04 | Phase 18 | Planned |
| REXP-01 | Phase 19 | Planned |
| REXP-02 | Phase 19 | Planned |
| REXP-03 | Phase 19 | Planned |
| REXP-04 | Phase 19 | Planned |
| RVIZ-01 | Phase 20 | Planned |
| RVIZ-02 | Phase 20 | Planned |
| RVIZ-03 | Phase 20 | Planned |
| RVIZ-04 | Phase 20 | Planned |
| PWA-01 | Phase 21 | Planned |
| PWA-02 | Phase 21 | Planned |
| PWA-03 | Phase 21 | Planned |
| PWA-04 | Phase 21 | Planned |
| QUAL-01 | Phase 22 | Planned |
| QUAL-02 | Phase 22 | Planned |
| QUAL-03 | Phase 22 | Planned |
| QUAL-04 | Phase 22 | Planned |

**Coverage:**
- v1.5 requirements: 20 total
- Mapped to phases: 20
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-28*
*Milestone: v1.5 Performance & Report Experience*
