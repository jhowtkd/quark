# Manual End-to-End Test: Milestone v1.3 Report Quality Pipeline

**Purpose:** Validate all 5 phases working together through the actual report generation API.
**Prerequisites:** Backend running, LLM API key configured, Zep graph available.

---

## Test Setup

### 1. Environment Check

```bash
cd /Users/jhonatan/Repos/Futuria/futuria-v2-refatorado/backend
python -c "from app.services.report_agent import ReportAgent; print('OK')"
python -c "from app.services.data_validation import DataValidationService; print('OK')"
python -c "from app.services.bias_audit import BiasAuditService; print('OK')"
python -c "from app.services.quality_gates import QualityGateService; print('OK')"
```

**Expected:** All imports succeed.

### 2. Start Backend (if not running)

```bash
cd /Users/jhonatan/Repos/Futuria/futuria-v2-refatorado/backend
# Using Flask development server
flask run --port 5000
# OR using your preferred WSGI server
```

### 3. Prepare Test Data

You need:
- A project with `simulation_requirement` set
- A built Zep graph (or the fallback search will be used)
- A completed simulation

**Quick path:** Use an existing simulation ID from your database, or create a new project with:
```json
{
  "name": "v1.3 E2E Test - Tesla Q1 2026",
  "simulation_requirement": "Analisar o desempenho da Tesla no primeiro trimestre de 2026, incluindo receita, margens, entregas e perspectivas para o ano."
}
```

Profile: **`economia`** (required to activate all v1.3 features)

---

## Test Procedure

### TEST 1: Generate Report with economia Profile

**Endpoint:** `POST /api/report/generate`

**Request:**
```json
{
  "simulation_id": "YOUR_SIMULATION_ID",
  "profile": "economia"
}
```

**Steps:**
1. Send the request
2. Poll `GET /api/report/generate/status?task_id=YOUR_TASK_ID` until status is `completed` or `failed`
3. Note the `report_id` from the response

**Expected Result:**
- Status: `completed`
- Report generation takes slightly longer than pre-v1.3 (due to validation + audit + gates)

---

### TEST 2: Verify Phase 8 — Data Provenance

**Check the generated report:**
```bash
cat uploads/reports/{report_id}/full_report.md
```

**Acceptance Criteria:**
- [ ] Every numeric claim has a tag: 📊, 🔮, or ⚠️
- [ ] Report ends with "## Fontes de Dados" section
- [ ] Simulated/projected data is tagged with 🔮 (not 📊)
- [ ] No untagged monetary values (US$ X, R$ X, etc.)

**Check meta.json:**
```bash
cat uploads/reports/{report_id}/meta.json | python -m json.tool
```

**Acceptance Criteria:**
- [ ] `"provenance_version": "1.0"` is present
- [ ] `"profile_type": "economia"` is present
- [ ] `"provenance_enabled": true` is present

**Check agent_log.jsonl:**
```bash
grep "provenance_tag" uploads/reports/{report_id}/agent_log.jsonl | head -5
```

**Acceptance Criteria:**
- [ ] Tool call entries include `provenance_tag` field

---

### TEST 3: Verify Phase 9 — Data Validation

**Check agent_log.jsonl:**
```bash
grep "data_validation" uploads/reports/{report_id}/agent_log.jsonl | python -m json.tool
```

**Acceptance Criteria:**
- [ ] `action: "data_validation"` entry exists
- [ ] Validation report contains extracted metrics (revenue, EPS, margins, etc.)
- [ ] If GAAP and non-GAAP EPS both appear, both are captured and distinguished

**If validation found discrepancies:**
```bash
grep -i "discrepanc\|warning\|flag" uploads/reports/{report_id}/agent_log.jsonl | head -10
```

**Acceptance Criteria:**
- [ ] Discrepancies are logged with severity and expected vs actual values

---

### TEST 4: Verify Phase 10 — Structured Report Format

**Check full_report.md structure:**

```bash
grep "^## " uploads/reports/{report_id}/full_report.md
```

**Expected section order (case-insensitive):**
1. `## Resumo Executivo` (or similar)
2. `## Panorama Macroeconomico` (or similar)
3. `## Tese Principal` or thesis section
4. `## Evidencias Verificadas` or evidence section
5. `## Fragilidades e Riscos` or risks section
6. `## Premissas Explicitas` or assumptions section
7. `## Cenarios` or scenarios section (Bear/Base/Bull)
8. `## Recomendacoes` or recommendations
9. `## Fontes de Dados`

**Acceptance Criteria:**
- [ ] Report follows due-diligence structure
- [ ] Scenarios include probability weights (e.g., "Probabilidade: 60%")
- [ ] Scenarios include trigger conditions (e.g., "Gatilho: se X acontecer")
- [ ] Tables accompany narrative where appropriate

---

