# Phase 8: Data Provenance and Labeling - Context

**Gathered:** 2026-04-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Enforce strict source tagging and transparency for every data point in generated reports. Every quantitative claim must carry an explicit source-type label, and simulated/projected data must never be presented as verified fact.

Requirements: PROV-01, PROV-02, PROV-03, PROV-04
</domain>

<decisions>
## Implementation Decisions

### Label Taxonomy and Detection
- **D-01:** Labels are simplified to a binary-plus system: **📊 Fato** (verified/extracted data), **🔮 Hipótese** (projection, inference, or LLM-completed claim), **⚠️ Dados insuficientes** (when evidence is missing).
- **D-02:** Data from the Zep graph is labeled **"📊 Fato — extraído da base de conhecimento"** by default. The extraction process itself is acknowledged as a potential error source, so "extraído da base" is used rather than claiming absolute ground truth.
- **D-03:** The LLM must always cite whether a claim is based on an exact source or a projection/hipótese. No unlabeled numeric claims are allowed in the final report.
- **D-04:** Fallback search results (Brave/Tavily/Jina) are labeled **"📊 Fato — fonte externa"** and must include the specific source URL or name when available.
- **D-05:** When the LLM emits "Nao possuo informacoes suficientes" or similar insufficient-data language, it is automatically tagged as **"⚠️ Dados insuficientes"**.

### Injection Point in the Pipeline (Defense in Depth)
- **D-06:** Provenance is enforced at **three layers simultaneously**:
  - **Layer A (Data Retrieval):** ZepTools and fallback search results are wrapped with metadata blocks (`source`, `tool_name`, `query`, `retrieved_at`, `connector_name`) before being fed into the LLM context.
  - **Layer B (LLM Prompt):** The `economia` profile system prompt and section prompts are updated to instruct the LLM to use inline emoji tags (`📊`, `🔮`, `⚠️`) around every quantitative claim.
  - **Layer C (Report Assembly):** Post-processing validates that all numeric claims have an associated tag. Missing tags trigger a warning in the observability log.
- **D-07:** Inline emoji format in the final report: each claim or paragraph ends with the corresponding emoji tag. Example: `"Receita de 2025: US$ 94,8 bilhões 📊"` or `"Projeção de crescimento para 2026: 8% 🔮"`.
- **D-08:** Provenance metadata is visible in **both** the user-facing report (emoji tags) and the technical logs (`agent_log.jsonl` + `meta.json`).
- **D-09:** The **Data Sources** section at the end of the report is written by the LLM (not auto-generated from tool logs). It is instructed in the prompt to summarize and contextualize all sources used, with specific URLs/names for external sources.

### Scope: economia-only initially
- **D-10:** Provenance labeling is **hardcoded into the `ECONOMIA_CONFIG` profile** for this phase. The `ReportAgent` architecture should not block future expansion to other profiles, but no engineering effort is spent on generic toggles now.
- **D-11:** The generic profile (`generico`) will inherit provenance behavior if and when the user requests it in a future milestone. For now, only `economia` activates the provenance prompts and validation.

### Existing Reports and Backward Compatibility
- **D-12:** Old reports (generated before this phase) are displayed **as-is**, without provenance labels or banners. No retroactive processing.
- **D-13:** Each report's `meta.json` receives a `provenance_version` field set at generation time. The version is immutable for that report — future provenance schema changes do not affect previously generated reports.
- **D-14:** The `agent_log.jsonl` schema is extended with a `provenance_tag` field on each tool call and LLM response entry. This is the chosen approach over a separate `provenance.json` file.
- **D-15:** If a report generation is in-flight during the deployment of this phase, the system **aborts the generation** and prompts the user to restart the simulation. No hybrid or partial-provenance reports are allowed.

### Claude's Discretion
- Exact placement of emoji tags within sentences (end-of-sentence vs end-of-paragraph)
- Visual styling of the Data Sources section (heading level, formatting)
- Implementation details of the post-processing validator (regex vs NLP-based claim detection)
- Error handling when the LLM refuses to use emoji tags (retry strategy)
</decisions>

