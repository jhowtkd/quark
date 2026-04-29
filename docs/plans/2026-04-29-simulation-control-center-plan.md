# Simulation Control Center — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reorganize the existing simulation monitor in `Step3Simulation.vue` into a tabbed Mission Control with Overview, Agents, and Timeline views, extracting reusable components and adding agent-level filtering.

**Architecture:** Keep `SimulationRunView.vue` and the graph panel untouched. Extract polling logic into `useSimulationMonitor.js`, decompose `Step3Simulation.vue` into 5 sub-components under `components/simulation/`, and introduce tab navigation. Zero backend changes.

**Tech Stack:** Vue 3, Vite, JavaScript (no TypeScript in this repo), CSS with Blueprint Noir v2 tokens.

---

## Prerequisite Reading

- Design doc: `docs/plans/2026-04-29-simulation-control-center-design.md`
- Existing simulation API: `frontend/src/api/simulation.js`
- Existing component to refactor: `frontend/src/components/Step3Simulation.vue`
- Backend run-status endpoint: `backend/app/api/simulation.py` lines 1712+

---

## Task 1: Install Vitest + @vue/test-utils

**Context:** The frontend has no test runner. We need one for TDD.

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/vitest.config.js`

**Step 1: Install dependencies**

```bash
cd /Users/jhonatan/Repos/Futuria/futuria-v2-refatorado/frontend
npm install -D vitest @vue/test-utils jsdom
```

Expected: packages install successfully.

**Step 2: Create vitest.config.js**

```javascript
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    globals: true,
  },
})
```

**Step 3: Add test script to package.json**

In `frontend/package.json`, add to `scripts`:
```json
"test": "vitest run",
"test:watch": "vitest"
```

**Step 4: Verify Vitest works**

```bash
cd frontend && npx vitest run --reporter=verbose
```

Expected: "No test files found" (exit 0). If it crashes with config error, fix plugin import.

**Step 5: Commit**

```bash
git add frontend/package.json frontend/vitest.config.js
git commit -m "test: add vitest and @vue/test-utils for frontend testing"
```

---

## Task 2: Create Simulation Data Mocks

**Files:**
- Create: `frontend/tests/mocks/simulationState.js`

**Step 1: Write the mock file**

```javascript
export const mockRunningState = {
  simulation_id: 'sim_test_001',
  runner_status: 'running',
  current_round: 5,
  total_rounds: 10,
  progress_percent: 50,
  simulated_hours: 2,
  total_simulation_hours: 72,
  twitter_current_round: 5,
  reddit_current_round: 4,
  twitter_simulated_hours: 2,
  reddit_simulated_hours: 1,
  twitter_running: true,
  reddit_running: true,
  twitter_completed: false,
  reddit_completed: false,
  twitter_actions_count: 12,
  reddit_actions_count: 8,
  total_actions_count: 20,
  started_at: '2026-04-29T10:00:00.000Z',
  updated_at: '2026-04-29T10:05:00.000Z',
  completed_at: null,
  error: null,
}

export const mockCompletedState = {
  ...mockRunningState,
  runner_status: 'completed',
  current_round: 10,
  progress_percent: 100,
  twitter_completed: true,
  reddit_completed: true,
  twitter_running: false,
  reddit_running: false,
  completed_at: '2026-04-29T11:00:00.000Z',
}

export const mockActions = [
  {
    round_num: 1,
    timestamp: '2026-04-29T10:01:00.000Z',
    platform: 'twitter',
    agent_id: 1,
    agent_name: 'Alice',
    action_type: 'CREATE_POST',
    action_args: { content: 'Hello world' },
    success: true,
  },
  {
    round_num: 1,
    timestamp: '2026-04-29T10:01:05.000Z',
    platform: 'reddit',
    agent_id: 2,
    agent_name: 'Bob',
    action_type: 'CREATE_COMMENT',
    action_args: { content: 'Nice post' },
    success: true,
  },
  {
    round_num: 2,
    timestamp: '2026-04-29T10:02:00.000Z',
    platform: 'twitter',
    agent_id: 3,
    agent_name: 'Charlie',
    action_type: 'LIKE_POST',
    action_args: {},
    success: true,
  },
]
```

**Step 2: Commit**

```bash
git add frontend/tests/mocks/simulationState.js
git commit -m "test: add simulation state mocks"
```

---

## Task 3: Extract useSimulationMonitor Composable

**Context:** `Step3Simulation.vue` currently has inline polling (`statusTimer`, `detailTimer`, `fetchRunStatus`, `fetchRunStatusDetail`). We extract this into a reusable composable with visibility-aware polling and error backoff.

**Files:**
- Create: `frontend/src/composables/useSimulationMonitor.js`
- Create: `frontend/tests/composables/useSimulationMonitor.test.js`

**Step 1: Write the failing test**

```javascript
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref, nextTick } from 'vue'
import { useSimulationMonitor } from '../../src/composables/useSimulationMonitor.js'

// Mock API
vi.mock('../../src/api/simulation.js', () => ({
  getRunStatus: vi.fn(),
  getRunStatusDetail: vi.fn(),
}))

import { getRunStatus, getRunStatusDetail } from '../../src/api/simulation.js'

describe('useSimulationMonitor', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should start polling on mount and stop on unmount', async () => {
    getRunStatus.mockResolvedValue({ success: true, data: { runner_status: 'running' } })
    getRunStatusDetail.mockResolvedValue({ success: true, data: { all_actions: [] } })

    const simulationId = ref('sim_001')
    const { state, isPolling } = useSimulationMonitor(simulationId)

    await nextTick()
    expect(isPolling.value).toBe(true)

    // Advance 3s
    vi.advanceTimersByTime(3000)
    await nextTick()
    expect(getRunStatus).toHaveBeenCalled()
  })
})
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npx vitest run tests/composables/useSimulationMonitor.test.js
```

Expected: FAIL — "useSimulationMonitor is not defined" or file not found.

**Step 3: Implement the composable**

```javascript
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { getRunStatus, getRunStatusDetail } from '../api/simulation.js'