### TEST 5: Verify Phase 11 — Bias Audit

**Check agent_log.jsonl:**
```bash
grep "bias_audit" uploads/reports/{report_id}/agent_log.jsonl | python -m json.tool
```

**Acceptance Criteria:**
- [ ] `action: "bias_audit"` entry exists
- [ ] `bias_score` is present (0.0 to 1.0)
- [ ] `is_balanced` boolean is present

**Check meta.json:**
```bash
cat uploads/reports/{report_id}/meta.json | grep -i bias
```

**Acceptance Criteria:**
- [ ] `bias_audit_report` or `bias_audit_enabled` field is present

**Manual review of report content:**
- [ ] Bull and bear arguments have comparable depth
- [ ] No section is entirely one-sided (all positive or all negative)
- [ ] Strong claims are backed by 📊 (factual) tags
- [ ] Competitive analysis includes numbers, not just adjectives

---

### TEST 6: Verify Phase 12 — Quality Gates

**Check agent_log.jsonl:**
```bash
grep "quality_gate\|language_consistency\|numeric_consistency\|self_contradiction\|known_limitations" uploads/reports/{report_id}/agent_log.jsonl | head -10
```

**Acceptance Criteria:**
- [ ] Quality gate entries exist in logs
- [ ] `language_consistency` gate passed (no mixed-language output)
- [ ] `known_limitations` section is present in final report

**Manual review:**
- [ ] Report is entirely in Portuguese (or entirely in English, per profile)
- [ ] No mid-document language switching
- [ ] "## Limitacoes Conhecidas" section exists at the end
- [ ] No numeric contradictions (e.g., revenue stated as both $95B and $94B)
- [ ] No unsupported valuation conclusions (e.g., target price without methodology)

**Check for warnings file:**
```bash
ls uploads/reports/{report_id}/provenance_warnings.txt 2>/dev/null && cat uploads/reports/{report_id}/provenance_warnings.txt
```

**Expected:** File may or may not exist. If it exists, review warnings but they should not block report delivery.

---

### TEST 7: Compare economia vs generico Profile

**Generate with `generico` profile:**
```json
{
  "simulation_id": "SAME_SIMULATION_ID",
  "profile": "generico"
}
```

**Acceptance Criteria:**
- [ ] Report generates successfully
- [ ] `meta.json` has `"provenance_enabled": false`
- [ ] `meta.json` has `"bias_audit_enabled": false`
- [ ] `meta.json` has `"quality_gates_enabled": false`
- [ ] Report does NOT have provenance emoji tags (or has fewer/less consistent tags)
- [ ] Report structure is less rigid (free-form)

This confirms that v1.3 features are **profile-gated** and only activate for `economia`.

---

### TEST 8: Backward Compatibility — Old Reports

**Find a pre-v1.3 report:**
```bash
ls uploads/reports/ | head -5
# Pick an old report_id (one without provenance_version in meta.json)
```

**Check old report meta.json:**
```bash
cat uploads/reports/{old_report_id}/meta.json | grep provenance_version || echo "NO provenance_version — this is an old report"
```

**View old report:**
```bash
cat uploads/reports/{old_report_id}/full_report.md | head -20
```

**Acceptance Criteria:**
- [ ] Old reports display without modification
- [ ] No provenance tags retroactively added
- [ ] No errors when loading old reports

---

## Failure Diagnosis

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Report generation fails with `Provenance support incomplete` | Agent missing `provenance_version` | Check `ReportAgent.__init__` has `self.provenance_version = "1.0"` |
| No provenance tags in report | `profile` not set to `economia` | Verify request includes `"profile": "economia"` |
| Bias audit not running | `require_bias_audit` not set | Check `ECONOMIA_CONFIG` has `"require_bias_audit": True` |
| Quality gates missing | `require_quality_gates` not set | Check `ECONOMIA_CONFIG` has `"require_quality_gates": True` |
| `json` import error in data validation | Missing import | Add `import json` to `data_validation.py` |
| Report takes too long | Validation + audit + gates add overhead | Expected; monitor via task status endpoint |

---

## Sign-off

**Tester:** _______________  
**Date:** _______________  
**Backend version/commit:** _______________

| Phase | Pass | Fail | Notes |
|-------|------|------|-------|
| 8 — Provenance | [ ] | [ ] | |
| 9 — Data Validation | [ ] | [ ] | |
| 10 — Structured Format | [ ] | [ ] | |
| 11 — Bias Audit | [ ] | [ ] | |
| 12 — Quality Gates | [ ] | [ ] | |
| Profile Gating | [ ] | [ ] | |
| Backward Compatibility | [ ] | [ ] | |

**Overall:** [ ] PASS  [ ] FAIL

---

*Test plan version: 1.0*  
*Created: 2026-04-27*  
*Scope: Milestone v1.3 end-to-end validation*
