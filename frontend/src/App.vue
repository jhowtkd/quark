<template>
  <div>
    <router-view v-slot="{ Component }">
      <Transition name="page" mode="out-in">
        <component :is="Component" />
      </Transition>
    </router-view>
    <AgentationWrapper />
    <InstallPrompt />
    <NetworkIndicator />
    <UpdateNotification />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import AgentationWrapper from './components/AgentationWrapper.vue'
import InstallPrompt from './components/InstallPrompt.vue'
import NetworkIndicator from './components/NetworkIndicator.vue'
import UpdateNotification from './components/UpdateNotification.vue'
import { useTheme } from './composables/useTheme.js'

const { initTheme } = useTheme()

// Initialize profile on body
const initProfile = () => {
  const savedProfile = localStorage.getItem('futuria_profile') || 'generico'
  document.body.setAttribute('data-profile', savedProfile)
}

onMounted(() => {
  initTheme()
  initProfile()
})
</script>

<style>
:root {
  /* Brand / Action */
  --color-primary: #000000;
  --color-primary-hover: #333333;
  --color-primary-active: #1a1a1a;
  --color-secondary: #444444;
  --color-on-primary: #e2e2e2;

  /* Surfaces */
  --color-background: #f9f9f9;
  --color-surface: #ffffff;
  --color-surface-elevated: #ffffff;
  --color-surface-overlay: #ffffff;
  --color-surface-container-low: #f3f3f3;
  --color-surface-container-highest: #e2e2e2;

  /* Text */
  --color-on-background: #1b1b1b;
  --color-on-surface: #1b1b1b;
  --color-muted: #666666;
  --color-disabled: #999999;

  /* Outlines */
  --color-outline: #777777;
  --color-outline-strong: #444444;

  /* Feedback */
  --color-error: #ba1a1a;
  --color-error-bg: rgba(186, 26, 26, 0.12);
  --color-success: #2e7d32;
  --color-success-bg: rgba(46, 125, 50, 0.12);
  --color-warning: #ed6c02;
  --color-warning-bg: rgba(237, 108, 2, 0.12);
  --color-info: #0288d1;
  --color-info-bg: rgba(2, 136, 209, 0.12);

  /* Code */
  --color-code-bg: #f0f0f0;
  --color-code-text: #1b1b1b;

  /* Overlays */
  --color-overlay: rgba(0, 0, 0, 0.65);
  --color-overlay-light: rgba(255, 255, 255, 0.95);
  --color-overlay-subtle: rgba(0, 0, 0, 0.15);

  /* Links */
  --color-link: #000000;
  --color-link-hover: #444444;

  /* Shadows */
  --shadow-none: none;
  --shadow-brutalist: 4px 4px 0 var(--color-on-background);
  --shadow-soft: 0 2px 8px rgba(0, 0, 0, 0.08);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 24px rgba(0, 0, 0, 0.15);

  /* Radius */
  --radius-none: 0px;
  --radius-sm: 0px;
  --radius-md: 0px;
  --radius-lg: 0px;
  --radius-full: 999px;
  --radius-circle: 50%;

  /* Typography */
  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.25rem;
  --text-2xl: 1.5rem;
  --text-3xl: 2rem;
  --text-4xl: 2.5rem;
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-bold: 700;
  --line-height-tight: 1.25;
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.75;

  /* Spacing */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;

  /* Typography */
  --font-machine: 'Space Grotesk', monospace;
  --font-human: 'Work Sans', sans-serif;

  /* Profile colors (light defaults) */
  --profile-primary: #000000;
  --profile-accent: #444444;
  --profile-light: #f0f0f0;
}

/* Explicit light mode (same as :root, for specificity) */
[data-theme="light"] {
  --color-primary: #000000;
  --color-primary-hover: #333333;
  --color-primary-active: #1a1a1a;
  --color-secondary: #444444;
  --color-on-primary: #e2e2e2;
  --color-background: #f9f9f9;
  --color-surface: #ffffff;
  --color-surface-elevated: #ffffff;
  --color-surface-overlay: #ffffff;
  --color-surface-container-low: #f3f3f3;
  --color-surface-container-highest: #e2e2e2;
  --color-on-background: #1b1b1b;
  --color-on-surface: #1b1b1b;
  --color-muted: #666666;
  --color-disabled: #999999;
  --color-outline: #777777;
  --color-outline-strong: #444444;
  --color-error-bg: rgba(186, 26, 26, 0.12);
  --color-success-bg: rgba(46, 125, 50, 0.12);
  --color-warning-bg: rgba(237, 108, 2, 0.12);
  --color-info-bg: rgba(2, 136, 209, 0.12);
  --color-code-bg: #f0f0f0;
  --color-code-text: #1b1b1b;
  --color-overlay: rgba(0, 0, 0, 0.65);
  --color-overlay-light: rgba(255, 255, 255, 0.95);
  --color-overlay-subtle: rgba(0, 0, 0, 0.15);
  --color-link: #000000;
  --color-link-hover: #444444;
  --shadow-none: none;
  --shadow-brutalist: 4px 4px 0 var(--color-on-background);
  --shadow-soft: 0 2px 8px rgba(0, 0, 0, 0.08);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 24px rgba(0, 0, 0, 0.15);
}

