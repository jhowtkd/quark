"""
Report API

"""

import os
import threading
from datetime import datetime
from flask import request, jsonify, send_file
from pydantic import ValidationError as PydanticValidationError

from ..schemas.report import (
    ReportGenerateRequest,
    ReportGenerateStatusRequest,
    ReportChatRequest,
    ReportSearchToolRequest,
    ReportStatisticsToolRequest,
)
from ..utils.response import success_response, error_response, validation_error_response

from . import report_bp
from ..config import Config
from ..services.report_agent import ReportAgent, ReportManager, ReportStatus
from ..services.simulation_manager import SimulationManager
from ..services.report_orchestrator import ReportOrchestratorService
from ..services.reliability_scorer import ReliabilityScorer, ReliabilityReport
from ..models.project import ProjectManager
from ..models.task import TaskManager, TaskStatus
from ..utils.logger import get_logger
from ..utils.locale import t, get_locale, set_locale
from ..profiles import ProfileManager

logger = get_logger('futuria.api.report')


# ==============  ==============

@report_bp.route('/generate', methods=['POST'])
def generate_report():
    """Generate a report for a simulation."""
    try:
        data = request.get_json() or {}
        try:
            req = ReportGenerateRequest.model_validate(data)
        except PydanticValidationError as exc:
            return validation_error_response(
                [{"field": e["loc"][-1], "message": e["msg"]} for e in exc.errors()]
            )
        
        simulation_id = req.simulation_id
        if not simulation_id:
            return error_response(t('api.requireSimulationId'), 400)

        try:
            ctx = ReportOrchestratorService.resolve_generation_context(simulation_id, data)
        except ValueError as exc:
            return error_response(str(exc), 404 if "Not found" in str(exc) else 400)

        if ctx.get("already_generated"):
            return jsonify({
                "success": True,
                "data": {
                    "simulation_id": simulation_id,
                    "report_id": ctx["report_id"],
                    "status": "completed",
                    "message": t('api.reportAlreadyExists'),
                    "already_generated": True
                }
            })

        graph_id = ctx["graph_id"]
        simulation_requirement = ctx["simulation_requirement"]
        profile = ctx["profile"]
        report_id = f"report_{__import__('uuid').uuid4().hex[:12]}"

        task_manager = TaskManager()
        task_id = task_manager.create_task(
            task_type="report_generate",
            metadata={
                "simulation_id": simulation_id,
                "graph_id": graph_id,
                "report_id": report_id,
                "profile": profile.profile_type.value,
                "provenance_version": "1.0" if profile.require_provenance else None
            }
        )

        current_locale = get_locale()
        thread = threading.Thread(
            target=ReportOrchestratorService.start_report_generation,
            args=(simulation_id, report_id, task_id, graph_id, simulation_requirement, profile, current_locale),
            daemon=True
        )
        thread.start()

        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "report_id": report_id,
                "task_id": task_id,
                "status": "generating",
                "message": t('api.reportGenerateStarted'),
                "already_generated": False
            }
        })
    except Exception as e:
        logger.error(f": {str(e)}")
        return error_response(str(e), 500)


