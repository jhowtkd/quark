# Plan: Phase 14 — Design System Refinements

**Phase:** 14  
**Goal:** Establish and apply Blueprint Noir v2 design tokens consistently across all reusable components.  
**Requirements:** DSYS-01, DSYS-02, DSYS-03, DSYS-04  
**Defined:** 2026-04-28  
**Depends on:** Phase 13 (completed)

---

## Context

Phase 13 established a token-driven dark mode system with ~30 CSS custom properties in `App.vue`. However, the UI lacks reusable components and consistency:

- **No shared components**: Every view defines its own buttons, inputs, cards, and badges. There is no `BaseButton`, `BaseInput`, or `BaseCard`.
- **Inconsistent radius**: `border-radius` ranges from `0px` to `50%` across the app (0px, 2px, 3px, 4px, 6px, 8px, 10px, 12px, 16px, 20px, 22px, 30px, 50%).
- **Inconsistent shadows**: `box-shadow` values vary wildly — some use the brutalist `4px 4px 0`, others use soft shadows like `0 2px 4px rgba(0,0,0,0.05)`.
- **No icon library**: Icons are Unicode characters (☀, ☾, ↻, ↗, ⏻, ◆) or inline SVG strings. No consistent sizing or semantic mapping.
- **No style guide**: Developers cannot preview tokens or components in one place.

The Analog Brutalism aesthetic (from v1.0) mandates:
- `0px` border-radius as the default
- Bottom-border inputs (no rounded corners)
- Block-shadow hovers (`4px 4px 0` offset shadows)
- Monochrome tonal layering

### Key Files
| File | Role |
|------|------|
| `frontend/src/App.vue` | Global tokens (from Phase 13) |
| `frontend/src/components/ThemeToggle.vue` | Example of a small reusable component |
| `frontend/src/views/*.vue` | Each defines its own UI elements |
| `frontend/src/components/Step*.vue` | Step panels with heavy custom styling |

---

## Architecture Decisions

1. **Component library**: Create `frontend/src/components/base/` with `BaseButton`, `BaseInput`, `BaseCard`, `BaseBadge`, `BaseModal`, `BaseSelect`.
2. **Icon library**: Install `lucide-vue-next` (lightweight, tree-shakeable, MIT license) and replace all Unicode/icon strings.
3. **Radius standard**: Default `0px` (Analog Brutalism). Exceptions: `50%` only for avatars/circles, `999px` only for pills.
4. **Shadow standard**: Three tiers — `shadow-none`, `shadow-brutalist` (`4px 4px 0 var(--color-on-background)`), `shadow-soft` (`0 2px 8px rgba(0,0,0,0.08)` in light, `0 2px 8px rgba(0,0,0,0.3)` in dark).
5. **Focus rings**: Standard `2px solid var(--color-primary)` with `outline-offset: 2px`.
6. **Style guide**: A dedicated `/style-guide` route with sections for tokens, components, and icons.

---

## Plan Steps

### Step 1 — Install and configure Lucide icons
**File:** `frontend/package.json`, `frontend/src/main.js`

- `npm install lucide-vue-next`
- Create `frontend/src/components/Icon.vue` wrapper:
  - Props: `name` (Lucide icon name), `size` (16 | 20 | 24 | 32), `strokeWidth` (1.5 | 2)
  - Default size: 20px
  - Color inherited from parent (`currentColor`)
- Create a mapping file `frontend/src/icons.js` exporting all used icons:
  - sun, moon, monitor (for theme toggle)
  - log-out, github, globe (for nav)
  - refresh-cw, maximize, minimize (for graph controls)
  - check, circle, alert-circle, info, x (for status/feedback)
  - chevron-down, chevron-up, chevron-left, chevron-right (for navigation)
  - loader-2 (for loading spinners)
  - file-text, bar-chart-3, message-square (for content types)

**Replacement sweep**: In all 19 Vue files, replace Unicode icon characters with `<Icon name="..." />`:
- `☀` → `<Icon name="sun" />`
- `☾` → `<Icon name="moon" />`
- `⏻` → `<Icon name="log-out" />`
- `↗` → `<Icon name="external-link" />`
- `↻` → `<Icon name="refresh-cw" />`
- `↙` → `<Icon name="minimize-2" />`
- `↓` → `<Icon name="chevron-down" />`
- `◆` → `<Icon name="diamond" />`
- `⏵` / `▶` → `<Icon name="play" />`
- `✓` / `✔` → `<Icon name="check" />`
- `✕` / `×` → `<Icon name="x" />`

### Step 2 — Create base components
**Directory:** `frontend/src/components/base/`

