import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'
import ActionExplorer from '../../src/components/ActionExplorer.vue'

const tFn = (key, params = {}) => {
  const translations = {
    'step5.explorer.title': 'Explorar Ações',
    'step5.explorer.searchPlaceholder': 'Buscar em posts e comentários...',
    'step5.explorer.filterAgent': 'Agente',
    'step5.explorer.filterPlatform': 'Plataforma',
    'step5.explorer.filterActionType': 'Tipo de ação',
    'step5.explorer.filterRound': 'Round',
    'step5.explorer.filterSuccess': 'Sucesso',
    'step5.explorer.clearFilters': 'Limpar filtros',
    'step5.explorer.resultsCount': '{count} ações encontradas',
    'step5.explorer.colRound': 'Round',
    'step5.explorer.colTime': 'Hora',
    'step5.explorer.colAgent': 'Agente',
    'step5.explorer.colPlatform': 'Plataforma',
    'step5.explorer.colAction': 'Ação',
    'step5.explorer.colContent': 'Conteúdo',
    'step5.explorer.colSuccess': 'Sucesso',
    'step5.explorer.prevPage': 'Anterior',
    'step5.explorer.nextPage': 'Próxima',
    'step5.explorer.pageInfo': 'Página {page} de {total} ({count} ações)',
    'step5.explorer.all': 'Todos',
    'step5.explorer.success': 'Sucesso',
    'step5.explorer.failure': 'Falha',
    'step5.explorer.noData': 'Nenhuma ação encontrada com os filtros atuais.',
    'step5.actions.types.CREATE_POST': 'Criar post',
    'step5.actions.types.LIKE_POST': 'Curtir',
    'step5.actions.types.QUOTE_POST': 'Citar',
    'step5.actions.types.REPOST_POST': 'Repostar',
    'step5.actions.types.CREATE_COMMENT': 'Comentar',
    'step5.actions.types.FOLLOW': 'Seguir',
    'common.loading': 'Carregando...',
    'common.unknownError': 'Erro desconhecido'
  }
  let text = translations[key] || key
  Object.entries(params).forEach(([k, v]) => {
    text = text.replace(`{${k}}`, String(v))
  })
  return text
}

// Mock vue-i18n
vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: tFn })
}))

// Mock API
const mockGetSimulationActions = vi.fn()
const mockGetSimulationPosts = vi.fn()

vi.mock('../../src/api/simulation.js', () => ({
  getSimulationActions: (...args) => mockGetSimulationActions(...args),
  getSimulationPosts: (...args) => mockGetSimulationPosts(...args)
}))

const mountWithMocks = (props = {}) => {
  return mount(ActionExplorer, { props })
}

const createMockActions = (count = 5) => {
  const actions = []
  for (let i = 0; i < count; i++) {
    actions.push({
      id: `action-${i}`,
      round_num: (i % 3) + 1,
      timestamp: new Date(2024, 0, 1, 10, i, 0).toISOString(),
      agent_id: i % 2,
      agent_name: i % 2 === 0 ? 'Alice' : 'Bob',
      platform: i % 2 === 0 ? 'twitter' : 'reddit',
      action_type: ['CREATE_POST', 'LIKE_POST', 'QUOTE_POST', 'REPOST_POST', 'CREATE_COMMENT', 'FOLLOW'][i % 6],
      action_args: { content: `Content number ${i}` },
      result: `Result ${i}`,
      success: i % 3 !== 0
    })
  }
  return actions
}

