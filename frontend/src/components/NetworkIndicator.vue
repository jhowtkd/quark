<template>
  <div v-if="!online" class="network-indicator" role="status" aria-live="polite">
    <span class="indicator-dot" aria-hidden="true"></span>
    <span class="indicator-text">Sem conexão</span>
  </div>
</template>

<script setup>
import { useNetworkStatus } from '../composables/useNetworkStatus.js'

const { online } = useNetworkStatus()
</script>

<style scoped>
.network-indicator {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 10001;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-2);
  background: var(--color-error);
  color: #ffffff;
  font-family: var(--font-machine);
  font-size: var(--text-xs);
  font-weight: var(--font-weight-medium);
}

.indicator-dot {
  width: 8px;
  height: 8px;
  background: #ffffff;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
</style>
