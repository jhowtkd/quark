import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref, nextTick } from 'vue'
import Step3Simulation from '../../src/components/Step3Simulation.vue'
import { mockRunningState, mockCompletedState, mockFailedState } from '../mocks/simulationState.js'

const mockMonitorState = ref(null)
const mockMonitorActions = ref([])
const mockMonitorIsPolling = ref(false)
const mockMonitorError = ref(null)
const mockStartPolling = vi.fn()
const mockStopPolling = vi.fn()
const mockReset = vi.fn()

vi.mock('../../src/composables/useSimulationMonitor.js', () => ({
  useSimulationMonitor: () => ({
    state: mockMonitorState,
    actions: mockMonitorActions,
    isPolling: mockMonitorIsPolling,
    error: mockMonitorError,
    startPolling: mockStartPolling,
    stopPolling: mockStopPolling,
    reset: mockReset,
  })
}))

vi.mock('../../src/composables/useSimulationEta.js', () => ({
  useSimulationEta: () => ({
    elapsedSeconds: ref(120),
    etaSeconds: ref(300),
    estimatedCompletionTime: ref('14:30'),
    confidence: ref('medium'),
    startTimer: vi.fn(),
    stopTimer: vi.fn(),
  })
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() })
}))

function mockT(key) { return key }
vi.mock('vue-i18n', async () => {
  return {
    useI18n: () => ({ t: mockT }),
    createI18n: () => ({ global: { t: mockT } })
  }
})

describe('Step3Simulation', () => {
  beforeEach(() => {
    mockMonitorState.value = null
    mockMonitorActions.value = []
    mockMonitorIsPolling.value = false
    mockMonitorError.value = null
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  const mountComponent = (props = {}) => {
    return mount(Step3Simulation, {
      props: {
        simulationId: 'sim_test_001',
        maxRounds: 10,
        minutesPerRound: 30,
        projectData: {},
        graphData: {},
        systemLogs: [],
        simulationConfig: {},
        ...props
      },
      global: {
        mocks: {
          $t: mockT,
        },
        stubs: {
          ParamTooltip: true,
          SimConfirmModal: true,
          SimLogPanel: true,
        }
      }
    })
  }

  it('renders running state correctly', async () => {
    mockMonitorState.value = { ...mockRunningState }
    mockMonitorIsPolling.value = true
    const wrapper = mountComponent()
    await nextTick()

    wrapper.vm.showConfirmModal = false
    wrapper.vm.phase = 1
    await nextTick()

    expect(wrapper.text()).toContain('50%')
    expect(wrapper.text()).toContain('Round 5 / 10')
  })

  it('renders completed state correctly', async () => {
    mockMonitorState.value = { ...mockCompletedState }
    const wrapper = mountComponent()
    await nextTick()

    wrapper.vm.phase = 2
    wrapper.vm.showConfirmModal = false
    await nextTick()

    expect(wrapper.text()).toContain('100%')

    const advanceBtn = wrapper.find('.action-btn.primary')
    expect(advanceBtn.attributes('disabled')).toBeUndefined()
  })

  it('renders failed state with clear message', async () => {
    mockMonitorState.value = { ...mockFailedState }
    const wrapper = mountComponent()
    await nextTick()

    wrapper.vm.phase = 2
    wrapper.vm.showConfirmModal = false
    await nextTick()

    const errorBanners = wrapper.findAll('.monitor-error-banner')
    const failedBanner = errorBanners.find(b => b.text().includes('step3.simulationFailed'))
    expect(failedBanner.exists()).toBe(true)
    // Should not show raw technical traceback in the DOM
    expect(wrapper.text()).not.toContain('exit code 1')
  })

  it('disables advance button while running', async () => {
    mockMonitorState.value = { ...mockRunningState }
    const wrapper = mountComponent()
    await nextTick()

    wrapper.vm.showConfirmModal = false
    wrapper.vm.phase = 1
    await nextTick()

    const advanceBtn = wrapper.find('.action-btn.primary')
    expect(advanceBtn.attributes('disabled')).toBeDefined()
  })

  it('shows ETA when running', async () => {
    mockMonitorState.value = { ...mockRunningState }
    mockMonitorIsPolling.value = true
    const wrapper = mountComponent()
    await nextTick()

    wrapper.vm.showConfirmModal = false
    wrapper.vm.phase = 1
    await nextTick()

    expect(wrapper.find('.eta-bar').exists()).toBe(true)
    expect(wrapper.text()).toContain('Restante (est.)')
  })
})
