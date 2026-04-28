# Changelog - Futur.ia v2.0

## Data: 2026-04-27
## Versão: v2.0 "Multi-Profile Refactor"

---

### ✅ FASE 1 - HOTFIXES CRÍTICOS (Backend)

**Arquivos modificados:**

1. **`backend/app/services/zep_tools.py`**
   - **P0 - Regex inválido corrigido:** Removido `re.sub(r'[^]+', ...)` + `re.split(r'[]', ...)` que causava `re.error`. Substituído por `re.split(r"[^\w]+", ...)` para tokenização segura.
   - **P1 - Tokenização quebrada corrigida:** `.replace('', ' ')` (NO-OP) substituído por `re.split(r"[^\w]+", ...)` em ambas as ocorrências (linhas ~584 e ~1269).
   - **P1 - Span duplo corrigido:** Adicionada flag `span_ended` em `insight_forge()` para prevenir chamada dupla de `span.end()`.
   - **P1 - Path relativo frágil corrigido:** `os.path.join(os.path.dirname(__file__), '../../uploads/simulations')` → `Config.OASIS_SIMULATION_DATA_DIR`.
   - **P2 - `check_graph_health()` adicionado:** Nova função que verifica N nodes, edges com `fact`, e retorna status: `"empty"`, `"no_facts"`, `"sparse"`, `"healthy"`.

2. **`backend/app/services/zep_entity_reader.py`**
   - **Filtro de entidades corrigido:** Entidades com labels genéricos `["Entity", "Node"]` NÃO são mais descartadas (antes: 92% perdidas).
   - **Inferência de tipo adicionada:** `_infer_entity_type_from_context()` usa heurística por palavras-chave (Person, Organization, Event, Location, Technology, Product, Concept).
   - **Validação de idioma adicionada:** `_contains_forbidden_script()` detecta chinês/japonês/coreano. Entidades com scripts proibidos são filtradas.
   - Parâmetro `forbidden_scripts` adicionado a `filter_defined_entities()`.

3. **`backend/app/services/graph_builder.py`**
   - **`_generate_edge_fact()` adicionado:** Gera descrição factual para edges que não têm campo `fact` preenchido, usando heurística + LLM.
   - `get_graph_data()` modificado para garantir que 100% das edges retornadas tenham `fact` preenchido.

---

### ✅ FASE 2 - SISTEMA DE PERFIS (Backend)

**Arquivos criados:**

4. **`backend/app/profiles/__init__.py`** — Exporta `ProfileManager`, `UserProfile`, `ProfileConfiguration`.

