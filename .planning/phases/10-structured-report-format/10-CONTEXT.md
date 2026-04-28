# Phase 10: Structured Report Format - Context

**Gathered:** 2026-04-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace free-form narrative with a disciplined due-diligence structure that separates tese from evidência and quantifies scenarios. Reports must follow a fixed section order and each section must contain only content relevant to its heading.

Requirements: FORMAT-01, FORMAT-02, FORMAT-03, FORMAT-04
Depends on: Phase 9 (validation context now available)
</domain>

<decisions>
## Implementation Decisions

### Due-Diligence Section Structure
- **D-01:** For the `economia` profile, reports MUST follow this exact 5-section structure:
  1. **Tese Principal** — The core investment/simulation thesis in 1-2 sentences
  2. **Evidências Verificadas** — Facts, data, and quotes from the simulation/graph
  3. **Fragilidades e Riscos** — Bear case arguments, vulnerabilities, counter-evidence
  4. **Premissas Explícitas** — Assumptions that must hold for the thesis to be true
  5. **Cenários (Bear / Base / Bull)** — Quantified outcomes with probability weights and trigger conditions
- **D-02:** The outline generation prompt (`outline_system_prompt`) is the enforcement layer. It instructs the LLM to return exactly these 5 section titles. If the LLM deviates, the fallback outline also uses these titles for economia.
- **D-03:** Each section's content boundaries are enforced via the `report_section_prompt` (injected into every section's system prompt). The prompt explicitly forbids mixing tese content into evidências, etc.

### Content Boundary Enforcement
- **D-04:** `report_section_prompt` for economia is updated with strict content-type rules:
  - Tese: only thesis statement, no evidence tables
  - Evidências: only verified facts with sources, no opinion or speculation
  - Fragilidades: only risks and counter-arguments, no bullish mitigation unless as rebuttal
  - Premissas: only explicit assumptions, each with a "if false then..." consequence
  - Cenários: only quantified projections with probabilities and triggers
- **D-05:** Quantified tables (FORMAT-03) are required in Evidências and Cenários sections. The existing table format rule is preserved and strengthened.

### Scenario Format (FORMAT-04)
- **D-06:** The Cenários section must include:
  - Bear case: probability weight (e.g., 25%), key trigger condition, quantified outcome
  - Base case: probability weight (e.g., 50%), key trigger condition, quantified outcome
  - Bull case: probability weight (e.g., 25%), key trigger condition, quantified outcome
  - Probability weights must sum to 100%
  - Triggers must be observable events, not vague sentiments
- **D-07:** Scenario formatting rules are injected via a dedicated prompt addition in the section prompt for Cenários.

### Integration with Phase 9
- **D-08:** The validation report from Phase 9 influences the Cenários section: if validation confidence is low, the Base case probability should be wider or the bull/bear ranges expanded.
- **D-09:** Provenance tags (Phase 8) continue to be required. Structured format does not replace provenance; it complements it.

### Scope
- **D-10:** Economy profile only. Other profiles retain their existing structures.
- **D-11:** No frontend changes. Structure is enforced in the backend prompt layer.
</decisions>

<specifics>
## Specific Ideas

- The Tesla report mixed thesis and evidence in unstructured blocks. This phase eliminates that by forcing explicit section separation.
- The LLM sometimes "cheats" by putting bullish arguments in the Fragilidades section with immediate rebuttals. The prompt must explicitly forbid this: "Nao rebata fragilidades dentro da mesma secao. Deixe o leitor avaliar."
- Probability weights are a known weakness of LLMs (they don't sum to 100%). The prompt should require the LLM to state probabilities explicitly and we can add a lightweight post-processor to verify the sum.
- Tables are already required in ECONOMIA_CONFIG but often ignored by the LLM. Strengthening the section prompt with "Obrigatorio: inclua tabela" helps.
</specifics>

<canonical_refs>
## Canonical References

### Report Generation Pipeline
- `backend/app/services/report_agent.py`:
  - `plan_outline()` lines ~1404-1518 — where outline structure is enforced
  - `_generate_section_react()` lines ~1517-1913 — where section content boundaries are enforced
  - `PLAN_SYSTEM_PROMPT` and `PLAN_USER_PROMPT_TEMPLATE` lines ~548-591
- `backend/app/profiles/profile_manager.py`:
  - `ECONOMIA_CONFIG` lines ~188-275 — where prompts and structure rules live
  - `ProfileConfiguration` dataclass — where new fields are added

### Existing Phase 8/9 Integration
- `backend/app/services/data_validation.py` — ValidationReport with confidence levels
- Provenance tags (📊🔮⚠️) already enforced in section prompts
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ProfileConfiguration.apply_to_report_agent()` already injects `system_prompt` and `section_prompt`. Adding `outline_system_prompt` follows the same pattern.
- `ReportAgent._get_profile_section_prompt()` dynamically adds section guidance per profile.
- `ReportAgent.plan_outline()` already applies `profile_system` to the planning system prompt.

### Established Patterns
- Profile-specific configuration is applied via `profile.apply_to_report_agent(agent)`.
- Fallback outlines are hardcoded in `plan_outline()` exception handler.
- Post-processing (`_post_process_report`) cleans headings and deduplicates.

### Integration Points
- **Outline enforcement:** `plan_outline()` system prompt injection.
- **Fallback outline:** Exception handler in `plan_outline()` returns default sections.
- **Section boundaries:** `_generate_section_react()` system prompt via `_get_profile_section_prompt()`.
- **Scenario rules:** Can be injected as part of `section_prompt` or as a dedicated conditional block in `_generate_section_react()`.
</code_context>

<deferred>
## Deferred Ideas

- Automatic probability-sum validator (100% check) — lightweight but not critical for v1.3
- Interactive report builder UI — out of scope
- Multi-language due-diligence templates — single language per report is the rule
- Custom section structures per user request — future milestone
</deferred>

---

*Phase: 10-structured-report-format*
*Context gathered: 2026-04-27*