const POLL_INTERVAL_RUNNING = 3000
const POLL_INTERVAL_IDLE = 10000
const MAX_BACKOFF_MS = 30000

export function useSimulationMonitor(simulationIdRef) {
  const state = ref(null)
  const actions = ref([])
  const isPolling = ref(false)
  const error = ref(null)
  const errorCount = ref(0)

  let statusTimer = null
  let detailTimer = null
  let actionIds = new Set()

  const getInterval = () => {
    if (state.value?.runner_status === 'running') {
      const backoff = Math.min(2 ** errorCount.value * 1000, MAX_BACKOFF_MS)
      return Math.max(POLL_INTERVAL_RUNNING, backoff)
    }
    return POLL_INTERVAL_IDLE
  }

  const fetchStatus = async () => {
    if (!simulationIdRef.value) return
    try {
      const res = await getRunStatus(simulationIdRef.value)
      if (res.success && res.data) {
        state.value = res.data
        error.value = null
        errorCount.value = 0
      }
    } catch (err) {
      error.value = err.message
      errorCount.value++
    }
  }

  const fetchDetail = async () => {
    if (!simulationIdRef.value) return
    try {
      const res = await getRunStatusDetail(simulationIdRef.value)
      if (res.success && res.data) {
        const serverActions = res.data.all_actions || []
        serverActions.forEach(action => {
          const id = action.id || `${action.timestamp}-${action.platform}-${action.agent_id}-${action.action_type}`
          if (!actionIds.has(id)) {
            actionIds.add(id)
            actions.value.push({ ...action, _uniqueId: id })
          }
        })
      }
    } catch (err) {
      // Silently fail detail fetch; status fetch handles errors
    }
  }

  const tick = async () => {
    if (document.hidden) return
    await fetchStatus()
    await fetchDetail()

    // Reschedule with dynamic interval
    if (isPolling.value) {
      clearTimeout(statusTimer)
      statusTimer = setTimeout(tick, getInterval())
    }
  }

  const startPolling = () => {
    if (isPolling.value) return
    isPolling.value = true
    errorCount.value = 0
    tick()
  }

  const stopPolling = () => {
    isPolling.value = false
    if (statusTimer) {
      clearTimeout(statusTimer)
      statusTimer = null
    }
  }

  const reset = () => {
    stopPolling()
    state.value = null
    actions.value = []
    actionIds = new Set()
    error.value = null
    errorCount.value = 0
  }

  onMounted(() => {
    if (simulationIdRef.value) startPolling()
  })

  onUnmounted(() => {
    stopPolling()
  })

  watch(simulationIdRef, (newId, oldId) => {
    if (newId !== oldId) {
      reset()
      if (newId) startPolling()
    }
  })

  // Pause when tab hidden
  const onVisibilityChange = () => {
    if (document.hidden) {
      // Don't stop, just let tick skip
    } else {
      // Immediate tick when visible again
      if (isPolling.value) tick()
    }
  }

  onMounted(() => {
    document.addEventListener('visibilitychange', onVisibilityChange)
  })

  onUnmounted(() => {
    document.removeEventListener('visibilitychange', onVisibilityChange)
  })

  return {
    state,
    actions,
    isPolling,
    error,
    startPolling,
    stopPolling,
    reset,
  }
}
```

**Step 4: Run tests**

```bash
cd frontend && npx vitest run tests/composables/useSimulationMonitor.test.js
```

Expected: PASS.

If FAIL due to timers, adjust test to handle setTimeout instead of setInterval.

**Step 5: Commit**

```bash
git add frontend/src/composables/useSimulationMonitor.js frontend/tests/composables/useSimulationMonitor.test.js
git commit -m "feat: add useSimulationMonitor composable with visibility-aware polling"
```

---

## Task 4: Create SimActionFeedItem.vue

**Context:** Extract the timeline item rendering from `Step3Simulation.vue` (lines ~137-262) into a reusable atomic component.

**Files:**
- Create: `frontend/src/components/simulation/SimActionFeedItem.vue`
- Create: `frontend/tests/components/simulation/SimActionFeedItem.test.js`

**Step 1: Write failing test**

```javascript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SimActionFeedItem from '../../../src/components/simulation/SimActionFeedItem.vue'

describe('SimActionFeedItem', () => {
  it('renders agent name and action type', () => {
    const wrapper = mount(SimActionFeedItem, {
      props: {
        action: {
          agent_name: 'Alice',
          action_type: 'CREATE_POST',
          platform: 'twitter',
          timestamp: '2026-04-29T10:01:00.000Z',
          round_num: 1,
          action_args: { content: 'Hello' },
          success: true,
        },
      },
    })
    expect(wrapper.text()).toContain('Alice')
    expect(wrapper.text()).toContain('POST')
  })
})
```

Run: `cd frontend && npx vitest run tests/components/simulation/SimActionFeedItem.test.js`
Expected: FAIL — component not found.

**Step 2: Implement component**

Copy the existing card rendering logic from `Step3Simulation.vue`, adapting props:

```vue
<template>
  <div class="timeline-item" :class="action.platform">
    <div class="timeline-marker">
      <div class="marker-dot"></div>
    </div>
    <div class="timeline-card">
      <div class="card-header">
        <div class="agent-info">
          <div class="avatar-placeholder">{{ (action.agent_name || 'A')[0] }}</div>
          <span class="agent-name">{{ action.agent_name }}</span>
        </div>
        <div class="header-meta">
          <div class="platform-indicator">
            <svg v-if="action.platform === 'twitter'" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
            <svg v-else viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>
          </div>
          <div class="action-badge" :class="getActionTypeClass(action.action_type)">
            {{ getActionTypeLabel(action.action_type) }}
          </div>
        </div>
      </div>
      <div class="card-body">
        <div v-if="action.action_type === 'CREATE_POST' && action.action_args?.content" class="content-text main-text">
          {{ action.action_args.content }}
        </div>
        <div v-if="action.action_type === 'CREATE_COMMENT' && action.action_args?.content" class="content-text">
          {{ action.action_args.content }}
        </div>
        <div v-if="action.action_type === 'LIKE_POST'" class="like-info">
          <svg class="icon-small filled" viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
          <span class="like-label">Liked a post</span>
        </div>
        <div v-if="action.action_type === 'DO_NOTHING'" class="idle-info">
          <svg class="icon-small" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
          <span class="idle-label">Action Skipped</span>
        </div>
        <div v-if="!['CREATE_POST','CREATE_COMMENT','LIKE_POST','DO_NOTHING'].includes(action.action_type) && action.action_args?.content" class="content-text">
          {{ action.action_args.content }}
        </div>
      </div>
      <div class="card-footer">
        <span class="time-tag">R{{ action.round_num }} • {{ formatTime(action.timestamp) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  action: { type: Object, required: true }
})

