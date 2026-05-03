# BETA Privacy Gaps Audit

**Scope:** `backend/app/api/report.py`, `backend/app/api/simulation.py`, `backend/app/api/graph.py`  
**Date:** 2026-05-02  
**Agent:** Kimi Code CLI  

## Methodology
1. Read every endpoint in the three API files.
2. Check for ownership / auth validation (user can only access their own simulation, report, project).
3. Check whether responses exclude sensitive fields: `llm_raw_response`, `prompt_text`, `traceback`, `internal_metadata`.
4. Verify with `grep -i traceback backend/app/api/*.py` that no endpoint returns raw traceback.

## Ownership / Auth Findings

| File | Endpoint | Method | Ownership Validated | Risk |
|------|----------|--------|---------------------|------|
| `report.py:38` | `/generate` | POST | **GAP** | No user_id / Convex auth check. Any client can trigger report generation for any simulation_id. |
| `report.py:258` | `/<report_id>` | GET | **GAP** | No ownership check. Any client can fetch any report by ID. |
| `report.py:296` | `/by-simulation/<simulation_id>` | GET | **GAP** | No ownership check. Any client can fetch a report via simulation_id. |
| `report.py:331` | `/list` | GET | **GAP** | No auth filter by user. Lists all reports (or any simulation_id provided). |
| `report.py:372` | `/<report_id>/download` | GET | **GAP** | No ownership check before sending file. |
| `report.py:417` | `/<report_id>` | DELETE | **GAP** | No ownership check. Any client can delete any report. |
| `report.py:882` | `/<report_id>/agent-log` | GET | **GAP** | No ownership check. Returns raw agent log entries. |
| `report.py:977` | `/<report_id>/console-log` | GET | **GAP** | No ownership check. Returns raw console log lines. |
| `simulation.py:63` | `/entities/<graph_id>` | GET | **GAP** | No auth. Any client can list entities of any graph. |
| `simulation.py:184` | `/create` | POST | **GAP** | No user_id check. Any client can create a simulation for any project_id. |
| `simulation.py:624` | `/<simulation_id>` | GET | **GAP** | No ownership check. Returns full simulation state. |
| `simulation.py:717` | `/list` | GET | **GAP** | No auth. Lists all simulations (optionally filtered by project_id without ownership). |
| `simulation.py:799` | `/<simulation_id>/profiles` | GET | **GAP** | No ownership check. Returns agent profiles. |
| `simulation.py:1657` | `/<simulation_id>/actions` | GET | **GAP** | No ownership check. Returns simulation action history. |
| `simulation.py:1780` | `/<simulation_id>/posts` | GET | **GAP** | No ownership check. Returns SQLite posts. |
| `simulation.py:1855` | `/<simulation_id>/comments` | GET | **GAP** | No ownership check. Returns SQLite comments. |
| `graph.py:37` | `/project/<project_id>` | GET | **GAP** | No ownership check. Returns project details. |
| `graph.py:56` | `/project/list` | GET | **GAP** | No auth. Lists all projects. |
| `graph.py:71` | `/project/<project_id>` | DELETE | **GAP** | No ownership check. Any client can delete any project. |
| `graph.py:527` | `/data/<graph_id>` | GET | **GAP** | No auth. Returns full graph node/edge data. |
| `graph.py:567` | `/info/<graph_id>` | GET | **GAP** | No auth. Returns graph metadata. |

## Sensitive-Field Findings

| File | Endpoint | `llm_raw_response` | `prompt_text` | `traceback` | `internal_metadata` |
|------|----------|--------------------|---------------|-------------|---------------------|
| `report.py:258` | `GET /<report_id>` | OK – not in `Report.to_dict()` | OK – not in model | OK – not returned | OK – not in model |
| `report.py:882` | `GET /<report_id>/agent-log` | OK – not currently logged | OK – not currently logged | **POTENTIAL GAP** – raw JSONL returned unfiltered; if future code logs traceback, it will leak. | OK – not currently logged |
| `report.py:977` | `GET /<report_id>/console-log` | OK – plain text logs do not contain it | OK – plain text logs do not contain it | **POTENTIAL GAP** – raw text returned unfiltered; future traceback logging would leak. | OK – not in text logs |
| `simulation.py:624` | `GET /<simulation_id>` | OK – not in `SimulationState.to_dict()` | OK – not in model | OK – not returned | OK – not in model |
| `graph.py:37` | `GET /project/<project_id>` | OK – not in `Project.to_dict()` | OK – not in model | OK – not returned | OK – not in model |

### Traceback Verification
`grep -i traceback backend/app/api/*.py` returned **zero matches**.  
`backend/app/utils/response.py:23` explicitly states: *"NUNCA inclui traceback na resposta HTTP."*  
Therefore **no endpoint currently returns `traceback` to the client**.

## Mitigation Recommendations

1. **Add ownership middleware** – Every mutating and data-export endpoint must verify that the authenticated user (e.g., via Convex auth token or session) owns the requested `simulation_id`, `report_id`, or `project_id`.
2. **Filter logs at read time** – `agent-log` and `console-log` endpoints should strip or redact any lines containing `traceback`, `llm_raw_response`, `prompt_text`, or `internal_metadata` before returning them to the client.
3. **Project-level ACL** – Store `owner_user_id` in `Project` (and propagate to `Simulation` / `Report`) and enforce it in `ProjectManager`, `SimulationManager`, and `ReportManager`.
4. **Audit other blueprints** – Extend this audit to `research.py`, `health.py`, and `observability.py` before public beta launch.