@report_bp.route('/generate/status', methods=['POST'])
def get_generate_status():
    """
    
    
    JSON
        {
            "task_id": "task_xxxx",         // generatetask_id
            "simulation_id": "sim_xxxx"     // ID
        }
    
    
        {
            "success": true,
            "data": {
                "task_id": "task_xxxx",
                "status": "processing|completed|failed",
                "progress": 45,
                "message": "..."
            }
        }
    """
    try:
        data = request.get_json() or {}
        
        try:
            req = ReportGenerateStatusRequest.model_validate(data)
        except PydanticValidationError as exc:
            return validation_error_response(
                [{"field": e["loc"][-1], "message": e["msg"]} for e in exc.errors()]
            )
        
        task_id = req.task_id
        simulation_id = req.simulation_id
        
        # simulation_id
        def _build_snapshot(report, sim_id):
            snapshot = {"graph": {}, "simulation": {}, "report": {}}
            if report:
                snapshot["report"] = {
                    "section_count": len(report.outline.sections) if report.outline else 0,
                    "has_summary": bool(report.outline.summary) if report.outline else False,
                    "has_conclusions": any(
                        "conclus" in (s.title or "").lower()
                        for s in (report.outline.sections if report.outline else [])
                    ),
                    "estimated_word_count": len(report.markdown_content.split()) if report.markdown_content else 0,
                    "language_detected": "pt",
                    "markdown_content": report.markdown_content or "",
                }
            try:
                from ..services.simulation_runner import SimulationRunner
                run_state = SimulationRunner.get_run_state(sim_id)
                if run_state:
                    snapshot["simulation"] = {
                        "simulated_hours": run_state.simulated_hours,
                        "total_actions": run_state.twitter_actions_count + run_state.reddit_actions_count,
                        "rounds_completed": run_state.current_round,
                        "agents_count": 0,
                    }
            except Exception:
                pass
            try:
                sim_mgr = SimulationManager()
                sim_state = sim_mgr.get_simulation(sim_id)
                if sim_state:
                    snapshot["graph"] = {
                        "nodes_count": sim_state.entities_count,
                        "edges_count": sim_state.resolved_entity_count,
                        "unknown_count": sim_state.unknown_entity_count,
                    }
                    if not snapshot["simulation"]:
                        snapshot["simulation"] = {
                            "simulated_hours": 0,
                            "total_actions": 0,
                            "rounds_completed": sim_state.current_round,
                            "agents_count": sim_state.profiles_count,
                        }
            except Exception:
                pass
            return snapshot

        def _enrich_with_reliability(data_dict, report, sim_id):
            try:
                scorer = ReliabilityScorer()
                snapshot = _build_snapshot(report, sim_id)
                rel = scorer.score_reliability(snapshot)
                data_dict["reliability_score"] = rel.total_score
                if data_dict.get("status") == "completed":
                    data_dict["reliability_report"] = {
                        "total_score": rel.total_score,
                        "pillar_scores": rel.pillar_scores,
                        "gates_passed": rel.gates_passed,
                        "gates_failed": rel.gates_failed,
                    }
                    data_dict["beta_ready"] = rel.passed_beta
                    if rel.gates_failed:
                        data_dict["warnings"] = rel.gates_failed
                    else:
                        data_dict["warnings"] = []
            except Exception as exc:
                logger.warning(f"Reliability scoring failed for {sim_id}: {exc}")
                data_dict["reliability_score"] = None
            return data_dict

        if simulation_id:
            existing_report = ReportManager.get_report_by_simulation(simulation_id)
            if existing_report and existing_report.status == ReportStatus.COMPLETED:
                resp_data = {
                    "simulation_id": simulation_id,
                    "report_id": existing_report.report_id,
                    "status": "completed",
                    "progress": 100,
                    "message": t('api.reportGenerated'),
                    "already_completed": True
                }
                resp_data = _enrich_with_reliability(resp_data, existing_report, simulation_id)
                return jsonify({"success": True, "data": resp_data})
        
        if not task_id:
            return error_response(t('api.requireTaskOrSimId'), 400)
        
        task_manager = TaskManager()
        task = task_manager.get_task(task_id)
        
        if not task:
            return error_response(t('api.taskNotFound', id=task_id), 404)
        
        data = task.to_dict()
        if data.get("status") == "completed":
            sim_id = task.metadata.get("simulation_id") if task.metadata else None
            if sim_id:
                report = ReportManager.get_report_by_simulation(sim_id)
                data = _enrich_with_reliability(data, report, sim_id)
        return jsonify({
            "success": True,
            "data": data
        })
        
    except Exception as e:
        logger.error(f": {str(e)}")
        return error_response(str(e), 500)


# ==============  ==============

@report_bp.route('/<report_id>', methods=['GET'])
def get_report(report_id: str):
    """
    
    
    
        {
            "success": true,
            "data": {
                "report_id": "report_xxxx",
                "simulation_id": "sim_xxxx",
                "status": "completed",
                "outline": {...},
                "markdown_content": "...",
                "created_at": "...",
                "completed_at": "..."
            }
        }
    """
    try:
        report = ReportManager.get_report(report_id)
        
        if not report:
            return jsonify({
                "success": False,
                "error": t('api.reportNotFound', id=report_id)
            }), 404
        
        return jsonify({
            "success": True,
            "data": report.to_dict()
        })
        
    except Exception as e:
        logger.error(f": {str(e)}")
        return error_response(str(e), 500)


