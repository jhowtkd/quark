<template>
  <div class="agents-tab">
    <!-- Filters -->
    <div class="filters-bar">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Search agent..."
        class="search-input"
        aria-label="Search agents"
      />
      <div class="platform-toggles">
        <button
          v-for="p in ['twitter', 'reddit']"
          :key="p"
          class="toggle-chip"
          :class="{ active: selectedPlatforms.includes(p) }"
          :aria-pressed="selectedPlatforms.includes(p)"
          @click="togglePlatform(p)"
        >
          {{ p === 'twitter' ? 'Plaza' : 'Community' }}
        </button>
      </div>
      <select v-model="sortBy" class="sort-select" aria-label="Sort by">
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
  flex: 1;
  overflow-y: auto;
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
