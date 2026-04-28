# Phase 12: Output Quality Gates — Research

## Current Code Architecture

### Report Generation Pipeline (report_agent.py)
```
generate_report()
  ├── plan_outline()
  ├── DataValidation (Phase 9) — optional
  ├── for each section: _generate_section_react()
  ├── BiasAudit (Phase 11) — optional, after sections
  ├── assemble_full_report() → _post_process_report()
  └── save_report()
```

The natural hook for quality gates is **after bias audit, before assembly** — identical pattern to Phase 11.

### Existing Assets

#### 1. `language_integrity.py`
- `assess_text_integrity()` — checks forbidden scripts, missing entities, suspect terms, entity drift
- `enforce_controlled_output()` — returns fallback text if integrity fails
- **Gap:** No detection of language switching within a document (e.g., PT → EN mid-report)

#### 2. `report_agent.py`
- `_post_process_report()` — currently handles title deduplication, heading flattening, whitespace cleanup
- `assemble_full_report()` — reads sections, builds header, calls `_post_process_report()`, validates provenance tags
- **Gap:** No post-generation quality gate checks

#### 3. `profile_manager.py`
- `ECONOMIA_CONFIG.report_system_prompt` — already has extensive structure rules
- **Gap:** No instruction to include "## Limitacoes Conhecidas" section

#### 4. `bias_audit.py`
- `BiasAuditService` with keyword dictionaries, regex patterns, dimension scoring
- `BiasReport` dataclass with score, dimensions, warnings, is_balanced
- **Pattern to replicate:** Keyword dictionaries → regex patterns → per-dimension analysis → composite score

---

## Quality Gate Design

### QUAL-01: Language Consistency Gate
**Approach:**
- Portuguese stopwords vs English stopwords density per paragraph
- If a paragraph has >60% English stopwords while the report is set to Portuguese (or vice versa), flag it
- Report language determined by profile or simulation requirement

**Pattern:** Stopword-based detection (no external library needed)

### QUAL-02: Known Limitations Gate
**Approach:**
- Check if markdown contains heading matching "Limitacoes Conhecidas" / "Known Limitations"
- If missing, auto-append a generic limitations section based on detected data gaps
- Also update ECONOMIA_CONFIG prompt to explicitly require this section

### QUAL-03: Numeric Consistency Gate
**Approach:**
- Extract all numeric claims with their metric context (e.g., "revenue: $95B")
- Detect same metric with different values in different sections
- Detect probability sums that don't equal 100% (for scenario sections)
- Detect margin calculations that don't reconcile

**Pattern:** Context-aware numeric extraction with contradiction detection

### QUAL-04: Self-Contradiction Gate
**Approach:**
- Maintain logical-opposite keyword pairs (growing/declining, strong/weak, etc.)
- Detect when both members of a pair appear in different sections referring to the same entity
- Flag unsupported valuation conclusions (e.g., "target price $X" without derivation)

**Pattern:** Similar to bias audit's bullish/bearish keyword detection
