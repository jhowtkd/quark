import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import BaseModal from '../../../src/components/base/BaseModal.vue'

describe('BaseModal', () => {
  it('opens when open prop is true', () => {
    const wrapper = mount(BaseModal, {
      props: { open: true, title: 'Test Modal' },
      global: { stubs: { teleport: true, Icon: true } }
    })
    expect(wrapper.find('.modal-overlay').exists()).toBe(true)
    expect(wrapper.find('.modal-content').exists()).toBe(true)
  })

  it('closes when open prop is false', () => {
    const wrapper = mount(BaseModal, {
      props: { open: false, title: 'Test Modal' },
      global: { stubs: { teleport: true, Icon: true } }
    })
    expect(wrapper.find('.modal-overlay').exists()).toBe(false)
  })

  it('renders content slot', () => {
    const wrapper = mount(BaseModal, {
      props: { open: true, title: 'Test Modal' },
      slots: { default: '<p class="custom-content">Hello</p>' },
      global: { stubs: { teleport: true, Icon: true } }
    })
    expect(wrapper.find('.custom-content').exists()).toBe(true)
    expect(wrapper.text()).toContain('Hello')
  })

  it('emits update:open false on overlay click', async () => {
    const wrapper = mount(BaseModal, {
      props: { open: true, title: 'Test Modal' },
      global: { stubs: { teleport: true, Icon: true } }
    })
    await wrapper.find('.modal-overlay').trigger('click')
    expect(wrapper.emitted('update:open')).toEqual([[false]])
  })
})