5. **`backend/app/profiles/profile_manager.py`** — Implementação completa:
   - 5 perfis: `GENERICO` (preto), `MARKETING` (azul #0066FF), `DIREITO` (marrom #8B4513), `ECONOMIA` (verde #006400), `SAUDE` (vermelho #C41E3A).
   - Cada perfil define: `persona_system_prompt`, `persona_user_prompt_suffix`, `report_system_prompt`, `report_section_prompt`, `simulation_overrides`, `entity_type_weights`, `deep_research_prompt_suffix`.
   - Regras de linguagem: `max_words_per_sentence` (25 ou 30), `report_temperature=0.3`, `forbidden_scripts=['zh','ja','ko']`.
   - Métodos: `apply_to_persona_generator()`, `apply_to_report_agent()`, `apply_to_simulation_config()`, `list_profiles()`.

**Arquivos modificados:**

6. **`backend/app/services/simulation_manager.py`**
   - `SimulationState` dataclass: campo `profile: str = "generico"` adicionado.
   - `to_dict()`, `to_simple_dict()`, `_load_simulation_state()` atualizados.
   - `create_simulation()` aceita parâmetro `profile: str = "generico"`.

7. **`backend/app/api/simulation.py`**
   - `POST /api/simulation/create` aceita `profile` no body JSON (opcional).
   - Nova rota: `GET /api/simulation/profiles/available` → lista perfis com metadata.

8. **`backend/app/api/report.py`**
   - `POST /api/report/generate` aceita `profile` no body (opcional).
   - Aplica `ProfileConfiguration.apply_to_report_agent()` antes de gerar.

9. **`backend/app/api/research.py`**
   - `POST /api/research/start` aceita `profile` no body (opcional).
   - Anexa `deep_research_prompt_suffix` do perfil à query.

---

### ✅ FASE 3 - REFRESH VISUAL (Frontend)

**Arquivos criados:**

10. **`frontend/src/components/ProfileSelector.vue`** — Componente de seleção de 5 perfis:
    - Cards clicáveis com bordas duras, sombras, cores por perfil (estilo brutalista).
    - Salva preferência no `localStorage` com chave `futuria_profile`.
    - Emite evento `profile-selected`.
    - Responsivo: 5→3→2 colunas.

**Arquivos modificados:**

11. **`frontend/src/views/Home.vue`**
    - `<ProfileSelector />` adicionado acima do botão "Iniciar Motor".
    - Toggle de tema escuro (`☾`/`☀`) na navbar.
    - Carrega perfil salvo do localStorage no `onMounted`.

12. **`frontend/src/store/pendingUpload.js`**
    - Campo `profile` no estado (default: `'generico'`).
    - `setProfile()` e `getProfile()` adicionados.

13. **`frontend/src/components/Step1GraphBuild.vue`**
    - Envia `profile` no body de `POST /api/simulation/create`.
    - CSS atualizado para usar `var(--profile-primary)` e `var(--profile-accent)`.

14. **`frontend/src/api/simulation.js`**
    - `listProfiles()` adicionado.

15. **`frontend/src/App.vue`**
    - CSS variables dinâmicas por perfil (`body[data-profile="X"]`).
    - Tema escuro `[data-theme="dark"]`: background `#0a0a0a`, surface `#1a1a1a`.
    - Progress bars, badges, scrollbars respondem ao perfil selecionado.

16. **`frontend/src/views/Process.vue`** — Toggle de tema escuro + CSS variables.
17. **`frontend/src/components/Step2EnvSetup.vue`** — CSS atualizado para variáveis de perfil.

---

### ✅ FASE 4 - QUALIDADE DE RELATÓRIOS & DEEP RESEARCH

**Arquivos modificados:**

18. **`backend/app/services/report_agent.py`**
    - Regras duras de linguagem injetadas em todos os prompts:
      - Máximo 25 palavras por frase.
      - Proibir adjetivos poéticos, metáforas, linguagem figurada.
      - Toda afirmação factual deve ter fonte identificável.
      - Notação numérica: `1,5%` em vez de "um vírgula cinco".
      - Se não houver dados suficientes, declarar explicitamente.
      - Nunca usar chinês, japonês ou coreano.
      - Tabelas estruturadas: headers e dados apenas.
    - Fallback de busca externa: quando grafo retorna 0 fatos, automaticamente aciona `ConnectorFallbackRouter.search()` (Brave/Tavily/Jina).
    - `profile` aceito em `__init__` (opcional, default `generico`).
    - `_validate_output_against_profile()` valida scripts proibidos e conta palavras por frase.
    - `_trigger_fallback_search()` formata resultados: `Fonte: [URL] | Data: [data] | Conteúdo: [resumo]`.
    - `check_graph_health()` usado em pre-check antes do ReACT loop.

19. **`backend/app/services/deep_research_agent.py`**
    - `ResearchState` expandido com `profile`, `graph_id`, `fallback_used`.
    - `search_node` reescrito com `check_graph_health()`:
      - `"healthy"` → grafo Zep como fonte primária + busca externa suplementar.
      - `"empty"` / `"no_facts"` / `"sparse"` → busca externa imediata (fallback).
    - `deep_research_prompt_suffix` do perfil aplicado à query.
    - `run_deep_research()` nova API pública: aceita `query`, `run_id`, `profile`, `graph_id`.
    - Resultados do fallback injetados no contexto do relatório.

---

### 📊 MÉTRICAS DE CORREÇÃO

| Problema Original | Correção | Arquivo |
|---|---|---|
| Regex `r'[^]+'` + `re.split(r'[]', ...)` causava `re.error` | Regex segura `re.split(r"[^\w]+", ...)` | zep_tools.py |
| `.replace('', ' ')` era NO-OP | `re.split(r"[^\w]+", ...)` funcional | zep_tools.py |
| `span.end()` chamado 2x para mesma span | Flag `span_ended` | zep_tools.py |
| Path relativo frágil | `Config.OASIS_SIMULATION_DATA_DIR` | simulation_manager.py |
| 92% entidades descartadas (labels genéricos) | Inferência heurística + não descartar | zep_entity_reader.py |
| Contaminação chinês/japonês | `_contains_forbidden_script()` + filtro | zep_entity_reader.py |
| Deep Research: 0 fatos, 0 entidades | `check_graph_health()` + fallback externo | deep_research_agent.py |
| Edges sem campo `fact` | `_generate_edge_fact()` preenche automaticamente | graph_builder.py |
| Linguagem rebuscada (80 palavras/frase) | Regras duras: max 25 palavras | report_agent.py |
| Sem sistema de perfis | 5 perfis com parâmetros próprios | profiles/profile_manager.py |
| Sem tema escuro | `data-theme="dark"` + CSS variables | App.vue |

---

### 🔒 PRESERVAÇÃO DE APIs

Todas as APIs existentes foram preservadas. O parâmetro `profile` é **opcional** em todos os endpoints:
- `POST /api/simulation/create`
- `POST /api/report/generate`
- `POST /api/research/start`
- `GET /api/simulation/{simulation_id}`

Se `profile` não for enviado, o sistema usa `UserProfile.GENERICO` automaticamente.

Tecnologias preservadas: Zep Cloud Graph, Brave Search, Tavily Search, Jina AI, OpenAI LLM, LangGraph, Langfuse, OASIS/CAMEL, Flask API, Vue 3 + Vite, D3.js, Convex.

---

### 🧪 TESTES RECOMENDADOS

1. **Teste de criação de simulação com perfil:**
   ```bash
   curl -X POST http://localhost:5000/api/simulation/create \
     -H "Content-Type: application/json" \
     -d '{"project_id": "test", "graph_id": "test", "profile": "marketing"}'
   ```

2. **Teste de listagem de perfis:**
   ```bash
   curl http://localhost:5000/api/simulation/profiles/available
   ```

3. **Teste de geração de relatório com perfil:**
   ```bash
   curl -X POST http://localhost:5000/api/report/generate \
     -H "Content-Type: application/json" \
   -d '{"simulation_id": "test", "profile": "direito"}'
   ```

4. **Teste de Deep Research com perfil:**
   ```bash
   curl -X POST http://localhost:5000/api/research/start \
     -H "Content-Type: application/json" \
   -d '{"query": "tendências mercado saúde 2026", "task_id": "test", "profile": "saude"}'
   ```

5. **Teste do frontend:**
   - Abrir Home → ver ProfileSelector com 5 cards
   - Selecionar perfil → verificar `localStorage.futuria_profile`
   - Alternar tema escuro → verificar `data-theme="dark"`
   - Cores do perfil devem aparecer em scrollbars, progress bars, badges

---

### 📝 NOTAS DE IMPLEMENTAÇÃO

- A refatoração foi executada com cautela para evitar quebra de APIs existentes.
- Todos os arquivos passaram em validação de sintaxe Python (`py_compile`).
- O frontend Vue foi modificado mantendo o estilo Neo-Brutalista original.
- O módulo `profiles/` é independente e pode ser estendido com novos perfis futuramente.
