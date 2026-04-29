import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref, nextTick } from 'vue'
import { useSimulationMonitor } from '../../src/composables/useSimulationMonitor.js'

vi.mock('../../src/api/simulation.js', () => ({
  getRunStatus: vi.fn(),
  getRunStatusDetail: vi.fn(),
}))

import { getRunStatus, getRunStatusDetail } from '../../src/api/simulation.js'

describe('useSimulationMonitor', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should start polling when simulationId is provided', async () => {
    getRunStatus.mockResolvedValue({ success: true, data: { runner_status: 'running' } })
    getRunStatusDetail.mockResolvedValue({ success: true, data: { all_actions: [] } })

    const simulationId = ref('sim_001')
    const { state, isPolling } = useSimulationMonitor(simulationId)

    await nextTick()
    expect(isPolling.value).toBe(true)

    await vi.advanceTimersByTimeAsync(3000)
    await nextTick()
    expect(getRunStatus).toHaveBeenCalledWith('sim_001')
  })

  it('should stop polling on unmount', async () => {
    getRunStatus.mockResolvedValue({ success: true, data: { runner_status: 'running' } })
    getRunStatusDetail.mockResolvedValue({ success: true, data: { all_actions: [] } })

    const simulationId = ref('sim_001')
    const { isPolling, stopPolling } = useSimulationMonitor(simulationId)
    await nextTick()
    expect(isPolling.value).toBe(true)

    stopPolling()
    expect(isPolling.value).toBe(false)
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

    const simulationId = ref('sim_001')
    const { actions } = useSimulationMonitor(simulationId)

    // Let the initial tick's async operations complete
    await Promise.resolve()
    await Promise.resolve()

    await vi.advanceTimersByTimeAsync(3000)
    await nextTick()

    expect(actions.value.length).toBe(1)
    expect(actions.value[0].agent_name).toBe('Alice')

    // Second poll with same action should not duplicate
    await vi.advanceTimersByTimeAsync(3000)
    await nextTick()

    expect(actions.value.length).toBe(1)
  })
})
