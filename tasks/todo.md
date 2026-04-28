# Landfuse / Langfuse Observability Plan

## Objetivo
Fechar observabilidade do backend com tracing consistente e smoke final sem quebrar modo no-op.

## Plano
- [x] Validar base atual de observability e corrigir fallback do SDK quando `langfuse` não estiver instalado.
- [x] S01: manter tracing em `SimulationConfigGenerator`, `OasisProfileGenerator` e `ZepToolsService`.
- [x] S02: manter tracing de lifecycle em `SimulationManager` e `SimulationRunner`.
- [x] S03: manter tracing em `GraphBuilderService` e `SimulationIPCClient`.
- [x] Rodar smoke full de observability e confirmar compatibilidade com `NoOpObservabilityClient`.

## Review
- Base validada.
- Fallback de SDK ausente corrigido em `backend/app/observability/langfuse_client.py`.
- Root span de `SimulationConfigGenerator.generate_config()` agora fecha também em erro.
- `SimulationRunner.start_simulation()` e `stop_simulation()` agora fecham span em caminhos de erro e início inválido.
- `OasisProfileGenerator` agora expõe retry attempts como spans filhos (`profile_generation.attempt`).
- Smoke de observability passou: `84 passed`.

---

# Zep Alternatives Research Plan

## Objetivo
Investigar alternativas ao Zep para Quark, com foco em menor custo sem perder efetividade para memória temporal, entity graph, graph search e recuperação de contexto.

## Plano
- [x] Confirmar função exata que Zep cumpre hoje no projeto e quais capacidades são obrigatórias.
- [x] Levantar preço e capacidades atuais do Zep Cloud em fontes oficiais.
- [x] Pesquisar alternativas oficiais mais baratas ou open source viáveis para mesma classe de problema.
- [x] Comparar custo, aderência funcional, esforço de migração e risco operacional.
- [x] Registrar recomendação objetiva com cenários: menor custo, menor retrabalho e melhor equilíbrio.

## Review
- Quark usa Zep como grafo temporal com ontologia customizada, ingestão por episódios, busca em edges/nodes e recuperação de contexto; não é uso simples de chat memory.
- Zep Flex verificado em fonte oficial: `$25/mês`, `20.000` créditos incluídos, `1 crédito` por episode base; episódios maiores que `350 bytes` consomem múltiplos créditos.
- Alternativa mais próxima funcionalmente é `Graphiti` open source, porque é o core aberto por trás do Zep, mas exige operar stack própria e construir gestão de usuários/sessões/tooling.
- `Mem0` é candidato viável só com mais composição: Graph Memory OSS + graph backend + vector DB. Mais barato em alguns cenários, porém menos drop-in para fluxo atual.
- `LangGraph + Postgres/pgvector`, `Qdrant`, `Supabase` e `Letta` podem reduzir custo, mas não replicam sozinhos grafo temporal + ontologia + busca híbrida do jeito que Quark usa hoje.

---

# Phase 5 Execution Plan

## Objetivo
Executar a Fase 5 do milestone de otimização de custo do Zep: novos defaults de chunking, preview de custo antes do build e confirmação explícita no frontend.

## Plano
- [x] Validar backend da Fase 5 com testes para defaults, preview de custo e guardrails.
- [x] Remover auto-build do frontend e exigir preview antes da confirmação.
- [x] Exibir preview com chunks, bytes, créditos estimados e warning de custo.
- [x] Permitir ajuste de `chunk_size` e `chunk_overlap` no fluxo do Step 1.
- [x] Rodar verificação final do backend e build do frontend.

## Review
- Backend passou a aceitar preview sem `ZEP_API_KEY`, mantendo a exigência da chave apenas no build real.
- `MainView` agora segura a construção automática, preserva `chunk_size/chunk_overlap` no estado da tela e exige preview antes de confirmar o build.
- `Step1GraphBuild` ganhou controles de chunking, preview com métricas estimadas e confirmação explícita antes da ingestão.
- Verificação concluída com `9 passed` nos testes de backend da Fase 5 e `vite build` ok no frontend.
- Smoke com projeto clone real confirmou o fluxo de preview: projeto legado `500/50` foi normalizado para `300/30` e retornou `54` chunks / `12016` bytes / `54` créditos estimados.
- Normalização do backend agora adapta entities/source_targets para `PascalCase`, edge keys para `SCREAMING_SNAKE_CASE` e atributos para `snake_case` antes do `set_ontology`, sem mutar a ontologia persistida.
- Re-smoke com a ontologia original do projeto avançou além do ponto de falha anterior: `set_ontology` aceito, `graph_id` criado e ingestão de `54` chunks concluída, ficando apenas na espera do processamento assíncrono do Zep.
- Smoke estendido fechou o ciclo completo até `graph_completed`: `54` chunks ingeridos, `65` nós e `72` arestas gerados, com conclusão em ~`270s` para o documento de referência usado no teste.
- Guardrail adicionado no preview/build: backend agora expõe `ontology_guardrails`, bloqueia builds com erros de compatibilidade antes de chamar o Zep e mostra avisos/erros na UI antes da confirmação.
- Cleanup concluído: clones temporários removidos do storage local e grafos temporários apagados do Zep após os smokes.