#### BaseButton
**Props:**
- `variant`: `'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'`
- `size`: `'sm' | 'md' | 'lg'`
- `disabled`: boolean
- `loading`: boolean (shows loader icon, disables clicks)
- `brutalist`: boolean (adds `4px 4px 0` shadow)

**Styles:**
- Radius: `var(--radius-md)` (0px)
- Padding: sm=`6px 12px`, md=`10px 16px`, lg=`14px 24px`
- Font: `var(--font-machine)`
- Focus: `2px solid var(--color-primary)`, offset 2px
- Hover: translate(-2px, -2px) + shadow offset when brutalist
- Active: translate(0, 0) + no shadow
- Disabled: opacity 0.5, cursor not-allowed

#### BaseInput
**Props:**
- `modelValue`
- `type`: `'text' | 'password' | 'email' | 'number' | 'textarea'`
- `placeholder`
- `disabled`
- `error`: boolean (adds error border)

**Styles:**
- Radius: 0px
- Border: bottom-only `2px solid var(--color-outline)`
- Background: transparent
- Focus: border-color → `var(--color-primary)`
- Error: border-color → `var(--color-error)`
- Disabled: opacity 0.5

#### BaseCard
**Props:**
- `variant`: `'default' | 'elevated' | 'outlined'`
- `padding`: `'sm' | 'md' | 'lg'`
- `brutalist`: boolean

**Styles:**
- Background: `var(--color-surface)`
- Border: `1px solid var(--color-outline)` (default), `none` + shadow (elevated)
- Radius: 0px
- Brutalist: `4px 4px 0 var(--color-on-background)`

#### BaseBadge
**Props:**
- `variant`: `'default' | 'success' | 'warning' | 'error' | 'info' | 'accent'`
- `size`: `'sm' | 'md'`

**Styles:**
- Uses token backgrounds (`--color-success-bg`, etc.)
- Radius: 0px
- Font: `var(--font-machine)`

#### BaseModal
**Props:**
- `open`: boolean (v-model)
- `title`: string
- `size`: `'sm' | 'md' | 'lg'`

**Styles:**
- Overlay: `rgba(0,0,0,0.5)`
- Background: `var(--color-surface-elevated)`
- Radius: 0px
- Shadow: `shadow-lg`
- Close button: top-right, Icon `x`

#### BaseSelect
**Props:**
- `modelValue`
- `options`: Array<{value, label}>
- `placeholder`

**Styles:**
- Similar to BaseInput but with dropdown chevron
- Dropdown list: `var(--color-surface-elevated)` background

### Step 3 — Audit and replace ad-hoc elements
**Files:** All 19 Vue files

Systematically find and replace ad-hoc HTML elements with base components:

1. **Buttons**: Find all `<button>` elements and classify:
   - If they match a BaseButton variant → replace with `<BaseButton>`
   - If they are unique (e.g., graph controls) → keep but standardize styles

2. **Inputs**: Find all `<input>` and `<textarea>` elements → replace with `<BaseInput>`

3. **Cards**: Find all card-like containers (divs with borders/padding) → replace with `<BaseCard>`

4. **Badges**: Find all `.badge.*` classes → replace with `<BaseBadge>`

**Priority order:**
1. `Home.vue` (landing page, most visible)
2. `Process.vue` (main workflow)
3. `LoginPage.vue` / `RegisterPage.vue` (auth)
4. `MainView.vue` (dashboard)
5. `Step*.vue` components
6. Other views and components

### Step 4 — Standardize radius and shadows
**File:** `frontend/src/App.vue` (token expansion)

Add to `:root`:
```css
--radius-none: 0px;
--radius-sm: 0px;
--radius-md: 0px;
--radius-lg: 0px;
--radius-full: 999px;
--radius-circle: 50%;

--shadow-none: none;
--shadow-brutalist: 4px 4px 0 var(--color-on-background);
--shadow-soft: 0 2px 8px rgba(0, 0, 0, 0.08);
--shadow-md: 0 4px 12px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 24px rgba(0, 0, 0, 0.15);
```

Add dark overrides:
```css
[data-theme="dark"] {
  --shadow-soft: 0 2px 8px rgba(0, 0, 0, 0.4);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.5);
  --shadow-lg: 0 10px 24px rgba(0, 0, 0, 0.6);
}
```

**Replacement sweep**: Replace all hardcoded `border-radius` and `box-shadow` values with token references:
- `border-radius: 0px` → `border-radius: var(--radius-md)`
- `border-radius: 50%` → keep as `50%` (or `var(--radius-circle)`)
- `box-shadow: 4px 4px 0 ...` → `box-shadow: var(--shadow-brutalist)`
- `box-shadow: 0 2px 4px rgba(...)` → `box-shadow: var(--shadow-soft)`
- `box-shadow: 0 4px 12px rgba(...)` → `box-shadow: var(--shadow-md)`

