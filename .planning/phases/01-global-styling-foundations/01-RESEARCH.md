<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Must use Space Grotesk for display, headline, and label roles.
- Must use Work Sans for body and title text.
- Must establish the monochrome color palette.
- Do not modify backend or database schemas.
- Do not alter the actual functionality of the Vue components.

### Claude's Discretion
- Best approach for CSS framework variable updates (e.g. Vanilla CSS vs whatever is in the Vue setup).

### Deferred Ideas (OUT OF SCOPE)
None explicitly mentioned in CONTEXT.md.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| UI-01 | Implement "Blueprint Noir" typography (Space Grotesk & Work Sans) globally. | `index.html` needs Google Font import updates. Vue global styles in `App.vue` must implement specific classes or variables mapping to these two fonts per design specs. |
| UI-02 | Apply monochrome color palette (Black, White, Greys) across all views. | `DESIGN-SYSTEM.json` exposes 40+ specific token names (e.g., `background`, `primary`, `surface-container`). These should be registered as `--color-*` CSS variables in `:root` inside `App.vue`. `--orange` and similar hardcoded accents must be replaced on the home page and global views. |
</phase_requirements>

# Phase 1: Global Styling Foundations - Research

**Researched:** 2026-04-14
**Domain:** Global Styling & CSS Architecture (Vue.js)
**Confidence:** HIGH

## Summary

The current application utilizes a Vue 3 frontend managed via Vite. No external CSS framework like Tailwind or Bootstrap is currently installed or required; instead, the project relies on vanilla CSS defined globally in `App.vue` and locally scoped to various `.vue` components. The "Blueprint Noir" design system (`DESIGN-SYSTEM.json`) dictates a strict Brutalist/Monochrome aesthetic consisting of two primary font families (Space Grotesk, Work Sans) and roughly 45 precise monochrome color tokens.

**Primary recommendation:** Use plain CSS variables (Custom Properties) defined in `:root` within the `App.vue` `<style>` block to establish global color tokens and typography variables. Do not install new CSS frameworks.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Vue SFC `<style>` | 3.5.24 | Global CSS Definitions | Native to the project stack, avoids unnecessary build complexity |
| Vanilla CSS Variables | Native | Theming and tokens | Provides runtime flexibility and is universally compatible with Vue's scoped and global styles |
| Google Fonts | API | Typography loading | Already in use in `index.html`; simply extend the import URL |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Vanilla CSS Vars | Tailwind CSS | While Tailwind is standard, retrofitting an entire codebase in Phase 1 violates the constraint of establishing foundations quickly without rewriting all component markup. |
| Vanilla CSS Vars | SCSS | SCSS variables require build-step setup and don't natively update DOM in real-time. Native CSS properties are better suited. |

## Architecture Patterns

### Recommended Project Structure
For CSS implementation, keep it minimal and close to the root entrypoint:
```
frontend/
├── index.html         # Add <link> for Work Sans alongside Space Grotesk
└── src/
    └── App.vue        # Register :root { ... } CSS variables globally here
```

### Pattern 1: Native CSS Tokens
**What:** Mapping `DESIGN-SYSTEM.json` variables into CSS Custom Properties.
**When to use:** Global theming without a framework.
**Example:**
```css
/* App.vue */
:root {
  /* Colors */
  --color-primary: #000000;
  --color-background: #f9f9f9;
  --color-surface-container-low: #f3f3f3;
  
  /* Typography */
  --font-machine: 'Space Grotesk', monospace;
  --font-human: 'Work Sans', sans-serif;
}
```

### Anti-Patterns to Avoid
- **SCSS/Sass Variables:** Avoid locking into a preprocessor for base tokens when Native CSS Variables provide better DevTools introspection and live updating.
- **Scattered Overrides:** Do not inject generic `style=""` overrides directly on elements.
- **Class-Name Pollution:** Avoid creating hundreds of utility classes manually (e.g., `.bg-surface-low`). Let individual component `<style scoped>` blocks use `var(--color-...)` natively.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Typography Scaling | Hand-calculated REMs without tokens | Define `--text-display`, `--text-body` etc. in `:root` | Ensures consistency across "Machine" and "Human" typographic rules without scattered `font-size` declarations. |
| Font Importing | Local WOFF imports unless necessary | Existing Google Fonts CDN in `index.html` | Already correctly configured with `<link rel="preconnect">` tags. |