---

# Investigação do 500 em /api/graph/ontology/generate

## Objetivo
Encontrar a causa raiz do erro `500 (INTERNAL SERVER ERROR)` no fluxo de geração de ontologia e corrigir apenas se a falha for do código do projeto.

## Plano
- [x] Mapear a rota `/api/graph/ontology/generate`, os serviços encadeados e os pontos de exceção possíveis.
- [x] Reproduzir a falha localmente com evidências do backend para identificar a camada exata da quebra.
- [x] Validar a hipótese de causa raiz comparando com fluxos/testes existentes.
- [x] Implementar correção mínima e teste de regressão se a falha estiver no código.
- [x] Rodar verificação final e registrar os resultados.

## Review
- Causa raiz identificada em `backend/app/utils/llm_client.py`: `chat_json()` removia apenas code fences e ainda exigia JSON puro; com `LLM_BASE_URL=https://api.minimax.io/v1` e `LLM_MODEL_NAME=MiniMax-M2.7`, o provedor retornou `<think>...</think>` antes do bloco JSON, quebrando `json.loads()` e causando `500`.
- Reproduzido localmente no endpoint `/api/graph/ontology/generate` com traceback real mostrando `ValueError: LLM返回的JSON格式无效` e resposta contendo `<think>` seguido de ```json`.
- Correção aplicada no próprio `LLMClient`: novo helper `_extract_json_payload()` remove `<think>`, extrai fenced JSON quando existir e faz fallback para o primeiro objeto `{...}` antes do parse.
- Regressão coberta em `backend/tests/utils/test_llm_client_observability.py` com caso explícito de `<think>...</think>` + fenced JSON.
- Verificação concluída:
  - `uv run python -m pytest tests/utils/test_llm_client_observability.py` → `8 passed`
- Reexecução real do fluxo via `Flask test_client` em `/api/graph/ontology/generate` → `status=200`, `entity_count=10`, `edge_count=8`

---

# Investigação Deep Research falhando no Step 1

## Objetivo
Encontrar causa raiz do fluxo de deep research que entra em `extracting`/`summarizing`, depois falha no frontend com `Research failed`.

## Plano
- [x] Mapear fluxo completo frontend (`Step1GraphBuild`/`MainView`) e backend (`/api/research`, `deep_research_agent`) com evidência do run real `res_0abf44cbe73a`.
- [x] Escrever teste(s) que reproduzam a falha antes de alterar código.
- [x] Corrigir causa raiz mínima no backend e ajustar frontend se houver comportamento enganoso.
- [x] Rodar verificação final e registrar impacto/causa no review.

## Review
- Causa raiz principal em `backend/app/api/research.py`: worker tratava último chunk de `graph.stream()` como estado final achatado, mas LangGraph entrega deltas aninhados por nó; `summary/claims/sources` se perdiam e o run era marcado como `failed` mesmo após chegar em `completed`.
- Segunda causa no backend em `backend/app/services/deep_research_agent.py`: `validate_artifact()` calculava fim de seção com índice relativo incorreto e marcava `Summary`/`Claims` como ausentes mesmo com markdown válido.
- Ajuste de UX no frontend: botão de deep research parou de disparar run com placeholder; agora só entra em modo research, e o start real continua usando query derivada do projeto.
- Ajuste de i18n/feedback: adicionada chave `step1.deepResearch` e simplificadas mensagens genéricas `progress.taskComplete`/`progress.taskFailed` para não mascarar erro real.
- Regressão coberta em `backend/tests/services/test_deep_research_api.py` com caso explícito de estado final aninhado do LangGraph.
- Verificação concluída:
  - `uv run pytest tests/services/test_deep_research_api.py -q` → `9 passed`
  - `npm run build` no frontend → `ok` (mantidos warnings existentes de chunk grande/import dinâmico)

---

# Carousel Slides Redesign Plan

## Objetivo
Redesenhar fluxo de criação de carrossel para usar proporção fixa `1350x1080`, dar mais liberdade de design para IA e introduzir aprovação progressiva: extração do conteúdo → definição da linha narrativa → confirmação do conteúdo de cada slide → geração do slide 1 em 3 estilos → confirmação → elaboração do deck completo. Avaliar integração com `huashu-design`.

## Plano
- [x] Revisar contexto do projeto, lessons, tarefas abertas e fluxo atual relevante.
- [x] Confirmar escopo de origem do conteúdo e ponto de entrada do novo fluxo com o usuário.
- [x] Propor 2-3 abordagens de arquitetura/UX para pipeline de carrossel com trade-offs.
- [ ] Validar design alvo com o usuário por seções.
- [ ] Escrever design doc em `docs/plans/` para fluxo aprovado.
- [ ] Derivar plano de implementação detalhado antes de codar.

## Review
- Em andamento.
