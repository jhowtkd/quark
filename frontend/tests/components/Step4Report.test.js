import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'
import Step4Report from '../../src/components/Step4Report.vue'

const mockT = (key, params) => {
  if (params) {
    let msg = key
    Object.entries(params).forEach(([k, v]) => {
      msg = msg.replace(new RegExp(`{${k}}`, 'g'), v)
    })
    return msg
  }
  return key
}

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() })
}))

vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: mockT })
}))

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

vi.mock('../../src/utils/payloadValidator', () => ({
  detectContamination: vi.fn(() => ({ severity: 'warning', reasons: ['thinking'] })),
  sanitizeContent: vi.fn((c) => c.replace(/I have gathered[^.]*/gi, '[filtered]')),
  validateAgentLog: vi.fn(() => true)
}))

global.IntersectionObserver = class IntersectionObserver {
  constructor(callback) { this.callback = callback }
  observe() {}
  disconnect() {}
  unobserve() {}
}

describe('Step4Report', () => {
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

  const mountWithOutline = async (props = {}) => {
    const wrapper = mount(Step4Report, {
      props: {
        reportId: 'report_test',
        simulationId: 'sim_test',
        systemLogs: [],
        ...props
      },
      global: {
        mocks: { $t: mockT },
        stubs: {
          'router-link': true,
          'router-view': true
        }
      },
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

  it('renders report content when loaded', async () => {
    mockGetReport.mockResolvedValue({ success: true, data: { report_id: 'report_test' } })
    mockGetReportProgress.mockResolvedValue({ success: true, data: { failed_sections: [] } })

    const wrapper = await mountWithOutline()
    wrapper.vm.generatedSections = {
      1: '# Markdown Content\n\nThis is **bold** text.',
      2: '## Section 2 Title\n\nMore content here.'
    }
    await nextTick()

    const generatedContent = wrapper.findAll('.generated-content')
    expect(generatedContent.length).toBeGreaterThan(0)
    expect(wrapper.text()).toContain('Test Report')
    expect(wrapper.text()).toContain('Test Summary')
  })

  it('shows loading state before response', async () => {
    mockGetReport.mockResolvedValue({ success: true, data: { report_id: 'report_test' } })
    mockGetReportProgress.mockResolvedValue({ success: true, data: { failed_sections: [] } })

    const wrapper = mount(Step4Report, {
      props: { reportId: 'report_test', simulationId: 'sim_test', systemLogs: [] },
      global: { mocks: { $t: mockT } },
      attachTo: document.body
    })
    await flushPromises()

    // Before reportOutline is set manually, check waiting placeholder exists
    expect(wrapper.find('.waiting-placeholder').exists()).toBe(true)
  })

  it('shows retry button on failure', async () => {
    mockGetReport.mockRejectedValue(new Error('Network error 500'))

    const wrapper = mount(Step4Report, {
      props: { reportId: 'report_test', simulationId: 'sim_test', systemLogs: [] },
      global: { mocks: { $t: mockT } },
      attachTo: document.body
    })
    await flushPromises()
    await nextTick()

    const retryBtn = wrapper.find('.retry-btn')
    expect(retryBtn.exists()).toBe(true)
    expect(retryBtn.text()).toContain('common.retry')
  })

  it('does not render thinking process', async () => {
    mockGetReport.mockResolvedValue({ success: true, data: { report_id: 'report_test' } })
    mockGetReportProgress.mockResolvedValue({ success: true, data: { failed_sections: [] } })

    const wrapper = await mountWithOutline()
    wrapper.vm.generatedSections = {
      1: 'Some analysis. I have gathered the data and thought about it. Conclusion follows.'
    }
    await nextTick()

    const generatedContent = wrapper.find('.generated-content')
    expect(generatedContent.exists()).toBe(true)
    expect(generatedContent.text()).not.toContain('I have gathered')
  })

  it('renders quality indicator when available', async () => {
    mockGetReport.mockResolvedValue({ success: true, data: { report_id: 'report_test' } })
    mockGetReportProgress.mockResolvedValue({ success: true, data: { failed_sections: [] } })

    const wrapper = await mountWithOutline()
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
})
