/**
 * Payload contamination detection utilities
 * Handles detection of policy-violating, malformed, or suspicious content
 */

// Known patterns that indicate contamination or policy violations
const CONTAMINATION_PATTERNS = {
  // Excessive repetition suggesting data corruption
  EXCESSIVE_REPETITION: /(.+?)\1{5,}/gi,
  
  // Very long words suggesting encoding issues or injection attempts
  LONG_WORD: /\b\w{500,}\b/g,
  
  // Null bytes and control characters that shouldn't be in valid content
  CONTROL_CHARS: /[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g,
  
  // Potential script injection patterns
  SCRIPT_INJECTION: /<script[\s\S]*?>[\s\S]*?<\/script>/gi,
  
  // Potential event handler injection
  EVENT_INJECTION: /\bon\w+\s*=/gi,
  
  // Potential javascript: URI injection
  JAVASCRIPT_URI: /javascript:/gi,
  
  // Potential data: URI injection
  DATA_URI: /data:/gi,
  
  // Potential vbscript injection
  VBSCRIPT_URI: /vbscript:/gi,
  
  // Excessive HTML tags suggesting template injection
  EXCESSIVE_HTML: /<[a-z][^>]*>/gi,
}

// Maximum acceptable lengths for various content types
const MAX_LENGTHS = {
  SECTION_CONTENT: 100000,    // 100KB for section content
  CHAT_MESSAGE: 50000,       // 50KB for chat messages
  AGENT_LOG: 500000,         // 500KB for agent logs
  PARSED_ITEM: 10000,        // 10KB for individual parsed items
}

/**
 * Detect if content is contaminated with policy violations or malformed data
 * @param {string} content - Content to check
 * @param {Object} options - Validation options
 * @returns {Object} - { isContaminated: boolean, reasons: string[], severity: 'none'|'warning'|'critical' }
 */
export function detectContamination(content, options = {}) {
  const {
    maxLength = MAX_LENGTHS.SECTION_CONTENT,
    checkInjection = true,
    checkRepetition = true,
    checkEncoding = true
  } = options
  
  if (!content || typeof content !== 'string') {
    return { isContaminated: true, reasons: ['empty_or_invalid'], severity: 'warning' }
  }
  
  const reasons = []
  let severity = 'none'
  
  // Check for empty content
  if (content.trim().length === 0) {
    reasons.push('empty_content')
    severity = 'warning'
  }
  
  // Check length limits
  if (content.length > maxLength) {
    reasons.push(`excessive_length_${content.length}`)
    severity = severity === 'none' ? 'warning' : severity
  }
  
  // Check for encoding issues
  if (checkEncoding) {
    const controlCharMatch = content.match(CONTAMINATION_PATTERNS.CONTROL_CHARS)
    if (controlCharMatch) {
      reasons.push('control_characters')
      severity = 'critical'
    }
    
    const longWordMatch = content.match(CONTAMINATION_PATTERNS.LONG_WORD)
    if (longWordMatch) {
      reasons.push('excessive_word_length')
      severity = severity === 'none' ? 'warning' : severity
    }
  }
  
  // Check for injection patterns
  if (checkInjection) {
    if (CONTAMINATION_PATTERNS.SCRIPT_INJECTION.test(content)) {
      reasons.push('script_injection')
      severity = 'critical'
    }
    
    if (CONTAMINATION_PATTERNS.EVENT_INJECTION.test(content)) {
      reasons.push('event_injection')
      severity = 'critical'
    }
    
    const uriMatches = content.match(/javascript:|data:|vbscript:/gi)
    if (uriMatches) {
      reasons.push('dangerous_uri_scheme')
      severity = 'critical'
    }
  }
  
  // Check for excessive repetition (data corruption indicator)
  if (checkRepetition) {
    const repetitionMatch = content.match(CONTAMINATION_PATTERNS.EXCESSIVE_REPETITION)
    if (repetitionMatch && repetitionMatch.length > 0) {
      reasons.push('excessive_repetition')
      severity = severity === 'none' ? 'warning' : severity
    }
  }
  
  return {
    isContaminated: severity !== 'none',
    reasons,
    severity
  }
}

/**
 * Sanitize content to remove obviously dangerous patterns
 * This is a best-effort cleanup - not a security guarantee
 * @param {string} content - Content to sanitize
 * @returns {string} - Sanitized content
 */
export function sanitizeContent(content) {
  if (!content || typeof content !== 'string') {
    return ''
  }
  
  let sanitized = content
  
  // Remove control characters
  sanitized = sanitized.replace(CONTAMINATION_PATTERNS.CONTROL_CHARS, '')
  
  // Remove script tags (basic XSS prevention for v-html)
  sanitized = sanitized.replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, '[removed]')
  sanitized = sanitized.replace(/<script[\s\S]*?\/>/gi, '[removed]')
  
  // Remove on* event handlers
  sanitized = sanitized.replace(/\bon\w+\s*=\s*["'][^"']*["']/gi, '')
  sanitized = sanitized.replace(/\bon\w+\s*=\s*[^\s>]+/gi, '')
  
  // Remove javascript: URIs
  sanitized = sanitized.replace(/javascript:\s*/gi, '')
  
  // Remove data: URIs (potential mime type attacks)
  sanitized = sanitized.replace(/data:\s*/gi, '')
  
  return sanitized
}

