# Plan: Phase 13 — Dark Mode System

**Phase:** 13  
**Goal:** Every screen renders correctly in light, dark, and auto modes via a token-driven CSS variable system.  
**Requirements:** DARK-01, DARK-02, DARK-03, DARK-04  
**Defined:** 2026-04-28  
**Depends on:** Phase 12 (completed)

---

## Context

The app already has a partial dark mode implementation in `App.vue` (`[data-theme="dark"]` override), but it is incomplete:

- **Duplicated toggle logic**: `App.vue`, `Home.vue`, and `Process.vue` each re-implement theme switching with local state.
- **Hardcoded colors**: 19 Vue files contain 22 `<style>` blocks with hardcoded hex colors (`#000`, `#FFF`, `#F5F5F5`, `#E5E5E5`, `#CCC`, `#FAFAFA`, `#EEE`) inside scoped styles. These do not respond to `[data-theme="dark"]`.
- **No auto mode**: Only light/dark toggle exists; no `prefers-color-scheme` support.
- **Token gaps**: The current token set (~15 properties) does not cover all UI surfaces needed (elevated cards, borders, hover states, disabled states, code blocks, etc.).

### Key Files
| File | Role |
|------|------|
| `frontend/src/App.vue` | Global tokens, dark override, profile colors, global reset |
| `frontend/src/main.js` | App bootstrap |
| `frontend/src/views/Home.vue` | Duplicated toggle, heavy scoped styles with hardcoded colors |
| `frontend/src/views/Process.vue` | Duplicated toggle, heavy scoped styles with hardcoded colors |
| `frontend/src/views/LoginPage.vue` | Scoped styles, likely hardcoded colors |
| `frontend/src/views/RegisterPage.vue` | Scoped styles, likely hardcoded colors |
| `frontend/src/views/MainView.vue` | Scoped styles |
| `frontend/src/views/InteractionView.vue` | Scoped styles |
| `frontend/src/views/ReportView.vue` | Scoped styles |
| `frontend/src/views/SimulationView.vue` | Scoped styles |
| `frontend/src/views/SimulationRunView.vue` | Scoped styles |
| `frontend/src/components/*.vue` | 10 component files with scoped styles |

---

## Architecture Decisions

1. **Single source of truth**: Extract all theme logic (read, write, persist, auto-detect) into a `useTheme` composable at `frontend/src/composables/useTheme.js`.
2. **Three modes**: `light` | `dark` | `auto`. Auto uses `matchMedia('(prefers-color-scheme: dark)')`.
3. **Persistence**: Store preference in `localStorage` as `futuria_theme` (backward-compatible key). On `auto`, do not write `data-theme`; let the CSS `@media (prefers-color-scheme: dark)` handle it.
4. **Token expansion**: Expand the `:root` token set in `App.vue` to cover all semantic surfaces, then add `[data-theme="dark"]` overrides for each.
5. **Hardcoded color audit**: Use a systematic file-by-file pass to replace hex/rgb colors with CSS custom properties. No new colors should be introduced.

---

## Plan Steps

### Step 1 — Create `useTheme` composable
**File:** `frontend/src/composables/useTheme.js`

Implement:
- `theme` ref with values `'light' | 'dark' | 'auto'`
- `effectiveTheme` computed: resolves `auto` → `prefers-color-scheme`
- `setTheme(mode)` — persists to `localStorage`, sets/unsets `data-theme` on `<html>`, adds/removes media listener
- `toggleTheme()` — cycles light → dark → auto → light
- `initTheme()` — reads `localStorage` on app mount, applies immediately (call from `App.vue`)
- Expose reactive state so any component can bind to it

**Cleanup:**
- Remove theme toggle logic from `App.vue` script (keep the token CSS)
- Remove theme toggle logic from `Home.vue` script
- Remove theme toggle logic from `Process.vue` script
- Replace inline toggle buttons in `Home.vue` and `Process.vue` with calls to `useTheme().toggleTheme()`

### Step 2 — Expand CSS token system in `App.vue`
**File:** `frontend/src/App.vue` (unscoped `<style>` block)

