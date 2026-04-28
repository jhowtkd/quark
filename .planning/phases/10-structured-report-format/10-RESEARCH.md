# Phase 10: Structured Report Format - Research

**Gathered:** 2026-04-27

## Current Outline Generation

The `plan_outline()` method uses:
- `PLAN_SYSTEM_PROMPT`: Generic instructions to design a concise report outline (2-5 sections)
- `PLAN_USER_PROMPT_TEMPLATE`: Simulation context injected into the user prompt
- `profile_system`: `ECONOMIA_CONFIG.report_system_prompt` is prepended to the system prompt

Current `ECONOMIA_CONFIG.report_system_prompt` has:
```
ESTRUTURA OBRIGATORIA:
1. Resumo Executivo (3 bullets com KPIs principais)
2. Panorama Macroeconomico (indicadores atuais)
3. Analise de Cenarios (Otimista / Base / Pessimista com probabilidades)
4. Impacto Setorial
5. Riscos e Sensibilidades
6. Recomendacoes Estrategicas (com retorno esperado)
```

This is a 6-section generic structure. The due-diligence structure requires 5 specific sections.

## Current Section Generation

`_generate_section_react()` builds the system prompt from:
1. `SECTION_SYSTEM_PROMPT_TEMPLATE` (generic ReACT rules)
2. `self._get_profile_section_prompt(section.title)` — adds `ECONOMIA_CONFIG.report_section_prompt`
3. `get_reporting_language_instruction()`

The `report_section_prompt` currently says:
```
Gere uma secao de relatorio economico com rigor quantitativo.
Inclua fontes, datas e margens de erro. Use terminologia padronizada.
Proibir metaforas ou adjetivos emocionais.
Lembre-se: etiquete TODO dado quantitativo...
```

This is generic across all sections. We need section-type-specific guidance.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LLM ignores outline structure prompt | Medium | Medium | Fallback outline uses due-diligence titles; post-processing can detect and warn |
| LLM mixes content types within sections | Medium | High | Stronger section prompt with explicit negative examples; validation in post-processing |
| Scenarios lack probability weights | Medium | Medium | Dedicated scenario prompt with mandatory fields; post-processing regex check |
| Tables missing from evidence sections | Medium | Low | Prompt explicitly says "obrigatorio"; not blocking |
| Breaking non-economia reports | Low | High | Changes are profile-scoped only |

## Implementation Strategy

1. **Profile config**: Add `outline_system_prompt` to `ECONOMIA_CONFIG` and `ProfileConfiguration`
2. **Outline enforcement**: Modify `plan_outline()` to inject `outline_system_prompt`
3. **Fallback outline**: Modify exception handler to return due-diligence sections for economia
4. **Section boundaries**: Update `ECONOMIA_CONFIG.report_section_prompt` with strict content-type rules per section
5. **Scenario rules**: Add scenario formatting block to the Cenários section prompt

## Files to Modify

- `backend/app/profiles/profile_manager.py` (~40 lines)
- `backend/app/services/report_agent.py` (~30 lines)

No new modules needed.
