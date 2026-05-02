import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref, nextTick } from 'vue'
import Step4Report from '../../src/components/Step4Report.vue'

// Mock vue-router
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn()
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
  'contamination.contentRemoved': 'Conteúdo removido por violação de política'
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

// Mock report API
vi.mock('../../src/api/report', () => ({
  getAgentLog: vi.fn(() => Promise.resolve({ success: true, data: { logs: [], from_line: 0 } })),
  getConsoleLog: vi.fn(() => Promise.resolve({ success: true, data: { logs: [], from_line: 0 } }))
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
          $t: mockT
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