const getActionTypeLabel = (type) => {
  const labels = {
    'CREATE_POST': 'POST',
    'REPOST': 'REPOST',
    'LIKE_POST': 'LIKE',
    'CREATE_COMMENT': 'COMMENT',
    'LIKE_COMMENT': 'LIKE',
    'DO_NOTHING': 'IDLE',
    'FOLLOW': 'FOLLOW',
    'SEARCH_POSTS': 'SEARCH',
    'QUOTE_POST': 'QUOTE',
    'UPVOTE_POST': 'UPVOTE',
    'DOWNVOTE_POST': 'DOWNVOTE'
  }
  return labels[type] || type || 'UNKNOWN'
}

const getActionTypeClass = (type) => {
  const classes = {
    'CREATE_POST': 'badge-post',
    'REPOST': 'badge-action',
    'LIKE_POST': 'badge-action',
    'CREATE_COMMENT': 'badge-comment',
    'LIKE_COMMENT': 'badge-action',
    'QUOTE_POST': 'badge-post',
    'FOLLOW': 'badge-meta',
    'SEARCH_POSTS': 'badge-meta',
    'UPVOTE_POST': 'badge-action',
    'DOWNVOTE_POST': 'badge-action',
    'DO_NOTHING': 'badge-idle'
  }
  return classes[type] || 'badge-default'
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  try {
    return new Date(timestamp).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return ''
  }
}
</script>

<style scoped>
.timeline-item {
  display: flex;
  gap: 12px;
  padding: 8px 0;
}
.timeline-marker {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.marker-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--color-primary);
  margin-top: 6px;
}
.timeline-card {
  flex: 1;
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  padding: 12px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.agent-info {
  display: flex;
  align-items: center;
  gap: 8px;
}
.avatar-placeholder {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--color-primary-container);
  color: var(--color-on-primary-container);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
}
.agent-name {
  font-weight: 600;
  font-size: 13px;
}
.header-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}
.platform-indicator {
  color: var(--color-muted);
}
.action-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.badge-post { background: var(--color-primary-container); color: var(--color-on-primary-container); }
.badge-action { background: var(--color-secondary-container); color: var(--color-on-secondary-container); }
.badge-comment { background: var(--color-tertiary-container); color: var(--color-on-tertiary-container); }
.badge-meta { background: var(--color-surface-container-high); color: var(--color-on-surface-variant); }
.badge-idle { background: var(--color-surface-container); color: var(--color-disabled); }
.badge-default { background: var(--color-surface-container); color: var(--color-on-surface); }
.card-body {
  margin-bottom: 8px;
}
.content-text {
  font-size: 13px;
  line-height: 1.5;
  color: var(--color-on-background);
}
.like-info, .idle-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--color-muted);
}
.icon-small.filled {
  color: var(--color-error);
}
.card-footer {
  display: flex;
  justify-content: flex-end;
}
.time-tag {
  font-size: 11px;
  color: var(--color-disabled);
  font-family: 'JetBrains Mono', monospace;
}
</style>
```

**Step 3: Run tests**

```bash
cd frontend && npx vitest run tests/components/simulation/SimActionFeedItem.test.js
```

Expected: PASS.

**Step 4: Commit**

```bash
git add frontend/src/components/simulation/SimActionFeedItem.vue frontend/tests/components/simulation/SimActionFeedItem.test.js
git commit -m "feat: add SimActionFeedItem component"
```

---

## Task 5: Create SimOverviewTab.vue

**Context:** Show aggregated metrics: progress bar, platform cards, mini-stats.

**Files:**
- Create: `frontend/src/components/simulation/SimOverviewTab.vue`
- Create: `frontend/tests/components/simulation/SimOverviewTab.test.js`

**Step 1: Write failing test**

```javascript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SimOverviewTab from '../../../src/components/simulation/SimOverviewTab.vue'
import { mockRunningState } from '../../mocks/simulationState.js'