<specifics>
## Specific Ideas

- The user explicitly referenced the Tesla report (report_0166d514bfa1) as the catalyst for this phase. The root cause was unlabeled "simulated financial data" being presented as fact.
- The user prefers a **binary-plus** label system (Fato/Hipótese/Dados insuficientes) over the original four-category system (realizado/consenso/projeção/simulação). This simplifies both prompt engineering and user comprehension.
- Emojis were chosen over footnotes or bracketed text because they are visually scannable and language-agnostic.
- The Data Sources section being LLM-written (not auto-generated) means the prompt must strongly instruct citation of URLs and source names to prevent hallucination.
</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Report Generation Pipeline
- `backend/app/services/report_agent.py` — Core `ReportAgent`, `ReportManager`, `ReportLogger`. Lines ~1088 (`_execute_tool()`) is the central bottleneck for provenance injection.
- `backend/app/profiles/profile_manager.py` — `ECONOMIA_CONFIG` definition. Where provenance prompts and `require_provenance` logic live.
- `backend/app/api/report.py` — API endpoints. Where in-flight generation abort logic may be needed.

### Data Retrieval Layer
- `backend/app/services/zep_tools.py` — Zep graph tools (`insight_forge`, `panorama_search`, `quick_search`, `interview_agents`). Where Layer A metadata wrapping happens.
- `backend/app/services/deep_research_agent.py` — Fallback research pipeline. Where external source tagging happens.

### Quality & Observability
- `backend/app/utils/language_integrity.py` — Existing validation framework. Provenance post-processing validator can live here or in a new module.
- `backend/app/observability/reporting.py` — Langfuse scoring. New provenance coverage score should be added.

### Project Requirements
- `.planning/REQUIREMENTS.md` — PROV-01 through PROV-04, VALID-01 through VALID-04 (overlap with Phase 9).
- `.planning/ROADMAP.md` — Phase 8 goal and success criteria.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ReportLogger` (`agent_log.jsonl`) already captures every tool call with parameters and full results. Extending it with `provenance_tag` is minimal friction.
- `ProfileManager.get_profile_or_default()` already applies profile-specific prompts and rules. `ECONOMIA_CONFIG` is the natural place to add provenance instructions.
- `ReportAgent._post_process_report()` already deduplicates headings and cleans whitespace. Provenance tag validation can be added here.

### Established Patterns
- Profile-specific rules are applied via `profile.apply_to_report_agent(agent)` which sets `system_prompt`, `section_prompt`, `temperature`, `max_words_per_sentence`, `forbidden_scripts`, `entity_type_weights`.
- The ReACT loop enforces minimum 3 and maximum 5 tool calls per section. Provenance metadata from each tool call feeds into the section's evidence pool.
- Reports are saved to `reports/{id}/section_{NN}.md` then assembled into `full_report.md` + `meta.json`.

### Integration Points
- **Layer A:** `ZepTools` result formatting → add `provenance` field to `SearchResult`, `InsightForgeResult`, `PanoramaResult`.
- **Layer B:** `ReportAgent._generate_section_react()` → update `SECTION_SYSTEM_PROMPT_TEMPLATE` and `ECONOMIA_CONFIG.section_prompt` to require emoji tags.
- **Layer C:** `ReportAgent.assemble_full_report()` → validate emoji tag coverage; append Data Sources section if missing.
- **Abort logic:** `backend/app/api/report.py` → detect version mismatch between simulation start and current `ReportAgent` provenance capability; abort if mismatch.
</code_context>

<deferred>
## Deferred Ideas

- Generic provenance toggle for all profiles (`marketing`, `direito`, `saude`, `generico`) — future milestone
- Retroactive provenance inference for old reports — explicitly rejected
- Separate `provenance.json` file alongside `meta.json` — explicitly rejected in favor of extending `agent_log.jsonl`
- Auto-generated Data Sources section from tool logs — explicitly rejected in favor of LLM-written section
- Footnote or bracketed-text citation format — explicitly deferred in favor of emoji tags
</deferred>

---

*Phase: 08-data-provenance-and-labeling*
*Context gathered: 2026-04-27*
