# Reporting Language Integrity — Browser Regression Checklist

**Milestone:** M003 — S03 Language Policy Enforcement  
**Last verified:** 2026-04-17  
**Status:** ✅ All checks passing

---

## Purpose

This document describes the repeatable browser-level regression flow for the reporting
screens (Step 4 — Report Generation, Step 5 — Report Interaction). It was created after
the S03 remediation that:

1. Normalized all user-facing UI labels to Portuguese (T01)
2. Added client-side contamination detection with safe fallback UI (T02)
3. Verified end-to-end language stability and payload integrity (T03)

---

## Known Failure Modes (Historical)

Before S03:

- Report section titles and body text appeared in English or mixed language.
- Contaminated backend payloads (e.g. repeated tokens, control characters, injected
  scripts) were rendered directly into `v-html` without validation.
- Report-chat answers could contain XSS vectors silently passed through as valid content.
- Entity names from chat responses had no fidelity check.

---

## Layer 1: Build-Time Verification

```bash
cd /path/to/project/frontend
npm run build
```

**Expected:** exit 0, no TypeScript/Vue compilation errors, 755+ modules transformed.

---

## Layer 2: i18n Label Checks (Login / Public Routes)

Navigate to `http://localhost:4000`. The router redirects to `/login`.

| Element | Expected (pt) | NOT expected |
|---------|--------------|--------------|
| Page heading | `Entrar` | `Login` |
| Email field label | `E-mail` | `Email` / `E-mail address` |
| Password field label | `Senha` | `Password` |
| Register link | `Cadastre-se` | `Sign up` |
| Brand name | `FUTUR.IA` | (unchanged) |
| Language switcher | `Português ▼` | `English` |

```
browser_assert checks:
  - text_visible: "Entrar"
  - text_visible: "E-mail"
  - text_visible: "Senha"
  - text_visible: "Cadastre-se"
  - text_visible: "FUTUR.IA"
  - no_console_errors
```

**Result (2026-04-17):** ✅ 7/7 assertions passed

---

## Layer 3: Contamination Detection — Payload Validator Unit

These cases are exercisable via `browser_evaluate` against the `payloadValidator.js` logic
(importable from `frontend/src/utils/payloadValidator.js`).

### 3a. Clean Payloads (must render, not be flagged)

| Case ID | Input | Expected Severity |
|---------|-------|------------------|
| `clean_pt_title` | `Relatório de Previsão Eleitoral 2026 - Brasil` | `none` |
| `clean_section_body` | `O candidato Lula da Silva liderou...` | `none` |
| `clean_entity_name` | `Lula da Silva` | `none` |
| `clean_chat_answer` | `O partido PT obteve 35% dos votos válidos.` | `none` |

### 3b. Contaminated Payloads (must be flagged, not rendered)

| Case ID | Injection Type | Expected Severity | Expected Reason |
|---------|---------------|------------------|-----------------|
| `xss_script_tag` | `<script>alert(1)</script>` | `critical` | `script_injection` |
| `event_handler_injection` | `onclick=alert(1)` | `critical` | `event_injection` |
| `javascript_uri` | `javascript:document.cookie` | `critical` | `dangerous_uri_scheme` |
| `data_uri` | `data:text/html,...` | `critical` | `dangerous_uri_scheme` |
| `vbscript_uri` | `vbscript:msgbox(...)` | `critical` | `dangerous_uri_scheme` |
| `control_chars` | `\x00` embedded in text | `critical` | `control_characters` |
| `excessive_repetition` | word repeated 10+ times | `warning` | `excessive_repetition` |
| `empty_content` | `""` | `warning` | `empty_or_invalid` |
| `whitespace_only` | `"   "` | `warning` | `empty_content` |

**Result (2026-04-17):** ✅ 13/13 cases passed

---

## Layer 4: Section Rendering Simulation (Step4Report.vue)

Simulates `renderSafeSectionContent()` behavior for each payload class:

| Case | Input Pattern | Expected Output |
|------|--------------|-----------------|
| `section_clean_pt` | Valid Portuguese prose | `type: rendered` |
| `section_xss` | `<script>...</script>` in content | `type: fallback` |
| `section_event_injection` | `onclick=...` attribute | `type: fallback` |
| `section_js_uri` | `javascript:` in content | `type: fallback` |
| `section_control_chars` | `\x00` null byte in text | `type: fallback` |