describe('SimOverviewTab', () => {
  it('renders progress percent', () => {
    const wrapper = mount(SimOverviewTab, {
      props: { state: mockRunningState, actions: [] },
    })
    expect(wrapper.text()).toContain('50%')
    expect(wrapper.text()).toContain('Plaza')
    expect(wrapper.text()).toContain('Community')
  })
})
```

Run and verify FAIL.

**Step 2: Implement component**

```vue
<template>
  <div class="overview-tab">
    <!-- Progress -->
    <div class="progress-section">
      <div class="progress-header">
        <span class="progress-label">Progress</span>
        <span class="progress-value">{{ state?.progress_percent || 0 }}%</span>
      </div>
      <div class="progress-bar-bg">
        <div class="progress-bar-fill" :style="{ width: (state?.progress_percent || 0) + '%' }"></div>
      </div>
      <div class="progress-meta">
        <span class="meta-item">Round {{ state?.current_round || 0 }} / {{ state?.total_rounds || '-' }}</span>
        <span class="meta-item">{{ totalActions }} actions</span>
      </div>
    </div>

    <!-- Platform Cards -->
    <div class="platform-cards">
      <div class="platform-card twitter" :class="{ active: state?.twitter_running, completed: state?.twitter_completed }">
        <div class="card-title">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
          <span>Info Plaza</span>
        </div>
        <div class="card-stats">
          <div class="stat"><span class="stat-label">Round</span><span class="stat-value">{{ state?.twitter_current_round || 0 }}</span></div>
          <div class="stat"><span class="stat-label">Time</span><span class="stat-value">{{ state?.twitter_simulated_hours || 0 }}h</span></div>
          <div class="stat"><span class="stat-label">Acts</span><span class="stat-value">{{ state?.twitter_actions_count || 0 }}</span></div>
        </div>
      </div>

      <div class="platform-card reddit" :class="{ active: state?.reddit_running, completed: state?.reddit_completed }">
        <div class="card-title">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>
          <span>Topic Community</span>
        </div>
        <div class="card-stats">
          <div class="stat"><span class="stat-label">Round</span><span class="stat-value">{{ state?.reddit_current_round || 0 }}</span></div>
          <div class="stat"><span class="stat-label">Time</span><span class="stat-value">{{ state?.reddit_simulated_hours || 0 }}h</span></div>
          <div class="stat"><span class="stat-label">Acts</span><span class="stat-value">{{ state?.reddit_actions_count || 0 }}</span></div>
        </div>
      </div>
    </div>

    <!-- Recent Actions Mini-Feed -->
    <div class="mini-feed" v-if="recentActions.length > 0">
      <div class="mini-feed-title">Recent Actions</div>
      <SimActionFeedItem
        v-for="action in recentActions"
        :key="action._uniqueId"
        :action="action"
      />
    </div>

    <!-- Empty State -->
    <div v-else class="empty-state">
      <div class="pulse-ring"></div>
      <span>Waiting for agent actions...</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import SimActionFeedItem from './SimActionFeedItem.vue'

const props = defineProps({
  state: { type: Object, default: () => ({}) },
  actions: { type: Array, default: () => [] },
})

const totalActions = computed(() => props.actions.length)

const recentActions = computed(() => {
  return props.actions.slice(-5).reverse()
})
</script>

<style scoped>
.overview-tab {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.progress-section {
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  padding: 12px;
}
.progress-header {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 8px;
}
.progress-bar-bg {
  height: 6px;
  background: var(--color-surface-container-highest);
  overflow: hidden;
}
.progress-bar-fill {
  height: 100%;
  background: var(--color-primary);
  transition: width 0.3s ease;
}
.progress-meta {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 11px;
  color: var(--color-muted);
  font-family: 'JetBrains Mono', monospace;
}
.platform-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.platform-card {
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  padding: 12px;
  opacity: 0.7;
}
.platform-card.active {
  opacity: 1;
  border-color: var(--color-primary);
}
.platform-card.completed {
  opacity: 1;
  border-color: var(--color-success);
}
.card-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 10px;
  color: var(--color-on-surface-variant);
}
.card-stats {
  display: flex;
  justify-content: space-between;
}
.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}
.stat-label {
  font-size: 9px;
  color: var(--color-disabled);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.stat-value {
  font-size: 14px;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
}
.mini-feed {
  margin-top: 8px;
}
.mini-feed-title {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--color-muted);
  margin-bottom: 8px;
}
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  gap: 12px;
  color: var(--color-muted);
  font-size: 13px;
}
.pulse-ring {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 2px solid var(--color-primary);
  animation: pulse 1.5s infinite;
}
@keyframes pulse {
  0% { transform: scale(0.8); opacity: 1; }
  100% { transform: scale(1.3); opacity: 0; }
}
</style>
```

**Step 3: Run tests**

```bash
cd frontend && npx vitest run tests/components/simulation/SimOverviewTab.test.js
```

Expected: PASS.

**Step 4: Commit**

```bash
git add frontend/src/components/simulation/SimOverviewTab.vue frontend/tests/components/simulation/SimOverviewTab.test.js
git commit -m "feat: add SimOverviewTab with progress and platform cards"
```

---

## Task 6: Create SimAgentsTab.vue

**Context:** List agents with filters and sorting. Derive agent list from actions array (no new API).

**Files:**
- Create: `frontend/src/components/simulation/SimAgentsTab.vue`
- Create: `frontend/tests/components/simulation/SimAgentsTab.test.js`

**Step 1: Write failing test**

```javascript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SimAgentsTab from '../../../src/components/simulation/SimAgentsTab.vue'
import { mockActions } from '../../mocks/simulationState.js'