### Step 5 — Focus ring standardization
**File:** `frontend/src/App.vue` (global styles)

Add global focus styles:
```css
:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

button:focus-visible,
a:focus-visible,
input:focus-visible,
select:focus-visible,
textarea:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
```

Remove all individual `:focus` styles from components (they often conflict or are inconsistent).

### Step 6 — Build living style guide
**File:** `frontend/src/views/StyleGuide.vue`

Create a new route `/style-guide` (dev-only or behind a simple check).

Sections:
1. **Tokens**
   - Color swatches for all tokens (light + dark side-by-side)
   - Typography samples (headings, body, mono)
   - Shadow previews
   - Radius samples

2. **Components**
   - BaseButton: all variants × all sizes
   - BaseInput: default, focus, error, disabled
   - BaseCard: default, elevated, outlined, brutalist
   - BaseBadge: all variants
   - BaseModal: trigger + example

3. **Icons**
   - Grid of all available icons with names
   - Size variants (16, 20, 24, 32)

4. **Theme Preview**
   - Toggle between light/dark/auto
   - Shows how all components look in each theme

Add to router:
```js
{ path: '/style-guide', component: () => import('./views/StyleGuide.vue') }
```

### Step 7 — Typography refinement
**File:** `frontend/src/App.vue`

Expand typography tokens:
```css
--text-xs: 0.75rem;
--text-sm: 0.875rem;
--text-base: 1rem;
--text-lg: 1.125rem;
--text-xl: 1.25rem;
--text-2xl: 1.5rem;
--text-3xl: 2rem;
--text-4xl: 2.5rem;

--font-weight-normal: 400;
--font-weight-medium: 500;
--font-weight-bold: 700;

--line-height-tight: 1.25;
--line-height-normal: 1.5;
--line-height-relaxed: 1.75;
```

Replace hardcoded font-size values in components with token references where practical.

### Step 8 — Spacing standardization
**File:** `frontend/src/App.vue`

Add spacing scale:
```css
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 20px;
--space-6: 24px;
--space-8: 32px;
--space-10: 40px;
--space-12: 48px;
--space-16: 64px;
```

This is informational for now — full adoption happens incrementally as components are refactored.

---

## Verification

### Tests

1. **Build**: `npm run build` passes with zero errors.
2. **Icon sweep**: No Unicode icon characters remain in `.vue` files:
   ```bash
   grep -rE '☀|☾|⏻|↗|↻|↙|↓|◆|⏵|▶|✓|✔|✕|×' src --include='*.vue'
   ```
   Should return empty.
3. **Component usage**: Every view uses `<BaseButton>`, `<BaseInput>`, `<BaseCard>` where appropriate.
4. **Style guide**: `/style-guide` renders all tokens and components correctly in both themes.

### Checklist

- [ ] DSYS-01: Token documentation exists in running app (style guide page)
- [ ] DSYS-02: Components audited — consistent radius (0px), shadows, focus rings, disabled states
- [ ] DSYS-03: Single icon library (Lucide) adopted, legacy Unicode icons replaced
- [ ] DSYS-04: Developers can preview tokens/components in both themes from style guide

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Replacing all buttons/inputs at once is risky | Split into 2 PRs: (a) create base components + style guide, (b) replace ad-hoc elements |
| Lucide icons may not match brutalist aesthetic | Use `stroke-width="2"` and monochrome (`currentColor`) — fits well |
| Some custom button behaviors may be lost | Audit each button's click handler before replacement |
| Style guide in production | Guard route with `import.meta.env.DEV` or simple env check |

---

## Effort Estimate

| Step | Estimated Time |
|------|---------------|
| Step 1: Lucide icons + Icon wrapper | 1–1.5h |
| Step 2: Create base components | 2–3h |
| Step 3: Audit and replace ad-hoc elements | 3–4h |
| Step 4: Standardize radius/shadows | 1h |
| Step 5: Focus rings | 30min |
| Step 6: Style guide page | 2h |
| Step 7: Typography refinement | 30min |
| Step 8: Spacing tokens | 15min |
| **Total** | **~10–13h** |

---

## Post-Phase

After Phase 14 completes:
- Phase 15 (Animations) can leverage the base components to add consistent transitions.
- Phase 16 (Report Viewer) can use BaseCard, BaseBadge, and standardized tables.
- The style guide becomes the reference for all future UI work.

---
*Plan created: 2026-04-28*
*Next: Execute with `/gsd:execute-phase 14` or begin implementation*
