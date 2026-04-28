"""
Deep Research API Blueprint.

Provides endpoints to:
  POST /research/start       — kick off an async research run
  GET  /research/status/<id> — poll for status + progress
  GET  /research/result/<id> — retrieve the completed markdown artifact

All background work runs in a daemon thread, mirroring the pattern from graph.py.
"""

from __future__ import annotations

import logging
import os
import threading
from datetime import datetime
from flask import Blueprint, request, jsonify

from . import research_bp
from ..models.research_run import ResearchRunManager, ResearchRunStatus
from ..models.project import ProjectManager, ProjectStatus
from ..models.task import TaskManager, TaskStatus
from ..services.deep_research_agent import (
    compile_research_graph,
    validate_artifact,
    write_draft,
)
from ..utils.locale import get_locale, set_locale
from ..utils.logger import get_logger
from ..profiles import ProfileManager

logger = get_logger("futuria.api.research")

# Progress checkpoints per graph phase
_PHASE_PROGRESS = {
    "searching": 20,
    "extracting": 40,
    "summarizing": 60,
    "formatting": 80,
    "completed": 100,
}


def _current_progress(status: str) -> int:
    """Map a graph-phase status string to a 0-100 progress value."""
    return _PHASE_PROGRESS.get(status, 0)


# ─── Background worker ─────────────────────────────────────────────────────────

def _research_task(
    run_id: str,
    task_id: str,
    query: str,
    profile_suffix: str = "",
) -> None:
    """
    Background thread entry point.

    Follows the same daemon-thread + locale-capture pattern as build_task()
    in graph.py.
    """
    try:
        # Set locale captured at request time
        logger.debug(f"[research:{run_id}] Thread starting, locale set")
    except Exception:
        pass

    research_logger = get_logger("futuria.research")

    # Append profile-specific deep research suffix to query if provided
    enriched_query = query
    if profile_suffix:
        enriched_query = f"{query} {profile_suffix}"
        research_logger.info(f"[research:{run_id}] Query enriched with profile suffix")

    try:
        # 1. Mark both run and task as running
        ResearchRunManager().update_run(run_id, status=ResearchRunStatus.RUNNING)
        TaskManager().update_task(
            task_id,
            status=TaskStatus.PROCESSING,
            message="Starting research pipeline",
            progress=5,
        )

        research_logger.info(f"[research:{run_id}] Pipeline started query_len={len(enriched_query)}")

        # 2. Compile and invoke the graph
        graph = compile_research_graph()

        initial_state = {
            "query": enriched_query,
            "search_results": [],
            "claims": "",
            "summary": "",
            "sources": "",
            "status": "searching",
            "error": "",
            "retry_count": 0,
        }

        # Stream through graph to update progress on phase transitions
        connector_used = "none"
        prev_status = "searching"
        final_state: dict[str, object] = dict(initial_state)

        try:
            for state in graph.stream(initial_state):
                # Extract the most recent phase status from the streamed state values
                for node_name, node_state in state.items():
                    if isinstance(node_state, dict) and "status" in node_state:
                        current_status = node_state.get("status", prev_status)
                    else:
                        current_status = prev_status

                    if current_status != prev_status:
                        progress = _current_progress(current_status)
                        TaskManager().update_task(
                            task_id,
                            progress=progress,
                            message=f"Phase: {current_status}",
                            progress_detail={
                                "phase": current_status,
                                "node": node_name,
                            },
                        )
                        research_logger.info(
                            f"[research:{run_id}] Phase transition: "
                            f"{prev_status} -> {current_status} progress={progress}"
                        )
                        prev_status = current_status

                    # Flatten node outputs into one accumulated state snapshot.
                    # LangGraph stream chunks are keyed by node name, but later
                    # logic expects top-level summary/claims/sources fields.
                    if isinstance(node_state, dict):
                        final_state.update(node_state)

                    # Capture connector used after search completes
                    if isinstance(node_state, dict):
                        cu = node_state.get("connector_used", "")
                        if cu and cu != "none":
                            connector_used = cu

        except Exception as e:
            research_logger.warning(
                f"[research:{run_id}] Graph stream error: {e}"
            )
            raise

        # Re-fetch the run to get the latest status
        run = ResearchRunManager().get_run(run_id)
        if run and run.status == ResearchRunStatus.FAILED:
            research_logger.info(f"[research:{run_id}] Run was marked FAILED by graph, aborting write")
            return

        # 4. Extract results from final state
        summary = (
            final_state.get("summary", "")
            if isinstance(final_state, dict)
            else ""
        )
        claims = (
            final_state.get("claims", "")
            if isinstance(final_state, dict)
            else ""
        )
        sources = (
            final_state.get("sources", "")
            if isinstance(final_state, dict)
            else ""
        )
        final_status = (
            final_state.get("status", "completed")
            if isinstance(final_state, dict)
            else "completed"
        )
        final_error = (
            final_state.get("error", "")
            if isinstance(final_state, dict)
            else ""
        )

        if final_status == "failed" or not summary:
            research_logger.warning(
                f"[research:{run_id}] Research failed: {final_error}"
            )
            ResearchRunManager().fail_run(run_id, error=final_error or "Research failed")
            TaskManager().fail_task(task_id, error=final_error or "Research failed")
            return

        # 5. Validate artifact structure
        tmp_markdown = (
            f"# Deep Research: {query}\n\n"
            f"## Summary\n{summary}\n\n"
            f"## Claims\n{claims}\n\n"
            f"## Sources\n{sources}"
        )
        if not validate_artifact(tmp_markdown, run_id):
            research_logger.warning(f"[research:{run_id}] Artifact validation failed, skipping write")
            TaskManager().fail_task(task_id, error="Artifact validation failed")
            return

        # 6. Write draft to disk
        draft_path = write_draft(
            run_id=run_id,
            query=query,
            summary=summary,
            claims=claims,
            sources=sources,
            connector_used=connector_used,
        )

        # 7. Mark complete
        ResearchRunManager().complete_run(run_id, artifact_path=draft_path, connector_used=connector_used)
        TaskManager().update_task(
            task_id,
            status=TaskStatus.COMPLETED,
            progress=100,
            message="Research complete",
            result={
                "run_id": run_id,
                "artifact_path": draft_path,
                "connector_used": connector_used,
            },
            progress_detail={"connector_used": connector_used},
        )

        research_logger.info(
            f"[research:{run_id}] Research completed connector={connector_used}"
        )

    except Exception as e:
        import traceback

        research_logger.error(
            f"[research:{run_id}] Unhandled exception in research task: {e}\n"
            f"{traceback.format_exc()}"
        )
        ResearchRunManager().fail_run(run_id, error=str(e))
        TaskManager().fail_task(task_id, error=str(e))