describe('ActionExplorer', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    mockGetSimulationActions.mockReset()
    mockGetSimulationPosts.mockReset()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders table when simulationId is provided', async () => {
    mockGetSimulationActions.mockResolvedValue({
      success: true,
      data: { actions: createMockActions(5), count: 5 }
    })
    mockGetSimulationPosts.mockResolvedValue({
      success: true,
      data: { posts: [], count: 0 }
    })

    const wrapper = mountWithMocks({ simulationId: 'sim-123' })

    await flushPromises()

    expect(wrapper.find('.explorer-table').exists()).toBe(true)
    expect(wrapper.findAll('.explorer-row').length).toBe(5)
  })

  it('calls getSimulationActions on mount', async () => {
    mockGetSimulationActions.mockResolvedValue({
      success: true,
      data: { actions: createMockActions(3), count: 3 }
    })
    mockGetSimulationPosts.mockResolvedValue({
      success: true,
      data: { posts: [], count: 0 }
    })

    mountWithMocks({ simulationId: 'sim-123' })

    await flushPromises()

    expect(mockGetSimulationActions).toHaveBeenCalledWith('sim-123', { limit: 1000, offset: 0 })
  })

  it('updates displayed list when filters change', async () => {
    mockGetSimulationActions.mockResolvedValue({
      success: true,
      data: { actions: createMockActions(6), count: 6 }
    })
    mockGetSimulationPosts.mockResolvedValue({
      success: true,
      data: { posts: [], count: 0 }
    })

    const wrapper = mountWithMocks({ simulationId: 'sim-123' })

    await flushPromises()
    expect(wrapper.findAll('.explorer-row').length).toBe(6)

    // Filter by agent Alice
    const agentSelect = wrapper.findAll('.filter-select')[0]
    await agentSelect.setValue('Alice')
    await nextTick()

    const rows = wrapper.findAll('.explorer-row')
    expect(rows.length).toBeLessThan(6)
    rows.forEach(row => {
      expect(row.text()).toContain('Alice')
    })
  })

  it('filters results by text search', async () => {
    const actions = createMockActions(5)
    actions[0].result = 'special keyword here'
    actions[1].action_args.content = 'another special keyword'

    mockGetSimulationActions.mockResolvedValue({
      success: true,
      data: { actions, count: 5 }
    })
    mockGetSimulationPosts.mockResolvedValue({
      success: true,
      data: { posts: [], count: 0 }
    })

    const wrapper = mountWithMocks({ simulationId: 'sim-123' })

    await flushPromises()
    expect(wrapper.findAll('.explorer-row').length).toBe(5)

    const searchInput = wrapper.find('.explorer-search')
    await searchInput.setValue('special keyword')
    vi.advanceTimersByTime(400)
    await nextTick()

    const rows = wrapper.findAll('.explorer-row')
    expect(rows.length).toBe(2)
  })

  it('sorts by column when header is clicked', async () => {
    mockGetSimulationActions.mockResolvedValue({
      success: true,
      data: { actions: createMockActions(4), count: 4 }
    })
    mockGetSimulationPosts.mockResolvedValue({
      success: true,
      data: { posts: [], count: 0 }
    })

    const wrapper = mountWithMocks({ simulationId: 'sim-123' })

    await flushPromises()

    const headers = wrapper.findAll('.sortable-header')
    const agentHeader = headers.find(h => h.text().includes('Agente'))
    expect(agentHeader).toBeDefined()

    // Click agent header to sort by agent_name
    await agentHeader.trigger('click')
    await nextTick()

    let rows = wrapper.findAll('.explorer-row')
    const firstAgent = rows[0].findAll('td')[2].text()
    const lastAgent = rows[rows.length - 1].findAll('td')[2].text()
    expect(firstAgent <= lastAgent).toBe(true)

    // Click again to reverse
    await agentHeader.trigger('click')
    await nextTick()

    rows = wrapper.findAll('.explorer-row')
    const firstAgentDesc = rows[0].findAll('td')[2].text()
    const lastAgentDesc = rows[rows.length - 1].findAll('td')[2].text()
    expect(firstAgentDesc >= lastAgentDesc).toBe(true)
  })

  it('shows only pageSize rows per page', async () => {
    mockGetSimulationActions.mockResolvedValue({
      success: true,
      data: { actions: createMockActions(30), count: 30 }
    })
    mockGetSimulationPosts.mockResolvedValue({
      success: true,
      data: { posts: [], count: 0 }
    })

    const wrapper = mountWithMocks({ simulationId: 'sim-123' })

    await flushPromises()

    // Default pageSize is 25, so 25 rows should show
    expect(wrapper.findAll('.explorer-row').length).toBe(25)

    // Change page size to 10
    const pageSizeSelect = wrapper.find('.page-size-select')
    await pageSizeSelect.setValue(10)
    await nextTick()

    expect(wrapper.findAll('.explorer-row').length).toBe(10)
  })

  it('shows empty state when no actions match filters', async () => {
    mockGetSimulationActions.mockResolvedValue({
      success: true,
      data: { actions: createMockActions(3), count: 3 }
    })
    mockGetSimulationPosts.mockResolvedValue({
      success: true,
      data: { posts: [], count: 0 }
    })

    const wrapper = mountWithMocks({ simulationId: 'sim-123' })

    await flushPromises()
    expect(wrapper.findAll('.explorer-row').length).toBe(3)

    // Search for something that doesn't exist
    const searchInput = wrapper.find('.explorer-search')
    await searchInput.setValue('NONEXISTENT_QUERY_999')
    vi.advanceTimersByTime(400)
    await nextTick()

    expect(wrapper.findAll('.explorer-row').length).toBe(0)
    expect(wrapper.find('.explorer-empty').exists()).toBe(true)
    expect(wrapper.text()).toContain('Nenhuma ação encontrada')
  })

  it('disables prev on first page and next on last page', async () => {
    mockGetSimulationActions.mockResolvedValue({
      success: true,
      data: { actions: createMockActions(30), count: 30 }
    })
    mockGetSimulationPosts.mockResolvedValue({
      success: true,
      data: { posts: [], count: 0 }
    })

    const wrapper = mountWithMocks({ simulationId: 'sim-123' })

    await flushPromises()

    const prevBtn = wrapper.find('.page-btn.prev')
    const nextBtn = wrapper.find('.page-btn.next')

    expect(prevBtn.attributes('disabled')).toBeDefined()
    expect(nextBtn.attributes('disabled')).toBeUndefined()

    // Change page size to 10
    const pageSizeSelect = wrapper.find('.page-size-select')
    await pageSizeSelect.setValue(10)
    await nextTick()

    // Click next twice to reach last page (3 pages)
    await nextBtn.trigger('click')
    await nextTick()
    await nextBtn.trigger('click')
    await nextTick()

    expect(prevBtn.attributes('disabled')).toBeUndefined()
    expect(nextBtn.attributes('disabled')).toBeDefined()
  })
})