Expand `:root` tokens to a complete semantic palette:

```
--color-background        (page bg)
--color-surface           (cards, panels)
--color-surface-elevated  (modals, dropdowns, popovers)
--color-surface-overlay   (tooltips, toasts)
--color-on-background     (primary text on bg)
--color-on-surface        (primary text on surface)
--color-on-primary        (text on primary button)
--color-primary           (brand/action)
--color-primary-hover     (action hover)
--color-primary-active    (action pressed)
--color-secondary         (secondary action)
--color-outline           (borders, dividers)
--color-outline-strong    (focused borders)
--color-error             (destructive)
--color-error-bg          (destructive surface)
--color-success           (positive)
--color-success-bg        (positive surface)
--color-warning           (caution)
--color-warning-bg        (caution surface)
--color-info              (info)
--color-info-bg           (info surface)
--color-muted             (secondary text, placeholders)
--color-disabled          (disabled text)
--color-disabled-bg       (disabled surface)
--color-code-bg           (inline code blocks)
--color-code-text         (inline code text)
--color-link              (hyperlink)
--color-link-hover        (hyperlink hover)
--shadow-sm               (subtle shadow)
--shadow-md               (card shadow)
--shadow-lg               (modal shadow)
--radius-sm               (small radius)
--radius-md               (medium radius)
--radius-lg               (large radius)
```

For `[data-theme="dark"]`, override each token with dark-appropriate values.

For `@media (prefers-color-scheme: dark)` (no `[data-theme]` set = auto mode), apply the same overrides.

Keep existing profile color tokens (`--profile-primary`, etc.) but add dark variants under `[data-theme="dark"]` and `@media (prefers-color-scheme: dark)`.

### Step 3 — Build theme toggle UI component
**File:** `frontend/src/components/ThemeToggle.vue`

- Small icon-button component with sun/moon/auto icons
- Uses `useTheme()` to display current mode and handle clicks
- Tooltip or aria-label indicating current mode
- Placed in shared navbars (Home, Process, and any other screens with a header)

### Step 4 — Systematic hardcoded color replacement
**Files:** All 19 `.vue` files in `frontend/src/views/` and `frontend/src/components/`

**Method:** File-by-file pass. For each file:

1. Open `<style>` and `<style scoped>` blocks.
2. Find every hardcoded color value (`#...`, `rgb(...)`, `rgba(...)`, named colors like `white`, `black`).
3. Map each to the closest semantic token from Step 2.
4. Replace the value with `var(--token-name)`.
5. If no token exists, add one to `App.vue` rather than leaving a hardcoded value.
6. Verify the visual result in both light and dark modes.

**Priority order (high impact first):**
1. `Home.vue` — landing page, most visible
2. `Process.vue` — main workflow screen
3. `ReportView.vue` — report display
4. `MainView.vue` — dashboard
5. `LoginPage.vue` / `RegisterPage.vue` — auth flows
6. `SimulationView.vue` / `SimulationRunView.vue`
7. `InteractionView.vue`
8. All components (`GraphPanel.vue`, `Step*.vue`, etc.)

**Common mapping guide:**
| Hardcoded | Token replacement |
|-----------|-------------------|
| `#000`, `#000000`, `black` | `var(--color-on-background)` or `var(--color-on-surface)` |
| `#FFF`, `#FFFFFF`, `white` | `var(--color-background)` or `var(--color-surface)` |
| `#F5F5F5`, `#FAFAFA`, `#EEE` | `var(--color-surface)` or `var(--color-surface-elevated)` |
| `#E5E5E5`, `#CCC`, `#DDD` | `var(--color-outline)` |
| `#333`, `#444` | `var(--color-on-surface)` |
| `#666`, `#888` | `var(--color-muted)` |
| `#999` | `var(--color-disabled)` |
| `#222` | `var(--color-on-background)` |

### Step 5 — Auto-mode CSS support
**File:** `frontend/src/App.vue`

Add a CSS block:

```css
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    /* same overrides as [data-theme="dark"] */
  }
}
```

This ensures that when `data-theme` is absent (auto mode) or when the user has not explicitly chosen a theme, the OS preference drives the appearance.