# ─── HTTP Endpoints ────────────────────────────────────────────────────────────

@research_bp.route("/start", methods=["POST"])
def start_research():
    """
    POST /research/start

    Body (JSON):
        query: str           — research query string
        project_id?: str     — optional project association
        profile?: str        — optional profile (marketing, direito, economia, saude, generico)

    Returns:
        {run_id, task_id}
    """
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        data = {}

    query = data.get("query", "").strip()
    project_id = data.get("project_id")
    profile_name = data.get("profile", "generico")

    if not query:
        return jsonify({
            "success": False,
            "error": "query is required",
        }), 400

    # Get profile configuration
    profile = ProfileManager.get_profile_or_default(profile_name)
    profile_suffix = profile.deep_research_prompt_suffix

    # 1. Create research run
    run = ResearchRunManager().create_run(
        query=query,
        metadata={
            "project_id": project_id,
            "profile": profile.profile_type.value,
        } if project_id else {"profile": profile.profile_type.value},
    )

    # 2. Create background task
    task_manager = TaskManager()
    task_id = task_manager.create_task(
        task_type="deep_research",
        metadata={"run_id": run.run_id, "query": query, "profile": profile.profile_type.value},
    )
    task_manager.update_task(
        task_id,
        progress=0,
        message="Research queued",
    )

    # 3. Update run with task_id
    ResearchRunManager().update_run(run.run_id, task_id=task_id)

    # 4. Capture locale before spawning daemon thread
    current_locale = get_locale()

    def background_wrapper():
        set_locale(current_locale)
        _research_task(run.run_id, task_id, query, profile_suffix=profile_suffix)

    thread = threading.Thread(target=background_wrapper, daemon=True)
    thread.start()

    logger.info(f"[research:{run.run_id}] Started task={task_id} query={query!r} profile={profile.profile_type.value}")

    return jsonify({
        "success": True,
        "data": {
            "run_id": run.run_id,
            "task_id": task_id,
            "profile": profile.profile_type.value,
        },
    })


