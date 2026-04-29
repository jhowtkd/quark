import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref, toRef, defineComponent, h, nextTick } from 'vue'
import { mount } from '@vue/test-utils'
import { useSimulationMonitor } from '../../src/composables/useSimulationMonitor.js'

vi.mock('../../src/api/simulation.js', () => ({
  getRunStatus: vi.fn(),
  getRunStatusDetail: vi.fn(),
}))

import { getRunStatus, getRunStatusDetail } from '../../src/api/simulation.js'

const TestComponent = defineComponent({
  props: ['simulationId'],
  setup(props) {
    const { state, actions, isPolling, error, errorCount, startPolling, stopPolling, reset } =
      useSimulationMonitor(toRef(props, 'simulationId'))
    return { state, actions, isPolling, error, errorCount, startPolling, stopPolling, reset }
  },
  render() {
    return h('div')
  },
})

describe('useSimulationMonitor', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.clearAllMocks()
    Object.defineProperty(document, 'hidden', {
      writable: true,
      configurable: true,
      value: false,
    })
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should start polling when simulationId is provided', async () => {
    getRunStatus.mockResolvedValue({ success: true, data: { runner_status: 'running' } })
    getRunStatusDetail.mockResolvedValue({ success: true, data: { all_actions: [] } })

    const wrapper = mount(TestComponent, { props: { simulationId: 'sim_001' } })

    expect(wrapper.vm.isPolling).toBe(true)

    await vi.advanceTimersByTimeAsync(0)
    await nextTick()

    expect(getRunStatus).toHaveBeenCalledWith('sim_001')
    expect(getRunStatusDetail).toHaveBeenCalledWith('sim_001')

    wrapper.unmount()
  })

  it('should stop polling on unmount', async () => {
    getRunStatus.mockResolvedValue({ success: true, data: { runner_status: 'running' } })
    getRunStatusDetail.mockResolvedValue({ success: true, data: { all_actions: [] } })

    const wrapper = mount(TestComponent, { props: { simulationId: 'sim_001' } })
    expect(wrapper.vm.isPolling).toBe(true)

    wrapper.unmount()
    expect(wrapper.vm.isPolling).toBe(false)
  })

  it('should accumulate actions without duplicates', async () => {
    const action = {
      id: 'act_1',
      timestamp: '2026-04-29T10:00:00Z',
      platform: 'twitter',
      agent_id: 1,
      agent_name: 'Alice',
      action_type: 'CREATE_POST',
      action_args: {},
      success: true,
    }
    getRunStatus.mockResolvedValue({ success: true, data: { runner_status: 'running' } })
    getRunStatusDetail.mockResolvedValue({ success: true, data: { all_actions: [action] } })

    const wrapper = mount(TestComponent, { props: { simulationId: 'sim_001' } })

    await vi.advanceTimersByTimeAsync(0)
    await nextTick()

    expect(wrapper.vm.actions.length).toBe(1)
    expect(wrapper.vm.actions[0].agent_name).toBe('Alice')

    // Second poll with same action should not duplicate
    await vi.advanceTimersByTimeAsync(3000)
    await nextTick()

    expect(wrapper.vm.actions.length).toBe(1)

    wrapper.unmount()
  })

  it('should reset state and start new polling when simulation ID switches', async () => {
    getRunStatus.mockResolvedValue({ success: true, data: { runner_status: 'running' } })
    getRunStatusDetail.mockResolvedValue({ success: true, data: { all_actions: [] } })

    const wrapper = mount(TestComponent, { props: { simulationId: 'sim_001' } })

    await vi.advanceTimersByTimeAsync(0)
    await nextTick()

    expect(wrapper.vm.isPolling).toBe(true)
    expect(getRunStatus).toHaveBeenCalledWith('sim_001')

    await wrapper.setProps({ simulationId: 'sim_002' })
    await nextTick()

    // Actions should have been cleared by reset
    expect(wrapper.vm.actions).toEqual([])
    expect(wrapper.vm.isPolling).toBe(true)

    await vi.advanceTimersByTimeAsync(0)
    await nextTick()

    expect(getRunStatus).toHaveBeenCalledWith('sim_002')

    wrapper.unmount()
  })

  it('should pause and resume polling on visibility change', async () => {
    getRunStatus.mockResolvedValue({ success: true, data: { runner_status: 'running' } })
    getRunStatusDetail.mockResolvedValue({ success: true, data: { all_actions: [] } })

    const wrapper = mount(TestComponent, { props: { simulationId: 'sim_001' } })

    await vi.advanceTimersByTimeAsync(0)
    await nextTick()

    const callsAfterInitial = getRunStatus.mock.calls.length
    expect(callsAfterInitial).toBeGreaterThanOrEqual(1)

    // Simulate hidden tab: tick should reschedule without calling API
    document.hidden = true
    await vi.advanceTimersByTimeAsync(3000)
    await nextTick()

    expect(getRunStatus.mock.calls.length).toBe(callsAfterInitial)

    // Simulate visible tab: should trigger immediate tick
    document.hidden = false
    document.dispatchEvent(new Event('visibilitychange'))

    await vi.advanceTimersByTimeAsync(0)
    await nextTick()

    expect(getRunStatus.mock.calls.length).toBe(callsAfterInitial + 1)

    wrapper.unmount()
  })

  it('should increase interval on error backoff then reset on success', async () => {
    getRunStatus
      .mockResolvedValueOnce({ success: true, data: { runner_status: 'running' } })
      .mockRejectedValueOnce(new Error('Network error'))
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({ success: true, data: { runner_status: 'running' } })

    getRunStatusDetail.mockResolvedValue({ success: true, data: { all_actions: [] } })

    const wrapper = mount(TestComponent, { props: { simulationId: 'sim_001' } })

    // First tick succeeds, runner_status = running
    await vi.advanceTimersByTimeAsync(0)
    await nextTick()

    expect(wrapper.vm.errorCount).toBe(0)
    expect(getRunStatus).toHaveBeenCalledTimes(1)

    // Second tick fails, errorCount = 1, backoff = 3000 * 2 = 6000
    await vi.advanceTimersByTimeAsync(3000)
    await nextTick()

    expect(wrapper.vm.errorCount).toBe(1)
    expect(wrapper.vm.error).toBe('Network error')

    // Third tick fails, errorCount = 2, backoff = 3000 * 4 = 12000
    await vi.advanceTimersByTimeAsync(6000)
    await nextTick()

    expect(wrapper.vm.errorCount).toBe(2)

    // Fourth tick succeeds, errorCount resets to 0
    await vi.advanceTimersByTimeAsync(12000)
    await nextTick()

    expect(wrapper.vm.errorCount).toBe(0)
    expect(wrapper.vm.error).toBeNull()

    wrapper.unmount()
  })

  it('should deduplicate actions with fallback key when no id field', async () => {
    const actionWithoutId = {
      timestamp: '2026-04-29T10:00:00Z',
      platform: 'twitter',
      agent_id: 1,
      agent_name: 'Alice',
      action_type: 'CREATE_POST',
      action_args: {},
      success: true,
    }
    getRunStatus.mockResolvedValue({ success: true, data: { runner_status: 'running' } })
    getRunStatusDetail.mockResolvedValue({ success: true, data: { all_actions: [actionWithoutId] } })

    const wrapper = mount(TestComponent, { props: { simulationId: 'sim_001' } })

    await vi.advanceTimersByTimeAsync(0)
    await nextTick()

    expect(wrapper.vm.actions.length).toBe(1)
    expect(wrapper.vm.actions[0]._uniqueId).toBe(
      '2026-04-29T10:00:00Z-twitter-1-CREATE_POST'
    )

    // Second poll with same action should not duplicate
    await vi.advanceTimersByTimeAsync(3000)
    await nextTick()

    expect(wrapper.vm.actions.length).toBe(1)

    wrapper.unmount()
  })

  it('should not break loop when fetchDetail silently fails', async () => {
    getRunStatus.mockResolvedValue({ success: true, data: { runner_status: 'running' } })
    getRunStatusDetail.mockRejectedValue(new Error('Detail fetch failed'))

    const wrapper = mount(TestComponent, { props: { simulationId: 'sim_001' } })

    await vi.advanceTimersByTimeAsync(0)
    await nextTick()

    expect(wrapper.vm.isPolling).toBe(true)
    expect(getRunStatus).toHaveBeenCalledWith('sim_001')
    expect(getRunStatusDetail).toHaveBeenCalledWith('sim_001')

    // Loop should continue after silent failure
    await vi.advanceTimersByTimeAsync(3000)
    await nextTick()

    expect(getRunStatus).toHaveBeenCalledTimes(2)
    expect(getRunStatusDetail).toHaveBeenCalledTimes(2)
    expect(wrapper.vm.isPolling).toBe(true)

    wrapper.unmount()
  })
})
