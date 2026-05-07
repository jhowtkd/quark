# Agent Evolution Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add controlled, auditable agent evolution to FUTUR.IA simulations.

**Architecture:** Add a deterministic backend evolution service that turns simulation actions into per-agent metric deltas, snapshots, and summaries. Expose the evolution state through existing simulation status APIs, then surface aggregate signals in Step 3 and inspection views in Step 5. The LLM may consume and explain evolution state, but numeric updates stay owned by backend rules.

**Tech Stack:** Python 3.11, Flask, Pydantic, pytest, Vue 3, Vite, Vitest.

---

## Task 1: Backend Evolution Domain Model

**Files:**
- Create: `futuria-v2-refatorado/backend/app/services/agent_evolution.py`
- Test: `futuria-v2-refatorado/backend/tests/services/test_agent_evolution.py`

**Step 1: Write failing tests**

Create tests for:

- default initial state has all six metrics between `0` and `1`;
- `Stable`, `Sensitive`, and `Polarizable` policies produce different delta sizes;
- every applied delta records at least one event cause;
- fixed action input produces deterministic snapshots.

Use minimal action dictionaries shaped like existing `AgentAction.to_dict()` output:

```python
def test_polarizable_policy_increases_polarization_more_than_stable():
    actions = [
        {
            "round_num": 1,
            "agent_id": 7,
            "agent_name": "Ana",
            "platform": "twitter",
            "action_type": "REPOST",
            "success": True,
            "timestamp": "2026-05-07T10:00:00",
        },
        {
            "round_num": 1,
            "agent_id": 7,
            "agent_name": "Ana",
            "platform": "twitter",
            "action_type": "QUOTE_POST",
            "success": True,
            "timestamp": "2026-05-07T10:01:00",
        },
    ]

    stable = EvolutionService(policy=EvolutionPolicy.stable()).advance_round({}, actions, round_num=1)
    polarizable = EvolutionService(policy=EvolutionPolicy.polarizable()).advance_round({}, actions, round_num=1)

    assert polarizable.snapshots[7].polarization_risk > stable.snapshots[7].polarization_risk
    assert polarizable.events
    assert all(event.causes for event in polarizable.events)
```

**Step 2: Run the failing test**

Run:

```bash
cd futuria-v2-refatorado/backend && uv run pytest tests/services/test_agent_evolution.py -q
```

Expected: fail because `agent_evolution.py` does not exist.

**Step 3: Implement domain model**

In `agent_evolution.py`, add:

- `AgentEvolutionState`;
- `AgentEvolutionEvent`;
- `AgentEvolutionSnapshot`;
- `EvolutionPolicy`;
- `EvolutionRoundResult`;
- `EvolutionService.advance_round()`;
- `summarize_evolution()`.

Keep rules simple:

- successful social actions increase `social_influence`;
- repeated same-platform actions increase `polarization_risk`;
- failed or `DO_NOTHING` actions increase `fatigue`;
- evidence-like actions such as `SEARCH_POSTS` increase `evidence_openness`;
- quote/comment/reply actions adjust `narrative_alignment`;
- clamp every metric to `0.0 <= value <= 1.0`.

**Step 4: Verify**

Run:

```bash
cd futuria-v2-refatorado/backend && uv run pytest tests/services/test_agent_evolution.py -q
```

Expected: pass.

**Step 5: Commit**

```bash
git add futuria-v2-refatorado/backend/app/services/agent_evolution.py futuria-v2-refatorado/backend/tests/services/test_agent_evolution.py
git commit -m "feat(futuria): add agent evolution domain model"
```

## Task 2: API Contract and Run State Integration

**Files:**
- Modify: `futuria-v2-refatorado/backend/app/schemas/simulation.py`
- Modify: `futuria-v2-refatorado/backend/app/services/simulation_runner.py`
- Test: `futuria-v2-refatorado/backend/tests/services/test_simulation_runner_agent_evolution.py`

**Step 1: Write failing tests**

Add tests proving:

- `SimulationRunState.to_detail_dict()` includes `agent_evolution`;
- the field is empty and well-shaped when no evolution snapshots exist;
- evolution summary includes averages and top changed agents.

**Step 2: Run failing tests**

```bash
cd futuria-v2-refatorado/backend && uv run pytest tests/services/test_simulation_runner_agent_evolution.py -q
```

Expected: fail because run state has no evolution field.

**Step 3: Extend schemas**

In `schemas/simulation.py`, add response fields to `RunStatusData`:

- `agent_evolution: Dict[str, Any] = Field(default_factory=dict)`
- `agent_evolution_enabled: bool = False`
- `agent_evolution_preset: str | None = None`

Extend `SimulationStartRequest` with:

- `enable_agent_evolution: bool = True`
- `agent_evolution_preset: str = "stable"`

Validate preset is one of `stable`, `sensitive`, `polarizable`.

**Step 4: Extend run state**

In `simulation_runner.py`:

