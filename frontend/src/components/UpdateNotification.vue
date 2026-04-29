<template>
  <div v-if="showUpdate" class="update-notification" role="alert">
    <span class="update-text">Nova versão disponível</span>
    <button class="update-btn" type="button" @click="applyUpdate">Atualizar</button>
    <button class="dismiss-btn" type="button" @click="dismiss">Depois</button>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const showUpdate = ref(false)
let registration = null
let updateTimer = null

const checkForUpdates = async () => {
  if (!registration) return
  try {
    await registration.update()
  } catch (e) {
    // Silently fail
  }
}

const applyUpdate = () => {
  if (!registration?.waiting) {
    showUpdate.value = false
    return
  }
  registration.waiting.postMessage({ type: 'SKIP_WAITING' })
  showUpdate.value = false
  window.location.reload()
}

const dismiss = () => {
  showUpdate.value = false
}

const onUpdateFound = () => {
  const newWorker = registration.installing
  if (!newWorker) return

  newWorker.addEventListener('statechange', () => {
    if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
      showUpdate.value = true
    }
  })
}

onMounted(async () => {
  if (!('serviceWorker' in navigator)) return

  try {
    registration = await navigator.serviceWorker.ready
    registration.addEventListener('updatefound', onUpdateFound)

    // Check for updates every 30 minutes
    updateTimer = setInterval(checkForUpdates, 30 * 60 * 1000)

    // Also check immediately if there's already a waiting worker
    if (registration.waiting) {
      showUpdate.value = true
    }
  } catch (e) {
    // Silently fail
  }
})

onUnmounted(() => {
  if (registration) {
    registration.removeEventListener('updatefound', onUpdateFound)
  }
  if (updateTimer) {
    clearInterval(updateTimer)
  }
})
</script>

<style scoped>
.update-notification {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 10002;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-3);
  background: var(--color-surface-elevated);
  border-bottom: 1px solid var(--color-outline);
  box-shadow: var(--shadow-md);
}

.update-text {
  font-family: var(--font-human);
  font-size: var(--text-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-on-background);
}

.update-btn {
  font-family: var(--font-machine);
  font-size: var(--text-xs);
  font-weight: var(--font-weight-medium);
  padding: var(--space-1) var(--space-3);
  background: var(--color-primary);
  color: var(--color-on-primary);
  border: none;
  cursor: pointer;
}

.update-btn:hover {
  background: var(--color-primary-hover);
}

.dismiss-btn {
  font-family: var(--font-machine);
  font-size: var(--text-xs);
  padding: var(--space-1) var(--space-3);
  background: transparent;
  color: var(--color-muted);
  border: 1px solid var(--color-outline);
  cursor: pointer;
}

.dismiss-btn:hover {
  color: var(--color-on-background);
  border-color: var(--color-on-background);
}
</style>