/* Dark mode override */
[data-theme="dark"] {
  --color-primary: #e0e0e0;
  --color-primary-hover: #ffffff;
  --color-primary-active: #cccccc;
  --color-secondary: #aaaaaa;
  --color-on-primary: #1b1b1b;
  --color-background: #0a0a0a;
  --color-surface: #1a1a1a;
  --color-surface-elevated: #222222;
  --color-surface-overlay: #2a2a2a;
  --color-surface-container-low: #141414;
  --color-surface-container-highest: #2a2a2a;
  --color-on-background: #e0e0e0;
  --color-on-surface: #e0e0e0;
  --color-muted: #999999;
  --color-disabled: #555555;
  --color-outline: #555555;
  --color-outline-strong: #777777;
  --color-error-bg: rgba(255, 100, 100, 0.12);
  --color-success-bg: rgba(100, 255, 100, 0.12);
  --color-warning-bg: rgba(255, 200, 100, 0.12);
  --color-info-bg: rgba(100, 200, 255, 0.12);
  --color-code-bg: #1a1a1a;
  --color-code-text: #e0e0e0;
  --color-overlay: rgba(0, 0, 0, 0.75);
  --color-overlay-light: rgba(30, 30, 30, 0.98);
  --color-overlay-subtle: rgba(255, 255, 255, 0.1);
  --color-link: #e0e0e0;
  --color-link-hover: #ffffff;
  --shadow-soft: 0 2px 8px rgba(0, 0, 0, 0.4);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.5);
  --shadow-lg: 0 10px 24px rgba(0, 0, 0, 0.6);
  --profile-light: #1a1a1a;
}

/* Auto mode: respect OS preference when no data-theme is set */
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]):not([data-theme="dark"]) {
    --color-primary: #e0e0e0;
    --color-primary-hover: #ffffff;
    --color-primary-active: #cccccc;
    --color-secondary: #aaaaaa;
    --color-on-primary: #1b1b1b;
    --color-background: #0a0a0a;
    --color-surface: #1a1a1a;
    --color-surface-elevated: #222222;
    --color-surface-overlay: #2a2a2a;
    --color-surface-container-low: #141414;
    --color-surface-container-highest: #2a2a2a;
    --color-on-background: #e0e0e0;
    --color-on-surface: #e0e0e0;
    --color-muted: #999999;
    --color-disabled: #555555;
    --color-outline: #555555;
    --color-outline-strong: #777777;
    --color-error-bg: rgba(255, 100, 100, 0.12);
    --color-success-bg: rgba(100, 255, 100, 0.12);
    --color-warning-bg: rgba(255, 200, 100, 0.12);
    --color-info-bg: rgba(100, 200, 255, 0.12);
    --color-code-bg: #1a1a1a;
    --color-code-text: #e0e0e0;
    --color-overlay: rgba(0, 0, 0, 0.75);
    --color-overlay-light: rgba(30, 30, 30, 0.98);
    --color-overlay-subtle: rgba(255, 255, 255, 0.1);
    --color-link: #e0e0e0;
    --color-link-hover: #ffffff;
    --shadow-soft: 0 2px 8px rgba(0, 0, 0, 0.4);
    --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.5);
    --shadow-lg: 0 10px 24px rgba(0, 0, 0, 0.6);
    --profile-light: #1a1a1a;
  }
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

/* Auto-mode profile overrides */
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]):not([data-theme="dark"]) body[data-profile="marketing"] {
    --profile-light: #0a1a3a;
  }
  :root:not([data-theme="light"]):not([data-theme="dark"]) body[data-profile="direito"] {
    --profile-light: #2a1a0a;
  }
  :root:not([data-theme="light"]):not([data-theme="dark"]) body[data-profile="economia"] {
    --profile-light: #0a2a0a;
  }
  :root:not([data-theme="light"]):not([data-theme="dark"]) body[data-profile="saude"] {
    --profile-light: #2a0a0a;
  }
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
  background: var(--color-success-bg);
  color: var(--color-success);
}

.badge.processing,
.badge.accent {
  background: var(--profile-primary);
  color: var(--color-on-primary);
}

.badge.pending {
  background: var(--color-surface-container-highest);
  color: var(--color-muted);
}

.badge.error {
  background: var(--color-error-bg);
  color: var(--color-error);
}

/* Step card active state uses profile color */
.step-card.active {
  border: 2px solid var(--profile-primary);
  box-shadow: var(--shadow-brutalist);
  transform: translate(-2px, -2px);
}

/* Global focus styles */
:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

button:focus-visible,
a:focus-visible,
input:focus-visible,
select:focus-visible,
textarea:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* Route transitions */
.page-enter-active,
.page-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.page-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.page-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* Respect reduced motion preference */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* Link hover */
a {
  transition: color 0.15s ease;
}
</style>
