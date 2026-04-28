"""
Deep research run model and manager

Mirrors ProjectManager disk structure under backend/uploads/research/<run_id>/
"""

import os
import json
import uuid
import threading
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from ..config import Config


class ResearchRunStatus(str, Enum):
    """Deep research run status"""
    PENDING = "pending"           # Waiting to start
    RUNNING = "running"           # Actively processing
    COMPLETED = "completed"        # Finished successfully
    FAILED = "failed"             # Failed or errored
    APPROVED = "approved"          # User approved the artifact
    RERUN_REQUESTED = "rerun_requested"  # User requested rerun with feedback


@dataclass
class ResearchRun:
    """Deep research run data model"""
    run_id: str
    query: str
    status: ResearchRunStatus
    connector_used: Optional[str] = None
    artifact_path: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    task_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "run_id": self.run_id,
            "query": self.query,
            "status": self.status.value if isinstance(self.status, ResearchRunStatus) else self.status,
            "connector_used": self.connector_used,
            "artifact_path": self.artifact_path,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "task_id": self.task_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResearchRun':
        """Create from dictionary"""
        status = data.get('status', 'pending')
        if isinstance(status, str):
            status = ResearchRunStatus(status)
        return cls(
            run_id=data['run_id'],
            query=data.get('query', ''),
            status=status,
            connector_used=data.get('connector_used'),
            artifact_path=data.get('artifact_path'),
            created_at=data.get('created_at', ''),
            updated_at=data.get('updated_at', ''),
            task_id=data.get('task_id'),
            metadata=data.get('metadata', {}),
        )