Fallback renders the contamination warning UI:

```html
<!-- Step4Report.vue — v-else-if="contaminatedSections.has(idx + 1)" -->
<div class="contamination-warning">
  <svg><!-- triangle warning icon --></svg>
  <span class="warning-text">{{ $t('contamination.contentRemoved') }}</span>
</div>
```

Translated value: `"Conteúdo removido por violação de política"` (Portuguese)

**Result (2026-04-17):** ✅ 5/5 section cases passed

---

## Layer 5: Chat Response Validation (Step5Interaction.vue)

Simulates `validateChatMessage()` logic from Step5Interaction.vue:

| Case | Input | Expected Show | Entity Fidelity |
|------|-------|--------------|-----------------|
| `chat_clean_answer` | Valid Portuguese answer | `true` | — |
| `chat_entity_fidelity` | `Lula da Silva (PT) e Jair Bolsonaro (PL)...` | `true` | ✅ names preserved |
| `chat_xss` | `<script>steal(cookies)</script>` | `false` | — |
| `chat_event_injection` | `<img onerror=alert(1) src=x>` | `false` | — |
| `chat_js_uri` | `javascript:document.location` | `false` | — |

Contaminated chat messages are suppressed and replaced by the i18n key
`contamination.chatContaminated` → `"Mensagem com conteúdo comprometido - não exibida"`.

**Result (2026-04-17):** ✅ 5/5 chat cases passed

---

## Layer 6: i18n Keys for Contamination Warnings (pt.json)

Verify these keys exist and render the correct Portuguese text:

| i18n Key | Portuguese Value |
|----------|-----------------|
| `contamination.warning` | `Aviso de Segurança` |
| `contamination.contentRemoved` | `Conteúdo removido por violação de política` |
| `contamination.contentSanitized` | `Conteúdo sanitizado - alguns elementos foram removidos` |
| `contamination.sectionContaminated` | `Seção com conteúdo comprometido - mostrando placeholder` |
| `contamination.chatContaminated` | `Mensagem com conteúdo comprometido - não exibida` |
| `contamination.fallbackMessage` | `O conteúdo original não pôde ser exibido. Motivo: {reason}` |

---

## Layer 7: Report View Structural Labels

Once authenticated and a report is loaded at `/report/:reportId`:

| Location | Expected Portuguese Label |
|----------|--------------------------|
| Step indicator (header) | `Etapa 4/5` |
| Report tag badge | `Prediction Report` |
| Waiting state | `Esperando pelo Agente de Relatório...` |
| Section generating | `Gerando {title}...` |
| Complete banner | `Geração do Relatório Concluída` |
| Console title | `SAÍDA DO CONSOLE` |
| Empty report ID | `SEM_REL` |
| Agent activity empty | `Aguardando atividade do agente...` |
| Go to interaction button | `Entrar em Interação` |

---

## How to Run

### Automated (browser_evaluate)

Paste the test script from `.gsd/milestones/M003/slices/S03/tasks/T03-SUMMARY.md`
verification evidence into `browser_evaluate` in any Quark frontend browser session.

### Manual (step-by-step)

1. `cd frontend && npm run dev` — start on port 4000
2. Open `http://localhost:4000` — verify redirect to `/login` and Portuguese labels
3. Log in with valid credentials
4. Navigate to a completed simulation → trigger report generation
5. In Step 4 (ReportView): verify section titles are in configured language, no raw
   English strings appear, contaminated sections show warning banner
6. Navigate to Step 5 (InteractionView): send a question about an entity by name
7. Verify the response preserves entity names exactly (e.g. `Lula da Silva`, `PT`)
8. Inject a contaminated payload via dev tools → verify warning UI appears instead
   of raw injection content

---

## Re-run Triggers

Re-run this checklist when:
- `frontend/src/components/Step4Report.vue` is modified
- `frontend/src/components/Step5Interaction.vue` is modified
- `frontend/src/utils/payloadValidator.js` is modified
- `locales/pt.json` is modified (especially `contamination.*` or `step4.*` keys)
- Backend report payload schema changes
- A new injection pattern is discovered in production logs