@report_bp.route('/by-simulation/<simulation_id>', methods=['GET'])
def get_report_by_simulation(simulation_id: str):
    """
    ID
    
    
        {
            "success": true,
            "data": {
                "report_id": "report_xxxx",
                ...
            }
        }
    """
    try:
        report = ReportManager.get_report_by_simulation(simulation_id)
        
        if not report:
            return jsonify({
                "success": False,
                "error": t('api.noReportForSim', id=simulation_id),
                "has_report": False
            }), 404
        
        return jsonify({
            "success": True,
            "data": report.to_dict(),
            "has_report": True
        })
        
    except Exception as e:
        logger.error(f": {str(e)}")
        return error_response(str(e), 500)


@report_bp.route('/list', methods=['GET'])
def list_reports():
    """
    
    
    Query
        simulation_id: ID
        limit: 50
    
    
        {
            "success": true,
            "data": [...],
            "count": 10
        }
    """
    try:
        simulation_id = request.args.get('simulation_id')
        limit = request.args.get('limit', 50, type=int)
        
        reports = ReportManager.list_reports(
            simulation_id=simulation_id,
            limit=limit
        )
        
        return jsonify({
            "success": True,
            "data": [r.to_dict() for r in reports],
            "count": len(reports)
        })
        
    except Exception as e:
        logger.error(f": {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            
        }), 500


@report_bp.route('/<report_id>/download', methods=['GET'])
def download_report(report_id: str):
    """
    Markdown
    
    Markdown
    """
    try:
        report = ReportManager.get_report(report_id)
        
        if not report:
            return jsonify({
                "success": False,
                "error": t('api.reportNotFound', id=report_id)
            }), 404
        
        md_path = ReportManager._get_report_markdown_path(report_id)
        
        if not os.path.exists(md_path):
            # MD
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                f.write(report.markdown_content)
                temp_path = f.name
            
            return send_file(
                temp_path,
                as_attachment=True,
                download_name=f"{report_id}.md"
            )
        
        return send_file(
            md_path,
            as_attachment=True,
            download_name=f"{report_id}.md"
        )
        
    except Exception as e:
        logger.error(f": {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            
        }), 500


@report_bp.route('/<report_id>', methods=['DELETE'])
def delete_report(report_id: str):
    """"""
    try:
        success = ReportManager.delete_report(report_id)
        
        if not success:
            return jsonify({
                "success": False,
                "error": t('api.reportNotFound', id=report_id)
            }), 404
        
        return jsonify({
            "success": True,
            "message": t('api.reportDeleted', id=report_id)
        })
        
    except Exception as e:
        logger.error(f": {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            
        }), 500


# ============== Report Agent ==============

@report_bp.route('/chat', methods=['POST'])
def chat_with_report_agent():
    """
    Report Agent
    
    Report Agent
    
    JSON
        {
            "simulation_id": "sim_xxxx",        // ID
            "message": "",    // 
            "chat_history": [                   // 
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."}
            ]
        }
    
    
        {
            "success": true,
            "data": {
                "response": "Agent...",
                "tool_calls": [],
                "sources": []
            }
        }
    """
    try:
        data = request.get_json() or {}
        
        try:
            req = ReportChatRequest.model_validate(data)
        except PydanticValidationError as exc:
            return validation_error_response(
                [{"field": e["loc"][-1], "message": e["msg"]} for e in exc.errors()]
            )
        
        simulation_id = req.simulation_id
        message = req.message
        chat_history = [msg.model_dump() for msg in req.chat_history]
        
        if not simulation_id:
            return error_response(t('api.requireSimulationId'), 400)

        if not message:
            return error_response(t('api.requireMessage'), 400)
        
        # 
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)
        
        if not state:
            return error_response(t('api.simulationNotFound', id=simulation_id), 404)

        project = ProjectManager.get_project(state.project_id)
        if not project:
            return error_response(t('api.projectNotFound', id=state.project_id), 404)
        
        graph_id = state.graph_id or project.graph_id
        if not graph_id:
            return error_response(t('api.missingGraphId'), 400)
        
        simulation_requirement = project.simulation_requirement or ""
        
        # Agent
        agent = ReportAgent(
            graph_id=graph_id,
            simulation_id=simulation_id,
            simulation_requirement=simulation_requirement
        )
        
        result = agent.chat(message=message, chat_history=chat_history)
        
        return jsonify({
            "success": True,
            "data": result
        })
        
    except Exception as e:
        logger.error(f": {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            
        }), 500