describe('SimAgentsTab', () => {
  it('lists unique agents from actions', () => {
    const wrapper = mount(SimAgentsTab, {
      props: { actions: mockActions },
    })
    expect(wrapper.text()).toContain('Alice')
    expect(wrapper.text()).toContain('Bob')
    expect(wrapper.text()).toContain('Charlie')
  })

  it('filters by name', async () => {
    const wrapper = mount(SimAgentsTab, {
      props: { actions: mockActions },
    })
    const input = wrapper.find('input[type="text"]')
    await input.setValue('ali')
    expect(wrapper.text()).toContain('Alice')
    expect(wrapper.text()).not.toContain('Bob')
  })
})
```

Run and verify FAIL.

**Step 2: Implement component**

```vue
<template>
  <div class="agents-tab">
    <!-- Filters -->
    <div class="filters-bar">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Search agent..."
        class="search-input"
      />
      <div class="platform-toggles">
        <button
          v-for="p in ['twitter', 'reddit']"
          :key="p"
          class="toggle-chip"
          :class="{ active: selectedPlatforms.includes(p) }"
          @click="togglePlatform(p)"
        >
          {{ p === 'twitter' ? 'Plaza' : 'Community' }}
        </button>
      </div>
      <select v-model="sortBy" class="sort-select">
        <option value="activity">Most Active</option>
        <option value="name">Name A-Z</option>
      </select>
    </div>

    <!-- Agent List -->
    <div class="agent-list">
      <div v-for="agent in sortedAgents" :key="agent.agent_id" class="agent-row">
        <div class="agent-avatar">{{ (agent.agent_name || 'A')[0] }}</div>
        <div class="agent-info">
          <div class="agent-name">{{ agent.agent_name }}</div>
          <div class="agent-meta">
            <span class="platform-badge" :class="agent.platform">{{ agent.platform }}</span>
            <span class="action-count">{{ agent.action_count }} actions</span>
          </div>
        </div>
        <div class="agent-last-action">
          <span class="last-type">{{ getActionTypeLabel(agent.last_action_type) }}</span>
          <span class="last-time">{{ formatTime(agent.last_timestamp) }}</span>
        </div>
      </div>
    </div>

    <!-- Empty -->
    <div v-if="sortedAgents.length === 0" class="empty-state">
      <span v-if="searchQuery || selectedPlatforms.length < 2">No agents match filters</span>
      <button v-if="searchQuery || selectedPlatforms.length < 2" class="clear-btn" @click="clearFilters">Clear filters</button>
      <span v-else>No agents active yet</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  actions: { type: Array, default: () => [] },
})

const searchQuery = ref('')
const selectedPlatforms = ref(['twitter', 'reddit'])
const sortBy = ref('activity')

const togglePlatform = (p) => {
  if (selectedPlatforms.value.includes(p)) {
    selectedPlatforms.value = selectedPlatforms.value.filter(x => x !== p)
  } else {
    selectedPlatforms.value.push(p)
  }
}

const clearFilters = () => {
  searchQuery.value = ''
  selectedPlatforms.value = ['twitter', 'reddit']
}

const agentsMap = computed(() => {
  const map = new Map()
  props.actions.forEach(action => {
    const id = action.agent_id
    const existing = map.get(id)
    if (!existing) {
      map.set(id, {
        agent_id: id,
        agent_name: action.agent_name,
        platform: action.platform,
        action_count: 1,
        last_timestamp: action.timestamp,
        last_action_type: action.action_type,
      })
    } else {
      existing.action_count++
      if (action.timestamp > existing.last_timestamp) {
        existing.last_timestamp = action.timestamp
        existing.last_action_type = action.action_type
      }
    }
  })
  return Array.from(map.values())
})

const filteredAgents = computed(() => {
  return agentsMap.value.filter(agent => {
    const matchPlatform = selectedPlatforms.value.includes(agent.platform)
    const matchName = !searchQuery.value ||
      agent.agent_name.toLowerCase().includes(searchQuery.value.toLowerCase())
    return matchPlatform && matchName
  })
})

const sortedAgents = computed(() => {
  const list = [...filteredAgents.value]
  if (sortBy.value === 'name') {
    list.sort((a, b) => a.agent_name.localeCompare(b.agent_name))
  } else {
    list.sort((a, b) => b.action_count - a.action_count)
  }
  return list
})

const getActionTypeLabel = (type) => {
  const labels = {
    'CREATE_POST': 'POST',
    'REPOST': 'REPOST',
    'LIKE_POST': 'LIKE',
    'CREATE_COMMENT': 'COMMENT',
    'DO_NOTHING': 'IDLE',
    'FOLLOW': 'FOLLOW',
    'SEARCH_POSTS': 'SEARCH',
    'QUOTE_POST': 'QUOTE',
    'UPVOTE_POST': 'UPVOTE',
    'DOWNVOTE_POST': 'DOWNVOTE'
  }
  return labels[type] || type || 'UNKNOWN'
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  try {
    return new Date(timestamp).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' })
  } catch { return '' }
}
</script>

<style scoped>
.agents-tab {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.filters-bar {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}
.search-input {
  flex: 1;
  min-width: 120px;
  padding: 8px 12px;
  border: 1px solid var(--color-outline);
  background: var(--color-surface);
  color: var(--color-on-background);
  font-size: 13px;
}
.platform-toggles {
  display: flex;
  gap: 4px;
}
.toggle-chip {
  padding: 6px 10px;
  border: 1px solid var(--color-outline);
  background: var(--color-surface-container);
  color: var(--color-muted);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  cursor: pointer;
}
.toggle-chip.active {
  background: var(--color-primary-container);
  color: var(--color-on-primary-container);
  border-color: var(--color-primary);
}
.sort-select {
  padding: 6px 8px;
  border: 1px solid var(--color-outline);
  background: var(--color-surface);
  color: var(--color-on-background);
  font-size: 12px;
}
.agent-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.agent-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
}
.agent-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-primary-container);
  color: var(--color-on-primary-container);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}
.agent-info {
  flex: 1;
  min-width: 0;
}
.agent-name {
  font-weight: 600;
  font-size: 13px;
  margin-bottom: 2px;
}
.agent-meta {
  display: flex;
  gap: 8px;
  font-size: 11px;
  color: var(--color-muted);
}
.platform-badge {
  text-transform: uppercase;
  font-weight: 700;
  font-size: 9px;
  padding: 1px 4px;
}
.platform-badge.twitter {
  background: var(--color-primary-container);
  color: var(--color-on-primary-container);
}
.platform-badge.reddit {
  background: var(--color-secondary-container);
  color: var(--color-on-secondary-container);
}
.agent-last-action {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}
.last-type {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-on-surface-variant);
}
.last-time {
  font-size: 10px;
  color: var(--color-disabled);
  font-family: 'JetBrains Mono', monospace;
}
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px;
  gap: 8px;
  color: var(--color-muted);
  font-size: 13px;
}
.clear-btn {
  padding: 6px 12px;
  background: var(--color-primary);
  color: var(--color-on-primary);
  border: none;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}
