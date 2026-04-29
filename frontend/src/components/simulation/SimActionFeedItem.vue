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
            <svg v-if="action.platform === 'twitter'" aria-label="Twitter" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
            <svg v-else aria-label="Reddit" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>
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
          <svg class="icon-small filled" aria-hidden="true" viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
          <span class="like-label">Liked a post</span>
        </div>
        <div v-if="action.action_type === 'DO_NOTHING'" class="idle-info">
          <svg class="icon-small" aria-hidden="true" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
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
