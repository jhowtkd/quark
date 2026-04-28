# Requirements: Milestone v1.4 Blueprint Noir v2

**Defined:** 2026-04-28
**Core Value:** Execute and manage simulations with an intuitive, reliable user interface.

## v1 Requirements

### Dark Mode System (DARK)

- [ ] **DARK-01**: A theme toggle (light/dark/auto) is available in the UI header or settings, persisted to user preferences (Convex).
- [ ] **DARK-02**: All existing screens (auth, dashboard, simulation, graph, report viewer, settings) render correctly in dark mode without visual regressions.
- [ ] **DARK-03**: CSS custom properties (variables) drive theming; no hardcoded colors in components — all colors resolve through tokens.
- [ ] **DARK-04**: The `auto` setting respects `prefers-color-scheme` and updates dynamically without page reload.

### Design System Refinements (DSYS)

- [ ] **DSYS-01**: Blueprint Noir v2 tokens are documented and applied: expanded color palette (surface, elevated, overlay tiers), refined typography scale, and consistent spacing scale (4px base grid).
- [ ] **DSYS-02**: All reusable components (Button, Input, Card, Modal, Select, Table, Badge) are audited and updated to v2 specs: consistent border-radius, shadows, focus rings, and disabled states.
- [ ] **DSYS-03**: Iconography is standardized: single icon library (e.g., Lucide or Phosphor), consistent sizing (16/20/24px), and semantic usage across all screens.
- [ ] **DSYS-04**: A living style guide page/component exists in the app for developers to preview tokens and components in both themes.

### Animations and Micro-interactions (ANIM)

- [ ] **ANIM-01**: Page and route transitions use consistent enter/exit animations (fade/slide) without jank or layout shift.
- [ ] **ANIM-02**: Interactive elements provide immediate visual feedback: hover states (scale, shadow, border), active/pressed states, and focus rings.
- [ ] **ANIM-03**: Loading states use skeleton screens or shimmer placeholders instead of generic spinners for content-heavy areas (reports, graphs, tables).
- [ ] **ANIM-04**: Async operations (simulation runs, ingestion, report generation) show progress indicators with time estimates or step labels where applicable.

### Report Viewer Redesign (RPTV)

- [ ] **RPTV-01**: Reports render in a redesigned layout: clear visual hierarchy, section cards, and scannable structure matching the due-diligence format (Tese, Evidências, Fragilidades, Premissas, Cenários).
- [ ] **RPTV-02**: Quantitative data is presented in interactive tables and inline sparkline/bar mini-charts where appropriate (revenue, margins, deliveries).
- [ ] **RPTV-03**: Data source labels (📊 realizado, 🔮 hipótese, etc.) are visually distinct and accessible (color + icon + tooltip).
- [ ] **RPTV-04**: The viewer supports anchor navigation (jump to section) and a floating/minimap outline for long reports.

### Global UI Polish and Accessibility (POLY)

- [ ] **POLY-01**: All interactive elements meet WCAG 2.1 AA: sufficient color contrast in both themes, focus visibility, and keyboard operability.
- [ ] **POLY-02**: The app is fully usable at 320px width (responsive baseline) and scales gracefully to 1440px+ without awkward whitespace.
- [ ] **POLY-03**: No console warnings or errors related to Vue reactivity, deprecated APIs, or accessibility violations in dev build.
- [ ] **POLY-04**: A final UI consistency audit confirms all screens use v2 tokens, no legacy color values remain, and no visual drift between similar components.

## v2 Requirements

### Advanced UX

- **ADVX-01**: Customizable dashboard layout — users can rearrange, resize, or hide report/simulation widgets.
- **ADVX-02**: Keyboard shortcuts and command palette for power users.
- **ADVX-03**: Offline-ready PWA shell with service worker caching for static assets.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Framework migration (Nuxt/Next) | Stay on Vue 3 + Vite to limit risk and scope |
| Real-time collaborative editing | Focus on single-user experience polish first |
| Mobile native app | Responsive web is the target for v1.4 |
| Complete brand redesign | Evolve Blueprint Noir, not replace it |
| Multi-language UI (i18n) | Report language is profile-driven; UI stays Portuguese for now |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DARK-01 | Phase 13 | Planned |
| DARK-02 | Phase 13 | Planned |
| DARK-03 | Phase 13 | Planned |
| DARK-04 | Phase 13 | Planned |
| DSYS-01 | Phase 14 | Planned |
| DSYS-02 | Phase 14 | Planned |
| DSYS-03 | Phase 14 | Planned |
| DSYS-04 | Phase 14 | Planned |
| ANIM-01 | Phase 15 | Planned |
| ANIM-02 | Phase 15 | Planned |
| ANIM-03 | Phase 15 | Planned |
| ANIM-04 | Phase 15 | Planned |
| RPTV-01 | Phase 16 | Planned |
| RPTV-02 | Phase 16 | Planned |
| RPTV-03 | Phase 16 | Planned |
| RPTV-04 | Phase 16 | Planned |
| POLY-01 | Phase 17 | Planned |
| POLY-02 | Phase 17 | Planned |
| POLY-03 | Phase 17 | Planned |
| POLY-04 | Phase 17 | Planned |

**Coverage:**
- v1 requirements: 20 total
- Mapped to phases: 20
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-28*
*Milestone: v1.4 Blueprint Noir v2*
