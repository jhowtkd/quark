# 35-01 — Step5 como Dashboard — Resumo de Implementação

## O que foi construído

Transformação do `Step5Interaction.vue` de um painel exclusivo de chat/survey para um **dashboard de inspeção analítica** com cards macro, timeline de atividade e ranking de agentes, mantendo o chat e survey acessíveis via abas secundárias.

## Arquivos alterados

### 1. `frontend/src/components/Step5Interaction.vue`
- **Dashboard tabs**: adicionada barra de navegação com 3 abas (`overview`, `chat`, `survey`) usando classe `dashboard-tab` e estado `dashboardTab`.
- **Cards macro**: grid de 6 cards (Agentes, Rounds, Ações, Posts, Likes, Quotes) com classes `macro-cards-grid`, `macro-card`, `macro-card-value`, `macro-card-label`. Dados carregados via `loadDashboardStats()` consumindo `getSimulation`, `getAgentStats`, `getSimulationActions`, `getSimulationPosts`.
- **Timeline**: barras horizontais empilhadas (Twitter = azul primário, Reddit = laranja #F97316) por round. Toggle "Por Round" / "Por Hora" via `timeline-toggle`. Suporte a "Carregar mais" (limite de 50 rounds).
- **Top agents**: tabela compacta `top-agents-table` com top 5 agentes por `total_actions`, incluindo ranking, nome, ações totais, Twitter, Reddit e tipo mais frequente.
- **Estados de carregamento/vazio**: skeleton cards (`skeleton-card`), skeleton bars, mensagem `noSimulation` quando `simulationId` é nulo, mensagem `noTimelineData` quando timeline vazia, badge quando `actions === 0`.
- **CSS**: todas as classes do dashboard adicionadas ao `<style scoped>` com grid responsivo (3/2/1 colunas), transições `0.2s ease`, cores do Blueprint Noir v2.

### 2. `locales/pt.json`
- Adicionadas 16 chaves sob `step5.dashboard`: `overviewTab`, `chatTab`, `surveyTab`, `agents`, `rounds`, `actions`, `posts`, `likes`, `quotes`, `noSimulation`, `noTimelineData`, `loadMore`, `byRound`, `byHour`, `topAgents`, `viewAll`.

### 3. `frontend/tests/components/Step5Interaction.spec.js` (novo)
- 5 testes cobrindo:
  1. Aba "Visão Geral" ativa por padrão ao montar com `simulationId`
  2. Clicar na aba "Chat" alterna para chat
  3. 6 macro cards renderizados quando `dashboardStats` populado
  4. `loadDashboardStats` chamado no `onMounted` quando `simulationId` existe
  5. Estado vazio exibido quando `simulationId` é null

## Compatibilidade preservada
- O painel esquerdo (relatório) permaneceu **intocado**.
- Chat e survey continuam funcionais nas abas secundárias.
- `activeTab` e `chatTarget` mantidos para compatibilidade interna do chat.
- Todos os eventos existentes (`selectReportAgentChat`, `selectSurveyTab`, `toggleAgentDropdown`, `selectAgent`) atualizam `dashboardTab` adequadamente.

## Verificação
- ✅ `npm run test -- Step5Interaction` — 5/5 passaram
- ✅ `npm run build` — build sem erros