/**
 * Validate a parsed tool result object
 * @param {Object} result - Parsed result object
 * @param {string} type - Type of result (insight_forge, panorama, interview, etc.)
 * @returns {Object} - { isValid: boolean, cleanedResult: Object|null, warnings: string[] }
 */
export function validateParsedResult(result, type) {
  const warnings = []
  let cleanedResult = { ...result }
  let isValid = true
  
  // Validate insight_forge results
  if (type === 'insight_forge') {
    if (cleanedResult.stats) {
      if (typeof cleanedResult.stats.facts !== 'number' || cleanedResult.stats.facts < 0) {
        cleanedResult.stats.facts = 0
        warnings.push('invalid_facts_count')
      }
      if (typeof cleanedResult.stats.entities !== 'number' || cleanedResult.stats.entities < 0) {
        cleanedResult.stats.entities = 0
        warnings.push('invalid_entities_count')
      }
    }
    
    // Check facts array
    if (Array.isArray(cleanedResult.facts)) {
      cleanedResult.facts = cleanedResult.facts.filter(fact => {
        const contamination = detectContamination(fact, { maxLength: MAX_LENGTHS.PARSED_ITEM })
        if (contamination.isContaminated) {
          warnings.push('fact_contaminated')
          return false
        }
        return true
      })
    }
    
    // Check entities array
    if (Array.isArray(cleanedResult.entities)) {
      cleanedResult.entities = cleanedResult.entities.filter(entity => {
        if (entity.name) {
          const contamination = detectContamination(entity.name, { maxLength: 500 })
          if (contamination.isContaminated) {
            warnings.push('entity_contaminated')
            return false
          }
        }
        return true
      })
    }
  }
  
  // Validate panorama results
  if (type === 'panorama') {
    if (cleanedResult.stats) {
      if (typeof cleanedResult.stats.nodes !== 'number') {
        cleanedResult.stats.nodes = 0
        warnings.push('invalid_nodes_count')
      }
      if (typeof cleanedResult.stats.edges !== 'number') {
        cleanedResult.stats.edges = 0
        warnings.push('invalid_edges_count')
      }
    }
    
    // Validate facts arrays
    if (Array.isArray(cleanedResult.activeFacts)) {
      cleanedResult.activeFacts = cleanedResult.activeFacts.filter(fact => {
        const contamination = detectContamination(fact, { maxLength: MAX_LENGTHS.PARSED_ITEM })
        if (contamination.isContaminated) {
          warnings.push('active_fact_contaminated')
          return false
        }
        return true
      })
    }
    
    if (Array.isArray(cleanedResult.historicalFacts)) {
      cleanedResult.historicalFacts = cleanedResult.historicalFacts.filter(fact => {
        const contamination = detectContamination(fact, { maxLength: MAX_LENGTHS.PARSED_ITEM })
        if (contamination.isContaminated) {
          warnings.push('historical_fact_contaminated')
          return false
        }
        return true
      })
    }
  }
  
  // Validate interview results
  if (type === 'interview') {
    if (Array.isArray(cleanedResult.interviews)) {
      cleanedResult.interviews = cleanedResult.interviews.filter(interview => {
        if (interview.name) {
          const contamination = detectContamination(interview.name, { maxLength: 200 })
          if (contamination.isContaminated) {
            warnings.push('interview_contaminated')
            return false
          }
        }
        return true
      })
    }
  }
  
  return { isValid, cleanedResult, warnings }
}

/**
 * Validate chat history entries
 * @param {Array} chatHistory - Array of chat messages
 * @returns {Object} - { validHistory: Array, contaminatedCount: number, removedEntries: string[] }
 */
