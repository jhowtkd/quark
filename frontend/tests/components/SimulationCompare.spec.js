import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'
import SimulationCompare from '../../src/components/SimulationCompare.vue'

const tFn = (key, params = {}) => {
  const translations = {
    'step5.compare.title': 'Comparar Simulações',
    'step5.compare.selectBase': 'Simulação base',
    'step5.compare.selectTarget': 'Selecione uma simulação...',
    'step5.compare.swap': 'Trocar',
    'step5.compare.metricsTitle': 'Métricas',
    'step5.compare.agentsTitle': 'Top Agentes',
    'step5.compare.timelineTitle': 'Distribuição Temporal',
    'step5.compare.agents': 'Agentes',
    'step5.compare.rounds': 'Rounds',
    'step5.compare.actions': 'Ações',
    'step5.compare.twitterActions': 'Twitter',
    'step5.compare.redditActions': 'Reddit',
    'step5.compare.simulatedHours': 'Horas simuladas',
    'step5.compare.commonAgents': 'Agentes em comum',
    'step5.compare.uniqueAgentsLhs': 'Agentes únicos (base)',
    'step5.compare.uniqueAgentsRhs': 'Agentes únicos (comparada)',
    'step5.compare.noHistory': 'Nenhuma simulação no histórico para comparar.',
    'step5.compare.selectToCompare': 'Selecione uma simulação para comparar',
    'step5.compare.errorLoading': 'Erro ao carregar dados de comparação',
    'step5.compare.retry': 'Tentar novamente',
    'step5.compare.expandAll': 'Expandir todos',
    'step5.compare.collapseAll': 'Recolher',
    'step5.dashboard.topAgents': 'Agentes mais ativos',
    'history.untitledSimulation': 'Projeto Anônimo'
  }
  let text = translations[key] || key
  Object.entries(params).forEach(([k, v]) => {
    text = text.replace(`{${k}}`, String(v))
  })
  return text
}

vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: tFn })
}))

const mockGetSimulationHistory = vi.fn()
const mockGetSimulation = vi.fn()
const mockGetAgentStats = vi.fn()
const mockGetSimulationTimeline = vi.fn()

vi.mock('../../src/api/simulation.js', () => ({
  getSimulationHistory: (...args) => mockGetSimulationHistory(...args),
  getSimulation: (...args) => mockGetSimulation(...args),
  getAgentStats: (...args) => mockGetAgentStats(...args),
  getSimulationTimeline: (...args) => mockGetSimulationTimeline(...args)
}))

const createMockHistory = () => [
  {
    simulation_id: 'sim-001',
    project_name: 'Project Alpha',
    status: 'completed',
    created_at: '2024-06-15T10:00:00Z',
    total_rounds: 10,
    profiles_count: 5
  },
  {
    simulation_id: 'sim-002',
    project_name: 'Project Beta',
    status: 'completed',
    created_at: '2024-06-14T10:00:00Z',
    total_rounds: 8,
    profiles_count: 4
  },
  {
    simulation_id: 'sim-003',
    project_name: 'Project Gamma',
    status: 'running',
    created_at: '2024-06-13T10:00:00Z',
    total_rounds: 5,
    profiles_count: 3
  }
]

const createMockSimData = (id) => ({
  success: true,
  data: {
    simulation_id: id,
    total_rounds: id === 'sim-001' ? 10 : 8,
    current_round: id === 'sim-001' ? 10 : 8,
    total_actions_count: id === 'sim-001' ? 100 : 80,
    twitter_actions_count: id === 'sim-001' ? 60 : 50,
    reddit_actions_count: id === 'sim-001' ? 40 : 30,
    simulated_hours: id === 'sim-001' ? 24 : 20,
    profiles_count: id === 'sim-001' ? 5 : 4
  }
})

const createMockAgentStats = (id) => {
  const baseAgents = [
    { agent_id: 1, agent_name: 'Alice', total_actions: 50, twitter_actions: 30, reddit_actions: 20, action_types: {} },
    { agent_id: 2, agent_name: 'Bob', total_actions: 40, twitter_actions: 25, reddit_actions: 15, action_types: {} },
    { agent_id: 3, agent_name: 'Charlie', total_actions: 30, twitter_actions: 20, reddit_actions: 10, action_types: {} },
    { agent_id: 4, agent_name: 'Diana', total_actions: 20, twitter_actions: 10, reddit_actions: 10, action_types: {} },
    { agent_id: 5, agent_name: 'Eve', total_actions: 10, twitter_actions: 5, reddit_actions: 5, action_types: {} }
  ]
  const rhsAgents = [
    { agent_id: 1, agent_name: 'Alice', total_actions: 45, twitter_actions: 28, reddit_actions: 17, action_types: {} },
    { agent_id: 2, agent_name: 'Bob', total_actions: 35, twitter_actions: 22, reddit_actions: 13, action_types: {} },
    { agent_id: 6, agent_name: 'Frank', total_actions: 25, twitter_actions: 15, reddit_actions: 10, action_types: {} }
  ]
  return {
    success: true,
    data: {
      stats: id === 'sim-001' ? baseAgents : rhsAgents
    }
  }
}

