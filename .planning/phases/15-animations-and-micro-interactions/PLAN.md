# Plan: Phase 15 — Animations and Micro-interactions

**Phase:** 15  
**Goal:** The UI feels responsive and alive through purposeful motion and clear loading states.  
**Requirements:** ANIM-01, ANIM-02, ANIM-03, ANIM-04  
**Defined:** 2026-04-28  
**Depends on:** Phase 14 (completed)

---

## Context

Phase 14 established a design system with base components and tokens. However, the UI currently lacks motion:

- **No route transitions**: Page changes are abrupt — the router-view renders instantly with no fade or slide.
- **Minimal hover feedback**: Some buttons have hover states, but inputs, cards, and links lack consistent feedback.
- **No skeleton loading**: Content-heavy areas (reports, graphs, tables) show generic spinners or blank space while loading.
- **No progress indicators**: Long-running operations (simulation runs, graph builds, ingestion) show only a spinner with no step labels or time estimates.

### Current State
| Area | Current | Target |
|------|---------|--------|
| Route changes | Instant | Fade/slide transition |
| Button hover | Basic color change | Translate + shadow shift (brutalist) |
| Card hover | None | Subtle lift or border glow |
| Input focus | Border color | Border color + glow |
| Loading graphs | Spinner or blank | Skeleton nodes/edges placeholder |
| Loading reports | Spinner | Skeleton paragraphs + table rows |
| Loading simulations | Spinner | Step-by-step progress with labels |

---

## Architecture Decisions

1. **Vue `<Transition>` for routes**: Wrap `<router-view>` in a `<Transition name="page">` with fade + slight slide.
2. **CSS transitions for micro-interactions**: All hover/active states use `transition: all 0.15s ease` (fast, snappy).
3. **Skeleton components**: Create `SkeletonBlock`, `SkeletonText`, `SkeletonTable`, `SkeletonGraph` in `components/skeleton/`.
4. **Progress steps component**: Create `ProgressSteps` for long-running operations with labeled steps.
5. **No external animation libraries**: Use only Vue built-ins and CSS transitions to keep bundle size minimal.

---

## Plan Steps

### Step 1 — Route/page transitions
**File:** `frontend/src/App.vue`

Wrap `<router-view>` in a `<Transition>`:

```vue
<router-view v-slot="{ Component }">
  <Transition name="page" mode="out-in">
    <component :is="Component" />
  </Transition>
</router-view>
```

Add CSS:
```css
.page-enter-active,
.page-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.page-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.page-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
```

This ensures all route changes have a consistent, subtle fade+slide.

### Step 2 — Enhance base component micro-interactions
**Files:** `frontend/src/components/base/*.vue`

#### BaseButton
- Already has hover/active for brutalist variant.
- Add for non-brutalist: `transform: translateY(-1px)` on hover + `box-shadow: var(--shadow-soft)`.
- Add `transition: all 0.15s ease` to all variants.
- Add ripple/press effect on active: `transform: scale(0.98)`.

#### BaseInput
- Add focus glow: `box-shadow: 0 0 0 3px rgba(var(--color-primary-rgb), 0.15)` — but since we don't have RGB tokens, use a subtle border glow instead.
- Actually, simpler: on focus, add `outline: 2px solid var(--color-primary)` with `outline-offset: 2px` — but this conflicts with global focus. Instead, enhance the bottom border transition: make it thicker (3px) and add a subtle shadow below.

#### BaseCard
- Add hover: `transform: translateY(-2px)` + `box-shadow: var(--shadow-md)` for elevated variant.
- Add transition.

#### BaseBadge
- Add hover: `opacity: 0.85` for clickable badges.

#### BaseModal
- Already has enter/leave transition. Enhance with a subtle scale:
  ```css
  .modal-enter-from .modal-content { transform: scale(0.96); opacity: 0; }
  .modal-enter-to .modal-content { transform: scale(1); opacity: 1; }
  .modal-enter-active .modal-content { transition: all 0.2s ease; }
  ```

### Step 3 — Create skeleton loading components
**Directory:** `frontend/src/components/skeleton/`

#### SkeletonBlock
A rectangular placeholder with shimmer animation.
Props: `width`, `height`, `rounded` (boolean).

#### SkeletonText
Multiple lines of text placeholder.
Props: `lines` (number), `lastLineWidth` (e.g., '60%').

#### SkeletonTable
Table header + row placeholders.
Props: `rows`, `columns`.

#### SkeletonGraph
A placeholder that mimics a graph layout — circle nodes + line edges in gray.
Props: `nodeCount`.