@research_bp.route("/status/<run_id>", methods=["GET"])
def get_research_status(run_id: str):
    """
    GET /research/status/<run_id>

    Returns merged state from ResearchRun and TaskManager.
    """
    run = ResearchRunManager().get_run(run_id)
    if not run:
        return jsonify({
            "success": False,
            "error": f"Run not found: {run_id}",
        }), 404

    task = TaskManager().get_task(run.task_id) if run.task_id else None

    return jsonify({
        "success": True,
        "data": {
            "run_id": run.run_id,
            "query": run.query,
            "status": run.status.value,
            "progress": task.progress if task else 0,
            "message": task.message if task else "",
            "connector_used": run.connector_used or "",
            "task_id": run.task_id,
            "error": run.metadata.get("error", "") if run.metadata else "",
            "created_at": run.created_at,
            "updated_at": run.updated_at,
        },
    })


@research_bp.route("/result/<run_id>", methods=["GET"])
def get_research_result(run_id: str):
    """
    GET /research/result/<run_id>

    Returns the markdown artifact if the run is COMPLETED, else 404.
    """
    run = ResearchRunManager().get_run(run_id)
    if not run:
        return jsonify({
            "success": False,
            "error": f"Run not found: {run_id}",
        }), 404

    if run.status != ResearchRunStatus.COMPLETED:
        return jsonify({
            "success": False,
            "error": f"Run not complete. Current status: {run.status.value}",
        }), 404

    draft_path = ResearchRunManager._get_draft_path(run_id)

    try:
        with open(draft_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return jsonify({
            "success": False,
            "error": "Artifact file not found on disk",
        }), 404
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error reading artifact: {e}",
        }), 500

    return jsonify({
        "success": True,
        "data": {
            "run_id": run.run_id,
            "query": run.query,
            "connector_used": run.connector_used or "",
            "markdown": content,
        },
    })


