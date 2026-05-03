import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import BaseButton from '../../../src/components/base/BaseButton.vue'

describe('BaseButton', () => {
  it('renders default state', () => {
    const wrapper = mount(BaseButton, {
      slots: { default: 'Click me' },
      global: { stubs: { Icon: true } }
    })
    expect(wrapper.text()).toBe('Click me')
    expect(wrapper.classes()).toContain('variant-primary')
    expect(wrapper.classes()).toContain('size-md')
  })

  it('renders disabled state', () => {
    const wrapper = mount(BaseButton, {
      props: { disabled: true },
      slots: { default: 'Click me' },
      global: { stubs: { Icon: true } }
    })
    expect(wrapper.attributes('disabled')).toBeDefined()
  })

  it('renders loading state with spinner', () => {
    const wrapper = mount(BaseButton, {
      props: { loading: true },
      slots: { default: 'Click me' },
      global: { stubs: { Icon: true } }
    })
    expect(wrapper.find('.spin').exists()).toBe(true)
    expect(wrapper.attributes('disabled')).toBeDefined()
  })

  it('emits click when enabled', async () => {
    const wrapper = mount(BaseButton, {
      slots: { default: 'Click me' },
      global: { stubs: { Icon: true } }
    })
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toHaveLength(1)
  })

  it('does not emit click when disabled', async () => {
    const wrapper = mount(BaseButton, {
      props: { disabled: true },
      slots: { default: 'Click me' },
      global: { stubs: { Icon: true } }
    })
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toBeUndefined()
  })
})