All skeletons use a shimmer animation:
```css
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
.skeleton {
  background: linear-gradient(90deg, var(--color-surface-container-low) 25%, var(--color-surface) 50%, var(--color-surface-container-low) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
```

### Step 4 — Replace spinners with skeletons
**Files:** Views and components with content loading

Identify loading areas and replace:

1. **ReportView.vue**: While report loads → show `SkeletonText` (3-4 lines) + `SkeletonTable`.
2. **GraphPanel.vue**: While graph loads → show `SkeletonGraph`.
3. **HistoryDatabase.vue**: While history loads → show `SkeletonTable`.
4. **MainView.vue**: While dashboard loads → show `SkeletonCard` grid.

Each view likely has a `loading` or `isLoading` state. Wrap content:
```vue
<div v-if="loading">
  <SkeletonText :lines="4" />
  <SkeletonTable :rows="5" :columns="3" />
</div>
<div v-else>
  <!-- actual content -->
</div>
```

### Step 5 — Create ProgressSteps component
**File:** `frontend/src/components/ProgressSteps.vue`

A vertical or horizontal step indicator for long-running operations.

Props:
- `steps`: Array<{ label, status: 'pending' | 'active' | 'completed' | 'error' }>
- `currentStep`: number
- `orientation`: 'horizontal' | 'vertical'

Visual:
- Completed: check icon + solid line
- Active: spinning loader + bold label + pulse dot
- Pending: circle outline + muted label
- Error: x icon + red line

Add CSS transitions for step state changes.

### Step 6 — Add progress steps to long operations
**Files:** Process.vue, Step1GraphBuild.vue, Step3Simulation.vue

Identify long-running operations and add `ProgressSteps`:

1. **Graph build** (Step1 → Process): Steps = ["Upload", "Ontology", "Graph", "Ready"]
2. **Simulation run** (Step3): Steps = ["Setup", "Agents", "Execution", "Report"]
3. **Report generation**: Steps = ["Data", "Analysis", "Writing", "Review"]

Pass the current step index based on backend status or local state.

### Step 7 — Link hover animations
**File:** `frontend/src/App.vue` (global styles)

Add global link hover:
```css
a {
  transition: color 0.15s ease;
}
a:hover {
  color: var(--color-link-hover);
}
```

### Step 8 — Scroll-triggered fade-in (optional)
**File:** `frontend/src/App.vue` or composable

For long pages (Home, Report), add a simple fade-in on scroll:
```css
.fade-in {
  opacity: 0;
  transform: translateY(16px);
  transition: opacity 0.4s ease, transform 0.4s ease;
}
.fade-in.visible {
  opacity: 1;
  transform: translateY(0);
}
```

Use `IntersectionObserver` in a `useFadeIn` composable. This is optional but adds polish.

---

## Verification

### Tests

1. **Route transitions**: Navigate between all routes — each should fade + slide smoothly.
2. **Hover states**: Hover over every button, card, link, badge — all should respond visually within 150ms.
3. **Skeleton loading**: Throttle network to 3G and verify skeletons appear before content.
4. **Progress steps**: Start a simulation/graph build and verify steps update visually.

### Checklist

- [ ] ANIM-01: Route transitions are smooth, consistent, no jank
- [ ] ANIM-02: All interactive elements have visible hover, active, focus feedback
- [ ] ANIM-03: Content-heavy loading areas use skeleton placeholders
- [ ] ANIM-04: Long operations show progress steps with labels

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Too many animations feel distracting | Keep durations short (150-200ms), use subtle transforms |
| Skeleton flash (skeleton → content too fast) | Add a minimum display time (300ms) for skeletons |
| Progress steps out of sync with backend | Drive steps from existing status polling, don't add new endpoints |

---

## Effort Estimate

| Step | Estimated Time |
|------|---------------|
| Step 1: Route transitions | 15min |
| Step 2: Enhance base components | 1h |
| Step 3: Create skeleton components | 1.5h |
| Step 4: Replace spinners with skeletons | 1.5h |
| Step 5: Create ProgressSteps | 1h |
| Step 6: Add progress to operations | 1h |
| Step 7: Link hover | 5min |
| Step 8: Scroll fade-in (optional) | 30min |
| **Total** | **~7–8h** |

---

## Post-Phase

After Phase 15 completes:
- Phase 16 (Report Viewer Redesign) can leverage skeleton components for report loading.
- The app feels significantly more polished and responsive.

---
*Plan created: 2026-04-28*
*Next: Execute with `/gsd:execute-phase 15` or begin implementation*
