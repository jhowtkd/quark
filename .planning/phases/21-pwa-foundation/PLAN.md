# Plan: Phase 21 — PWA Foundation

**Phase:** 21  
**Goal:** The app is installable and works offline for static assets.  
**Requirements:** PWA-01, PWA-02, PWA-03, PWA-04  
**Defined:** 2026-04-28  
**Depends on:** Phase 20 (completed)

---

## Context

The frontend is a Vue 3 + Vite SPA. Currently:
- No Web App Manifest
- No service worker
- No offline support
- Not installable

This phase adds PWA capabilities using Vite PWA plugin (vite-plugin-pwa) which integrates Workbox automatically.

---

## Architecture Decisions

1. **Use vite-plugin-pwa**: Handles manifest generation, service worker creation, and Workbox integration with minimal config.
2. **Offline strategy**: Cache-first for static assets (JS, CSS, fonts), network-first for API calls.
3. **Fallback page**: Show a simple offline page when the user has no connectivity and assets are not cached.
4. **Install prompt**: Use the `beforeinstallprompt` event to show a custom install button.

---

## Plan Steps

### Step 1 — Install and configure vite-plugin-pwa (PWA-01, PWA-02)
**Files:** `vite.config.js`, `index.html`

1. Install `vite-plugin-pwa`
2. Add plugin to vite.config.js with manifest configuration
3. Add manifest link to index.html
4. Configure Workbox for cache-first static assets

### Step 2 — Create offline fallback page (PWA-04)
**File:** `public/offline.html`

Create a simple HTML page shown when the app is offline:
- Brand logo/name
- "You are offline" message
- "Retry" button to reload

### Step 3 — Add install prompt (PWA-03)
**File:** `App.vue` or new `InstallPrompt.vue`

1. Listen for `beforeinstallprompt` event
2. Store the prompt event
3. Show a custom install button in the UI (e.g., in Home.vue or App.vue header)
4. Call `prompt()` when user clicks install

### Step 4 — Verify PWA compliance
**Command:** Build and check

1. Run `npm run build`
2. Verify manifest.json is generated
3. Verify service worker is registered
4. Check with Lighthouse PWA audit (if possible)

---

## Verification

### Tests

1. Build succeeds and generates manifest + service worker
2. App is installable on Chrome/Edge (shows install icon in address bar)
3. Offline: disconnect network, reload page — shows offline fallback or cached app
4. Static assets are served from cache when offline

### Checklist

- [x] PWA-01: Valid Web App Manifest with name, icons, theme colors, display mode
- [x] PWA-02: Service worker caches static assets for offline access
- [x] PWA-03: Install prompt appears on supported browsers
- [x] PWA-04: Offline fallback page shown when API is unreachable

---

## Effort Estimate

| Step | Estimated Time |
|------|---------------|
| Step 1: vite-plugin-pwa setup | 1h |
| Step 2: Offline fallback page | 30min |
| Step 3: Install prompt | 1h |
| Step 4: Verify compliance | 30min |
| **Total** | **~3h** |

---

## Implementation Notes

**Completed:** 2026-04-29

### What was implemented

1. **vite-plugin-pwa configured** in `vite.config.js` with:
   - Manifest: name, short_name, icons (192x192, 512x512), theme/background colors, standalone display
   - Workbox: cache-first for static assets, runtime caching for Google Fonts
   - navigateFallback: `/offline.html` with denylist for `/api` and `/auth`
   - autoUpdate registration type

2. **Offline fallback page** (`public/offline.html`):
   - Brutalist design matching Blueprint Noir v2
   - "You are offline" message with retry and go home buttons
   - Respects `prefers-color-scheme` (light/dark)
   - No external dependencies (self-contained)

3. **Install prompt** (`src/components/InstallPrompt.vue`):
   - Listens for `beforeinstallprompt` event
   - Shows floating prompt at bottom of screen
   - "Instalar" and "Fechar" buttons
   - Integrated into `App.vue`

4. **Network status indicator** (`src/components/NetworkIndicator.vue` + `useNetworkStatus.js`):
   - Fixed bar at top when offline
   - Pulsing dot animation
   - `aria-live="polite"` for accessibility
   - Integrated into `App.vue`

5. **Update notification** (`src/components/UpdateNotification.vue`):
   - Listens for service worker updates
   - Shows notification when new version is available
   - "Atualizar" and "Depois" buttons
   - Checks for updates every 30 minutes
   - Integrated into `App.vue`

6. **Icons generated** (`public/icon-192x192.png`, `public/icon-512x512.png`):
   - Simple "F" lettermark on dark background
   - Matching Blueprint Noir aesthetic

### Files changed
- `vite.config.js` — Added VitePWA plugin configuration
- `public/manifest.json` — Created (redundant with auto-generated, kept as fallback)
- `public/offline.html` — Created
- `public/icon-192x192.png` — Created
- `public/icon-512x512.png` — Created
- `src/main.js` — Removed manual SW registration (plugin handles it)
- `src/App.vue` — Added InstallPrompt, NetworkIndicator, UpdateNotification
- `src/components/InstallPrompt.vue` — Created
- `src/components/NetworkIndicator.vue` — Created
- `src/components/UpdateNotification.vue` — Created
- `src/composables/useNetworkStatus.js` — Created

### Build verification
- Build succeeds with `npm run build`
- Generates `dist/sw.js` and `dist/workbox-*.js`
- Generates `dist/manifest.webmanifest`
- `dist/offline.html` present
- Entry chunk: ~123KB gzipped (unchanged from Phase 18)

---
*Plan created: 2026-04-28*
*Implemented: 2026-04-29*
