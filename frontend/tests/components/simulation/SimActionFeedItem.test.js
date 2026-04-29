import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SimActionFeedItem from '../../../src/components/simulation/SimActionFeedItem.vue'

describe('SimActionFeedItem', () => {
  it('renders agent name and action type', () => {
    const wrapper = mount(SimActionFeedItem, {
      props: {
        action: {
          agent_name: 'Alice',
          action_type: 'CREATE_POST',
          platform: 'twitter',
          timestamp: '2026-04-29T10:01:00.000Z',
          round_num: 1,
          action_args: { content: 'Hello' },
          success: true,
        },
      },
    })
    expect(wrapper.text()).toContain('Alice')
    expect(wrapper.text()).toContain('POST')
  })

  it('renders platform icon for reddit', () => {
    const wrapper = mount(SimActionFeedItem, {
      props: {
        action: {
          agent_name: 'Bob',
          action_type: 'CREATE_COMMENT',
          platform: 'reddit',
          timestamp: '2026-04-29T10:01:00.000Z',
          round_num: 1,
          action_args: {},
          success: true,
        },
      },
    })
    expect(wrapper.text()).toContain('Bob')
    expect(wrapper.text()).toContain('COMMENT')
  })
})
