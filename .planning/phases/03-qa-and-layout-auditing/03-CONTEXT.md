# Phase 3: QA and Layout Auditing - Context

**Gathered:** 2026-04-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Verify that the Blueprint Noir design system changes from Phases 1 and 2 have not broken any existing functional workflows. This phase is purely validation and gap-fixing — no new features.

</domain>

<decisions>
## Implementation Decisions

### Verification Scope
- **D-01:** Test the three required functional flows: (1) user authentication (login/register), (2) simulation setup and execution, (3) report viewing.
- **D-02:** Verify the Graph UI renders legibly against the new monochrome backgrounds and component styling.

### Verification Method
- **D-03:** Use `npm run build` as the primary automated gate — any syntax error or type issue introduced by CSS changes must be caught before manual checks.
- **D-04:** Perform visual spot-checks on the key views touched in Phases 1–2: `LoginPage.vue`, `RegisterPage.vue`, `Home.vue`, `Process.vue`, `Step1GraphBuild.vue`, `Step2EnvSetup.vue`, `Step3Simulation.vue`, `Step4Report.vue`, `Step5Interaction.vue`, `HistoryDatabase.vue`, and `GraphPanel.vue`.

### Issue Handling
- **D-05:** Minor CSS/layout regressions (e.g., missing padding, misaligned text, hover state glitches) should be fixed inline during this phase.
- **D-06:** Any functional regression requiring logic changes (e.g., broken form submission, failed API calls, routing issues) should be documented in a gap plan if the fix exceeds a trivial one-liner.

### Claude's Discretion
- Specific browser or device testing matrix is at Claude's discretion — standard desktop viewport verification is sufficient unless issues are flagged.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Design Guidelines
- `.planning/research/DESIGN-SYSTEM.json` — The Blueprint Noir design system spec.
- `.planning/phases/02-component-refactoring/02-UI-SPEC.md` — The approved UI design contract for components.

### Prior Phase Context
- `.planning/phases/01-global-styling-foundations/01-CONTEXT.md` — Global styling decisions.
- `.planning/phases/02-component-refactoring/02-CONTEXT.md` — Component refactoring decisions (D-01 through D-03).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- All verification can be done against the existing Vue SFC files in `frontend/src/views/` and `frontend/src/components/`.

### Established Patterns
- The project uses Vue 3 with Vite. Build success is the fastest automated quality gate.

### Integration Points
- Authentication flows rely on Convex (backend auth logic should remain untouched).
- Simulation flows rely on the Python FastAPI backend (no backend changes in this phase).
- Graph UI is rendered inside `GraphPanel.vue` and `Step1GraphBuild.vue`.

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard QA approaches focused on build verification, visual spot-checks, and functional smoke-testing of the three key flows.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-qa-and-layout-auditing*
*Context gathered: 2026-04-14*