### Step 6 — Persistence and Convex sync (optional but recommended)
**File:** `frontend/src/composables/useTheme.js` (extension)

If the user is authenticated, also sync the theme preference to their Convex user document so it follows them across devices.

- On `setTheme()`, if authenticated, call a Convex mutation to store `themePreference`.
- On `initTheme()`, if authenticated and no `localStorage` value exists, read from Convex and apply.
- This is **optional** for DARK-01 but improves UX. Implement only if the Convex user schema already has a field for preferences or if adding one is trivial.

### Step 7 — Verification and visual regression check
**Method:** Manual browser testing + checklist

For each screen, verify in **light**, **dark**, and **auto (OS dark)** modes:

- [ ] No invisible text (text color matches background)
- [ ] No missing borders or dividers
- [ ] Buttons are readable in all states (default, hover, active, disabled)
- [ ] Inputs have visible borders and placeholder text
- [ ] Cards/panels have visible boundaries from background
- [ ] Scrollbars match theme (already partially implemented)
- [ ] No unthemed white flashes on page load
- [ ] Profile colors still work in both themes
- [ ] Toggle UI correctly shows current mode

**Screens to check:**
- [ ] Home (landing)
- [ ] Login
- [ ] Register
- [ ] Main Dashboard
- [ ] Process workflow (all 5 steps)
- [ ] Simulation setup
- [ ] Simulation run
- [ ] Report viewer
- [ ] Interaction/chat

---

## Verification

### Tests

1. **Unit: useTheme composable**
   - `setTheme('dark')` sets `data-theme="dark"` on `<html>`
   - `setTheme('light')` removes `data-theme` or sets `"light"`
   - `setTheme('auto')` removes `data-theme` and listens to media query
   - `localStorage` is updated on each change
   - `initTheme()` reads `localStorage` and applies correctly

2. **Integration: toggle across pages**
   - Toggle theme on Home → navigate to Process → theme persists
   - Refresh page → theme persists
   - Set OS to dark, select auto → page goes dark
   - Set OS to light, select auto → page goes light
   - Toggle cycles: light → dark → auto → light

3. **Visual: no hardcoded colors**
   - Run `grep -rE '#[0-9a-fA-F]{3,6}|rgb\(|rgba\(' frontend/src --include='*.vue'`
   - Only allowed exceptions: `transparent`, CSS variable fallbacks (`var(--x, #fff)`)

### Checklist

- [ ] DARK-01: Toggle (light/dark/auto) exists, works, persists across sessions
- [ ] DARK-02: All 9 screens render correctly in both themes with no regressions
- [ ] DARK-03: Zero hardcoded colors in component styles; all via CSS custom properties
- [ ] DARK-04: Auto mode reacts live to `prefers-color-scheme` changes without reload

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Replacing all hardcoded colors at once is error-prone | Split into 2–3 sub-PRs: (a) useTheme + tokens, (b) views, (c) components |
| Profile colors may clash with dark backgrounds | Add dark-variant profile tokens and test each profile in dark mode |
| Third-party library styles may be unthemed | Scope overrides in `App.vue` or accept as known limitation for v1.4 |
| Flash of wrong theme on load | Use a `<script>` in `index.html` that reads `localStorage` before Vue mounts |

---

## Effort Estimate

| Step | Estimated Time |
|------|---------------|
| Step 1: useTheme composable + cleanup | 1–2h |
| Step 2: Token expansion | 1–2h |
| Step 3: ThemeToggle component | 30–45min |
| Step 4: Hardcoded color replacement (19 files) | 4–6h |
| Step 5: Auto-mode CSS | 30min |
| Step 6: Convex sync (optional) | 1h |
| Step 7: Verification | 1–2h |
| **Total** | **~9–14h** |

---

## Post-Phase

After Phase 13 completes:
- Phase 14 (Design System Refinements) can build on the token system to add v2 specs, radius changes, and the living style guide.
- The token set defined here becomes the foundation for all subsequent UI work.

---
*Plan created: 2026-04-28*
*Next: Execute with `/gsd:execute-phase 13` or begin implementation*