@research_bp.route("/approve/<run_id>", methods=["POST"])
def approve_research_run(run_id: str):
    """
    POST /research/approve/<run_id>

    Approve a completed research run. Fail-closed validation ensures
    the draft.md exists on disk and has all required sections.

    Returns:
        {success, data: {run_id, status, approved_at}}
        or {success: False, error: ...}
    """
    run = ResearchRunManager().get_run(run_id)
    if not run:
        return jsonify({
            "success": False,
            "error": f"Run not found: {run_id}",
        }), 404

    if run.status != ResearchRunStatus.COMPLETED:
        return jsonify({
            "success": False,
            "error": f"Can only approve completed runs. Current status: {run.status.value}",
        }), 400

    # Fail-closed: validate draft.md exists and has required sections
    draft_path = ResearchRunManager._get_draft_path(run_id)
    if not os.path.exists(draft_path):
        logger.warning(f"[research:{run_id}] Approve failed: draft.md not found")
        ResearchRunManager().fail_run(run_id, error="Artifact missing from disk")
        return jsonify({
            "success": False,
            "error": "Artifact missing from disk",
        }), 400

    try:
        with open(draft_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        logger.warning(f"[research:{run_id}] Approve failed: cannot read draft.md: {e}")
        ResearchRunManager().fail_run(run_id, error=f"Cannot read artifact: {e}")
        return jsonify({
            "success": False,
            "error": f"Cannot read artifact: {e}",
        }), 500

    # Validate structure
    required_sections = ["Summary", "Claims", "Sources"]
    import re
    missing = []
    for section in required_sections:
        pattern = rf"(?i)^##\s+{section}\s*$"
        match = re.search(pattern, content, re.MULTILINE)
        if not match:
            missing.append(section)
            continue
        # Find the next heading or end of file
        # Look for next ## heading after current section
        start = match.end()
        # Find the pattern \n## which marks the start of next section
        next_heading_match = re.search(r"\n##\s+", content[start:])
        if next_heading_match:
            # Get content between current heading end and next heading start
            section_end = start + next_heading_match.start()
        else:
            section_end = len(content)
        
        section_body = content[start:section_end]
        # Skip the leading newline and get actual content
        section_body = section_body.lstrip('\n')
        # Strip blank lines and check for actual content
        lines = section_body.strip().split('\n')
        content_lines = [line.strip() for line in lines if line.strip()]
        if not content_lines:
            missing.append(section)

    if missing:
        logger.warning(f"[research:{run_id}] Approve failed: missing sections: {missing}")
        ResearchRunManager().fail_run(run_id, error=f"Missing sections: {', '.join(missing)}")
        return jsonify({
            "success": False,
            "error": f"Artifact is incomplete. Missing sections: {', '.join(missing)}",
        }), 400

    # Approve the run
    if not ResearchRunManager().approve_run(run_id):
        return jsonify({
            "success": False,
            "error": "Failed to approve run",
        }), 500

    logger.info(f"[research:{run_id}] Run approved")
    return jsonify({
        "success": True,
        "data": {
            "run_id": run_id,
            "status": "approved",
            "approved_at": datetime.now().isoformat(),
        },
    })


@research_bp.route("/reject/<run_id>", methods=["POST"])
def reject_research_run(run_id: str):
    """
    POST /research/reject/<run_id>

    Reject a research run and reset it to PENDING for reprocessing.

    Returns:
        {success, data: {run_id, status, rejected_at}}
    """
    run = ResearchRunManager().get_run(run_id)
    if not run:
        return jsonify({
            "success": False,
            "error": f"Run not found: {run_id}",
        }), 404

    if not ResearchRunManager().reject_run(run_id):
        return jsonify({
            "success": False,
            "error": "Failed to reject run",
        }), 500

    logger.info(f"[research:{run_id}] Run rejected, reset to pending")
    return jsonify({
        "success": True,
        "data": {
            "run_id": run_id,
            "status": "pending",
            "rejected_at": datetime.now().isoformat(),
        },
    })


@research_bp.route("/promote/<run_id>", methods=["POST"])
def promote_research_to_project(run_id: str):
    """
    POST /research/promote/<run_id>

    Copies the approved draft.md into the project's extracted_text.txt.
    If the project already has text, prepends with a header separator.

    Body (JSON):
        project_id?: str    — target project (creates new if omitted)

    Returns:
        {success, data: {run_id, project_id, promoted_char_count, merge_mode}}
    """
    run = ResearchRunManager().get_run(run_id)
    if not run:
        return jsonify({
            "success": False,
            "error": f"Run not found: {run_id}",
        }), 404

    if run.status != ResearchRunStatus.APPROVED:
        return jsonify({
            "success": False,
            "error": f"Can only promote approved runs. Current status: {run.status.value}",
        }), 400

    # Read the approved draft
    draft_path = ResearchRunManager._get_draft_path(run_id)
    try:
        with open(draft_path, "r", encoding="utf-8") as f:
            research_content = f.read()
    except FileNotFoundError:
        return jsonify({
            "success": False,
            "error": "Artifact file not found on disk",
        }), 404
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error reading artifact: {e}",
        }), 500

    data = request.get_json(force=True) or {}
    project_id = data.get("project_id")

    merge_mode = "append"  # default
    promoted_char_count = len(research_content)

    if project_id:
        project = ProjectManager.get_project(project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": f"Project not found: {project_id}",
            }), 404

        # Check if project already has extracted text
        existing_text = ProjectManager.get_extracted_text(project_id)
        if existing_text and existing_text.strip():
            # Append: existing text + separator + research
            separator = "\n\n# Research Promotion\n\n"
            new_text = existing_text + separator + research_content
            merge_mode = "append"
        else:
            new_text = research_content
            merge_mode = "new"

        ProjectManager.save_extracted_text(project_id, new_text)
    else:
        # Create new project from research
        project = ProjectManager.create_project(name=f"Research: {run.query[:80]}")
        ProjectManager.save_extracted_text(project.project_id, research_content)
        project_id = project.project_id
        merge_mode = "created"

    logger.info(
        f"[research:{run_id}] Promoted to project_id={project_id} "
        f"chars={promoted_char_count} mode={merge_mode}"
    )

    return jsonify({
        "success": True,
        "data": {
            "run_id": run_id,
            "project_id": project_id,
            "promoted_char_count": promoted_char_count,
            "merge_mode": merge_mode,
        },
    })


