# Manual End-to-End Regression Test

**Purpose:** Validate the full FUTUR.IA pipeline across all 5 scenario profiles.
**Scope:** Graph generation → Simulation → Report generation → Quality verification.

---

## Pre-requisitos

Before executing any scenario, ensure the following are available and running:

1. **Backend running** — Flask application started on the expected port (default `5000`).
   ```bash
   cd backend && flask run --port 5000
   ```
2. **LLM API key configured** — `OPENAI_API_KEY` (or provider equivalent) exported in the environment.
3. **Zep Cloud / Zep graph available** — `ZEP_API_KEY` set; graph service reachable or Docker container running.
4. **Docker** (optional but recommended) — for local Zep, OASIS, or database dependencies.

**Quick health check:**
```bash
curl http://localhost:5000/health
# Expected: {"status":"ok","service":"FUTUR.IA Backend"}
```

---

## Cenario Saude

**Profile:** `saude`  
**Topic:** Aprovacao de novo medicamento para diabetes tipo 2  
**Requirement:** Simular a reacao da comunidade medica e do publico geral a aprovacao de um novo medicamento para diabetes tipo 2 no Brasil, incluindo endocrinologistas, pacientes, influenciadores de saude e laboratorios farmaceuticos.

**Env config reference:**
```json
{
  "chunkSize": 800,
  "chunkOverlap": 150,
  "maxRounds": 8,
  "minutesPerRound": 30,
  "echo_chamber_strength": 0.3
}
```

### Steps

**Step 1 — Create project**
```bash
curl -X POST http://localhost:5000/api/graph/ontology/generate \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "E2E Regression - Saude",
    "simulation_requirement": "Simular a reacao da comunidade medica e do publico geral a aprovacao de um novo medicamento para diabetes tipo 2 no Brasil, incluindo endocrinologistas, pacientes, influenciadores de saude e laboratorios farmaceuticos.",
    "profile": "saude"
  }'
```
**Verify:** Response contains `project_id` and `ontology_generated` is `true`.

**Step 2 — Validate graph**
```bash
curl http://localhost:5000/api/graph/project/{project_id}
```
**Verify:** At least `6` entities and `4` relations returned; unknown rate ≤ `0.25`.

**Step 3 — Start simulation**
```bash
curl -X POST http://localhost:5000/api/simulation/create \
  -H "Content-Type: application/json" \
  -d '{"graph_id":"{project_id}"}'
```
**Verify:** `simulation_id` returned; prepare/start endpoints succeed.

**Step 4 — Generate report**
```bash
curl -X POST http://localhost:5000/api/report/generate \
  -H "Content-Type: application/json" \
  -d '{"simulation_id":"{simulation_id}","profile":"saude"}'
```
**Verify:** Task status reaches `completed`; `report_id` present.

**Step 5 — Verify report**
```bash
cat uploads/reports/{report_id}/full_report.md
cat uploads/reports/{report_id}/meta.json | python -m json.tool
```
**Verify:** Checklist below.

### Verification Checklist

- [ ] Relatorio nao vazio
- [ ] Sem thinking process exposto
- [ ] Sem contaminacao linguistica
- [ ] simulated_hours > 0 (minimo esperado: 4h)
- [ ] Acoes totais coerentes com rounds (minimo esperado: 20 acoes)
- [ ] Taxa de Unknown abaixo do limite (≤ 0.25)
- [ ] Falhas retornam erro claro (se houver)

---

## Cenario Marketing

**Profile:** `marketing`  
**Topic:** Lancamento de smartphone sustentavel  
**Requirement:** Simular o lancamento de uma campanha de marketing digital para um smartphone sustentavel, analisando a reacao de consumidores, tech reviewers, concorrentes e agencias de publicidade nas redes sociais.

**Env config reference:**
```json
{
  "chunkSize": 800,
  "chunkOverlap": 150,
  "maxRounds": 8,
  "minutesPerRound": 30,
  "echo_chamber_strength": 0.4
}
```

### Steps

**Step 1 — Create project**
```bash
curl -X POST http://localhost:5000/api/graph/ontology/generate \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "E2E Regression - Marketing",
    "simulation_requirement": "Simular o lancamento de uma campanha de marketing digital para um smartphone sustentavel, analisando a reacao de consumidores, tech reviewers, concorrentes e agencias de publicidade nas redes sociais.",
    "profile": "marketing"
  }'
```
**Verify:** Response contains `project_id` and `ontology_generated` is `true`.

**Step 2 — Validate graph**
```bash
curl http://localhost:5000/api/graph/project/{project_id}
```
**Verify:** At least `6` entities and `4` relations returned; unknown rate ≤ `0.25`.

**Step 3 — Start simulation**
```bash
curl -X POST http://localhost:5000/api/simulation/create \
  -H "Content-Type: application/json" \
  -d '{"graph_id":"{project_id}"}'
```
**Verify:** `simulation_id` returned; prepare/start endpoints succeed.