# ==============  ==============

@report_bp.route('/<report_id>/progress', methods=['GET'])
def get_report_progress(report_id: str):
    """
    
    
    
        {
            "success": true,
            "data": {
                "status": "generating",
                "progress": 45,
                "message": ": ",
                "current_section": "",
                "completed_sections": ["", ""],
                "updated_at": "2025-12-09T..."
            }
        }
    """
    try:
        progress = ReportManager.get_progress(report_id)
        
        if not progress:
            return jsonify({
                "success": False,
                "error": t('api.reportProgressNotAvail', id=report_id)
            }), 404
        
        return jsonify({
            "success": True,
            "data": progress
        })
        
    except Exception as e:
        logger.error(f": {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            
        }), 500


@report_bp.route('/<report_id>/sections', methods=['GET'])
def get_report_sections(report_id: str):
    """
    
    
    
    
    
        {
            "success": true,
            "data": {
                "report_id": "report_xxxx",
                "sections": [
                    {
                        "filename": "section_01.md",
                        "section_index": 1,
                        "content": "## \\n\\n..."
                    },
                    ...
                ],
                "total_sections": 3,
                "is_complete": false
            }
        }
    """
    try:
        sections = ReportManager.get_generated_sections(report_id)
        
        # 
        report = ReportManager.get_report(report_id)
        is_complete = report is not None and report.status == ReportStatus.COMPLETED
        
        return jsonify({
            "success": True,
            "data": {
                "report_id": report_id,
                "sections": sections,
                "total_sections": len(sections),
                "is_complete": is_complete
            }
        })
        
    except Exception as e:
        logger.error(f": {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            
        }), 500


@report_bp.route('/<report_id>/retry-section', methods=['POST'])
def retry_section(report_id: str):
    """
    Retry a failed section.
    
    JSON
        {
            "section_index": 1
        }
    
    Response
        {
            "success": true,
            "data": {
                "status": "retrying",
                "section_index": 1
            }
        }
    """
    try:
        data = request.get_json() or {}
        section_index = data.get('section_index')
        
        if section_index is None:
            return error_response(t('api.requireSectionIndex'), 400)
        
        try:
            section_index = int(section_index)
        except (TypeError, ValueError):
            return error_response(t('api.invalidSectionIndex'), 400)
        
        # Check report exists
        report = ReportManager.get_report(report_id)
        if not report:
            return error_response(t('api.reportNotFound', id=report_id), 404)
        
        # Check section is in failed_sections
        progress = ReportManager.get_progress(report_id)
        if not progress:
            return error_response(t('api.reportProgressNotAvail', id=report_id), 404)
        
        failed_sections = progress.get("failed_sections", [])
        failed_entry = next(
            (fs for fs in failed_sections if fs["section_index"] == section_index),
            None
        )
        if not failed_entry:
            return error_response(t('api.sectionNotFailed', index=f"{section_index:02d}"), 400)
        
        # Get outline
        if not report.outline:
            return error_response(t('api.reportOutlineMissing'), 400)
        
        # Find section in outline
        if section_index < 1 or section_index > len(report.outline.sections):
            return error_response(t('api.sectionNotFound', index=f"{section_index:02d}"), 404)
        
        section = report.outline.sections[section_index - 1]
        
        # Get previously generated sections for context
        generated = ReportManager.get_generated_sections(report_id)
        previous_sections = []
        for s in sorted(generated, key=lambda x: x["section_index"]):
            if s["section_index"] < section_index:
                previous_sections.append(s["content"])
        
        # Remove from failed_sections in progress before starting retry
        updated_failed = [fs for fs in failed_sections if fs["section_index"] != section_index]
        ReportManager.update_progress(
            report_id,
            progress.get("status", "generating"),
            progress.get("progress", 0),
            t('progress.retryingSection', title=section.title),
            current_section=section.title,
            completed_sections=progress.get("completed_sections", []),
            failed_sections=updated_failed
        )
        
        # Start retry in background thread
        def _retry_section_thread():
            try:
                from ..services.section_generator import SectionGenerator
                from ..utils.llm_client import LLMClient
                from ..services.zep_tools import ZepToolsService
                
                section_gen = SectionGenerator(
                    zep_tools=ZepToolsService(),
                    llm_client=LLMClient(),
                    simulation_requirement=report.simulation_requirement,
                    graph_id=report.graph_id,
                    simulation_id=report.simulation_id,
                )
                
                section_content = section_gen.generate(
                    section=section,
                    outline=report.outline,
                    previous_sections=previous_sections,
                    section_index=section_index,
                )
                
                section.status = ReportStatus.COMPLETED
                section.content = section_content
                section.error_message = None
                section.retry_count += 1
                
                ReportManager.save_section(report_id, section_index, section)
                
                # Update progress
                new_progress = ReportManager.get_progress(report_id)
                completed = new_progress.get("completed_sections", []) if new_progress else []
                if section.title not in completed:
                    completed = completed + [section.title]
                
                ReportManager.update_progress(
                    report_id,
                    "generating",
                    new_progress.get("progress", 0) if new_progress else 0,
                    t('progress.sectionRetryDone', title=section.title),
                    completed_sections=completed,
                    failed_sections=new_progress.get("failed_sections", []) if new_progress else []
                )
                
                logger.info(f"[ReportAPI] Secao {section_index} re-gerada com sucesso: {report_id}")
                
            except Exception as e:
                logger.error(f"[ReportAPI] Falha ao re-gerar secao {section_index}: {e}")
                # Re-add to failed_sections
                new_progress = ReportManager.get_progress(report_id)
                current_failed = new_progress.get("failed_sections", []) if new_progress else []
                current_failed.append({
                    "section_index": section_index,
                    "section_title": section.title,
                    "error_message": str(e),
                    "failed_at": datetime.now().isoformat()
                })
                ReportManager.update_progress(
                    report_id,
                    new_progress.get("status", "generating") if new_progress else "generating",
                    new_progress.get("progress", 0) if new_progress else 0,
                    t('progress.sectionRetryFailed', title=section.title),
                    failed_sections=current_failed
                )
        
        thread = threading.Thread(target=_retry_section_thread, daemon=True)
        thread.start()
        
        return jsonify({
            "success": True,
            "data": {
                "status": "retrying",
                "section_index": section_index
            }
        })
        
    except Exception as e:
        logger.error(f"[ReportAPI] Erro no retry-section: {str(e)}")
        return error_response(str(e), 500)


