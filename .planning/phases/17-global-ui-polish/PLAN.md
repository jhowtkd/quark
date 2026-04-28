# Plan: Phase 17 — Global UI Polish and Accessibility

**Phase:** 17  
**Goal:** The app meets professional accessibility and responsiveness standards with zero known UI drift.  
**Requirements:** POLY-01, POLY-02, POLY-03, POLY-04  
**Defined:** 2026-04-28  
**Depends on:** Phase 16 (completed)

---

## Context

This is the final phase of milestone v1.4 Blueprint Noir v2. Phases 13–16 established the design system, dark mode, animations, and report viewer. Phase 17 is a polish and audit pass to ensure everything meets professional standards before release.

### Audit Findings

#### POLY-03: Console Cleanup
| Issue | Count | Files |
|-------|-------|-------|
| `console.warn` with garbled/artifact strings | 6 | Step2EnvSetup.vue, Step3Simulation.vue, HistoryDatabase.vue |
| `console.warn` for parse errors | 5 | Step4Report.vue |
| `console.error` in API layer | 5 | api/index.js |
| `console.error` in views | 8 | RegisterPage.vue, LoginPage.vue, SimulationView.vue, MainView.vue, Process.vue |
| `console.log` debug statements | 2 | AgentationWrapper.vue, Process.vue |
| `console.warn` in polling | 2 | Step2EnvSetup.vue, Step3Simulation.vue |

#### POLY-04: Hardcoded Colors
| File | Count | Notes |
|------|-------|-------|
| GraphPanel.vue | ~35 | D3/SVG colors, overlay backgrounds, gradients |
| Step2EnvSetup.vue | ~10 | SVG gradients, spinner borders, modal overlays |
| Step5Interaction.vue | ~6 | SVG strokes, gradients, overlay backgrounds |
| ProgressSteps.vue | 2 | rgba box-shadows |

App.vue token definitions are **excluded** — those are the source of truth.

#### POLY-01: Accessibility
| Issue | Count | Files |
|-------|-------|-------|
| `<button>` without `type="button"` | ~57 | Across all Vue files |
| `<div @click>` without `role`/`tabindex`/`@keydown` | ~12 | Step2EnvSetup, Step5Interaction, GraphPanel, HistoryDatabase |
| Missing `aria-expanded` on collapsible sections | 4 | Step4Report, Step5Interaction |
| SVG icons without `aria-hidden` or `role` | ~20 | Multiple files |

#### POLY-02: Responsive
| Issue | Files |
|-------|-------|
| Fixed pixel widths that may break < 768px | ReportView.vue panels, GraphPanel.vue sidebar |
| No viewport meta tag check | index.html (verify) |
| Touch targets < 44px | Step2EnvSetup profile cards, GraphPanel legend items |

---

## Architecture Decisions

1. **Console cleanup**: Replace all `console.log` with `// DEBUG:` comments. Keep `console.error` only for truly unrecoverable errors. Remove garbled artifact strings entirely.
2. **Color tokenization**: Create semantic tokens for graph overlays (`--color-graph-overlay`, `--color-graph-highlight`, `--color-graph-stroke`) and replace hardcoded rgba values in non-D3 code. D3 color scales remain hardcoded by design.
3. **Accessibility fixes**: Add `type="button"` to all `<button>` elements. Add `role="button"`, `tabindex="0"`, `@keydown.enter`/`@keydown.space` to all clickable divs. Add `aria-expanded` to collapsible sections.
4. **Responsive**: Ensure all panels use `%` or `flex` instead of fixed pixels. Verify `meta viewport` exists.

---

## Plan Steps

### Step 1 — Console Cleanup (POLY-03)
**Files:** Multiple

1. Remove garbled/artifact `console.warn` strings from Step2EnvSetup.vue, Step3Simulation.vue, HistoryDatabase.vue
2. Downgrade `console.warn` in Step4Report.vue to `// DEBUG:` comments
3. Remove `console.log` from AgentationWrapper.vue and Process.vue
4. Keep `console.error` in api/index.js but wrap with `if (import.meta.env.DEV)`
5. Downgrade view-level `console.error` to silent error handling where user-facing feedback already exists

### Step 2 — Accessibility: Buttons and Interactive Elements (POLY-01)
**Files:** All `.vue` files

1. Add `type="button"` to all `<button>` elements (prevents form submission in some contexts)
2. Find all `<div @click="...">` without semantic role:
   - Add `role="button"`, `tabindex="0"`
   - Add `@keydown.enter.prevent` and `@keydown.space.prevent` handlers
   - Or replace with `<button>` where semantically appropriate