</style>
```

**Step 3: Run tests**

```bash
cd frontend && npx vitest run tests/components/simulation/SimAgentsTab.test.js
```

Expected: PASS.

**Step 4: Commit**

```bash
git add frontend/src/components/simulation/SimAgentsTab.vue frontend/tests/components/simulation/SimAgentsTab.test.js
git commit -m "feat: add SimAgentsTab with filters and sorting"
```

---

## Task 7: Create SimTimelineTab.vue

**Context:** Move the existing timeline from `Step3Simulation.vue` into this tab, adding filters.

**Files:**
- Create: `frontend/src/components/simulation/SimTimelineTab.vue`
- Create: `frontend/tests/components/simulation/SimTimelineTab.test.js`

**Step 1: Write failing test**

```javascript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SimTimelineTab from '../../../src/components/simulation/SimTimelineTab.vue'
import { mockActions } from '../../mocks/simulationState.js'

describe('SimTimelineTab', () => {
  it('filters by platform', async () => {
    const wrapper = mount(SimTimelineTab, {
      props: { actions: mockActions },
    })
    const twitterChip = wrapper.findAll('.toggle-chip').find(c => c.text() === 'Plaza')
    await twitterChip.trigger('click')
    await twitterChip.trigger('click') // deselect
    // After deselecting twitter, only reddit should show
    expect(wrapper.text()).toContain('Bob')
    expect(wrapper.text()).not.toContain('Alice')
  })
})
```

Run and verify FAIL.

**Step 2: Implement component**

```vue
<template>
  <div class="timeline-tab">
    <!-- Sticky Filters -->
    <div class="timeline-filters">
      <div class="platform-toggles">
        <button
          v-for="p in ['twitter', 'reddit']"
          :key="p"
          class="toggle-chip"
          :class="{ active: selectedPlatforms.includes(p) }"
          @click="togglePlatform(p)"
        >
          {{ p === 'twitter' ? 'Plaza' : 'Community' }}
        </button>
      </div>
      <div class="action-type-chips">
        <button
          v-for="type in uniqueActionTypes"
          :key="type"
          class="type-chip"
          :class="{ active: selectedTypes.includes(type) }"
          @click="toggleType(type)"
        >
          {{ getActionTypeLabel(type) }}
        </button>
      </div>
      <input
        v-model="agentSearch"
        type="text"
        placeholder="Filter by agent..."
        class="search-input"
      />
      <label class="autoscroll-label">
        <input v-model="autoScroll" type="checkbox" />
        <span>Follow latest</span>
      </label>
    </div>

    <!-- Feed -->
    <div class="timeline-feed" ref="feedRef">
      <div class="timeline-axis"></div>
      <SimActionFeedItem
        v-for="action in filteredActions"
        :key="action._uniqueId"
        :action="action"
      />
    </div>

    <!-- Empty -->
    <div v-if="filteredActions.length === 0" class="empty-state">
      <span v-if="hasFilters">No actions match filters</span>
      <button v-if="hasFilters" class="clear-btn" @click="clearFilters">Clear filters</button>
      <span v-else>Actions will appear here when simulation starts</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import SimActionFeedItem from './SimActionFeedItem.vue'

const props = defineProps({
  actions: { type: Array, default: () => [] },
})

const selectedPlatforms = ref(['twitter', 'reddit'])
const selectedTypes = ref([])
const agentSearch = ref('')
const autoScroll = ref(true)
const feedRef = ref(null)

const togglePlatform = (p) => {
  if (selectedPlatforms.value.includes(p)) {
    selectedPlatforms.value = selectedPlatforms.value.filter(x => x !== p)
  } else {
    selectedPlatforms.value.push(p)
  }
}

const toggleType = (t) => {
  if (selectedTypes.value.includes(t)) {
    selectedTypes.value = selectedTypes.value.filter(x => x !== t)
  } else {
    selectedTypes.value.push(t)
  }
}

const clearFilters = () => {
  selectedPlatforms.value = ['twitter', 'reddit']
  selectedTypes.value = []
  agentSearch.value = ''
}

const uniqueActionTypes = computed(() => {
  const types = new Set(props.actions.map(a => a.action_type))
  return Array.from(types)
})

const filteredActions = computed(() => {
  return props.actions.filter(action => {
    const matchPlatform = selectedPlatforms.value.includes(action.platform)
    const matchType = selectedTypes.value.length === 0 || selectedTypes.value.includes(action.action_type)
    const matchAgent = !agentSearch.value ||
      (action.agent_name || '').toLowerCase().includes(agentSearch.value.toLowerCase())
    return matchPlatform && matchType && matchAgent
  })
})

const hasFilters = computed(() =>
  selectedPlatforms.value.length < 2 ||
  selectedTypes.value.length > 0 ||
  !!agentSearch.value
)

const getActionTypeLabel = (type) => {
  const labels = {
    'CREATE_POST': 'POST',
    'REPOST': 'REPOST',
    'LIKE_POST': 'LIKE',
    'CREATE_COMMENT': 'COMMENT',
    'LIKE_COMMENT': 'LIKE',
    'DO_NOTHING': 'IDLE',
    'FOLLOW': 'FOLLOW',
    'SEARCH_POSTS': 'SEARCH',
    'QUOTE_POST': 'QUOTE',
    'UPVOTE_POST': 'UPVOTE',
    'DOWNVOTE_POST': 'DOWNVOTE'
  }
  return labels[type] || type || 'UNKNOWN'
}

