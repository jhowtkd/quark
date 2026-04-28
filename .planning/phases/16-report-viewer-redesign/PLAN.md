# Plan: Phase 16 — Report Viewer Redesign

**Phase:** 16  
**Goal:** Reports are scannable, visually rich, and easy to navigate with interactive data presentation.  
**Requirements:** RPTV-01, RPTV-02, RPTV-03, RPTV-04  
**Defined:** 2026-04-28  
**Depends on:** Phase 15 (completed)

---

## Context

The report viewer is implemented in `Step4Report.vue` (~5,252 lines) and `ReportView.vue` (~353 lines). Current state:

- **Content format**: Markdown strings streamed incrementally via agent logs
- **Renderer**: Custom `renderMarkdown()` function handles headings, bold/italic, code, lists, blockquotes — but **no tables**
- **Sections**: Numbered collapsible sections (`01`, `02`…) driven by `reportOutline.sections`
- **Data source tags**: **Do not exist** — no 📊/🔮 emojis or source tagging in the frontend
- **Navigation**: Section list with collapse/expand, but **no anchor links or floating outline**
- **Layout**: Left panel (report content) + Right panel (workflow timeline) + Bottom (console logs)

### Key Files
| File | Role |
|------|------|
| `frontend/src/views/ReportView.vue` | Layout shell (header + graph/report split) |
| `frontend/src/components/Step4Report.vue` | Main report rendering (~5,252 lines) |
| `frontend/src/api/report.js` | API client (`getReport`, `getAgentLog`) |

---

## Architecture Decisions

1. **Table support**: Extend `renderMarkdown()` to parse `|`-style Markdown tables into HTML `<table>` elements with styling.
2. **Data source tags**: Create a `DataSourceTag` component and a markdown extension: `@[realizado](valor)` → rendered tag. For now, also support plain-text patterns like `[📊 realizado]` or `[🔮 hipótese]` in the markdown renderer.
3. **Mini-charts**: Create `MiniBarChart` and `MiniSparkline` components for inline metric visualization. Parse special markdown blocks like ````chart` or simple tables with numeric data.
4. **Floating outline**: Create `ReportOutline` component that extracts headings from rendered content and provides click-to-scroll navigation.
5. **Section cards**: Wrap each report section in a `BaseCard`-styled container with clear visual hierarchy.
6. **Due-diligence structure**: The backend/prompt must generate the 5-section structure (Tese, Evidências, Fragilidades, Premissas, Cenários). The frontend will recognize these section titles and apply special styling — but we cannot force the backend to change in this phase. We prepare the frontend to render them beautifully when they appear.

---

## Plan Steps

### Step 1 — Add table support to renderMarkdown()
**File:** `frontend/src/components/Step4Report.vue`

Extend the `renderMarkdown()` function (or create a new `renderEnhancedMarkdown()`) to handle Markdown tables:

```markdown
| Métrica | Q1 2026 | Q2 2026 |
|---------|---------|---------|
| Receita | $10B    | $12B    |
| Margem  | 18%     | 20%     |
```

Should render as:
```html
<table class="report-table">
  <thead><tr><th>Métrica</th><th>Q1 2026</th><th>Q2 2026</th></tr></thead>
  <tbody><tr><td>Receita</td><td>$10B</td><td>$12B</td></tr>...</tbody>
