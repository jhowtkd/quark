import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SimOverviewTab from '../../../src/components/simulation/SimOverviewTab.vue'
import { mockRunningState } from '../../mocks/simulationState.js'

describe('SimOverviewTab', () => {
  it('renders progress percent', () => {
    const wrapper = mount(SimOverviewTab, {
      props: { state: mockRunningState, actions: [] },
    })
    expect(wrapper.text()).toContain('50%')
    expect(wrapper.text()).toContain('Info Plaza')
    expect(wrapper.text()).toContain('Topic Community')
  })

  it('shows recent actions', () => {
    const wrapper = mount(SimOverviewTab, {
      props: {
        state: mockRunningState,
        actions: [
          { _uniqueId: '1', agent_name: 'Alice', action_type: 'CREATE_POST', platform: 'twitter', timestamp: '2026-04-29T10:01:00Z', round_num: 1, action_args: {}, success: true },
        ],
      },
    })
    expect(wrapper.text()).toContain('Alice')
  })
})
