<template>
  <div :class="['progress-steps', `orientation-${orientation}`]">
    <div
      v-for="(step, index) in steps"
      :key="index"
      :class="['step-item', `status-${step.status}`]"
    >
      <div class="step-indicator">
        <Icon
          v-if="step.status === 'completed'"
          name="check"
          :size="14"
          class="step-icon"
        />
        <Icon
          v-else-if="step.status === 'error'"
          name="x"
          :size="14"
          class="step-icon"
        />
        <Icon
          v-else-if="step.status === 'active'"
          name="loader-2"
          :size="14"
          class="step-icon spin"
        />
        <span v-else class="step-dot" />
      </div>
      <div class="step-content">
        <span class="step-label">{{ step.label }}</span>
        <span v-if="step.status === 'active' && step.detail" class="step-detail">
          {{ step.detail }}
        </span>
      </div>
      <div
        v-if="index < steps.length - 1"
        :class="['step-connector', { completed: step.status === 'completed' }]"
      />
    </div>
  </div>
</template>

<script setup>
import Icon from './Icon.vue'

defineProps({
  steps: {
    type: Array,
    required: true,
    validator: (arr) => arr.every((s) => ['pending', 'active', 'completed', 'error'].includes(s.status)),
  },
  orientation: {
    type: String,
    default: 'horizontal',
    validator: (v) => ['horizontal', 'vertical'].includes(v),
  },
})
</script>

<style scoped>
.progress-steps {
  display: flex;
  gap: 0;
}

.orientation-horizontal {
  flex-direction: row;
  align-items: flex-start;
}

.orientation-vertical {
  flex-direction: column;
  gap: var(--space-2);
}

.step-item {
  display: flex;
  align-items: flex-start;
  position: relative;
  flex: 1;
}

.orientation-horizontal .step-item {
  align-items: flex-start;
}

.orientation-vertical .step-item {
  flex: none;
  gap: var(--space-3);
}

.step-indicator {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-circle);
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.status-pending .step-indicator {
  border: 2px solid var(--color-outline);
}

.status-active .step-indicator {
  background: var(--color-primary);
  color: var(--color-on-primary);
  box-shadow: 0 0 0 4px var(--color-overlay-subtle);
  animation: pulse-ring 2s infinite;
}

.status-completed .step-indicator {
  background: var(--color-success);
  color: var(--color-on-primary);
}

.status-error .step-indicator {
  background: var(--color-error);
  color: var(--color-on-primary);
}

.step-dot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-circle);
  background: var(--color-outline);
}

.step-content {
  display: flex;
  flex-direction: column;
  margin-left: var(--space-2);
  gap: 2px;
}

.orientation-vertical .step-content {
  margin-left: 0;
}

.step-label {
  font-family: var(--font-machine);
  font-size: var(--text-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-on-background);
  transition: color 0.3s ease;
}

.status-pending .step-label {
  color: var(--color-muted);
}

.step-detail {
  font-size: var(--text-xs);
  color: var(--color-muted);
}

.step-connector {
  flex: 1;
  height: 2px;
  background: var(--color-outline);
  margin: 0 var(--space-2);
  margin-top: 11px;
  transition: background 0.4s ease;
}

.step-connector.completed {
  background: var(--color-success);
}

.orientation-vertical .step-connector {
  display: none;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes pulse-ring {
  0%, 100% { box-shadow: 0 0 0 4px var(--color-overlay-subtle); }
  50% { box-shadow: 0 0 0 8px var(--color-overlay-subtle); }
}
</style>
