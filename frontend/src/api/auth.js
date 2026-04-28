// Auth API - uses localStorage for now (no Convex backend)
// For production, implement auth endpoints in backend

const AUTH_KEY = 'futuria_user'
const AUTH_FLAG = 'futuria_authenticated'

/**
 * Login stub - stores user in localStorage
 * @param {Object} data - { email, password }
 * @returns {Promise} Returns { userId, email, name }
 */
export const login = async (data) => {
  // Stub: accept any login, store mock user
  const user = { id: '1', email: data.email, name: data.email.split('@')[0] }
  localStorage.setItem(AUTH_KEY, JSON.stringify(user))
  localStorage.setItem(AUTH_FLAG, 'true')
  return user
}

/**
 * Register stub - stores user in localStorage
 * @param {Object} data - { email, password, name }
 * @returns {Promise} Returns { userId, email, name }
 */
export const register = async (data) => {
  const user = { id: '1', email: data.email, name: data.name || data.email.split('@')[0] }
  localStorage.setItem(AUTH_KEY, JSON.stringify(user))
  localStorage.setItem(AUTH_FLAG, 'true')
  return user
}

/**
 * Logout - clears localStorage
 * @returns {Promise}
 */
export const logout = async () => {
  clearUser()
  return {}
}

/**
 * Get current user from localStorage
 * @returns {Object|null}
 */
export const getCurrentUser = () => {
  const userStr = localStorage.getItem(AUTH_KEY)
  if (userStr) {
    try {
      return JSON.parse(userStr)
    } catch {
      return null
    }
  }
  return null
}

/**
 * Check if user is authenticated
 * @returns {boolean}
 */
export const isAuthenticated = () => {
  return localStorage.getItem(AUTH_FLAG) === 'true'
}

/**
 * Clear user data (logout)
 */
export const clearUser = () => {
  localStorage.removeItem(AUTH_KEY)
  localStorage.removeItem(AUTH_FLAG)
}

/**
 * Set user after successful login/register
 */
export const setUser = (user) => {
  localStorage.setItem(AUTH_KEY, JSON.stringify(user))
  localStorage.setItem(AUTH_FLAG, 'true')
}