**Step 4 — Generate report**
```bash
curl -X POST http://localhost:5000/api/report/generate \
  -H "Content-Type: application/json" \
  -d '{"simulation_id":"{simulation_id}","profile":"marketing"}'
```
**Verify:** Task status reaches `completed`; `report_id` present.

**Step 5 — Verify report**
```bash
cat uploads/reports/{report_id}/full_report.md
cat uploads/reports/{report_id}/meta.json | python -m json.tool
```
**Verify:** Checklist below.

### Verification Checklist

- [ ] Relatorio nao vazio
- [ ] Sem thinking process exposto
- [ ] Sem contaminacao linguistica
- [ ] simulated_hours > 0 (minimo esperado: 4h)
- [ ] Acoes totais coerentes com rounds (minimo esperado: 20 acoes)
- [ ] Taxa de Unknown abaixo do limite (≤ 0.25)
- [ ] Falhas retornam erro claro (se houver)

---

## Cenario Direito

**Profile:** `direito`  
**Topic:** Reforma do Codigo de Defesa do Consumidor  
**Requirement:** Simular o debate publico sobre uma proposta de reforma do Codigo de Defesa do Consumidor, incluindo advogados, juizes, associacoes de consumidores, empresas do varejo e jornalistas especializados.

**Env config reference:**
```json
{
  "chunkSize": 900,
  "chunkOverlap": 200,
  "maxRounds": 8,
  "minutesPerRound": 30,
  "echo_chamber_strength": 0.35
}
```

### Steps

**Step 1 — Create project**
```bash
curl -X POST http://localhost:5000/api/graph/ontology/generate \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "E2E Regression - Direito",
    "simulation_requirement": "Simular o debate publico sobre uma proposta de reforma do Codigo de Defesa do Consumidor, incluindo advogados, juizes, associacoes de consumidores, empresas do varejo e jornalistas especializados.",
    "profile": "direito"
  }'
```
**Verify:** Response contains `project_id` and `ontology_generated` is `true`.

**Step 2 — Validate graph**
```bash
curl http://localhost:5000/api/graph/project/{project_id}
```
**Verify:** At least `6` entities and `4` relations returned; unknown rate ≤ `0.25`.

**Step 3 — Start simulation**
```bash
curl -X POST http://localhost:5000/api/simulation/create \
  -H "Content-Type: application/json" \
  -d '{"graph_id":"{project_id}"}'
```
**Verify:** `simulation_id` returned; prepare/start endpoints succeed.

**Step 4 — Generate report**
```bash
curl -X POST http://localhost:5000/api/report/generate \
  -H "Content-Type: application/json" \
  -d '{"simulation_id":"{simulation_id}","profile":"direito"}'
```
**Verify:** Task status reaches `completed`; `report_id` present.

**Step 5 — Verify report**
```bash
cat uploads/reports/{report_id}/full_report.md
cat uploads/reports/{report_id}/meta.json | python -m json.tool
```
**Verify:** Checklist below.

### Verification Checklist

- [ ] Relatorio nao vazio
- [ ] Sem thinking process exposto
- [ ] Sem contaminacao linguistica
- [ ] simulated_hours > 0 (minimo esperado: 4h)
- [ ] Acoes totais coerentes com rounds (minimo esperado: 20 acoes)
- [ ] Taxa de Unknown abaixo do limite (≤ 0.25)
- [ ] Falhas retornam erro claro (se houver)

---

## Cenario Economia

**Profile:** `economia`  
**Topic:** Elevacao da taxa Selic em 2%  
**Requirement:** Analisar o impacto de uma elevacao de 2% na taxa Selic sobre o comportamento de investidores pessoa fisica, fintechs, bancos tradicionais e analistas do mercado financeiro nas redes sociais.

**Env config reference:**
```json
{
  "chunkSize": 800,
  "chunkOverlap": 150,
  "maxRounds": 10,
  "minutesPerRound": 30,
  "echo_chamber_strength": 0.3
}
```

### Steps

**Step 1 — Create project**
```bash
curl -X POST http://localhost:5000/api/graph/ontology/generate \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "E2E Regression - Economia",
    "simulation_requirement": "Analisar o impacto de uma elevacao de 2% na taxa Selic sobre o comportamento de investidores pessoa fisica, fintechs, bancos tradicionais e analistas do mercado financeiro nas redes sociais.",
    "profile": "economia"
  }'
```
**Verify:** Response contains `project_id` and `ontology_generated` is `true`.

**Step 2 — Validate graph**
```bash
curl http://localhost:5000/api/graph/project/{project_id}
```
**Verify:** At least `7` entities and `5` relations returned; unknown rate ≤ `0.20`.