@research_bp.route("/create-project/<run_id>", methods=["POST"])
def create_project_from_research(run_id: str):
    """
    POST /research/create-project/<run_id>

    Creates a new project from approved research.
    Saves research markdown as extracted_text.txt and sets
    a stub ontology.

    Returns:
        {success, data: {run_id, project_id, project_name}}
    """
    run = ResearchRunManager().get_run(run_id)
    if not run:
        return jsonify({
            "success": False,
            "error": f"Run not found: {run_id}",
        }), 404

    if run.status != ResearchRunStatus.APPROVED:
        return jsonify({
            "success": False,
            "error": f"Can only create project from approved runs. Current status: {run.status.value}",
        }), 400

    # Read the approved draft
    draft_path = ResearchRunManager._get_draft_path(run_id)
    try:
        with open(draft_path, "r", encoding="utf-8") as f:
            research_content = f.read()
    except FileNotFoundError:
        return jsonify({
            "success": False,
            "error": "Artifact file not found on disk",
        }), 404
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error reading artifact: {e}",
        }), 500

    # Create project with name derived from research query
    project_name = f"Research: {run.query[:80]}"
    project = ProjectManager.create_project(name=project_name)

    # Save research markdown as extracted_text.txt
    ProjectManager.save_extracted_text(project.project_id, research_content)

    # Set stub ontology
    project.ontology = {"entity_types": [], "edge_types": []}
    ProjectManager.save_project(project)

    logger.info(
        f"[research:{run_id}] Created project_id={project.project_id} "
        f"from approved research"
    )

    return jsonify({
        "success": True,
        "data": {
            "run_id": run_id,
            "project_id": project.project_id,
            "project_name": project.name,
        },
    })


@research_bp.route("/rerun/<run_id>", methods=["POST"])
def rerun_research(run_id: str):
    """
    POST /research/rerun/<run_id>

    Create a new research run based on the original with user feedback.
    The new run is spawned in a daemon thread immediately.

    Body (JSON):
        feedback: str  — user's feedback for improvement

    Returns:
        {success, data: {new_run_id, task_id, original_run_id}}
    """
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        data = {}

    feedback = data.get("feedback", "").strip()
    if not feedback:
        return jsonify({
            "success": False,
            "error": "feedback is required",
        }), 400

    # Get original run
    original = ResearchRunManager().get_run(run_id)
    if not original:
        return jsonify({
            "success": False,
            "error": f"Original run not found: {run_id}",
        }), 404

    # Request rerun - creates new run with feedback
    new_run = ResearchRunManager().request_rerun(run_id, feedback)
    if not new_run:
        return jsonify({
            "success": False,
            "error": "Failed to create rerun",
        }), 500

    # Create background task for the new run
    task_manager = TaskManager()
    task_id = task_manager.create_task(
        task_type="deep_research",
        metadata={"run_id": new_run.run_id, "query": new_run.query, "original_run_id": run_id},
    )
    task_manager.update_task(
        task_id,
        progress=0,
        message="Rerun queued",
    )

    # Update new run with task_id
    ResearchRunManager().update_run(new_run.run_id, task_id=task_id)

    # Spawn daemon thread to run the research
    current_locale = get_locale()

    def background_wrapper():
        set_locale(current_locale)
        _research_task(new_run.run_id, task_id, new_run.query)

    thread = threading.Thread(target=background_wrapper, daemon=True)
    thread.start()

    logger.info(f"[research:{run_id}] Rerun requested, new_run_id={new_run.run_id} task={task_id}")

    return jsonify({
        "success": True,
        "data": {
            "new_run_id": new_run.run_id,
            "task_id": task_id,
            "original_run_id": run_id,
        },
    })
