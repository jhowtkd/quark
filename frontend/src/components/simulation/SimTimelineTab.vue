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
          :aria-pressed="selectedPlatforms.includes(p)"
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
          :aria-pressed="selectedTypes.includes(type)"
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
        aria-label="Filter by agent"
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
