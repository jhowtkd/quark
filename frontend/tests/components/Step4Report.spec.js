import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref, nextTick } from 'vue'
import Step4Report from '../../src/components/Step4Report.vue'

const mockRouterPush = vi.fn()

// Mock vue-router
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockRouterPush
  })
}))

const i18nMessages = {
  'step4.focusMode.enter': 'Modo Foco',
  'step4.focusMode.exit': 'Sair do Modo Foco',
  'step4.focusMode.shortcut': '(F)',
  'step4.sectionNav.title': 'Conteudo',
  'step4.generatingSection': 'Gerando {title}...',
  'step4.waitingForReportAgent': 'Esperando pelo Agente de Relatório...',
  'step4.waitingForAgentActivity': 'Aguardando atividade do agente...',
  'step4.consoleOutput': 'SAÍDA DO CONSOLE',
  'step4.noReport': 'SEM_REL',
  'step4.goToInteraction': 'Entrar em Interação',
  'step4.reportGenerationComplete': 'Geração do Relatório Concluída',
  'step4.sectionContentGenerated': 'Conteúdo de "{title}" gerado',
  'common.retry': 'Tentar novamente',
  'contamination.contentRemoved': 'Conteúdo removido por violação de política',
  'step4.emptyState.title': 'Relatorio nao encontrado',
  'step4.emptyState.description': 'O relatorio solicitado nao existe ou foi removido.',
  'step4.emptyState.backButton': 'Voltar para o Workbench',
  'step4.sectionError.title': 'Falha ao gerar secao',
  'step4.sectionError.retryButton': 'Tentar novamente',
  'step4.sectionError.retrying': 'Tentando novamente...',
  'step4.qualityIndicator.title': 'Qualidade do relatorio',
  'step4.qualityIndicator.sectionsCompleted': '{completed}/{total} secoes',
  'step4.qualityIndicator.contaminated': '{count} secao(oes) com contaminacao',
  'step4.qualityIndicator.failed': '{count} secao(oes) com falha',
  'step4.qualityIndicator.filtered': 'Thinking process filtrado',
  'step4.reportLoadError': 'Falha ao carregar o relatorio: {error}'
}

const mockT = (key, params) => {
  let msg = i18nMessages[key] || key
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      msg = msg.replace(new RegExp(`{${k}}`, 'g'), v)
    })
  }
  return msg
}

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: mockT,
    $t: mockT
  })
}))

// Mock report API — use module-level fns that vitest can track
const mockGetReport = vi.fn(() => Promise.resolve({ success: true, data: { report_id: 'report_test' } }))
const mockGetReportProgress = vi.fn(() => Promise.resolve({ success: true, data: { failed_sections: [] } }))
const mockRetrySection = vi.fn(() => Promise.resolve({ success: true, data: { status: 'retrying', section_index: 1 } }))

vi.mock('../../src/api/report', () => ({
  getAgentLog: vi.fn(() => Promise.resolve({ success: true, data: { logs: [], from_line: 0 } })),
  getConsoleLog: vi.fn(() => Promise.resolve({ success: true, data: { logs: [], from_line: 0 } })),
  getReport: (...args) => mockGetReport(...args),
  getReportProgress: (...args) => mockGetReportProgress(...args),
  retrySection: (...args) => mockRetrySection(...args)
}))

// Mock payloadValidator
vi.mock('../../src/utils/payloadValidator', () => ({
  detectContamination: vi.fn(() => ({ severity: 'clean', reasons: [] })),
  sanitizeContent: vi.fn((c) => c),
  validateAgentLog: vi.fn(() => true)
}))

// Mock IntersectionObserver for jsdom
global.IntersectionObserver = class IntersectionObserver {
  constructor(callback) { this.callback = callback }
  observe() {}
  disconnect() {}
  unobserve() {}
}

