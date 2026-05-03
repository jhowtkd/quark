import service from './index'

/**
 * Create a new feedback item
 * @param {Object} data - { stage, category, rating, comment, simulation_id?, report_id?, user_email? }
 * @returns {Promise<{success: boolean, data: {feedback_id, created_at}}>}
 */
export const createFeedback = (data) => {
  return service.post('/feedback', data)
}

/**
 * List feedback items with optional filters
 * @param {Object} params - { limit?, category?, severity?, stage? }
 * @returns {Promise<{success: boolean, data: {items: Array, count: number}}>}
 */
export const listFeedback = (params = {}) => {
  return service.get('/feedback', { params })
}

/**
 * Get a single feedback item by ID
 * @param {string} feedbackId
 * @returns {Promise<{success: boolean, data: Object}>}
 */
export const getFeedback = (feedbackId) => {
  return service.get(`/feedback/${feedbackId}`)
}

/**
 * Update feedback (severity, triage_notes, converted_to_backlog)
 * @param {string} feedbackId
 * @param {Object} data - { severity?, triage_notes?, converted_to_backlog? }
 * @returns {Promise<{success: boolean, data: {updated_at}}>}
 */
export const updateFeedback = (feedbackId, data) => {
  return service.put(`/feedback/${feedbackId}`, data)
}

/**
 * Get feedback summary statistics for triage
 * @returns {Promise<{success: boolean, data: {total, by_category, by_stage, by_severity, avg_rating}}>}
 */
export const getFeedbackStats = () => {
  return service.get('/feedback/stats/summary')
}

/**
 * Get the most recent beta changelog
 * @returns {Promise<{success: boolean, data: {filename, date, content}|null}>}
 */
export const getLatestChangelog = () => {
  return service.get('/feedback/triage/latest-changelog')
}
