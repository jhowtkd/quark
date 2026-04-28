import service, { requestWithRetry } from './index'

/**
 * Gerar relatório iniciando
 * @param {Object} data - { simulation_id, force_regenerate? }
 */
export const generateReport = (data) => {
  return requestWithRetry(() => service.post('/report/generate', data), 3, 1000)
}

/**
 * Buscando status do relatório
 * @param {string} reportId
 */
export const getReportStatus = (reportId) => {
  return service.get(`/report/generate/status`, { params: { report_id: reportId } })
}

/**
 * Log de agentes (incrementais）
 * @param {string} reportId
 * @param {number} fromLine - Linha primária de busca
 */
export const getAgentLog = (reportId, fromLine = 0) => {
  return service.get(`/report/${reportId}/agent-log`, { params: { from_line: fromLine } })
}

/**
 * Buscando logs de console (incrementais）
 * @param {string} reportId
 * @param {number} fromLine - Linha primária de busca
 */
export const getConsoleLog = (reportId, fromLine = 0) => {
  return service.get(`/report/${reportId}/console-log`, { params: { from_line: fromLine } })
}

/**
 * Verificar datalhes do relatório
 * @param {string} reportId
 */
export const getReport = (reportId) => {
  return service.get(`/report/${reportId}`)
}

/**
 * Conversar com Repórter
 * @param {Object} data - { simulation_id, message, chat_history? }
 */
export const chatWithReport = (data) => {
  return requestWithRetry(() => service.post('/report/chat', data), 3, 1000)
}
