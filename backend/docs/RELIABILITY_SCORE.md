# Reliability Score

## Overview

The reliability score is a composite metric (0.0 – 1.0) that measures how well a FUTUR.IA pipeline run (graph → simulation → report) meets quality expectations. It is computed automatically after report generation and exposed via `POST /api/report/generate/status`.

## Formula

```
total_score = (structural + semantic + content + completeness) / 4
```

Each pillar is scored independently on a 0.0 – 1.0 scale:

| Pillar        | Weight | What it measures                                           |
|---------------|--------|------------------------------------------------------------|
| structural    | 25 %   | Graph quality (unknown-entity rate, node/edge counts)     |
| semantic      | 25 %   | Simulation depth (hours, actions, rounds completed)       |
| content       | 25 %   | Report structure (sections, summary, word count, language)|
| completeness  | 25 %   | Whether all 3 stages produced non-empty output            |

## Thresholds

| Gate                  | Threshold | Consequence when failed                        |
|-----------------------|-----------|------------------------------------------------|
| Total score           | ≥ 0.75    | `beta_ready: false` in status response         |
| Any individual pillar | ≥ 0.60    | Same; the specific pillar is listed in `warnings` |

## Interpretation Examples

### Score 0.92 — Ready for beta
- All pillars above 0.80
- Graph has low unknown rate, simulation ran for several hours, report is well-structured and in Portuguese
- `beta_ready: true`, `warnings: []`

### Score 0.68 — Below threshold
- Content pillar at 0.55 because the report contains exposed thinking process (`<think>` tags)
- Total is dragged down and the pillar minimum fails
- `beta_ready: false`, `warnings: ["content_pillar (0.55 < 0.60)"]`

### Score 0.45 — Multiple structural failures
- Empty report (`content = 0`), `simulated_hours = 0` (`semantic = 0`)
- Both total and pillar gates fail
- `beta_ready: false`, `warnings: ["total_score (0.45 < 0.75)", "semantic_pillar (0.00 < 0.60)", "content_pillar (0.00 < 0.60)"]`

## How to Add a New Scenario

1. **Create fixture files** under `backend/tests/fixtures/scenarios/`:
   - `<name>.py` — scenario definition
   - `snapshots/<name>/graph_snapshot.json`
   - `snapshots/<name>/simulation_snapshot.json`
   - `snapshots/<name>/report_snapshot.json`

2. **Register the fixture** in `backend/tests/fixtures/scenarios/loader.py`:
   ```python
   from .<name> import <NAME>_FIXTURE
   SCENARIOS["<name>"] = <NAME>_FIXTURE
   ```

3. **Run regression tests** to verify the ideal snapshot passes beta:
   ```bash
   cd backend && uv run pytest tests/services/test_reliability_scorer_regression.py -q
   ```

4. **Add failure-mode tests** (optional) if the scenario has unique risk patterns (e.g. high unknown rate, specific contamination).

## API Response Format

When report generation is `completed`, the status endpoint includes:

```json
{
  "success": true,
  "data": {
    "status": "completed",
    "reliability_score": 0.92,
    "reliability_report": {
      "total_score": 0.92,
      "pillar_scores": {
        "structural": 0.85,
        "semantic": 0.95,
        "content": 0.90,
        "completeness": 1.00
      },
      "gates_passed": ["total_score", "structural_pillar", ...],
      "gates_failed": []
    },
    "beta_ready": true,
    "warnings": []
  }
}
```

If beta is not met:

```json
{
  "status": "completed",
  "reliability_score": 0.68,
  "reliability_report": { ... },
  "beta_ready": false,
  "warnings": ["content_pillar (0.55 < 0.60)"]
}
```
