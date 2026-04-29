# Simulation Control Center — Design Document

**Date:** 2026-04-29  
**Status:** Approved  
**Scope:** Frontend-only (Vue 3 + Vite). No backend changes.

---

## 1. Overview

Transform the simulation run screen (Step 3) from a black-box "execute and wait" experience into a **Mission Control** dashboard that gives users real-time visibility into agent actions, round progress, and platform metrics while the simulation runs.

---

## 2. Goals

- Provide real-time visibility into simulation execution
- Display per-platform metrics (Twitter / Reddit)
- Show agent activity and chronological action feed
- Offer basic filtering (platform, action type, agent name)
- Maintain zero backend changes

---

## 3. Non-Goals

- Pause / resume / stop controls (backend already supports stop; UI controls preserved as-is)
- Agent interview or interaction (IPC commands out of scope)
- Simulation templates or replay
- Real-time graph updates beyond existing 30s refresh

---

## 4. Architecture

### 4.1 High-Level Structure

`SimulationRunView.vue` remains unchanged. All work happens inside `Step3Simulation.vue`.

```
SimulationRunView.vue (unchanged)
├── Left: GraphPanel (unchanged)
└── Right: Step3Simulation.vue (evolved)
    ├── Existing controls (Start / Stop)
    ├── SimMonitorTabs.vue (new)
    │   ├── SimOverviewTab.vue
    │   ├── SimAgentsTab.vue
    │   └── SimTimelineTab.vue
    └── SimActionFeedItem.vue (shared)
```

### 4.2 Data Contract

```ts
interface SimulationMonitorState {
  runnerStatus: 'idle' | 'running' | 'completed' | 'failed';
  currentRound: number;
  totalRounds: number;
  progressPercent: number;
  twitter: PlatformMetrics;
  reddit: PlatformMetrics;
  recentActions: AgentAction[];
  rounds: RoundSummary[];
}

interface PlatformMetrics {
  currentRound: number;
  actionsCount: number;
  simulatedHours: number;
  running: boolean;
  completed: boolean;
}

interface AgentAction {
  roundNum: number;
  timestamp: string;
  platform: 'twitter' | 'reddit';
  agentId: number;
  agentName: string;
  actionType: string;
  success: boolean;
}
```

### 4.3 Composable

`useSimulationMonitor(simulationId)` encapsulates polling logic:

- Polling interval: **3s** while `running`, **10s** when `completed/failed`
- Pauses when `document.visibilityState === 'hidden'`
- Exponential backoff on errors: 3s → 6s → 12s → max 30s
- Emits completion event to parent for header status sync

---

## 5. Components

### 5.1 SimMonitorTabs.vue

Tab container. Tabs: **Visão Geral** | **Agentes** | **Linha do Tempo**

- Active tab and filter state persisted to `sessionStorage` key `sim-monitor-{simulationId}`
- Uses Blueprint Noir v2 design tokens (CSS variables)

### 5.2 SimOverviewTab.vue

- Progress bar: `currentRound / totalRounds`
- Platform cards (2-column grid): Twitter vs Reddit metrics
- Mini stats: total actions, elapsed real time, ETA estimate
- Empty state: skeleton placeholders + "Aguardando início..."

### 5.3 SimAgentsTab.vue

- Filter bar: name search (debounced 300ms), platform toggle chips
- Agent list items: avatar (initial), name, platform badge, last action, timestamp
- Sort: by activity (default) or name A-Z
- Empty state: "Nenhum agente ativo ainda"

### 5.4 SimTimelineTab.vue

- Vertical timeline of `recentActions`
- Each item: relative timestamp, platform badge, agent name, action type, success icon
- Sticky filter bar: platform toggle, dynamic action-type chips (deduplicated from data), agent search
- Auto-scroll checkbox: "Seguir última ação" (auto-scrolls to bottom on update; disables on user scroll)
- Empty state: "As ações aparecerão aqui quando a simulação iniciar"

### 5.5 SimActionFeedItem.vue

Atomic component used by both Overview ("latest actions" mini-list) and Timeline.

---

## 6. Data Flow

1. `Step3Simulation.vue` mounts → `useSimulationMonitor` starts polling
2. Composable fetches `SimulationRunState` from existing backend endpoint
3. `state` passed as read-only prop to active tab
4. Tab computes filtered views locally (pure computed properties)
5. On `completed/failed`, composable emits `@update-status` to update global header
6. On unmount, polling stops

---

## 7. Error Handling & Empty States

| Runner Status | Overview Visual | Feed State |
|---------------|-----------------|------------|
| `idle` / `starting` | Skeleton pulse; "Iniciando motores..." | Timer icon empty state |
| `running` | Animated progress bar; live numbers | Real-time feed |
| `completed` | Green badge; 100% progress; "Ver Relatório" button | Complete feed; auto-scroll off |
| `failed` | Red badge; error card with message | Last actions + sticky error banner |
| `stopped` | Gray badge; summary of what ran | Feed up to stop point |

**Polling errors:**
- 3 consecutive failures → discreet top banner "Conexão instável. Tentando reconectar..."
- > 5 failures → stop polling; show retry button "Retomar monitoramento"
- Stale data remains visible while retrying (stale-while-revalidate)

---

## 8. Filters

All filters are frontend-only computed properties.

**Timeline filters:**
- Platforms: multi-select chips (`twitter`, `reddit`)
- Action types: dynamic chips from `unique(actionTypes)` in current data
- Agent name: case-insensitive substring search

**Agents filters:**
- Name search (debounced)
- Platform toggle
- Sort: activity count or name A-Z

---

## 9. Accessibility

- Tab navigation uses `role="tablist"`, `role="tab"`, `role="tabpanel"`
- Status banners use `role="status"` (info) or `role="alert"` (error)
- Color never sole indicator: icons + text always paired
- WCAG 2.1 AA contrast maintained via existing Blueprint Noir tokens

---

## 10. Testing

**Unit tests:**
- `useSimulationMonitor.test.ts`: polling lifecycle, visibility pause, backoff, completion event
- `SimTimelineTab.test.ts`: filter logic, dynamic chips, empty state
- `SimAgentsTab.test.ts`: search, sort, platform filter

**Component tests:**
- `Step3Simulation.test.ts`: tab switching, prop passing, status emission

**E2E (if Playwright exists):**
- Start simulation → Mission Control appears → actions populate → switch tabs → apply filters

**Mocks:**
- `tests/mocks/simulationState.ts` provides `mockRunningState`, `mockCompletedState`, `mockFailedState`

---

## 11. Dependencies

- No new NPM dependencies required
- Reuses existing: Vue 3, Vue Router, Vue I18n, Blueprint Noir CSS variables

---

## 12. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Large `recentActions` array causes render lag | Virtual scroll if > 200 items (deferred to Phase 2) |
| Polling overloads backend | 3s interval + visibility pause + backoff |
| Step3Simulation becomes too large | Decomposed into 5 sub-components under `components/simulation/` |

---

*Approved by: user*  
*Next step: Invoke writing-plans skill for implementation plan*