// Auto-scroll
watch(() => props.actions.length, async () => {
  if (autoScroll.value && feedRef.value) {
    await nextTick()
    feedRef.value.scrollTop = feedRef.value.scrollHeight
  }
})
</script>

<style scoped>
.timeline-tab {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.timeline-filters {
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-outline);
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  background: var(--color-surface);
  position: sticky;
  top: 0;
  z-index: 10;
}
.platform-toggles {
  display: flex;
  gap: 4px;
}
.toggle-chip {
  padding: 4px 8px;
  border: 1px solid var(--color-outline);
  background: var(--color-surface-container);
  color: var(--color-muted);
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  cursor: pointer;
}
.toggle-chip.active {
  background: var(--color-primary-container);
  color: var(--color-on-primary-container);
  border-color: var(--color-primary);
}
.action-type-chips {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}
.type-chip {
  padding: 4px 8px;
  border: 1px solid var(--color-outline);
  background: var(--color-surface-container-low);
  color: var(--color-on-surface-variant);
  font-size: 10px;
  font-weight: 600;
  cursor: pointer;
}
.type-chip.active {
  background: var(--color-secondary-container);
  color: var(--color-on-secondary-container);
  border-color: var(--color-secondary);
}
.search-input {
  flex: 1;
  min-width: 100px;
  padding: 6px 10px;
  border: 1px solid var(--color-outline);
  background: var(--color-surface);
  color: var(--color-on-background);
  font-size: 12px;
}
.autoscroll-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--color-muted);
  cursor: pointer;
}
.timeline-feed {
  flex: 1;
  overflow-y: auto;
  padding: 8px 16px 16px;
}
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px;
  gap: 8px;
  color: var(--color-muted);
  font-size: 13px;
}
.clear-btn {
  padding: 6px 12px;
  background: var(--color-primary);
  color: var(--color-on-primary);
  border: none;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}
</style>
```

**Step 3: Run tests**

```bash
cd frontend && npx vitest run tests/components/simulation/SimTimelineTab.test.js
```

Expected: PASS.

**Step 4: Commit**

```bash
git add frontend/src/components/simulation/SimTimelineTab.vue frontend/tests/components/simulation/SimTimelineTab.test.js
git commit -m "feat: add SimTimelineTab with platform, type, and agent filters"
```

---

## Task 8: Create SimMonitorTabs.vue Container

**Context:** Thin container that holds the tab nav and renders the active tab.

**Files:**
- Create: `frontend/src/components/simulation/SimMonitorTabs.vue`
- Create: `frontend/tests/components/simulation/SimMonitorTabs.test.js`

**Step 1: Write failing test**

```javascript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SimMonitorTabs from '../../../src/components/simulation/SimMonitorTabs.vue'
import { mockRunningState, mockActions } from '../../mocks/simulationState.js'

describe('SimMonitorTabs', () => {
  it('switches tabs', async () => {
    const wrapper = mount(SimMonitorTabs, {
      props: { state: mockRunningState, actions: mockActions },
    })
    const tabs = wrapper.findAll('[role="tab"]')
    expect(tabs.length).toBe(3)
    await tabs[1].trigger('click')
    expect(wrapper.find('.agents-tab').exists()).toBe(true)
  })
})
```

Run and verify FAIL.

**Step 2: Implement component**

```vue
<template>
  <div class="monitor-tabs">
    <div class="tab-list" role="tablist">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        role="tab"
        :aria-selected="activeTab === tab.id"
        :class="['tab-btn', { active: activeTab === tab.id }]"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
      </button>
    </div>
    <div class="tab-panel" role="tabpanel">
      <SimOverviewTab v-if="activeTab === 'overview'" :state="state" :actions="actions" />
      <SimAgentsTab v-else-if="activeTab === 'agents'" :actions="actions" />
      <SimTimelineTab v-else-if="activeTab === 'timeline'" :actions="actions" />
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import SimOverviewTab from './SimOverviewTab.vue'
import SimAgentsTab from './SimAgentsTab.vue'
import SimTimelineTab from './SimTimelineTab.vue'

const props = defineProps({
  state: { type: Object, default: () => ({}) },
  actions: { type: Array, default: () => [] },
})

const tabs = [
  { id: 'overview', label: 'Visão Geral' },
  { id: 'agents', label: 'Agentes' },
  { id: 'timeline', label: 'Linha do Tempo' },
]

const STORAGE_KEY = `sim-monitor-tab-${props.state?.simulation_id || 'default'}`
const savedTab = typeof sessionStorage !== 'undefined' ? sessionStorage.getItem(STORAGE_KEY) : null
const activeTab = ref(tabs.find(t => t.id === savedTab) ? savedTab : 'overview')

watch(activeTab, (val) => {
  if (typeof sessionStorage !== 'undefined') {
    sessionStorage.setItem(STORAGE_KEY, val)
  }
})
</script>

<style scoped>
.monitor-tabs {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}
.tab-list {
  display: flex;
  border-bottom: 1px solid var(--color-outline);
  background: var(--color-surface);
}
.tab-btn {
  flex: 1;
  padding: 10px 8px;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--color-muted);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.tab-btn.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}
