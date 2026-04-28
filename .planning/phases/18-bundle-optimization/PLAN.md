# Plan: Phase 18 — Bundle Optimization & Code Splitting

**Phase:** 18  
**Goal:** Reduce main JS bundle, lazy-load heavy components, and split vendor chunks for faster initial load.  
**Requirements:** PERF-01, PERF-02, PERF-03, PERF-04  
**Defined:** 2026-04-28  
**Depends on:** Phase 17 (completed)

---

## Context

The frontend bundle at the end of v1.4:
- Main JS chunk: ~1,169KB (~335KB gzipped)
- CSS: ~213KB (~28KB gzipped)
- StyleGuide lazy chunk: ~11KB

The largest contributors to the main bundle:
1. **Step4Report.vue** (~5,400 lines) — loaded on every route even though it's only used in ReportView
2. **D3** (~300KB+) — only needed for GraphPanel, but loaded globally
3. **Vue + Vue Router + Pinia + i18n** — core framework, unavoidable
4. **Step2EnvSetup.vue, Step3Simulation.vue, Step5Interaction.vue** — large step components loaded eagerly

Current Vite config uses default chunking with no manual chunks.

---

## Architecture Decisions

1. **Lazy load route components**: Convert all route-level components to `defineAsyncComponent` or dynamic `import()` in router.
2. **Manual vendor chunks**: Split D3, agentation, and other heavy deps into separate chunks via `build.rollupOptions.output.manualChunks`.
3. **Lazy load Step4Report**: Move Step4Report to a dynamic import within ReportView so it's only fetched when viewing a report.
4. **Keep core UI in main chunk**: App.vue, base components, useTheme, and router stay in the main chunk for fast initial paint.

---

## Plan Steps

### Step 1 — Audit current bundle composition
**File:** `frontend/vite.config.js`

1. Add `rollup-plugin-visualizer` to analyze bundle composition
2. Run build and inspect the generated stats.html
3. Document the top 10 largest modules and their sizes

### Step 2 — Configure manual chunks
**File:** `frontend/vite.config.js`

Add manual chunk splitting:
```js
build: {
  rollupOptions: {
    output: {
      manualChunks: {
        'vendor-vue': ['vue', 'vue-router', 'pinia'],
        'vendor-ui': ['vue-i18n'],
        'vendor-d3': ['d3'],
        'vendor-agentation': ['agentation'],
      }
    }
  }
}
```

Also consider chunking by route:
- `chunk-report`: Step4Report + report-related components
- `chunk-graph`: GraphPanel + D3 visualization code
- `chunk-simulation`: Step2EnvSetup + Step3Simulation + Step5Interaction

### Step 3 — Lazy load route components
**File:** `frontend/src/router/index.js`

Convert all route components to dynamic imports:
```js
{
  path: '/report/:reportId',
  component: () => import('../views/ReportView.vue'),
  // ...
}
```

Already lazy-loaded: StyleGuide.vue
Need to convert: Home.vue, Process.vue, SimulationView.vue, ReportView.vue, InteractionView.vue, LoginPage.vue, RegisterPage.vue

Keep eagerly loaded: App.vue (root), MainView.vue (if it's the dashboard shell)

### Step 4 — Lazy load Step4Report within ReportView
**File:** `frontend/src/views/ReportView.vue`

Currently Step4Report is statically imported. Convert to:
```js
import { defineAsyncComponent } from 'vue'
const Step4Report = defineAsyncComponent(() => import('../components/Step4Report.vue'))
```

Add a skeleton placeholder while Step4Report loads.

### Step 5 — Verify and measure
**Command:** `npm run build`

1. Verify build succeeds with no new warnings
2. Compare bundle sizes before/after:
   - Main chunk should be < 800KB
   - Step4Report should be a separate chunk
   - D3 should only appear in graph-related chunk
3. Run Lighthouse performance audit (if available)
4. Remove rollup-plugin-visualizer from build config

---

## Verification

### Tests

1. **Build**: `npm run build` succeeds without errors.
2. **Route loading**: Each route loads its chunk on first navigation.
3. **Report view**: Step4Report chunk loads with skeleton placeholder.
4. **Graph view**: D3 chunk loads when graph is first rendered.
5. **Lighthouse**: Performance score ≥ 70 mobile, ≥ 85 desktop.

### Checklist

- [x] PERF-01: Main JS bundle < 800KB (gzipped) — achieved 120KB entry point
- [x] PERF-02: Step4Report.vue loads as separate chunk (76KB)
- [x] PERF-03: D3 (62KB), React (11KB), i18n (54KB), framework (110KB) split into vendor chunks
- [ ] PERF-04: Lighthouse performance ≥ 70 mobile, ≥ 85 desktop — pending Lighthouse run

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Lazy loading causes route navigation delay | Add skeleton loaders for async components |
| D3 chunk still large | Consider tree-shaking D3 imports (import specific modules) |
| Code splitting breaks HMR in dev | Test dev server after each change |
| Too many small chunks hurt performance | Balance chunk count vs. size |

---

## Effort Estimate

| Step | Estimated Time |
|------|---------------|
| Step 1: Audit bundle composition | 30min |
| Step 2: Configure manual chunks | 1h |
| Step 3: Lazy load route components | 1h |
| Step 4: Lazy load Step4Report | 1h |
| Step 5: Verify and measure | 1h |
| **Total** | **~4.5h** |

---

## Post-Phase

After Phase 18 completes:
- Phase 19 (Report Export & Deep Linking) can begin.
- The app should feel noticeably faster on first load.

---
*Plan created: 2026-04-28*
*Next: Execute with `/gsd:execute-phase 18` or begin implementation*