describe('Step4Report - Focus Mode', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.useFakeTimers({ shouldAdvanceTime: true })
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.clearAllMocks()
  })

  const mountWithOutline = async (props = {}) => {
    const wrapper = mount(Step4Report, {
      props: {
        reportId: 'report_test',
        simulationId: 'sim_test',
        systemLogs: [],
        ...props
      },
      global: {
        mocks: {
          $t: mockT,
          $router: { push: mockRouterPush }
        },
        stubs: {
          'router-link': true,
          'router-view': true
        }
      },
      attachTo: document.body
    })
    await flushPromises()
    // Set report outline to make the toggle visible
    wrapper.vm.reportOutline = {
      title: 'Test Report',
      summary: 'Test Summary',
      sections: [
        { title: 'Section 1' },
        { title: 'Section 2' }
      ]
    }
    await nextTick()
    return wrapper
  }

  it('renders focus mode toggle button', async () => {
    const wrapper = await mountWithOutline()
    const toggle = wrapper.find('.focus-mode-toggle')
    expect(toggle.exists()).toBe(true)
    expect(toggle.text()).toContain('Modo Foco')
  })

  it('toggles focus-mode--active class when clicking toggle', async () => {
    const wrapper = await mountWithOutline()
    const panel = wrapper.find('.report-panel')
    expect(panel.classes()).not.toContain('focus-mode--active')

    const toggle = wrapper.find('.focus-mode-toggle')
    await toggle.trigger('click')
    await nextTick()

    expect(panel.classes()).toContain('focus-mode--active')
    expect(toggle.text()).toContain('Sair do Modo Foco')

    await toggle.trigger('click')
    await nextTick()

    expect(panel.classes()).not.toContain('focus-mode--active')
    expect(toggle.text()).toContain('Modo Foco')
  })

  it('hides right-panel when focus mode is active', async () => {
    const wrapper = await mountWithOutline()
    const rightPanel = wrapper.find('.right-panel')
    expect(rightPanel.isVisible()).toBe(true)

    const toggle = wrapper.find('.focus-mode-toggle')
    await toggle.trigger('click')
    await nextTick()

    expect(rightPanel.isVisible()).toBe(false)
  })

  it('hides console-logs when focus mode is active', async () => {
    const wrapper = await mountWithOutline()
    const consoleLogs = wrapper.find('.console-logs')
    expect(consoleLogs.isVisible()).toBe(true)

    const toggle = wrapper.find('.focus-mode-toggle')
    await toggle.trigger('click')
    await nextTick()

    expect(consoleLogs.isVisible()).toBe(false)
  })

  it('toggles focus mode with "f" key', async () => {
    const wrapper = await mountWithOutline()
    const panel = wrapper.find('.report-panel')
    expect(panel.classes()).not.toContain('focus-mode--active')

    // Simulate 'f' key press on document body
    const event = new KeyboardEvent('keydown', { key: 'f', bubbles: true })
    document.body.dispatchEvent(event)
    await nextTick()

    expect(panel.classes()).toContain('focus-mode--active')

    // Toggle back
    const event2 = new KeyboardEvent('keydown', { key: 'F', bubbles: true })
    document.body.dispatchEvent(event2)
    await nextTick()

    expect(panel.classes()).not.toContain('focus-mode--active')
  })

  it('does not toggle focus mode when typing in input', async () => {
    const wrapper = await mountWithOutline()
    const panel = wrapper.find('.report-panel')

    // Create an input element and focus it
    const input = document.createElement('input')
    document.body.appendChild(input)
    input.focus()

    const event = new KeyboardEvent('keydown', { key: 'f', bubbles: true })
    input.dispatchEvent(event)
    await nextTick()

    expect(panel.classes()).not.toContain('focus-mode--active')

    document.body.removeChild(input)
  })

  it('restores focus mode from localStorage on mount', async () => {
    localStorage.setItem('futuria-report-focus-mode', 'true')
    const wrapper = await mountWithOutline()
    const panel = wrapper.find('.report-panel')
    expect(panel.classes()).toContain('focus-mode--active')
  })

  it('persists focus mode to localStorage', async () => {
    const wrapper = await mountWithOutline()
    const toggle = wrapper.find('.focus-mode-toggle')

    await toggle.trigger('click')
    expect(localStorage.getItem('futuria-report-focus-mode')).toBe('true')

    await toggle.trigger('click')
    expect(localStorage.getItem('futuria-report-focus-mode')).toBe('false')
  })
})

describe('Step4Report - Empty State (404)', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.useFakeTimers({ shouldAdvanceTime: true })
    mockGetReport.mockReset()
    mockGetReportProgress.mockReset()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.clearAllMocks()
  })

  it('renders empty state when getReport returns 404', async () => {
    mockGetReport.mockResolvedValue({ success: false, status: 404, error: 'Not found' })
    mockGetReportProgress.mockResolvedValue({ success: true, data: { failed_sections: [] } })

    const wrapper = mount(Step4Report, {
      props: { reportId: 'report_missing', simulationId: 'sim_test', systemLogs: [] },
      global: { mocks: { $t: mockT } },
      attachTo: document.body
    })
    await flushPromises()

    expect(wrapper.find('.report-empty-state').exists()).toBe(true)
    expect(wrapper.find('.empty-state-title').text()).toContain('Relatorio nao encontrado')
    expect(wrapper.find('.waiting-placeholder').exists()).toBe(false)
  })

  it('back button navigates to Main route', async () => {
    mockRouterPush.mockClear()
    mockGetReport.mockResolvedValue({ success: false, status: 404, error: 'Not found' })
    mockGetReportProgress.mockResolvedValue({ success: true, data: { failed_sections: [] } })

    const wrapper = mount(Step4Report, {
      props: { reportId: 'report_missing', simulationId: 'sim_test', systemLogs: [] },
      global: { mocks: { $t: mockT, $router: { push: mockRouterPush } } },
      attachTo: document.body
    })
    await flushPromises()

    const backBtn = wrapper.find('.empty-state-back-btn')
    expect(backBtn.exists()).toBe(true)
    await backBtn.trigger('click')
    await flushPromises()
    expect(mockRouterPush).toHaveBeenCalledWith({ name: 'Main' })
  })
})