.tab-panel {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>
```

**Step 3: Run tests**

```bash
cd frontend && npx vitest run tests/components/simulation/SimMonitorTabs.test.js
```

Expected: PASS.

**Step 4: Commit**

```bash
git add frontend/src/components/simulation/SimMonitorTabs.vue frontend/tests/components/simulation/SimMonitorTabs.test.js
git commit -m "feat: add SimMonitorTabs container with tab persistence"
```

---

## Task 9: Refactor Step3Simulation.vue to Use Tabs

**Context:** Replace the existing inline timeline and polling logic with the composable and `SimMonitorTabs`. Keep controls, logs, and status behavior intact.

**Files:**
- Modify: `frontend/src/components/Step3Simulation.vue`

**Step 1: Before touching code, backup behavior**

The existing component:
- Calls `startSimulation`, `stopSimulation`, `generateReport`
- Polls status every 2s and detail every 3s
- Maintains `phase`, `isStarting`, `isStopping`, `isGeneratingReport`
- Emits `@go-back`, `@next-step`, `@add-log`, `@update-status`
- Shows platform status cards, timeline, and system logs

We replace only the data-fetching and display middle section. Controls and log emission stay.

**Step 2: Apply the refactor**

Replace the `<script setup>` block (keep props, emits, control methods) and the template middle section.

Key changes in script:
- Remove `runStatus`, `allActions`, `actionIds`, `statusTimer`, `detailTimer`, `prevTwitterRound`, `prevRedditRound`
- Remove `fetchRunStatus`, `fetchRunStatusDetail`, `startStatusPolling`, `startDetailPolling`, `stopPolling`, `checkPlatformsCompleted`
- Remove `chronologicalActions`, `twitterActionsCount`, `redditActionsCount`
- Import `useSimulationMonitor` and `SimMonitorTabs`
- Use `const { state, actions, isPolling, error, startPolling, stopPolling, reset } = useSimulationMonitor(toRef(props, 'simulationId'))`
- In `doStartSimulation`, after success call `reset()` then `startPolling()`
- In `handleStopSimulation`, call `stopPolling()` and `emit('update-status', 'completed')`
- Watch `state` for completion: when `state.value?.runner_status === 'completed'`, set `phase.value = 2`, `stopPolling()`, `emit('update-status', 'completed')`
- Remove `formatElapsedTime`, `twitterElapsedTime`, `redditElapsedTime` from template (moved to Overview tab)
- Keep `handleNextStep` (report generation) exactly as-is
- Keep `systemLogs` rendering at bottom exactly as-is

Template changes:
- Keep top control bar with platform status (simplified) and action buttons
- Replace the entire `.main-content-area` (timeline) with `<SimMonitorTabs :state="state" :actions="actions" />`
- Keep `.system-logs` at bottom

Because this is a large refactor, the exact diff is too long for this plan. The implementer should:

1. Comment out (don't delete yet) the old polling code and timeline template
2. Add imports and composable
3. Add `<SimMonitorTabs />` in place of timeline
4. Wire `startPolling` into `doStartSimulation`
5. Wire `stopPolling` into `handleStopSimulation`
6. Test that simulation starts, tabs appear, and actions populate
7. Only then delete commented code

**Step 3: Manual verification**

```bash
cd /Users/jhonatan/Repos/Futuria/futuria-v2-refatorado
npm run dev
```

In browser:
1. Open `http://localhost:4000`
2. Navigate to a simulation
3. Click Start
4. Verify:
   - "Visão Geral" tab shows progress and platform cards
   - "Agentes" tab lists agents after actions arrive
   - "Linha do Tempo" tab shows actions with filters working
   - System logs still appear at bottom
   - Stop button still works

**Step 4: Run existing build**

```bash
cd frontend && npm run build
```

Expected: Build succeeds with zero errors.

**Step 5: Commit**

```bash
git add frontend/src/components/Step3Simulation.vue
git commit -m "feat: integrate SimMonitorTabs into Step3Simulation"
```

---

## Task 10: Add Error Banner to Step3Simulation

**Context:** The composable exposes `error` and `isPolling`. Surface these in the UI.

**Files:**
- Modify: `frontend/src/components/Step3Simulation.vue`

**Step 1: Add banner markup**

Inside the template, above `SimMonitorTabs`, add:

```vue
<div v-if="error" class="monitor-error-banner" role="alert">
  <span>Connection unstable. {{ error }}</span>
  <button v-if="!isPolling" @click="startPolling" class="retry-btn">Retry</button>
</div>
<div v-else-if="isPolling && !state" class="monitor-loading-banner" role="status">
  <span>Connecting to simulation...</span>
</div>
```

**Step 2: Add scoped styles**

```css
.monitor-error-banner {
  padding: 10px 16px;
  background: var(--color-error-container);
  color: var(--color-on-error-container);
  font-size: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.retry-btn {
  padding: 4px 10px;
  background: var(--color-error);
  color: var(--color-on-error);
  border: none;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
}
.monitor-loading-banner {
  padding: 10px 16px;
  background: var(--color-surface-container-high);
  color: var(--color-muted);
  font-size: 12px;
}
```

**Step 3: Verify and commit**

```bash
cd frontend && npm run build
```

```bash
git add frontend/src/components/Step3Simulation.vue
git commit -m "feat: add monitor error and loading banners"
```

---

## Task 11: Run Full Test Suite

**Step 1: Run all new tests**

```bash
cd frontend && npx vitest run --reporter=verbose
```

Expected: All tests pass.

**Step 2: Run build**

```bash
cd frontend && npm run build
```

Expected: Zero errors.

**Step 3: Commit**

```bash
git commit --allow-empty -m "test: verify full test suite and build"
```

---

## Completion Checklist

- [ ] `useSimulationMonitor.js` extracted with tests
- [ ] `SimActionFeedItem.vue` extracted with tests
- [ ] `SimOverviewTab.vue` created with tests
- [ ] `SimAgentsTab.vue` created with tests
- [ ] `SimTimelineTab.vue` created with tests
- [ ] `SimMonitorTabs.vue` container created with tests
- [ ] `Step3Simulation.vue` refactored to use composable + tabs
- [ ] Error/loading banners added
- [ ] Build passes
- [ ] Manual browser test passes

---

**Plan saved to:** `docs/plans/2026-04-29-simulation-control-center-plan.md`

**Two execution options:**

**1. Subagent-Driven (this session)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Parallel Session (separate)** — Open a new session with executing-plans, batch execution with checkpoints.

Which approach do you prefer?
