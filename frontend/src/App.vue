<template>
  <div>
    <router-view />
    <AgentationWrapper />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import AgentationWrapper from './components/AgentationWrapper.vue'

const theme = ref(localStorage.getItem('futuria_theme') || 'light')

// Initialize profile on body
const initThemeAndProfile = () => {
  const savedProfile = localStorage.getItem('futuria_profile') || 'generico'
  document.body.setAttribute('data-profile', savedProfile)
  document.documentElement.setAttribute('data-theme', theme.value)
}

onMounted(() => {
  initThemeAndProfile()
})

watch(theme, (newTheme) => {
  document.documentElement.setAttribute('data-theme', newTheme)
  localStorage.setItem('futuria_theme', newTheme)
})

// Expose a helper for child components to toggle theme
const toggleTheme = () => {
  theme.value = theme.value === 'light' ? 'dark' : 'light'
}

// Make toggleTheme available globally for any component
window.__futuriaToggleTheme = toggleTheme
</script>

<style>
:root {
  --color-primary: #000000;
  --color-background: #f9f9f9;
  --color-surface-container-low: #f3f3f3;
  --color-on-background: #1b1b1b;
  --color-on-primary: #e2e2e2;
  --color-surface: #f9f9f9;
  --color-surface-container-highest: #e2e2e2;
  --color-outline: #777777;
  --color-error: #ba1a1a;
  --font-machine: 'Space Grotesk', monospace;
  --font-human: 'Work Sans', sans-serif;
  --profile-primary: #000000;
  --profile-accent: #444444;
  --profile-light: #f0f0f0;
  --color-success: #2e7d32;
  --color-warning: #ed6c02;
  --color-info: #0288d1;
}

/* Tema escuro base */
[data-theme="dark"] {
  --color-background: #0a0a0a;
  --color-surface: #1a1a1a;
  --color-surface-container-low: #141414;
  --color-surface-container-highest: #2a2a2a;
  --color-on-background: #e0e0e0;
  --color-on-primary: #1b1b1b;
  --color-outline: #555555;
  --profile-light: #1a1a1a;
}

/* Cores por perfil */
body[data-profile="marketing"] {
  --profile-primary: #0066FF;
  --profile-accent: #00CCFF;
  --profile-light: #e6f2ff;
}
body[data-profile="direito"] {
  --profile-primary: #8B4513;
  --profile-accent: #D2691E;
  --profile-light: #fdf5e6;
}
body[data-profile="economia"] {
  --profile-primary: #006400;
  --profile-accent: #228B22;
  --profile-light: #e6f5e6;
}
body[data-profile="saude"] {
  --profile-primary: #C41E3A;
  --profile-accent: #FF6B6B;
  --profile-light: #fff0f2;
}

/* Dark overrides per profile */
[data-theme="dark"] body[data-profile="marketing"] {
  --profile-light: #0a1a3a;
}
[data-theme="dark"] body[data-profile="direito"] {
  --profile-light: #2a1a0a;
}
[data-theme="dark"] body[data-profile="economia"] {
  --profile-light: #0a2a0a;
}
[data-theme="dark"] body[data-profile="saude"] {
  --profile-light: #2a0a0a;
}

/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: var(--font-human);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: var(--color-on-background);
  background-color: var(--color-background);
  min-height: 100vh;
}

h1, h2, h3, .headline, .label, .display {
  font-family: var(--font-machine);
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--color-surface-container-low);
}

::-webkit-scrollbar-thumb {
  background: var(--profile-primary);
}

::-webkit-scrollbar-thumb:hover {
  background: var(--profile-accent);
}

/* 全局按钮样式 */
button {
  font-family: var(--font-machine);
}

/* Progress bar theming */
.progress-bar {
  width: 100%;
  height: 4px;
  background: var(--color-surface-container-highest);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--profile-primary);
  transition: width 0.3s ease;
}

/* Status badges using profile colors */
.badge.success {
  background: rgba(46, 125, 50, 0.15);
  color: var(--color-success);
}

.badge.processing,
.badge.accent {
  background: var(--profile-primary);
  color: var(--color-on-primary);
}

.badge.pending {
  background: var(--color-surface-container-highest);
  color: var(--color-outline);
}

.badge.error {
  background: rgba(186, 26, 26, 0.15);
  color: var(--color-error);
}

/* Step card active state uses profile color */
.step-card.active {
  border: 2px solid var(--profile-primary);
  box-shadow: 4px 4px 0 var(--profile-primary);
  transform: translate(-2px, -2px);
}

/* Theme toggle button style */
.theme-toggle-btn {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: #fff;
  padding: 6px 10px;
  cursor: pointer;
  font-family: var(--font-machine);
  font-size: 0.8rem;
  border-radius: 0px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.theme-toggle-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.6);
}
</style>
