# Agent Evolution Design

**Date:** 2026-05-07
**Status:** Approved
**Scope:** Backend evolution model, simulation integration, Step 3/Step 5 visibility, and report usage.

---

## Goal

Add controlled agent evolution to FUTUR.IA so simulated agents can change during a run while remaining auditable, reproducible, and explainable.

The first version should favor analytical control over autonomous realism. Agent behavior changes through explicit metrics and recorded causes, not through opaque LLM judgment.

## Product Direction

Each agent gets a behavioral state that evolves by simulation round. The state is represented by explicit metrics:

- `trust_level`: how much the agent trusts received information.
- `narrative_alignment`: how closely the agent aligns with the dominant narrative or scenario hypothesis.
- `fatigue`: wear caused by excessive exposure, conflict, or interaction volume.
- `evidence_openness`: willingness to update position based on evidence.
- `social_influence`: ability to influence other agents.
- `polarization_risk`: tendency to become more extreme or isolated inside a cluster.

The final product value is explainability. Reports should be able to say why an agent changed by pointing to simulation evidence, such as repeated exposure, credible interaction, contradiction, cluster isolation, or influence from another agent.

## User Flow

### Step 2: Configuration

Add an agent evolution option to the simulation setup. It should be enabled by default and controlled through presets:

- `Stable`: agents change slowly; best for controlled simulations.
- `Sensitive`: agents react more strongly to evidence and social influence.
- `Polarizable`: agents are more susceptible to cluster effects, fatigue, and radicalization.

The user should not need to edit per-metric values in the first version.

### Step 3: Execution

Show aggregate evolution signals while the simulation runs:

- average fatigue;
- average polarization risk;
- average narrative alignment;
- agents with the largest behavioral change.

This panel should stay simple and operational, not diagnostic-heavy.

### Step 5: Inspection

Add an "Agent Evolution" inspection view with:

- most influenced agents;
- most influential agents;
- most polarized agents;
- largest position changes;
- per-agent metric timeline.

## Backend Model

Introduce an explicit evolution layer:

- `AgentEvolutionState`: current metric values for one agent.
- `AgentEvolutionEvent`: the cause of a metric change.
- `AgentEvolutionSnapshot`: consolidated state for a round.
- `EvolutionPolicy`: preset rules used to calculate deltas.

The simulation flow should be:

1. Start with initial metrics derived from the persona.
2. Collect actions, replies, exposures, and interactions during each round.
3. Use `EvolutionService` to calculate metric deltas from deterministic rules.
4. Store events and round snapshots.
5. Pass the updated state into the next agent prompt as behavioral context.
6. Use snapshots and events in Step 5 and the final report.

## AI Boundaries

The LLM can use the current evolution state to make an agent act consistently. It can also help explain trajectories after the simulation.

The LLM must not own numeric metric updates. Numeric updates belong to backend rules so the result remains auditable and reproducible.

## Quality Rules

- Every numeric change must have a recorded cause.
- The same scenario with the same seed should produce reproducible evolution.
- Reports must not claim psychological change without simulation evidence.
- Presets must have visible behavioral differences.
- When evidence is insufficient, the system should say so instead of inventing a trajectory.

## Testing

Required tests:

- unit tests for metric delta rules;
- contract tests for events and snapshots;
- regression test with a fixed seed and expected evolution;
- report test ensuring explanations cite real events;
- UI tests for Step 3 and Step 5 when evolution data is present or absent.

## Non-Goals

- Free-form autonomous psychological evolution.
- Per-agent manual metric editing in the first version.
- Replacing existing persona generation.
- Making report explanations without traceable simulation events.
