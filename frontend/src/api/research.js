/**
 * Deep Research API Client
 * 
 * Provides functions to interact with the research backend:
 * - startResearch: POST /research/start
 * - getResearchStatus: GET /research/status/<run_id>
 * - getResearchResult: GET /research/result/<run_id>
 * - approveResearch: POST /research/approve/<run_id>
 * - rejectResearch: POST /research/reject/<run_id>
 * - rerunResearch: POST /research/rerun/<run_id>
 * - promoteResearch: POST /research/promote/<run_id>
 * - createProjectFromResearch: POST /research/create-project/<run_id>
 */

import service, { requestWithRetry } from './index'

/**
 * Start a new deep research run
 * @param {Object} data - { query: string, project_id?: string }
 * @returns {Promise} - { success, data: { run_id, task_id } }
 */
export function startResearch(data) {
  return requestWithRetry(() => service.post('/research/start', data), 3, 1000)
}

/**
 * Get the status of a research run
 * @param {string} runId - The research run ID
 * @returns {Promise} - { success, data: { run_id, query, status, progress, message, connector_used, error } }
 */
export function getResearchStatus(runId) {
  return service.get(`/research/status/${runId}`)
}

/**
 * Get the markdown result of a completed research run
 * @param {string} runId - The research run ID
 * @returns {Promise} - { success, data: { run_id, query, connector_used, markdown } }
 */
export function getResearchResult(runId) {
  return service.get(`/research/result/${runId}`)
}

/**
 * Approve a completed research run
 * Fail-closed: validates draft.md has all required sections before approving
 * @param {string} runId - The research run ID
 * @returns {Promise} - { success, data: { run_id, status, approved_at } }
 */
export function approveResearch(runId) {
  return service.post(`/research/approve/${runId}`)
}

/**
 * Reject a research run and reset to pending
 * @param {string} runId - The research run ID
 * @returns {Promise} - { success, data: { run_id, status, rejected_at } }
 */
export function rejectResearch(runId) {
  return service.post(`/research/reject/${runId}`)
}

/**
 * Request a rerun with user feedback
 * @param {string} runId - The original research run ID
 * @param {string} feedback - User feedback for improvement
 * @returns {Promise} - { success, data: { new_run_id, task_id, original_run_id } }
 */
export function rerunResearch(runId, feedback) {
  return service.post(`/research/rerun/${runId}`, { feedback })
}

/**
 * Promote approved research to project sources
 * Copies approved draft.md into project extracted_text.txt
 * @param {string} runId - The approved research run ID
 * @param {string} [projectId] - Optional project ID to promote to (creates new project if not provided)
 * @returns {Promise} - { success, data: { run_id, project_id, promoted_chars, merge_mode, promoted_at } }
 */
export function promoteResearch(runId, projectId) {
  return requestWithRetry(
    () => service.post(`/research/promote/${runId}`, projectId ? { project_id: projectId } : {}),
    3,
    1000
  )
}

/**
 * Create a new project from approved research
 * Creates project with research markdown as extracted_text.txt and stub ontology
 * @param {string} runId - The approved research run ID
 * @returns {Promise} - { success, data: { run_id, project_id, project_name, created_at } }
 */
export function createProjectFromResearch(runId) {
  return requestWithRetry(() => service.post(`/research/create-project/${runId}`), 3, 1000)
}