class ResearchRunManager:
    """
    Deep research run manager
    Thread-safe singleton managing research run persistence on disk.
    Storage structure: backend/uploads/research/<run_id>/metadata.json + draft.md
    """

    _instance = None
    _lock = threading.Lock()

    # Research storage root
    RESEARCH_DIR = os.path.join(Config.UPLOAD_FOLDER, 'research')

    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._runs: Dict[str, ResearchRun] = {}
                    cls._instance._runs_lock = threading.Lock()
        return cls._instance

    @classmethod
    def _ensure_research_dir(cls) -> None:
        """Ensure the research root directory exists"""
        os.makedirs(cls.RESEARCH_DIR, exist_ok=True)

    @classmethod
    def _get_research_dir(cls, run_id: str) -> str:
        """Get the research run directory path"""
        return os.path.join(cls.RESEARCH_DIR, run_id)

    @classmethod
    def _get_meta_path(cls, run_id: str) -> str:
        """Get the metadata.json file path for a run"""
        return os.path.join(cls._get_research_dir(run_id), 'metadata.json')

    @classmethod
    def _get_draft_path(cls, run_id: str) -> str:
        """Get the draft.md artifact path for a run"""
        return os.path.join(cls._get_research_dir(run_id), 'draft.md')

    def create_run(self, query: str, metadata: Optional[Dict[str, Any]] = None) -> ResearchRun:
        """
        Create a new research run.

        Args:
            query: Research query string
            metadata: Optional extra metadata

        Returns:
            Newly created ResearchRun
        """
        self._ensure_research_dir()

        run_id = f"res_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()

        run = ResearchRun(
            run_id=run_id,
            query=query,
            status=ResearchRunStatus.PENDING,
            created_at=now,
            updated_at=now,
            metadata=metadata or {}
        )

        # Create run directory
        run_dir = self._get_research_dir(run_id)
        os.makedirs(run_dir, exist_ok=True)

        # Persist metadata to disk
        self._save_meta(run)

        with self._runs_lock:
            self._runs[run_id] = run

        return run

    def _save_meta(self, run: ResearchRun) -> None:
        """Persist run metadata to disk"""
        run.updated_at = datetime.now().isoformat()
        meta_path = self._get_meta_path(run.run_id)
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(run.to_dict(), f, ensure_ascii=False, indent=2)

    def get_run(self, run_id: str) -> Optional[ResearchRun]:
        """
        Retrieve a research run by ID.

        Args:
            run_id: Research run ID

        Returns:
            ResearchRun if found, else None
        """
        # Check in-memory cache first
        with self._runs_lock:
            cached = self._runs.get(run_id)
            if cached:
                return cached

        # Fall back to disk
        meta_path = self._get_meta_path(run_id)
        if not os.path.exists(meta_path):
            return None

        with open(meta_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        run = ResearchRun.from_dict(data)
        with self._runs_lock:
            self._runs[run_id] = run
        return run

    def update_run(
        self,
        run_id: str,
        status: Optional[ResearchRunStatus] = None,
        connector_used: Optional[str] = None,
        artifact_path: Optional[str] = None,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update a research run's fields.

        Args:
            run_id: Research run ID
            status: New status
            connector_used: Which connector succeeded
            artifact_path: Path to the generated artifact
            task_id: Associated background task ID
            metadata: Extra metadata to merge

        Returns:
            True if updated, False if run not found
        """
        run = self.get_run(run_id)
        if not run:
            return False

        if status is not None:
            run.status = status
        if connector_used is not None:
            run.connector_used = connector_used
        if artifact_path is not None:
            run.artifact_path = artifact_path
        if task_id is not None:
            run.task_id = task_id
        if metadata is not None:
            run.metadata.update(metadata)

        self._save_meta(run)

        with self._runs_lock:
            self._runs[run_id] = run

        return True

    def complete_run(self, run_id: str, artifact_path: str, connector_used: str) -> bool:
        """Mark run as completed with artifact path"""
        return self.update_run(
            run_id,
            status=ResearchRunStatus.COMPLETED,
            artifact_path=artifact_path,
            connector_used=connector_used,
        )

    def fail_run(self, run_id: str, error: str) -> bool:
        """Mark run as failed with error in metadata"""
        return self.update_run(
            run_id,
            status=ResearchRunStatus.FAILED,
            metadata={"error": error},
        )

    def approve_run(self, run_id: str) -> bool:
        """
        Approve a completed research run.

        Args:
            run_id: Research run ID

        Returns:
            True if approved, False if run not found or not in COMPLETED state
        """
        run = self.get_run(run_id)
        if not run:
            return False
        if run.status != ResearchRunStatus.COMPLETED:
            return False
        return self.update_run(run_id, status=ResearchRunStatus.APPROVED)

    def reject_run(self, run_id: str) -> bool:
        """
        Reject a research run and reset it to PENDING for reprocessing.

        Args:
            run_id: Research run ID

        Returns:
            True if reset, False if run not found
        """
        run = self.get_run(run_id)
        if not run:
            return False
        return self.update_run(
            run_id,
            status=ResearchRunStatus.PENDING,
            metadata={"rejected_at": datetime.now().isoformat(), "rejection_count": run.metadata.get("rejection_count", 0) + 1},
        )

    def request_rerun(self, run_id: str, feedback: str) -> Optional[ResearchRun]:
        """
        Request a rerun of a research run with user feedback.

        Creates a new run with the same query plus the feedback appended.
        Marks the original run as RERUN_REQUESTED.

        Args:
            run_id: Original research run ID
            feedback: User feedback for the rerun

        Returns:
            New ResearchRun if successful, None if original not found
        """
        original = self.get_run(run_id)
        if not original:
            return None

        # Update original run status
        self.update_run(
            run_id,
            status=ResearchRunStatus.RERUN_REQUESTED,
            metadata={
                "feedback": feedback,
                "feedback_provided_at": datetime.now().isoformat(),
                "feedback_count": original.metadata.get("feedback_count", 0) + 1,
            },
        )

        # Create new run with query + feedback
        new_query = f"{original.query}\n\nUser feedback for improvement: {feedback}"
        new_run = self.create_run(
            query=new_query,
            metadata={
                "original_run_id": run_id,
                "feedback": feedback,
            },
        )
        return new_run

    def list_runs(self, limit: int = 50) -> List[ResearchRun]:
        """
        List all research runs.

        Args:
            limit: Maximum number of runs to return

        Returns:
            List of ResearchRun objects sorted by created_at descending
        """
        self._ensure_research_dir()

        runs = []
        for run_id in os.listdir(self.RESEARCH_DIR):
            run = self.get_run(run_id)
            if run:
                runs.append(run)

        runs.sort(key=lambda r: r.created_at, reverse=True)
        return runs[:limit]