export function validateChatHistory(chatHistory) {
  if (!Array.isArray(chatHistory)) {
    return { validHistory: [], contaminatedCount: 0, removedEntries: ['invalid_format'] }
  }
  
  const validHistory = []
  let contaminatedCount = 0
  const removedEntries = []
  
  for (let i = 0; i < chatHistory.length; i++) {
    const msg = chatHistory[i]
    
    // Validate message structure
    if (!msg || typeof msg !== 'object') {
      removedEntries.push(`index_${i}_invalid_structure`)
      contaminatedCount++
      continue
    }
    
    // Validate role
    if (!['user', 'assistant', 'system'].includes(msg.role)) {
      removedEntries.push(`index_${i}_invalid_role`)
      contaminatedCount++
      continue
    }
    
    // Validate content
    if (msg.content !== undefined && msg.content !== null) {
      const contentContamination = detectContamination(
        String(msg.content),
        { maxLength: MAX_LENGTHS.CHAT_MESSAGE }
      )
      
      if (contentContamination.severity === 'critical') {
        removedEntries.push(`index_${i}_critical_contamination`)
        contaminatedCount++
        continue
      }
      
      if (contentContamination.severity === 'warning') {
        // Keep with warning but sanitize
        msg.content = sanitizeContent(String(msg.content))
        warnings.push(`index_${i}_sanitized`)
      }
    }
    
    // Validate timestamp if present
    if (msg.timestamp) {
      const timestamp = new Date(msg.timestamp)
      if (isNaN(timestamp.getTime())) {
        msg.timestamp = new Date().toISOString()
        removedEntries.push(`index_${i}_invalid_timestamp`)
      }
    } else {
      msg.timestamp = new Date().toISOString()
    }
    
    validHistory.push(msg)
  }
  
  return { validHistory, contaminatedCount, removedEntries }
}

/**
 * Validate report section content
 * @param {string} content - Section markdown content
 * @param {number} sectionIndex - Section index for logging
 * @returns {Object} - { isValid: boolean, sanitizedContent: string|null, contamination: Object }
 */
export function validateSectionContent(content, sectionIndex) {
  const contamination = detectContamination(content, {
    maxLength: MAX_LENGTHS.SECTION_CONTENT,
    checkRepetition: true,
    checkEncoding: true,
    checkInjection: true
  })
  
  if (contamination.severity === 'critical') {
    return {
      isValid: false,
      sanitizedContent: null,
      contamination,
      fallbackReason: 'critical_contamination'
    }
  }
  
  if (contamination.severity === 'warning') {
    // Try to sanitize and use with warning
    const sanitized = sanitizeContent(content)
    return {
      isValid: true,
      sanitizedContent: sanitized,
      contamination,
      fallbackReason: contamination.reasons.length > 0 ? contamination.reasons[0] : null
    }
  }
  
  return {
    isValid: true,
    sanitizedContent: content,
    contamination,
    fallbackReason: null
  }
}

/**
 * Validate agent log entry
 * @param {Object} log - Agent log entry
 * @returns {Object} - { isValid: boolean, cleanedLog: Object|null, issues: string[] }
 */
export function validateAgentLog(log) {
  const issues = []
  let cleanedLog = { ...log }
  
  // Check required fields
  if (!log || typeof log !== 'object') {
    return { isValid: false, cleanedLog: null, issues: ['invalid_structure'] }
  }
  
  if (!log.action || typeof log.action !== 'string') {
    issues.push('missing_or_invalid_action')
    cleanedLog.action = 'unknown'
  }
  
  if (log.timestamp && typeof log.timestamp === 'string') {
    const date = new Date(log.timestamp)
    if (isNaN(date.getTime())) {
      issues.push('invalid_timestamp')
      cleanedLog.timestamp = new Date().toISOString()
    }
  }
  
  // Validate details if present
  if (log.details && typeof log.details === 'object') {
    // Check for contaminated result content
    if (log.details.result && typeof log.details.result === 'string') {
      const resultContamination = detectContamination(log.details.result, {
        maxLength: MAX_LENGTHS.AGENT_LOG,
        checkRepetition: true,
        checkEncoding: true,
        checkInjection: true
      })
      
      if (resultContamination.severity === 'critical') {
        cleanedLog.details.result = '[content_removed]'
        issues.push('result_removed_critical')
      } else if (resultContamination.severity === 'warning') {
        cleanedLog.details.result = sanitizeContent(log.details.result)
        issues.push('result_sanitized_warning')
      }
    }
    
    // Check for contaminated response content
    if (log.details.response && typeof log.details.response === 'string') {
      const responseContamination = detectContamination(log.details.response, {
        maxLength: MAX_LENGTHS.AGENT_LOG,
        checkRepetition: true,
        checkEncoding: true,
        checkInjection: true
      })
      
      if (responseContamination.severity === 'critical') {
        cleanedLog.details.response = '[content_removed]'
        issues.push('response_removed_critical')
      } else if (responseContamination.severity === 'warning') {
        cleanedLog.details.response = sanitizeContent(log.details.response)
        issues.push('response_sanitized_warning')
      }
    }
  }
  
  return {
    isValid: issues.filter(i => i.includes('critical')).length === 0,
    cleanedLog,
    issues
  }
}

// Export constants for use in components
export { MAX_LENGTHS, CONTAMINATION_PATTERNS }