- add `agent_evolution_enabled`;
- add `agent_evolution_preset`;
- add `agent_evolution`;
- include these fields in `to_dict()` and `to_detail_dict()`;
- load them in `_load_run_state()`;
- set them when `start_simulation()` receives the request values.

Do not change process execution behavior yet.

**Step 5: Verify**

```bash
cd futuria-v2-refatorado/backend && uv run pytest tests/services/test_simulation_runner_agent_evolution.py -q
```

Expected: pass.

**Step 6: Commit**

```bash
git add futuria-v2-refatorado/backend/app/schemas/simulation.py futuria-v2-refatorado/backend/app/services/simulation_runner.py futuria-v2-refatorado/backend/tests/services/test_simulation_runner_agent_evolution.py
git commit -m "feat(futuria): expose agent evolution run state"
```

## Task 3: Evolution Calculation During Simulation Monitoring

**Files:**
- Modify: `futuria-v2-refatorado/backend/app/services/simulation_runner.py`
- Test: `futuria-v2-refatorado/backend/tests/services/test_simulation_runner_agent_evolution.py`

**Step 1: Add failing test**

Test that after mocked actions are available, the monitor/update path writes:

- per-agent snapshots;
- event causes;
- aggregate averages;
- largest changed agents.

**Step 2: Run failing test**

```bash
cd futuria-v2-refatorado/backend && uv run pytest tests/services/test_simulation_runner_agent_evolution.py -q
```

Expected: fail because snapshots are not calculated.

**Step 3: Implement update helper**

In `SimulationRunner`, add a private helper:

```python
@classmethod
def _update_agent_evolution(cls, state: SimulationRunState) -> None:
    if not state.agent_evolution_enabled:
        return
    actions = [a.to_dict() for a in cls.get_all_actions(state.simulation_id)]
    policy = EvolutionPolicy.from_name(state.agent_evolution_preset or "stable")
    result = EvolutionService(policy=policy).advance_all_rounds(actions)
    state.agent_evolution = result.to_dict()
```

Call it after action counts are refreshed in the monitoring path and before saving state.

**Step 4: Verify**

```bash
cd futuria-v2-refatorado/backend && uv run pytest tests/services/test_agent_evolution.py tests/services/test_simulation_runner_agent_evolution.py -q
```

Expected: pass.

**Step 5: Commit**

```bash
git add futuria-v2-refatorado/backend/app/services/simulation_runner.py futuria-v2-refatorado/backend/tests/services/test_simulation_runner_agent_evolution.py
git commit -m "feat(futuria): calculate agent evolution from simulation actions"
```

## Task 4: Frontend API and Step 3 Aggregate Panel

**Files:**
- Modify: `futuria-v2-refatorado/frontend/src/api/simulation.js`
- Modify: `futuria-v2-refatorado/frontend/src/components/Step3Simulation.vue`
- Create: `futuria-v2-refatorado/frontend/src/components/simulation/AgentEvolutionSummary.vue`
- Modify: `futuria-v2-refatorado/frontend/tests/mocks/simulationState.js`
- Test: `futuria-v2-refatorado/frontend/tests/components/simulation/AgentEvolutionSummary.test.js`
- Test: `futuria-v2-refatorado/frontend/tests/components/Step3Simulation.test.js`

**Step 1: Write failing component tests**

Test `AgentEvolutionSummary` renders:

- average fatigue;
- average polarization;
- average narrative alignment;
- largest changed agents;
- empty state when `agent_evolution` is missing.

**Step 2: Run failing tests**

```bash
cd futuria-v2-refatorado/frontend && npm run test -- AgentEvolutionSummary.test.js Step3Simulation.test.js
```

Expected: fail because the component does not exist.

**Step 3: Add mock data**

Extend `frontend/tests/mocks/simulationState.js` with:

```js
export const mockAgentEvolution = {
  enabled: true,
  preset: 'stable',
  averages: {
    fatigue: 0.22,
    polarization_risk: 0.31,
    narrative_alignment: 0.57,
  },
  top_changed_agents: [
    { agent_id: 1, agent_name: 'Alice', change_score: 0.42 },
  ],
}
```

Attach it to `mockRunningState.agent_evolution`.

**Step 4: Build the component**

Create `AgentEvolutionSummary.vue` with a compact, unframed panel:

- three metric rows;
- one small list of changed agents;
- `role="status"` for empty/loading states;
- no nested cards.

**Step 5: Mount in Step 3**

In `Step3Simulation.vue`, import the component and render it above `SimMonitorTabs`:

```vue
<AgentEvolutionSummary :evolution="state?.agent_evolution" />
```

**Step 6: Verify**

```bash
cd futuria-v2-refatorado/frontend && npm run test -- AgentEvolutionSummary.test.js Step3Simulation.test.js
```

Expected: pass.

**Step 7: Commit**

```bash
git add futuria-v2-refatorado/frontend/src/components/Step3Simulation.vue futuria-v2-refatorado/frontend/src/components/simulation/AgentEvolutionSummary.vue futuria-v2-refatorado/frontend/tests/mocks/simulationState.js futuria-v2-refatorado/frontend/tests/components/simulation/AgentEvolutionSummary.test.js futuria-v2-refatorado/frontend/tests/components/Step3Simulation.test.js
git commit -m "feat(futuria): show agent evolution during simulation"
```