**Step 3 — Start simulation**
```bash
curl -X POST http://localhost:5000/api/simulation/create \
  -H "Content-Type: application/json" \
  -d '{"graph_id":"{project_id}"}'
```
**Verify:** `simulation_id` returned; prepare/start endpoints succeed.

**Step 4 — Generate report**
```bash
curl -X POST http://localhost:5000/api/report/generate \
  -H "Content-Type: application/json" \
  -d '{"simulation_id":"{simulation_id}","profile":"economia"}'
```
**Verify:** Task status reaches `completed`; `report_id` present.

**Step 5 — Verify report**
```bash
cat uploads/reports/{report_id}/full_report.md
cat uploads/reports/{report_id}/meta.json | python -m json.tool
grep "provenance_tag" uploads/reports/{report_id}/agent_log.jsonl | head -5
```
**Verify:** Checklist below.

### Verification Checklist

- [ ] Relatorio nao vazio
- [ ] Sem thinking process exposto
- [ ] Sem contaminacao linguistica
- [ ] simulated_hours > 0 (minimo esperado: 5h)
- [ ] Acoes totais coerentes com rounds (minimo esperado: 25 acoes)
- [ ] Taxa de Unknown abaixo do limite (≤ 0.20)
- [ ] Falhas retornam erro claro (se houver)
- [ ] **Data provenance:** Every numeric claim tagged with 📊, 🔮, or ⚠️
- [ ] **Data provenance:** Report ends with "## Fontes de Dados" section
- [ ] **Data provenance:** `meta.json` contains `"provenance_enabled": true`
- [ ] **Data provenance:** Simulated/projected data tagged with 🔮 (not 📊)

---

## Cenario Geopolitica

**Profile:** `geopolitica`  
**Topic:** Descoberta de reservas de litio em territorio disputado  
**Requirement:** Simular a reacao internacional a uma descoberta de reservas de litio em territorio disputado na America do Sul, incluindo governos, ONGs ambientais, mineradoras, analistas geopoliticos e comunidades locais.

**Env config reference:**
```json
{
  "chunkSize": 900,
  "chunkOverlap": 200,
  "maxRounds": 10,
  "minutesPerRound": 30,
  "echo_chamber_strength": 0.45
}
```

### Steps

**Step 1 — Create project**
```bash
curl -X POST http://localhost:5000/api/graph/ontology/generate \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "E2E Regression - Geopolitica",
    "simulation_requirement": "Simular a reacao internacional a uma descoberta de reservas de litio em territorio disputado na America do Sul, incluindo governos, ONGs ambientais, mineradoras, analistas geopoliticos e comunidades locais.",
    "profile": "geopolitica"
  }'
```
**Verify:** Response contains `project_id` and `ontology_generated` is `true`.

**Step 2 — Validate graph**
```bash
curl http://localhost:5000/api/graph/project/{project_id}
```
**Verify:** At least `7` entities and `5` relations returned; unknown rate ≤ `0.25`.

**Step 3 — Start simulation**
```bash
curl -X POST http://localhost:5000/api/simulation/create \
  -H "Content-Type: application/json" \
  -d '{"graph_id":"{project_id}"}'
```
**Verify:** `simulation_id` returned; prepare/start endpoints succeed.

**Step 4 — Generate report**
```bash
curl -X POST http://localhost:5000/api/report/generate \
  -H "Content-Type: application/json" \
  -d '{"simulation_id":"{simulation_id}","profile":"geopolitica"}'
```
**Verify:** Task status reaches `completed`; `report_id` present.

**Step 5 — Verify report**
```bash
cat uploads/reports/{report_id}/full_report.md
cat uploads/reports/{report_id}/meta.json | python -m json.tool
```
**Verify:** Checklist below.

### Verification Checklist

- [ ] Relatorio nao vazio
- [ ] Sem thinking process exposto
- [ ] Sem contaminacao linguistica
- [ ] simulated_hours > 0 (minimo esperado: 5h)
- [ ] Acoes totais coerentes com rounds (minimo esperado: 25 acoes)
- [ ] Taxa de Unknown abaixo do limite (≤ 0.25)
- [ ] Falhas retornam erro claro (se houver)

---

## Sign-off

**Tester:** _______________  
**Date:** _______________  
**Backend version/commit:** _______________

| Cenario       | Pass | Fail | Notes |
|---------------|------|------|-------|
| Saude         | [ ]  | [ ]  |       |
| Marketing     | [ ]  | [ ]  |       |
| Direito       | [ ]  | [ ]  |       |
| Economia      | [ ]  | [ ]  |       |
| Geopolitica   | [ ]  | [ ]  |       |

**Overall:** [ ] PASS  [ ] FAIL

---

*Test plan version: 1.0*  
*Created: 2026-05-02*  
*Scope: Full scenario regression across all 5 FUTUR.IA profiles*