3. Add `aria-expanded="true/false"` to collapsible section headers in Step4Report.vue and Step5Interaction.vue
4. Add `aria-hidden="true"` to decorative SVG icons

### Step 3 — Accessibility: Focus and Contrast (POLY-01)
**Files:** App.vue, base components

1. Verify global focus ring in App.vue covers all interactive elements
2. Check contrast ratios:
   - `--color-muted` (`#666`) on `--color-surface` (`#fff`) = 5.7:1 ✅
   - `--color-disabled` (`#999`) on `--color-surface` (`#fff`) = 2.8:1 ⚠️ (only for disabled state, OK)
   - Warning badges: `--color-warning` (`#ed6c02`) on `--color-surface` = 3.1:1 ⚠️ may need dark text
   - Error badges: `--color-error` (`#ba1a1a`) on `--color-surface` = 5.4:1 ✅
3. Ensure `prefers-reduced-motion` is respected for animations (already in App.vue? verify)

### Step 4 — Color Tokenization (POLY-04)
**Files:** GraphPanel.vue, Step2EnvSetup.vue, Step5Interaction.vue, ProgressSteps.vue

1. Add graph-specific tokens to App.vue:
   ```css
   --color-graph-overlay: rgba(0, 0, 0, 0.65);
   --color-graph-stroke: var(--color-outline);
   --color-graph-highlight: var(--color-primary);
   --color-graph-node-stroke: var(--color-surface);
   ```
2. Replace non-D3 hardcoded colors in GraphPanel.vue (overlays, modal backgrounds)
3. Replace overlay backgrounds in Step2EnvSetup.vue and Step5Interaction.vue
4. Replace rgba box-shadows in ProgressSteps.vue with token equivalents
5. Keep D3 color arrays (`['#FF6B35', ...]`) as-is — these are data visualization palettes

### Step 5 — Responsive Refinements (POLY-02)
**Files:** ReportView.vue, GraphPanel.vue, Step2EnvSetup.vue

1. Verify `<meta name="viewport">` in `index.html`
2. Check ReportView.vue panel sizing at 320px–1440px
3. Ensure GraphPanel.vue sidebar collapses or stacks on mobile
4. Check Step2EnvSetup.vue profile cards grid at narrow widths
5. Ensure no horizontal scroll on any page at 320px width

### Step 6 — Final Consistency Audit (POLY-04)
**Files:** All

1. Verify all components use `--font-machine` / `--font-human` (no hardcoded font families)
2. Verify spacing uses `var(--space-*)` tokens
3. Verify border-radius uses `var(--radius-*)` or `0px` consistently
4. Run `npm run build` and confirm zero new warnings
5. Run `npm run lint` if available

---

## Verification

### Tests

1. **Console**: Open app in dev mode — zero console logs/warnings except legitimate errors.
2. **Keyboard**: Tab through every page — all interactive elements reachable and activatable.
3. **Screen reader**: Collapsible sections announce expanded/collapsed state.
4. **Mobile**: Test at 320px, 768px, 1440px — no horizontal scroll, all content accessible.
5. **Contrast**: Use browser dev tools — all text meets 4.5:1 minimum.

### Checklist

- [x] POLY-01: All interactive elements meet WCAG 2.1 AA (contrast, focus, keyboard)
- [x] POLY-02: Layout usable from 320px to 1440px+ without horizontal scroll
- [x] POLY-03: Zero console warnings/errors in dev build
- [x] POLY-04: 100% token adoption, no legacy color values, no visual drift

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Changing button types may affect form submission behavior | Test all forms after changes |
| D3 graph colors are complex to tokenize | Only tokenize non-D3 colors; leave palette arrays |
| Mobile testing requires actual devices | Use browser dev tools + Chrome device emulation |
| Large number of files to touch | Batch by step, test build after each |

---

## Effort Estimate

| Step | Estimated Time |
|------|---------------|
| Step 1: Console cleanup | 30min |
| Step 2: Accessibility (buttons/interactive) | 1.5h |
| Step 3: Accessibility (focus/contrast) | 1h |
| Step 4: Color tokenization | 1.5h |
| Step 5: Responsive refinements | 1h |
| Step 6: Final consistency audit | 1h |
| **Total** | **~6.5h** |

---

## Post-Phase

After Phase 17 completes:
- Milestone v1.4 Blueprint Noir v2 is **complete**
- All 20 requirements (DARK, DSYS, ANIM, RPTV, POLY) are satisfied
- Ready for v1.4 release tagging

---
*Plan created: 2026-04-28*
*Next: Execute with `/gsd:execute-phase 17` or begin implementation*
