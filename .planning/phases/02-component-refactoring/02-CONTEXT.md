# Phase 2: Component Refactoring - Context

**Gathered:** 2026-04-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Refactoring common UI components (buttons, inputs, cards) across the application to match the new "Blueprint Noir" analog brutalism aesthetic.

</domain>

<decisions>
## Implementation Decisions

### Component Strategy
- **D-01:** In-place CSS updates (updates existing classes, avoiding extraction to maintain logic safety).

### Input Style
- **D-02:** Inputs will use bottom borders only with a transparent background.

### Hover Effects
- **D-03:** Buttons and cards will use solid block shadows (e.g. `box-shadow: 4px 4px 0 var(--color-primary)`) on hover.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Design Guidelines
- `.planning/research/DESIGN-SYSTEM.json` — The Blueprint Noir design system spec.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Global monochrome variables set in `App.vue` (`var(--color-primary)`, etc.).

### Established Patterns
- Primitives (buttons, inputs) are currently styled directly in their respective view components using classes like `.form-input`, `.login-button`, `.action-btn`.

### Integration Points
- Updates need to be strictly scoped to `<style>` tags in `.vue` files or global styles in `App.vue` to avoid breaking functionality constraints.

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches based on the solid block shadow and bottom border decisions.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-component-refactoring*
*Context gathered: 2026-04-14*