"""
Report orchestrator service — moves business logic out of Flask routes.
"""

import uuid
from typing import Optional

from ..services.report_agent import ReportAgent, ReportManager, ReportStatus
from ..services.simulation_manager import SimulationManager
from ..services.zep_tools import ZepToolsService
from ..models.project import ProjectManager
from ..models.task import TaskManager, TaskStatus
from ..profiles import ProfileManager
from ..utils.logger import get_logger
from ..utils.locale import t, set_locale

logger = get_logger('futuria.api.report')


class ReportOrchestratorService:
    """Orchestrates report operations so Flask routes stay thin."""

    @staticmethod
    def resolve_generation_context(simulation_id: str, data: dict) -> dict:
        """
        Resolve project, graph_id, simulation_requirement and profile for report generation.

        Returns a dict with keys:
            project, graph_id, simulation_requirement, profile, profile_name
        or raises ValueError with an appropriate message if anything is missing.
        """
        force_regenerate = data.get('force_regenerate', False)

        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)

        if not state:
            raise ValueError(t('api.simulationNotFound', id=simulation_id))

        if not force_regenerate:
            existing_report = ReportManager.get_report_by_simulation(simulation_id)
            if existing_report and existing_report.status == ReportStatus.COMPLETED:
                return {
                    "already_generated": True,
                    "report_id": existing_report.report_id,
                }

        project = ProjectManager.get_project(state.project_id)
        if not project:
            raise ValueError(t('api.projectNotFound', id=state.project_id))

        graph_id = state.graph_id or project.graph_id
        if not graph_id:
            raise ValueError(t('api.missingGraphIdEnsure'))

        simulation_requirement = project.simulation_requirement
        if not simulation_requirement:
            raise ValueError(t('api.missingSimRequirement'))

        # Profile: from request body, or simulation state, or default to "generico"
        profile_name = data.get('profile') or getattr(state, 'profile', None) or 'generico'
        profile = ProfileManager.get_profile_or_default(profile_name)

        # Load agent evolution from simulation run state
        agent_evolution = getattr(state, 'agent_evolution', {}) or {}

        return {
            "project": project,
            "graph_id": graph_id,
            "simulation_requirement": simulation_requirement,
            "profile": profile,
            "profile_name": profile_name,
            "state": state,
            "agent_evolution": agent_evolution,
        }

    @staticmethod
    def start_report_generation(
        simulation_id: str,
        report_id: str,
        task_id: str,
        graph_id: str,
        simulation_requirement: str,
        profile,
        current_locale: str,
        agent_evolution: dict = None,
    ) -> None:
        """Body of the background thread started by the /generate route."""
        set_locale(current_locale)
        task_manager = TaskManager()
        try:
            task_manager.update_task(
                task_id,
                status=TaskStatus.PROCESSING,
                progress=0,
                message=t('api.initReportAgent')
            )

            # Report Agent
            agent = ReportAgent(
                graph_id=graph_id,
                simulation_id=simulation_id,
                simulation_requirement=simulation_requirement,
                agent_evolution=agent_evolution or {},
            )

            # Apply profile configuration to report agent
            profile.apply_to_report_agent(agent)
            logger.info(f"Relatorio perfil aplicado: {profile.profile_type.value} para sim={simulation_id}")

            # Rebuild system prompt to preserve evolution evidence rules after profile override
            agent.system_prompt = agent._build_system_prompt()

            # Progress callback
            def progress_callback(stage, progress, message):
                task_manager.update_task(
                    task_id,
                    progress=progress,
                    message=f"[{stage}] {message}"
                )

            # Generate report
            report = agent.generate_report(
                progress_callback=progress_callback,
                report_id=report_id
            )

            # Save report
            ReportManager.save_report(report)

            if report.status == ReportStatus.COMPLETED:
                task_manager.complete_task(
                    task_id,
                    result={
                        "report_id": report.report_id,
                        "simulation_id": simulation_id,
                        "status": "completed"
                    }
                )
            else:
                task_manager.fail_task(task_id, report.error or t('api.reportGenerateFailed'))

        except Exception as e:
            logger.error(f": {str(e)}")
            task_manager.fail_task(task_id, str(e))

    @staticmethod
    def search_graph(graph_id: str, query: str, limit: int):
        """Delegate graph search to ZepToolsService."""
        tools = ZepToolsService()
        return tools.search_graph(
            graph_id=graph_id,
            query=query,
            limit=limit
        )

    @staticmethod
    def get_graph_statistics(graph_id: str):
        """Delegate graph statistics to ZepToolsService."""
        tools = ZepToolsService()
        return tools.get_graph_statistics(graph_id)
