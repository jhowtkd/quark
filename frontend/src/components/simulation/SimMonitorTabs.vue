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