@report_bp.route('/<report_id>/section/<int:section_index>', methods=['GET'])
def get_single_section(report_id: str, section_index: int):
    """
    
    
    
        {
            "success": true,
            "data": {
                "filename": "section_01.md",
                "content": "## \\n\\n..."
            }
        }
    """
    try:
        section_path = ReportManager._get_section_path(report_id, section_index)
        
        if not os.path.exists(section_path):
            return jsonify({
                "success": False,
                "error": t('api.sectionNotFound', index=f"{section_index:02d}")
            }), 404
        
        with open(section_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            "success": True,
            "data": {
                "filename": f"section_{section_index:02d}.md",
                "section_index": section_index,
                "content": content
            }
        })
        
    except Exception as e:
        logger.error(f": {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            
        }), 500


# ==============  ==============

@report_bp.route('/check/<simulation_id>', methods=['GET'])
def check_report_status(simulation_id: str):
    """
    
    
    Interview
    
    
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "has_report": true,
                "report_status": "completed",
                "report_id": "report_xxxx",
                "interview_unlocked": true
            }
        }
    """
    try:
        report = ReportManager.get_report_by_simulation(simulation_id)
        
        has_report = report is not None
        report_status = report.status.value if report else None
        report_id = report.report_id if report else None
        
        # interview
        interview_unlocked = has_report and report.status == ReportStatus.COMPLETED
        
        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "has_report": has_report,
                "report_status": report_status,
                "report_id": report_id,
                "interview_unlocked": interview_unlocked
            }
        })
        
    except Exception as e:
        logger.error(f": {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            
        }), 500


# ============== Agent  ==============

