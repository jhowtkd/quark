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