## Task 5: Step 5 Agent Evolution Inspection

**Files:**
- Modify: `futuria-v2-refatorado/frontend/src/components/Step5Interaction.vue`
- Create: `futuria-v2-refatorado/frontend/src/components/simulation/AgentEvolutionInspector.vue`
- Test: `futuria-v2-refatorado/frontend/tests/components/AgentEvolutionInspector.test.js`
- Test: `futuria-v2-refatorado/frontend/tests/components/Step5Interaction.test.js`

**Step 1: Write failing tests**

Test that the inspector renders:

- most influenced agents;
- most influential agents;
- most polarized agents;
- per-agent metric timeline;
- "sem evidencia suficiente" empty state when snapshots are absent.

**Step 2: Run failing tests**

```bash
cd futuria-v2-refatorado/frontend && npm run test -- AgentEvolutionInspector.test.js Step5Interaction.test.js
```

Expected: fail because the inspector is missing.

**Step 3: Add inspector component**

Create `AgentEvolutionInspector.vue` with props:

```js
const props = defineProps({
  evolution: {
    type: Object,
    default: () => ({}),
  },
})
```

Keep it read-only. Render rankings and timeline from the backend payload; do not recompute business metrics in the UI.

**Step 4: Add Step 5 tab**

In `Step5Interaction.vue`, add a dashboard tab key `evolution` labeled "Evolucao dos Agentes" and render `AgentEvolutionInspector` when active.

Use existing tab styling. Avoid creating a second tab system.

**Step 5: Verify**

```bash
cd futuria-v2-refatorado/frontend && npm run test -- AgentEvolutionInspector.test.js Step5Interaction.test.js
```

Expected: pass.

**Step 6: Commit**

```bash
git add futuria-v2-refatorado/frontend/src/components/Step5Interaction.vue futuria-v2-refatorado/frontend/src/components/simulation/AgentEvolutionInspector.vue futuria-v2-refatorado/frontend/tests/components/AgentEvolutionInspector.test.js futuria-v2-refatorado/frontend/tests/components/Step5Interaction.test.js
git commit -m "feat(futuria): add agent evolution inspection tab"
```

## Task 6: Report Evidence Contract

**Files:**
- Modify: `futuria-v2-refatorado/backend/app/services/report_agent.py`
- Modify: `futuria-v2-refatorado/backend/app/services/report_orchestrator.py`
- Test: `futuria-v2-refatorado/tests/backend/test_report_agent_tool_parsing.py`

**Step 1: Write failing report test**

Add a test that a report section about agent evolution includes cited event causes and does not claim change when evidence is empty.

**Step 2: Run failing test**

```bash
cd futuria-v2-refatorado && pytest tests/backend/test_report_agent_tool_parsing.py -q
```

Expected: fail until report prompt/context includes evolution evidence rules.

**Step 3: Pass evolution evidence to report context**

In the report orchestration path:

- load run state by `simulation_id`;
- extract `agent_evolution`;
- pass a compact `agent_evolution_summary` into report generation context.

In `report_agent.py`, add prompt instruction:

- cite event causes for any behavioral-change claim;
- if `agent_evolution` is missing or empty, say evidence is insufficient;
- do not infer psychological change from persona alone.

**Step 4: Verify**

```bash
cd futuria-v2-refatorado && pytest tests/backend/test_report_agent_tool_parsing.py -q
```

Expected: pass.

**Step 5: Commit**

```bash
git add futuria-v2-refatorado/backend/app/services/report_agent.py futuria-v2-refatorado/backend/app/services/report_orchestrator.py futuria-v2-refatorado/tests/backend/test_report_agent_tool_parsing.py
git commit -m "feat(futuria): ground reports in agent evolution evidence"
```

## Task 7: Final Regression

**Files:**
- Modify only if failures reveal real defects.

**Step 1: Run backend tests**

```bash
cd futuria-v2-refatorado/backend && uv run pytest -q
```

Expected: pass.

**Step 2: Run frontend tests**

```bash
cd futuria-v2-refatorado/frontend && npm run test
```

Expected: pass.

**Step 3: Build frontend**

```bash
cd futuria-v2-refatorado/frontend && npm run build
```

Expected: build succeeds.

**Step 4: Run project preflight**

```bash
cd futuria-v2-refatorado && npm run preflight
```

Expected: language/reporting checks pass.

**Step 5: Commit any regression fixes**

Only if files changed:

```bash
git add <changed-files>
git commit -m "fix(futuria): stabilize agent evolution regression checks"
```

## Execution Notes

- Keep backend metric updates deterministic and clamped.
- Do not let LLM output set numeric evolution values.
- Do not add per-agent manual tuning in the first version.
- Keep UI copy in the existing locale system if the touched components already use i18n keys.
- Preserve existing simulation monitor behavior and polling intervals.
- Do not modify root-level files.
