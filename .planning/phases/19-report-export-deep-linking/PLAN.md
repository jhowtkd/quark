# Plan: Phase 19 — Report Export & Deep Linking

**Phase:** 19  
**Goal:** Reports are shareable and exportable, extending their utility beyond the app.  
**Requirements:** REXP-01, REXP-02, REXP-03, REXP-04  
**Defined:** 2026-04-28  
**Depends on:** Phase 18 (completed)

---

## Context

The report viewer (ReportView.vue + Step4Report.vue) now renders reports with section cards, tables, data source tags, and a floating outline. Users can navigate sections but cannot:
1. Share a direct link to a specific section
2. Export the report as PDF
3. Copy a shareable URL

This phase adds these capabilities.

---

## Plan Steps

### Step 1 — Deep Linking with Section Anchors (REXP-02)
**Files:** `ReportView.vue`, `Step4Report.vue`, `ReportOutline.vue`

1. Update URL hash when user scrolls to a section: `/report/123#evidencias`
2. On report load, check URL hash and scroll to the corresponding section
3. ReportOutline click-to-scroll should update the URL hash

### Step 2 — Shareable Link Button (REXP-03)
**File:** `ReportView.vue`

1. Add a "Copy Link" button to the report header
2. Generate URL with current section anchor
3. Use `navigator.clipboard.writeText()` to copy
4. Show toast/feedback confirming copy

### Step 3 — PDF Export (REXP-01)
**Files:** `ReportView.vue`, `Step4Report.vue`

1. Install `html2pdf.js` or use native `window.print()` with print styles
2. Add an "Export PDF" button to the report header
3. Create print-specific CSS that hides UI chrome (outline, header buttons, graph panel)
4. Ensure report content renders cleanly across pages

### Step 4 — PDF Metadata (REXP-04)
**File:** `ReportView.vue`

1. Add report title, date, and ID to the print header
2. Add page numbers and generation timestamp to the print footer
3. Use `@page` CSS rules for margins and headers

---

## Verification

### Tests

1. Navigate to `/report/123#evidencias` — page loads and scrolls to Evidências section
2. Click a section in ReportOutline — URL updates with hash
3. Click "Copy Link" — clipboard contains URL with current section hash
4. Click "Export PDF" — PDF downloads with proper styling and metadata

### Checklist

- [ ] REXP-01: PDF export preserves report styling and formatting
- [ ] REXP-02: URL anchors scroll to correct sections on page load
- [ ] REXP-03: Shareable links include report ID and section anchor
- [ ] REXP-04: PDF includes metadata header/footer

---

## Effort Estimate

| Step | Estimated Time |
|------|---------------|
| Step 1: Deep linking | 1h |
| Step 2: Copy link button | 30min |
| Step 3: PDF export | 1.5h |
| Step 4: PDF metadata | 30min |
| **Total** | **~3.5h** |

---
*Plan created: 2026-04-28*
*Next: Execute with `/gsd:execute-phase 19` or begin implementation*
