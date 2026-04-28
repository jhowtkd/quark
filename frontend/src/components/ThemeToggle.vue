<template>
  <button
    class="theme-toggle-btn"
    @click="toggleTheme"
    :title="title"
    :aria-label="title"
  >
    <span v-if="theme === 'light'">☾</span>
    <span v-else-if="theme === 'dark'">☀</span>
    <span v-else>A</span>
  </button>
</template>

<script setup>
import { computed } from 'vue'
import { useTheme } from '../composables/useTheme.js'

const { theme, toggleTheme, isDark } = useTheme()

const title = computed(() => {
  if (theme.value === 'light') return 'Modo escuro'
  if (theme.value === 'dark') return 'Modo claro'
  return 'Tema automático'
})
</script>

<style scoped>
.theme-toggle-btn {
  background: transparent;
  border: 1px solid var(--color-outline);
  color: var(--color-on-background);
  padding: 6px 10px;
  cursor: pointer;
  font-family: var(--font-machine);
  font-size: 0.8rem;
  border-radius: 0px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 32px;
  justify-content: center;
}

.theme-toggle-btn:hover {
  background: var(--color-surface-container-low);
  border-color: var(--color-on-background);
}
</style>
