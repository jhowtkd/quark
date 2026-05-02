# 35-03 — Comparação entre Simulações — Summary

## What Was Built

### 1. Aba "Comparar" em Step5Interaction.vue
- Adicionado valor `'compare'` ao conjunto de abas do dashboard (`dashboardTab`).
- Adicionado botão de aba "Comparar" com ícone de balance/escala ao lado das abas existentes (`overview`, `chat`, `survey`, `explore`).
- Renderização condicional `v-if="dashboardTab === 'compare'"` contendo o componente `<SimulationCompare :baseSimulationId="props.simulationId" />`.
- Estilos `.compare-container` adicionados ao CSS scoped.

### 2. Componente SimulationCompare.vue
Criado em `frontend/src/components/SimulationCompare.vue` com:
- **Props**: `baseSimulationId` (String, required)
- **Estado reativo**: `history`, `lhsId`, `rhsId`, `lhsData`, `rhsData`, `loading`, `error`, `timelineExpanded`, `showAllCommon`
- **Métodos**:
  - `loadHistory()` → `getSimulationHistory(50)`, filtra `status === 'completed'`
  - `loadComparisonData(simulationId, target)` → chamadas paralelas a `getSimulation`, `getAgentStats`, `getSimulationTimeline`
  - `retry()`, `swapSides()`, `formatDate()`
- **Watchers** em `lhsId` e `rhsId` para recarregar dados automaticamente
- **Lifecycle**: `loadHistory()` e `loadComparisonData(lhsId, 'lhs')` no `onMounted`

### 3. Seletores de Simulação
- Barra `compare-selectors` com duas colunas (LHS/RHS) e botão de swap central.
- Dropdown LHS (`sim-select lhs-select`) pré-selecionado com `baseSimulationId`.
- Dropdown RHS (`sim-select rhs-select`) com placeholder vazio, filtrado para excluir a simulação selecionada no LHS.
- Mini-cards abaixo de cada dropdown mostrando projeto, data, status badge e total rounds.
- Histórico ordenado por `created_at` descendente.

### 4. Cards de Métricas
- Seção `compare-metrics` com grid de 2 colunas + indicadores de delta no meio.
- 6 métricas por coluna: agentes, rounds, ações, Twitter, Reddit, horas simuladas.
- Delta indicador (↑/↓/=) com cores verde/vermelho/cinza.
- Placeholder em RHS quando `rhsData` é null.

### 5. Distribuição Temporal
- Seção `compare-timeline` com gráfico de barras lado a lado puramente em CSS.
- Eixo X: rounds até `max(total_rounds_lhs, total_rounds_rhs)`.
- Eixo Y normalizado ao máximo entre ambas as simulações.
- Barras LHS em cor primária, RHS em laranja secundário.
- Legenda indicando cores.
- Limite de 100 rounds por padrão, toggle "Expandir todos / Recolher".
- Tooltip/title com contagem exata em cada barra.

### 6. Top Agentes
- Seção `compare-agents` com duas mini-tabelas lado a lado (top 5 por `total_actions`).
- Seção `common-agents`: tabela comparativa de agentes com mesmo `agent_name` em ambas as simulações, mostrando ações LHS/RHS e delta percentual.
- Seções "Agentes únicos LHS" e "Agentes únicos RHS" listando agentes exclusivos (limitado a 5).

### 7. Estados de Carregamento/Erro/Vazio
- Skeleton `skeleton-compare-panel` com cards pulsantes quando `loading`.
- Alerta `compare-error` com botão retry quando `error`.
- Estado vazio quando `history.length === 0`.
- Placeholder CTA em RHS quando `rhsId` vazio.

### 8. Internacionalização
- Adicionadas 20 chaves sob `step5.compare` em `locales/pt.json`.
- Adicionada chave `step5.dashboard.compareTab` para o label da aba.

### 9. Testes
- Criado `frontend/tests/components/SimulationCompare.spec.js` com 11 testes:
  1. `getSimulationHistory` chamado no mount
  2. Dropdowns populados com histórico
  3. Seleção RHS dispara carregamento de `rhsData`
  4. Cards de métricas renderizam valores LHS e RHS
  5. Delta entre simulações calculado e exibido
  6. Timeline usa dados de ambas as simulações
  7. Top agentes de ambas listados
  8. Agentes em comum identificados corretamente
  9. Estado vazio quando histórico vazio
  10. Placeholder quando RHS não selecionado
  11. Troca LHS/RHS via botão swap

## Verification Results
- ✅ `npm run test -- --run SimulationCompare` → 11/11 tests passed
- ✅ `npm run test -- --run` → 173/173 tests passed (no regressions)
- ✅ `npm run build` → build successful, no errors

## Files Modified/Created
- `frontend/src/components/Step5Interaction.vue` (modified)
- `frontend/src/components/SimulationCompare.vue` (created)
- `frontend/locales/pt.json` (modified)
- `frontend/tests/components/SimulationCompare.spec.js` (created)
