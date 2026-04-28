# Phase 8 Research: Data Provenance and Labeling

**Date:** 2026-04-27
**Scope:** Backend Python report generation pipeline
**Goal:** Document current architecture and integration points for provenance labeling

---

## 1. Report Generation Pipeline Architecture

### 1.1 Entry Point
- **File:** `backend/app/api/report.py`
- **Endpoint:** `POST /api/report/generate`
- **Flow:** Validates simulation → creates `report_id` → spawns background thread → `ReportAgent.generate_report()` → `ReportManager.save_report()`
- **Profile selection:** `profile_name = data.get('profile') or getattr(state, 'profile', None) or 'generico'`

### 1.2 ReportAgent Core
- **File:** `backend/app/services/report_agent.py` (~3047 lines)
- **Key class:** `ReportAgent`
- **ReACT loop:** `MAX_TOOL_CALLS_PER_SECTION = 5`, `_execute_tool()` at line 1088 is the central bottleneck
- **Report assembly:** `assemble_full_report()` at line 2746
- **Post-processing:** `_post_process_report()` at line 2776 — deduplicates headings, cleans whitespace, flattens ### headings to bold

### 1.3 Profile Configuration
- **File:** `backend/app/profiles/profile_manager.py`
- **ECONOMIA_CONFIG** contains `report_system_prompt`, `report_section_prompt`, `simulation_overrides`, `entity_type_weights`
- **`apply_to_report_agent()`** injects: `system_prompt`, `section_prompt`, `max_tool_calls`, `temperature`, `max_reflection_rounds`, `forbidden_scripts`, `max_words_per_sentence`, `profile_type`, `entity_type_weights`
- **No existing provenance fields** in `ProfileConfiguration` dataclass

### 1.4 Data Retrieval Layer
- **File:** `backend/app/services/zep_tools.py`
- **Result types:** `SearchResult`, `InsightForgeResult`, `PanoramaResult`, `InterviewResult`
- **Current `SearchResult.to_text()`:** Only emits `facts`, `query`, `total_count` — no source metadata
- **`InsightForgeResult`** has `semantic_facts`, `entity_insights`, `top_sources` — `top_sources` is a list of dicts with `name`, `type`, `fact_count`

### 1.5 Fallback Search
- **File:** `backend/app/services/report_agent.py` lines 841-877 (`_trigger_fallback_search()`)
- Uses `ConnectorFallbackRouter.search()`
- Results formatted as: `Fonte: [URL] | Data: YYYY-MM-DD | Conteudo: snippet`
- No structured provenance metadata currently captured

### 1.6 Logging & Observability
- **File:** `backend/app/services/report_agent.py` lines 38-220 (`ReportLogger`)
- **Log file:** `reports/{report_id}/agent_log.jsonl`
- **Current fields:** `timestamp`, `elapsed_seconds`, `report_id`, `action`, `stage`, `section_title`, `section_index`, `details`
- **Actions logged:** `report_start`, `planning_start`, `planning_context`, `planning_complete`, `section_start`, `react_thought`, `tool_call`, `tool_result`, `section_complete`, `report_complete`
- **`log_tool_result()`** at line 191 logs `tool_name`, `result`, `iteration` but no provenance tag

### 1.7 Report Output Structure
- **Folder:** `uploads/reports/{report_id}/`
- **Files:**
  - `full_report.md` — assembled markdown
  - `meta.json` — metadata (currently: title, summary, sections, generation time)
  - `agent_log.jsonl` — execution trace
  - `section_{NN}.md` — individual sections

---

## 2. Integration Point Analysis

### 2.1 Layer A (Data Retrieval) — Low Friction
**Where:** `zep_tools.py` result dataclasses + `ReportAgent._execute_tool()`
**What needed:**
- Add `provenance: Dict[str, Any]` field to `SearchResult`, `InsightForgeResult`, `PanoramaResult`
- In `_execute_tool()`, wrap tool output with metadata: `source`, `tool_name`, `query`, `retrieved_at`, `connector_name`
- Pass provenance metadata through to LLM context

**Friction:** Low — dataclass additions are backward-compatible if using defaults

### 2.2 Layer B (LLM Prompt) — Medium Friction
**Where:** `ECONOMIA_CONFIG` prompts in `profile_manager.py`
**What needed:**
- Append provenance instructions to `report_system_prompt` and `report_section_prompt`
- Instruct LLM to tag every quantitative claim with emoji (📊, 🔮, ⚠️)
- Add Data Sources section instruction

**Friction:** Medium — prompt engineering requires testing to ensure LLM compliance without degrading output quality

### 2.3 Layer C (Post-Processing Validation) — Low Friction
**Where:** `ReportAgent._post_process_report()` + new validator
**What needed:**
- Add regex-based emoji tag coverage check in `_post_process_report()` or new method
- Check for numeric claims without tags
- Log warnings to observability

**Friction:** Low — post-processing is already extensible

### 2.4 ReportLogger Extension — Low Friction
**Where:** `ReportLogger` class in `report_agent.py`
**What needed:**
- Add `provenance_tag` parameter to `log_tool_result()` and `log_tool_call()`
- Add `provenance_version` to `log_start()`

**Friction:** Low — JSONL schema is flexible

### 2.5 meta.json Extension — Low Friction
**Where:** `ReportManager.save_report()` or `ReportAgent.generate_report()`
**What needed:**
- Add `provenance_version: "1.0"` field to `meta.json`
- Add `profile_type` to `meta.json` (useful for backward compatibility decisions)

**Friction:** Low — meta.json is a dict

### 2.6 Abort Logic — Medium Friction
**Where:** `backend/app/api/report.py` `generate_report()`
**What needed:**
- Detect version mismatch between simulation start and current `ReportAgent` provenance capability
- Abort in-flight generation if mismatch detected

**Friction:** Medium — requires careful state management to avoid race conditions

---

## 3. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LLM ignores emoji tags | High | High | Layer C validator + retry logic in prompt |
| Emoji tags break markdown rendering | Low | Medium | Test in frontend report viewer |
| Prompt bloat degrades report quality | Medium | Medium | A/B test with sample reports |
| Backward compatibility issues | Low | High | `provenance_version` per report, old reports untouched |
| Performance impact from validation | Low | Low | Regex check is O(n), negligible on report text |

---

## 4. Key Decisions Validated

1. **Binary-plus taxonomy** (📊 Fato / 🔮 Hipótese / ⚠️ Dados insuficientes) is simpler than 4-category and aligns with user preference.
2. **Emoji format** is scannable and language-agnostic, confirmed suitable for Portuguese reports.
3. **LLM-written Data Sources section** is preferred over auto-generation to allow contextualization.
4. **Three-layer defense** is necessary because LLM prompt compliance is probabilistic.
5. **economia-only scope** minimizes blast radius while proving the pattern.

---

*Research complete. Ready for planning.*