const createMockTimeline = (id) => {
  const rounds = id === 'sim-001' ? 10 : 8
  const timeline = []
  for (let i = 1; i <= rounds; i++) {
    timeline.push({
      round_num: i,
      twitter_actions: id === 'sim-001' ? i * 3 : i * 2,
      reddit_actions: id === 'sim-001' ? i * 2 : i + 1,
      active_agents: 3,
      action_types: {},
      first_action_time: '2024-01-01T10:00:00Z',
      last_action_time: '2024-01-01T10:05:00Z'
    })
  }
  return { success: true, data: { timeline } }
}

const mountWithMocks = (props = {}) => {
  return mount(SimulationCompare, {
    props,
    global: { mocks: { $t: tFn } }
  })
}

describe('SimulationCompare', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    mockGetSimulationHistory.mockReset()
    mockGetSimulation.mockReset()
    mockGetAgentStats.mockReset()
    mockGetSimulationTimeline.mockReset()

    mockGetSimulationHistory.mockResolvedValue({
      success: true,
      data: createMockHistory()
    })
    mockGetSimulation.mockImplementation((id) => Promise.resolve(createMockSimData(id)))
    mockGetAgentStats.mockImplementation((id) => Promise.resolve(createMockAgentStats(id)))
    mockGetSimulationTimeline.mockImplementation((id) => Promise.resolve(createMockTimeline(id)))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('calls getSimulationHistory on mount', async () => {
    mountWithMocks({ baseSimulationId: 'sim-001' })
    await flushPromises()
    expect(mockGetSimulationHistory).toHaveBeenCalledWith(50)
  })

  it('populates dropdowns with history', async () => {
    const wrapper = mountWithMocks({ baseSimulationId: 'sim-001' })
    await flushPromises()
    await nextTick()

    const lhsSelect = wrapper.find('.lhs-select')
    const rhsSelect = wrapper.find('.rhs-select')

    expect(lhsSelect.exists()).toBe(true)
    expect(rhsSelect.exists()).toBe(true)

    // LHS should have all completed sims (2 completed out of 3)
    const lhsOptions = lhsSelect.findAll('option')
    expect(lhsOptions.length).toBe(2)

    // RHS should have all completed sims except the one selected in LHS
    const rhsOptions = rhsSelect.findAll('option')
    expect(rhsOptions.length).toBe(2) // 1 placeholder + 1 remaining completed
  })

  it('selecting RHS triggers rhsData loading', async () => {
    const wrapper = mountWithMocks({ baseSimulationId: 'sim-001' })
    await flushPromises()
    await nextTick()

    const rhsSelect = wrapper.find('.rhs-select')
    await rhsSelect.setValue('sim-002')
    await flushPromises()
    await nextTick()

    expect(mockGetSimulation).toHaveBeenCalledWith('sim-002')
    expect(mockGetAgentStats).toHaveBeenCalledWith('sim-002')
    expect(mockGetSimulationTimeline).toHaveBeenCalledWith('sim-002', 0, null)
  })

  it('renders metric cards with LHS and RHS values', async () => {
    const wrapper = mountWithMocks({ baseSimulationId: 'sim-001' })
    await flushPromises()
    await nextTick()

    // Select RHS
    const rhsSelect = wrapper.find('.rhs-select')
    await rhsSelect.setValue('sim-002')
    await flushPromises()
    await nextTick()

    const metricCards = wrapper.findAll('.metric-value')
    expect(metricCards.length).toBeGreaterThan(0)

    // LHS should show 5 agents (from sim-001)
    const lhsValues = wrapper.findAll('.metrics-column').at(0).findAll('.metric-value')
    expect(lhsValues.at(0).text()).toBe('5')

    // RHS should show 4 agents (from sim-002)
    const rhsValues = wrapper.findAll('.metrics-column').at(1).findAll('.metric-value')
    expect(rhsValues.at(0).text()).toBe('4')
  })

  it('calculates and displays delta between simulations', async () => {
    const wrapper = mountWithMocks({ baseSimulationId: 'sim-001' })
    await flushPromises()
    await nextTick()

    const rhsSelect = wrapper.find('.rhs-select')
    await rhsSelect.setValue('sim-002')
    await flushPromises()
    await nextTick()

    const deltas = wrapper.findAll('.delta-row')
    expect(deltas.length).toBe(6)

    // RHS has fewer agents than LHS (4 vs 5), so first delta should be negative
    const firstDelta = deltas.at(0)
    expect(firstDelta.classes()).toContain('negative')
  })

  it('renders timeline using data from both simulations', async () => {
    const wrapper = mountWithMocks({ baseSimulationId: 'sim-001' })
    await flushPromises()
    await nextTick()

    const rhsSelect = wrapper.find('.rhs-select')
    await rhsSelect.setValue('sim-002')
    await flushPromises()
    await nextTick()

    const timelineRounds = wrapper.findAll('.timeline-round')
    expect(timelineRounds.length).toBeGreaterThan(0)

    // Should have 10 rounds (max of 10 and 8)
    expect(timelineRounds.length).toBe(10)

    // Check that both LHS and RHS bars exist in round 1
    const firstRoundBars = timelineRounds.at(0).findAll('.round-bars > div')
    expect(firstRoundBars.length).toBe(2)
  })

  it('lists top agents from both simulations', async () => {
    const wrapper = mountWithMocks({ baseSimulationId: 'sim-001' })
    await flushPromises()
    await nextTick()

    const rhsSelect = wrapper.find('.rhs-select')
    await rhsSelect.setValue('sim-002')
    await flushPromises()
    await nextTick()

    const agentsTables = wrapper.findAll('.agents-table')
    expect(agentsTables.length).toBeGreaterThanOrEqual(2)

    // LHS top agents table should have Alice as #1
    const lhsRows = agentsTables.at(0).findAll('tbody tr')
    expect(lhsRows.length).toBe(5)
    expect(lhsRows.at(0).text()).toContain('Alice')

    // RHS top agents table should also have Alice as #1
    const rhsRows = agentsTables.at(1).findAll('tbody tr')
    expect(rhsRows.length).toBe(3)
    expect(rhsRows.at(0).text()).toContain('Alice')
  })

  it('identifies common agents correctly', async () => {
    const wrapper = mountWithMocks({ baseSimulationId: 'sim-001' })
    await flushPromises()
    await nextTick()

    const rhsSelect = wrapper.find('.rhs-select')
    await rhsSelect.setValue('sim-002')
    await flushPromises()
    await nextTick()

    const commonSection = wrapper.find('.common-agents')
    expect(commonSection.exists()).toBe(true)

    const commonRows = commonSection.findAll('tbody tr')
    // Alice and Bob are common between sim-001 and sim-002
    expect(commonRows.length).toBe(2)

    const firstCommonName = commonRows.at(0).findAll('td').at(0).text()
    expect(['Alice', 'Bob']).toContain(firstCommonName)
  })

  it('shows empty state when history is empty', async () => {
    mockGetSimulationHistory.mockResolvedValue({
      success: true,
      data: []
    })

    const wrapper = mountWithMocks({ baseSimulationId: 'sim-001' })
    await flushPromises()
    await nextTick()

    expect(wrapper.find('.compare-empty').exists()).toBe(true)
    expect(wrapper.text()).toContain('Nenhuma simulação no histórico')
  })

  it('shows placeholder when rhs is not selected', async () => {
    const wrapper = mountWithMocks({ baseSimulationId: 'sim-001' })
    await flushPromises()
    await nextTick()

    const placeholder = wrapper.find('.sim-placeholder')
    expect(placeholder.exists()).toBe(true)
    expect(placeholder.text()).toContain('Selecione uma simulação para comparar')
  })

  it('swaps LHS and RHS when swap button clicked', async () => {
    const wrapper = mountWithMocks({ baseSimulationId: 'sim-001' })
    await flushPromises()
    await nextTick()

    // Select RHS first
    const rhsSelect = wrapper.find('.rhs-select')
    await rhsSelect.setValue('sim-002')
    await flushPromises()
    await nextTick()

    const swapBtn = wrapper.find('.swap-btn')
    await swapBtn.trigger('click')
    await flushPromises()
    await nextTick()

    // After swap, LHS should be sim-002 and RHS should be sim-001
    const lhsSelect = wrapper.find('.lhs-select')
    expect(lhsSelect.element.value).toBe('sim-002')
  })
})