## Common Pitfalls

### Pitfall 1: Residual Local Variables Breaking the Theme
**What goes wrong:** Old theme colors persist (e.g., `--orange: #FF4500;`).
**Why it happens:** Vue components like `Home.vue`, `Process.vue`, and `LoginPage.vue` declare their own CSS variables in scoped blocks, overriding or ignoring global tokens.
**How to avoid:** Globally search for `--orange` or `color: #` in target pages (like `Home.vue`) and replace them with `var(--color-primary)` or `var(--color-on-surface)`.

### Pitfall 2: Font Fallbacks Breaking Layout
**What goes wrong:** The app renders with default serifs for a brief moment, or the fonts fail to load.
**Why it happens:** Incorrect Google Font URLs or missing `sans-serif`/`monospace` fallbacks.
**How to avoid:** Ensure `Work+Sans:wght@300..700` is correctly formatted in the query string alongside `Space+Grotesk` in `index.html`.

## Code Examples

Verified patterns from official sources:

### Google Font Import Update
```html
<!-- frontend/index.html -->
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@100..800&family=Space+Grotesk:wght@300..700&family=Work+Sans:wght@300..700&display=swap" rel="stylesheet">
```

### Setting the Global Defaults
```css
/* frontend/src/App.vue */
<style>
:root {
  --color-primary: #000000;
  --color-background: #f9f9f9;
  /* (Add the rest of the 45 tokens from DESIGN-SYSTEM.json) */
  
  --font-machine: 'Space Grotesk', sans-serif;
  --font-human: 'Work Sans', sans-serif;
}

body {
  font-family: var(--font-human);
  background-color: var(--color-background);
  color: var(--color-on-background);
}

h1, h2, h3, .headline, .label, .display {
  font-family: var(--font-machine);
}
</style>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Multi-color Accent (`--orange: #FF4500`) | Monochrome Branding (`#000000` & `#FFFFFF`) | Phase 1 (Blueprint Noir) | Sharpens focus on technical ideation, mimicking a drafting table. |
| `JetBrains Mono` globally | Split `Space Grotesk` (machine) / `Work Sans` (human) | Phase 1 (Blueprint Noir) | Creates clear separation between AI output and user input. |

## Open Questions

1. **How strictly to enforce Tonal Shifting in Phase 1?**
   - What we know: Phase 1 focuses heavily on typography and basic color definitions. Tonal depth (no-line rule) is mentioned under the system but borders exist throughout `Home.vue`.
   - What's unclear: Should we strip *all* 1px borders in Phase 1 or wait for Phase 2 components?
   - Recommendation: Replace the actual color hexes in Phase 1, but defer removing the 1px structural borders/rounded corners to Phase 2 (UI-03).

## Environment Availability
Step 2.6: SKIPPED (no external dependencies identified, pure CSS phase)

## Validation Architecture
### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vite / Vue Native |
| Config file | none — see Wave 0 |
| Quick run command | `npm run preview` |
| Full suite command | `npm run build` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UI-01 | Space Grotesk/Work Sans applied globally | e2e/manual-only | `npm run build` | ❌ Wave 0 |
| UI-02 | Monochrome palette variables replacing existing colors | static-analysis | `grep -r "color: #FF4500" frontend/src` (Expect empty) | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `npm run build`
- **Per wave merge:** `npm run build`
- **Phase gate:** Frontend builds without errors and UI verified.

### Wave 0 Gaps
- Automated UI regression testing is not established. Visual/CSS changes require manual verification.

## Sources
### Primary (HIGH confidence)
- `.planning/research/DESIGN-SYSTEM.json` - High-contrast monochrome rules and specific hex codes.
- `.planning/phases/01-global-styling-foundations/01-CONTEXT.md` - Phase constraints.
- `frontend/src/App.vue` - Current entry point for global styles.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Vue 3 SFC style blocks are natively supported and already in use.
- Architecture: HIGH - Native CSS variables are standard for dynamic theming.
- Pitfalls: HIGH - Auditing `Home.vue` revealed hardcoded `--orange` tokens directly conflicting with the design system.

**Research date:** 2026-04-14
**Valid until:** 2026-05-14