@report_bp.route('/<report_id>/agent-log', methods=['GET'])
def get_agent_log(report_id: str):
    """
     Report Agent 
    
    
    - /
    - LLM
    - 
    
    Query
        from_line: 0
    
    
        {
            "success": true,
            "data": {
                "logs": [
                    {
                        "timestamp": "2025-12-13T...",
                        "elapsed_seconds": 12.5,
                        "report_id": "report_xxxx",
                        "action": "tool_call",
                        "stage": "generating",
                        "section_title": "",
                        "section_index": 1,
                        "details": {
                            "tool_name": "insight_forge",
                            "parameters": {...},
                            ...
                        }
                    },
                    ...
                ],
                "total_lines": 25,
                "from_line": 0,
                "has_more": false
            }
        }
    """
    try:
        from_line = request.args.get('from_line', 0, type=int)
        
        log_data = ReportManager.get_agent_log(report_id, from_line=from_line)
        
        return jsonify({
            "success": True,
            "data": log_data
        })
        
    except Exception as e:
        logger.error(f"Agent: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            
        }), 500


@report_bp.route('/<report_id>/agent-log/stream', methods=['GET'])
def stream_agent_log(report_id: str):
    """
     Agent 
    
    
        {
            "success": true,
            "data": {
                "logs": [...],
                "count": 25
            }
        }
    """
    try:
        logs = ReportManager.get_agent_log_stream(report_id)
        
        return jsonify({
            "success": True,
            "data": {
                "logs": logs,
                "count": len(logs)
            }
        })
        
    except Exception as e:
        logger.error(f"Agent: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            
        }), 500


# ==============  ==============

@report_bp.route('/<report_id>/console-log', methods=['GET'])
def get_console_log(report_id: str):
    """
     Report Agent 
    
    INFOWARNING
     agent-log  JSON 
    
    
    Query
        from_line: 0
    
    
        {
            "success": true,
            "data": {
                "logs": [
                    "[19:46:14] INFO: :  15 ",
                    "[19:46:14] INFO: : graph_id=xxx, query=...",
                    ...
                ],
                "total_lines": 100,
                "from_line": 0,
                "has_more": false
            }
        }
    """
    try:
        from_line = request.args.get('from_line', 0, type=int)
        
        log_data = ReportManager.get_console_log(report_id, from_line=from_line)
        
        return jsonify({
            "success": True,
            "data": log_data
        })
        
    except Exception as e:
        logger.error(f": {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            
        }), 500


@report_bp.route('/<report_id>/console-log/stream', methods=['GET'])
def stream_console_log(report_id: str):
    """
    
    
    
        {
            "success": true,
            "data": {
                "logs": [...],
                "count": 100
            }
        }
    """
    try:
        logs = ReportManager.get_console_log_stream(report_id)
        
        return jsonify({
            "success": True,
            "data": {
                "logs": logs,
                "count": len(logs)
            }
        })
        
    except Exception as e:
        logger.error(f": {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            
        }), 500


# ============== ==============

@report_bp.route('/tools/search', methods=['POST'])
def search_graph_tool():
    """
    
    
    JSON
        {
            "graph_id": "futuria_xxxx",
            "query": "",
            "limit": 10
        }
    """
    try:
        data = request.get_json() or {}
        
        try:
            req = ReportSearchToolRequest.model_validate(data)
        except PydanticValidationError as exc:
            return validation_error_response(
                [{"field": e["loc"][-1], "message": e["msg"]} for e in exc.errors()]
            )
        
        graph_id = req.graph_id
        query = req.query
        limit = req.limit
        
        if not graph_id or not query:
            return error_response(t('api.requireGraphIdAndQuery'), 400)
        
        result = ReportOrchestratorService.search_graph(graph_id, query, limit)
        
        return jsonify({
            "success": True,
            "data": result.to_dict()
        })
        
    except Exception as e:
        logger.error(f": {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            
        }), 500


@report_bp.route('/tools/statistics', methods=['POST'])
def get_graph_statistics_tool():
    """
    
    
    JSON
        {
            "graph_id": "futuria_xxxx"
        }
    """
    try:
        data = request.get_json() or {}
        
        try:
            req = ReportStatisticsToolRequest.model_validate(data)
        except PydanticValidationError as exc:
            return validation_error_response(
                [{"field": e["loc"][-1], "message": e["msg"]} for e in exc.errors()]
            )
        
        graph_id = req.graph_id
        
        if not graph_id:
            return error_response(t('api.requireGraphId'), 400)
        
        result = ReportOrchestratorService.get_graph_statistics(graph_id)
        
        return jsonify({
            "success": True,
            "data": result
        })
        
    except Exception as e:
        logger.error(f": {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            
        }), 500
