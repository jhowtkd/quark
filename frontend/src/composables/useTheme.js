import { ref, computed, onMounted, onUnmounted } from 'vue'

const STORAGE_KEY = 'futuria_theme'
const VALID_MODES = ['light', 'dark', 'auto']

const theme = ref('light')
const mediaQuery = ref(null)

const effectiveTheme = computed(() => {
  if (theme.value === 'auto') {
    return mediaQuery.value?.matches ? 'dark' : 'light'
  }
  return theme.value
})

function applyTheme(mode) {
  const html = document.documentElement
  if (mode === 'auto') {
    html.removeAttribute('data-theme')
  } else {
    html.setAttribute('data-theme', mode)
  }
}

function setupMediaListener() {
  if (mediaQuery.value) {
    mediaQuery.value.removeEventListener('change', onMediaChange)
  }
  mediaQuery.value = window.matchMedia('(prefers-color-scheme: dark)')
  mediaQuery.value.addEventListener('change', onMediaChange)
}

function onMediaChange() {
  if (theme.value === 'auto') {
    // CSS @media handles the visual change, but components
    // listening to effectiveTheme will recompute
  }
}

function setTheme(mode) {
  if (!VALID_MODES.includes(mode)) return
  theme.value = mode
  localStorage.setItem(STORAGE_KEY, mode)
  applyTheme(mode)
  if (mode === 'auto') {
    setupMediaListener()
  }
}

function toggleTheme() {
  const cycle = { light: 'dark', dark: 'auto', auto: 'light' }
  setTheme(cycle[theme.value])
}

function initTheme() {
  const saved = localStorage.getItem(STORAGE_KEY)
  const mode = VALID_MODES.includes(saved) ? saved : 'light'
  theme.value = mode
  applyTheme(mode)
  if (mode === 'auto') {
    setupMediaListener()
  }
}

let initialized = false

export function useTheme() {
  if (!initialized) {
    initialized = true
    // Run init immediately if DOM is available, otherwise defer
    if (typeof document !== 'undefined') {
      initTheme()
    }
  }

  return {
    theme: computed(() => theme.value),
    effectiveTheme,
    isDark: computed(() => effectiveTheme.value === 'dark'),
    setTheme,
    toggleTheme,
    initTheme,
  }
}
