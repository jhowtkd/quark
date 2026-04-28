// Convex is disabled - using Flask backend
// This file is kept for compatibility but Convex features are disabled

export function createConvexClient() {
  console.warn('[Convex] Convex is disabled - using Flask backend')
  return { client: null }
}

export function setupConvex(app, client) {
  // No-op - Convex disabled
}

export function useConvex() {
  return null
}

export async function convexQuery(queryName, args = {}) {
  throw new Error('Convex is disabled')
}

export async function convexMutation(mutationName, args = {}) {
  throw new Error('Convex is disabled')
}

export async function convexAction(actionName, args = {}) {
  throw new Error('Convex is disabled')
}