# Plan: Phase 20 — Advanced Report Visualization

**Phase:** 20  
**Goal:** Reports are more informative and interactive with inline charts and enhanced data presentation.  
**Requirements:** RVIZ-01, RVIZ-02, RVIZ-03, RVIZ-04  
**Defined:** 2026-04-28  
**Depends on:** Phase 19 (completed)

---

## Context

The report viewer now has card-based sections, tables, data source tags, and a floating outline. This phase adds interactivity and visual richness:
- Mini-charts (created in Phase 16) need to be integrated inline
- Tables need client-side sorting
- Data source tags need rich tooltips
- Section collapse needs smooth animation

---

## Plan Steps

### Step 1 — Integrate MiniBarChart/MiniSparkline (RVIZ-01)
**Files:** `Step4Report.vue`, `MiniBarChart.vue`, `MiniSparkline.vue`

When `renderMarkdown()` detects tables with numeric data, render a mini-chart alongside or above the table. For now, add a simple heuristic:
- If a table has 2+ numeric columns and 3+ rows, render a MiniBarChart
- If a table has a single numeric column with 5+ rows, render a MiniSparkline

### Step 2 — Table Column Sorting (RVIZ-02)
**File:** `Step4Report.vue`

Add client-side sorting to rendered tables:
- Click table header to sort ascending/descending
- Visual indicator (▲▼) on sorted column
- Support numeric and string sorting

### Step 3 — Data Source Tag Tooltips (RVIZ-03)
**File:** `Step4Report.vue` (or new `DataSourceTag.vue`)

Enhance the existing `[📊 realizado]` tags with interactive tooltips:
- Tooltip shows methodology explanation on hover/focus
- Tooltip uses semantic color + icon
- Accessible: shown on focus, hidden on blur/escape

### Step 4 — Smooth Section Collapse (RVIZ-04)
**Files:** `Step4Report.vue`, `Step5Interaction.vue`

Add CSS transitions to section collapse/expand:
- Use `grid-template-rows` or `max-height` trick for smooth height animation
- Respect `prefers-reduced-motion`

---

## Verification

### Tests

1. Report with numeric table shows inline mini-chart
2. Clicking table header sorts rows
3. Hovering data source tag shows methodology tooltip
4. Section collapse animates smoothly

### Checklist

- [x] RVIZ-01: Mini-charts render inline for numeric tables (bar chart + sparkline SVG)
- [x] RVIZ-02: Tables support client-side sorting (click headers, numeric/string)
- [x] RVIZ-03: Data source tags have rich tooltips (methodology on hover/focus)
- [x] RVIZ-04: Section collapse/expand animates smoothly (Vue Transition)

---

## Effort Estimate

| Step | Estimated Time |
|------|---------------|
| Step 1: Mini-charts inline | 1.5h |
| Step 2: Table sorting | 1h |
| Step 3: Tag tooltips | 1h |
| Step 4: Smooth collapse | 1h |
| **Total** | **~4.5h** |

---
*Plan created: 2026-04-28*
*Next: Execute with `/gsd:execute-phase 20` or begin implementation*