describe('Step4Report - Section Error & Retry', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.useFakeTimers({ shouldAdvanceTime: true })
    mockGetReport.mockReset()
    mockGetReportProgress.mockReset()
    mockRetrySection.mockReset()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.clearAllMocks()
  })

  const mountWithFailedSection = async () => {
    mockGetReport.mockResolvedValue({ success: true, data: { report_id: 'report_test' } })
    mockGetReportProgress.mockResolvedValue({
      success: true,
      data: {
        failed_sections: [
          { section_index: 1, section_title: 'Section 1', error_message: 'LLM timeout', failed_at: '2025-01-01T00:00:00Z' }
        ]
      }
    })

    const wrapper = mount(Step4Report, {
      props: { reportId: 'report_test', simulationId: 'sim_test', systemLogs: [] },
      global: { mocks: { $t: mockT } },
      attachTo: document.body
    })
    await flushPromises()
    wrapper.vm.reportOutline = {
      title: 'Test Report',
      summary: 'Test Summary',
      sections: [
        { title: 'Section 1' },
        { title: 'Section 2' }
      ]
    }
    await nextTick()
    return wrapper
  }

  it('shows section error state for failed sections', async () => {
    const wrapper = await mountWithFailedSection()
    const errorStates = wrapper.findAll('.section-error-state')
    expect(errorStates.length).toBeGreaterThan(0)
    expect(errorStates[0].find('.error-title').text()).toContain('Falha ao gerar secao')
  })

  it('clicking retry button calls retrySection API and removes from failedSections', async () => {
    mockRetrySection.mockResolvedValue({ success: true, data: { status: 'retrying', section_index: 1 } })

    const wrapper = await mountWithFailedSection()
    expect(wrapper.vm.failedSections.has(1)).toBe(true)

    const retryBtn = wrapper.find('.retry-section-btn')
    expect(retryBtn.exists()).toBe(true)
    expect(retryBtn.text()).toContain('Tentar novamente')

    await retryBtn.trigger('click')
    await flushPromises()

    expect(mockRetrySection).toHaveBeenCalledWith('report_test', 1)
    expect(wrapper.vm.failedSections.has(1)).toBe(false)
  })
})

describe('Step4Report - Quality Indicator', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.useFakeTimers({ shouldAdvanceTime: true })
    mockGetReport.mockReset()
    mockGetReportProgress.mockReset()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.clearAllMocks()
  })

  it('shows quality score based on completed sections', async () => {
    mockGetReport.mockResolvedValue({ success: true, data: { report_id: 'report_test' } })
    mockGetReportProgress.mockResolvedValue({ success: true, data: { failed_sections: [] } })

    const wrapper = mount(Step4Report, {
      props: { reportId: 'report_test', simulationId: 'sim_test', systemLogs: [] },
      global: { mocks: { $t: mockT } },
      attachTo: document.body
    })
    await flushPromises()

    wrapper.vm.reportOutline = {
      title: 'Test Report',
      summary: 'Test Summary',
      sections: [
        { title: 'Section 1' },
        { title: 'Section 2' },
        { title: 'Section 3' },
        { title: 'Section 4' }
      ]
    }
    wrapper.vm.generatedSections = { 1: 'content1', 2: 'content2' }
    await nextTick()

    const indicator = wrapper.find('.report-quality-indicator')
    expect(indicator.exists()).toBe(true)
    expect(indicator.find('.quality-value').text()).toBe('50%')
  })

  it('shows contaminated badge when sections are contaminated', async () => {
    mockGetReport.mockResolvedValue({ success: true, data: { report_id: 'report_test' } })
    mockGetReportProgress.mockResolvedValue({ success: true, data: { failed_sections: [] } })

    const wrapper = mount(Step4Report, {
      props: { reportId: 'report_test', simulationId: 'sim_test', systemLogs: [] },
      global: { mocks: { $t: mockT } },
      attachTo: document.body
    })
    await flushPromises()

    wrapper.vm.reportOutline = {
      title: 'Test Report',
      summary: 'Test Summary',
      sections: [{ title: 'Section 1' }]
    }
    wrapper.vm.contaminatedSections = new Set([1])
    await nextTick()

    const badge = wrapper.find('.badge--warning')
    expect(badge.exists()).toBe(true)
    expect(badge.text()).toContain('1')
  })

  it('shows failed badge when sections failed', async () => {
    mockGetReport.mockResolvedValue({ success: true, data: { report_id: 'report_test' } })
    mockGetReportProgress.mockResolvedValue({ success: true, data: { failed_sections: [] } })

    const wrapper = mount(Step4Report, {
      props: { reportId: 'report_test', simulationId: 'sim_test', systemLogs: [] },
      global: { mocks: { $t: mockT } },
      attachTo: document.body
    })
    await flushPromises()

    wrapper.vm.reportOutline = {
      title: 'Test Report',
      summary: 'Test Summary',
      sections: [{ title: 'Section 1' }]
    }
    wrapper.vm.failedSections = new Map([[1, { error: 'timeout' }]])
    await nextTick()

    const badge = wrapper.find('.badge--error')
    expect(badge.exists()).toBe(true)
    expect(badge.text()).toContain('1')
  })
})