</table>
```

Add CSS for `.report-table`:
- Full width, border-collapse
- Header: `background: var(--color-surface-container-low)`, bold
- Cells: `padding: var(--space-2) var(--space-3)`, border bottom
- Hover row: `background: var(--color-surface-container-low)`
- Responsive: horizontal scroll on narrow screens

### Step 2 — Create DataSourceTag component
**File:** `frontend/src/components/DataSourceTag.vue`

A small inline badge that shows data provenance:

Props:
- `type`: `'realizado' | 'consenso' | 'projecao' | 'simulacao'`
- `label`: optional override text

Visual:
- 📊 `realizado` — green badge (`--color-success`)
- 🔮 `consenso` — blue badge (`--color-info`)
- 📈 `projecao` — amber badge (`--color-warning`)
- ⚠️ `simulacao` — red badge (`--color-error`)

Also extend `renderMarkdown()` to auto-detect patterns:
- `\[📊 realizado\]` → `<DataSourceTag type="realizado" />`
- `\[🔮 hipótese\]` → `<DataSourceTag type="projecao" />`
- `\[📈 consenso\]` → `<DataSourceTag type="consenso" />`
- `\[⚠️ simulação\]` → `<DataSourceTag type="simulacao" />`

Since `renderMarkdown()` returns HTML strings (not Vue components), we'll use `<span>` elements with CSS classes instead:
- `<span class="source-tag source-realizado">📊 realizado</span>`

### Step 3 — Create mini-chart components
**Files:** `frontend/src/components/mini-charts/MiniBarChart.vue`, `MiniSparkline.vue`

#### MiniBarChart
Props: `data` (Array<{label, value}>), `color`
Renders horizontal bars with labels. Useful for comparing metrics side-by-side.

#### MiniSparkline
Props: `data` (Array<number>), `width`, `height`, `color`
Renders a tiny SVG line chart. Useful for showing trends over time.

Add a markdown extension for simple chart blocks:
````markdown
```chart
Receita: 10, 12, 14, 13
Margem: 18, 20, 19, 21
```
````
This is optional — tables alone may be sufficient for v1.4.

### Step 4 — Create ReportOutline floating navigation
**File:** `frontend/src/components/ReportOutline.vue`

A sticky/floating sidebar that:
1. Scans the report content for headings (`<h2>`, `<h3>`)
2. Builds a TOC tree
3. Highlights the current section on scroll (scroll-spy via IntersectionObserver)
4. Clicking a heading scrolls to it smoothly

Props:
- `contentRef`: ref to the report content container
- `headings`: Array<{id, text, level}>

Style:
- Position: sticky on desktop, collapsible drawer on mobile
- Active item: bold + left border accent
- Indentation based on heading level

### Step 5 — Redesign report section layout
**File:** `frontend/src/components/Step4Report.vue`

Wrap each rendered section in a card-like container:
```vue
<div class="report-section" :id="`section-${index}`">
  <div class="section-header" @click="toggleSectionCollapse(index)">
    <span class="section-number">{{ String(index + 1).padStart(2, '0') }}</span>
    <span class="section-title">{{ section.title }}</span>
    <Icon :name="isCollapsed(index) ? 'chevron-down' : 'chevron-up'" />
  </div>
  <div v-show="!isCollapsed(index)" class="section-body">
    <div v-html="renderEnhancedMarkdown(content)" />
  </div>
</div>
```

CSS:
- Section card: `background: var(--color-surface)`, border, padding
- Header: `font-family: var(--font-machine)`, clickable
- Number: large, muted color
- Due-diligence recognition: if title contains "Tese", "Evidências", "Fragilidades", "Premissas", or "Cenários", apply an accent border color

### Step 6 — Integrate outline into ReportView
**File:** `frontend/src/views/ReportView.vue`

Add the `ReportOutline` component alongside the report panel:
- Desktop: outline sticky on the left or right of the report content
- Mobile: outline as a toggleable drawer or dropdown

### Step 7 — Enhance ReportView header
**File:** `frontend/src/views/ReportView.vue`

Improve the view-mode switcher and add:
- Report title prominently displayed
- Export/print button (optional)
- Theme toggle (already exists)

---

## Verification

### Tests

1. **Tables**: Paste a markdown table into a report section — it should render as a styled HTML table.
2. **Data source tags**: Include `[📊 realizado]` in markdown — it should render as a colored badge.
3. **Outline**: Generate a report with multiple sections — the outline should show all headings and scroll-spy should work.
4. **Section cards**: Each section should be wrapped in a visually distinct card.

### Checklist

- [ ] RPTV-01: Report sections render in card layout with due-diligence styling
- [ ] RPTV-02: Markdown tables render as styled HTML tables; mini-charts available
- [ ] RPTV-03: Data source tags (`[📊 realizado]`, etc.) render as colored badges
- [ ] RPTV-04: Floating outline provides anchor navigation with scroll-spy

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Step4Report.vue is 5,252 lines — changes are risky | Make minimal, focused edits; test build after each change |
| renderMarkdown() is complex regex-based parser | Add table/tag parsing as separate functions, keep existing logic intact |
| Scroll-spy performance on long reports | Use IntersectionObserver with rootMargin, throttle updates |

---

## Effort Estimate

| Step | Estimated Time |
|------|---------------|
| Step 1: Table support in renderMarkdown | 1–1.5h |
| Step 2: DataSourceTag component + markdown extension | 1h |
| Step 3: Mini-chart components | 1–1.5h |
| Step 4: ReportOutline with scroll-spy | 1.5–2h |
| Step 5: Section card layout | 1h |
| Step 6: Integrate outline into ReportView | 30min |
| Step 7: Header enhancements | 30min |
| **Total** | **~7–9h** |

---

## Post-Phase

After Phase 16 completes:
- Phase 17 (Global UI Polish) can run accessibility and responsive audits on the new report viewer.
- The report viewer will be ready for the v1.4 release.

---
*Plan created: 2026-04-28*
*Next: Execute with `/gsd:execute-phase 16` or begin implementation*
