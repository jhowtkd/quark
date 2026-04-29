<template>
  <div v-if="showPrompt" class="install-prompt">
    <div class="install-content">
      <span class="install-text">Instalar FUTUR.IA no seu dispositivo</span>
      <div class="install-actions">
        <button class="install-btn" type="button" @click="install">Instalar</button>
        <button class="dismiss-btn" type="button" @click="dismiss">Fechar</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const showPrompt = ref(false)
let deferredPrompt = null

const onBeforeInstallPrompt = (e) => {
  e.preventDefault()
  deferredPrompt = e
  showPrompt.value = true
}

const install = async () => {
  if (!deferredPrompt) return
  deferredPrompt.prompt()
  const { outcome } = await deferredPrompt.userChoice
  if (outcome === 'accepted') {
    showPrompt.value = false
  }
  deferredPrompt = null
}

const dismiss = () => {
  showPrompt.value = false
  deferredPrompt = null
}

onMounted(() => {
  window.addEventListener('beforeinstallprompt', onBeforeInstallPrompt)
})

onUnmounted(() => {
  window.removeEventListener('beforeinstallprompt', onBeforeInstallPrompt)
})
</script>

<style scoped>
.install-prompt {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10000;
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-outline);
  box-shadow: var(--shadow-lg);
  padding: var(--space-4);
  max-width: 400px;
  width: calc(100% - 48px);
}

.install-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.install-text {
  font-family: var(--font-human);
  font-size: var(--text-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-on-background);
}

.install-actions {
  display: flex;
  gap: var(--space-2);
}

.install-btn {
  font-family: var(--font-machine);
  font-size: var(--text-sm);
  font-weight: var(--font-weight-medium);
  padding: var(--space-2) var(--space-4);
  background: var(--color-primary);
  color: var(--color-on-primary);
  border: none;
  cursor: pointer;
}

.install-btn:hover {
  background: var(--color-primary-hover);
}

.dismiss-btn {
  font-family: var(--font-machine);
  font-size: var(--text-sm);
  padding: var(--space-2) var(--space-4);
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
