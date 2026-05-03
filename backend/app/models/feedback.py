"""
Feedback model and manager

Persists feedback items as JSON on disk under backend/uploads/feedback/<feedback_id>/metadata.json
"""

import os
import json
import uuid
import threading
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict

from ..config import Config


class FeedbackCategory(str, Enum):
    """Feedback category"""
    BUG = "bug"
    UX_CONFUSION = "ux_confusion"
    SUGGESTION = "suggestion"


class FeedbackSeverity(str, Enum):
    """Feedback severity / triage level"""
    UNTRIAGED = "untriaged"
    P0 = "p0"
    P1 = "p1"
    P2 = "p2"
    P3 = "p3"


class PipelineStage(str, Enum):
    """Pipeline stage for rating"""
    GRAPH_BUILD = "graph_build"
    ENV_SETUP = "env_setup"
    SIMULATION = "simulation"
    REPORT = "report"
    INSPECTION = "inspection"


@dataclass
class FeedbackItem:
    """Feedback item data model"""
    feedback_id: str
    stage: PipelineStage
    category: FeedbackCategory
    rating: int
    comment: str = ""
    simulation_id: Optional[str] = None
    report_id: Optional[str] = None
    user_email: Optional[str] = None
    severity: FeedbackSeverity = FeedbackSeverity.UNTRIAGED
    triage_notes: str = ""
    converted_to_backlog: bool = False
    created_at: str = ""
    updated_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "feedback_id": self.feedback_id,
            "stage": self.stage.value if isinstance(self.stage, PipelineStage) else self.stage,
            "category": self.category.value if isinstance(self.category, FeedbackCategory) else self.category,
            "rating": self.rating,
            "comment": self.comment,
            "simulation_id": self.simulation_id,
            "report_id": self.report_id,
            "user_email": self.user_email,
            "severity": self.severity.value if isinstance(self.severity, FeedbackSeverity) else self.severity,
            "triage_notes": self.triage_notes,
            "converted_to_backlog": self.converted_to_backlog,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeedbackItem':
        """Create from dictionary"""
        stage = data.get('stage', 'simulation')
        if isinstance(stage, str):
            stage = PipelineStage(stage)

        category = data.get('category', 'bug')
        if isinstance(category, str):
            category = FeedbackCategory(category)

        severity = data.get('severity', 'untriaged')
        if isinstance(severity, str):
            severity = FeedbackSeverity(severity)

        return cls(
            feedback_id=data['feedback_id'],
            stage=stage,
            category=category,
            rating=data['rating'],
            comment=data.get('comment', ''),
            simulation_id=data.get('simulation_id'),
            report_id=data.get('report_id'),
            user_email=data.get('user_email'),
            severity=severity,
            triage_notes=data.get('triage_notes', ''),
            converted_to_backlog=data.get('converted_to_backlog', False),
            created_at=data.get('created_at', ''),
            updated_at=data.get('updated_at', ''),
            metadata=data.get('metadata', {}),
        )


class FeedbackManager:
    """
    Feedback manager
    Thread-safe singleton managing feedback persistence on disk.
    Storage structure: backend/uploads/feedback/<feedback_id>/metadata.json
    """
    _instance: Optional['FeedbackManager'] = None
    _lock: threading.Lock = threading.Lock()

    FEEDBACK_DIR = os.path.join(Config.UPLOAD_FOLDER, 'feedback')

    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._items: Dict[str, FeedbackItem] = {}
                    cls._instance._items_lock = threading.Lock()
        return cls._instance

    @classmethod
    def _ensure_feedback_dir(cls) -> None:
        """Ensure the feedback root directory exists"""
        os.makedirs(cls.FEEDBACK_DIR, exist_ok=True)

    @classmethod
    def _get_feedback_dir(cls, feedback_id: str) -> str:
        """Get the feedback item directory path"""
        return os.path.join(cls.FEEDBACK_DIR, feedback_id)

    @classmethod
    def _get_meta_path(cls, feedback_id: str) -> str:
        """Get the metadata.json file path for a feedback item"""
        return os.path.join(cls._get_feedback_dir(feedback_id), 'metadata.json')

    def create_feedback(self, data: Dict[str, Any]) -> FeedbackItem:
        """
        Create a new feedback item.

        Args:
            data: Dictionary with feedback data (stage, category, rating, comment, etc.)

        Returns:
            Newly created FeedbackItem
        """
        self._ensure_feedback_dir()

        feedback_id = f"fb_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()

        stage = data.get('stage', 'simulation')
        if isinstance(stage, str):
            stage = PipelineStage(stage)

        category = data.get('category', 'bug')
        if isinstance(category, str):
            category = FeedbackCategory(category)

        item = FeedbackItem(
            feedback_id=feedback_id,
            stage=stage,
            category=category,
            rating=int(data['rating']),
            comment=data.get('comment', ''),
            simulation_id=data.get('simulation_id'),
            report_id=data.get('report_id'),
            user_email=data.get('user_email'),
            severity=FeedbackSeverity.UNTRIAGED,
            triage_notes="",
            converted_to_backlog=False,
            created_at=now,
            updated_at=now,
            metadata=data.get('metadata', {}),
        )

        # Create item directory
        item_dir = self._get_feedback_dir(feedback_id)
        os.makedirs(item_dir, exist_ok=True)

        # Persist metadata to disk
        self._save_meta(item)

        with self._items_lock:
            self._items[feedback_id] = item

        return item

    def _save_meta(self, item: FeedbackItem) -> None:
        """Persist feedback metadata to disk"""
        item.updated_at = datetime.now().isoformat()
        meta_path = self._get_meta_path(item.feedback_id)
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(item.to_dict(), f, ensure_ascii=False, indent=2)

    def get_feedback(self, feedback_id: str) -> Optional[FeedbackItem]:
        """
        Retrieve a feedback item by ID.

        Args:
            feedback_id: Feedback item ID

        Returns:
            FeedbackItem if found, else None
        """
        # Check in-memory cache first
        with self._items_lock:
            cached = self._items.get(feedback_id)
            if cached:
                return cached

        # Fall back to disk
        meta_path = self._get_meta_path(feedback_id)
        if not os.path.exists(meta_path):
            return None

        with open(meta_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        item = FeedbackItem.from_dict(data)
        with self._items_lock:
            self._items[feedback_id] = item
        return item

    def update_feedback(self, feedback_id: str, **fields) -> bool:
        """
        Update a feedback item's fields.

        Args:
            feedback_id: Feedback item ID
            **fields: Fields to update

        Returns:
            True if updated, False if item not found
        """
        item = self.get_feedback(feedback_id)
        if not item:
            return False

        if 'severity' in fields:
            severity = fields['severity']
            if isinstance(severity, str):
                severity = FeedbackSeverity(severity)
            item.severity = severity

        if 'triage_notes' in fields:
            item.triage_notes = fields['triage_notes']

        if 'converted_to_backlog' in fields:
            item.converted_to_backlog = bool(fields['converted_to_backlog'])

        if 'comment' in fields:
            item.comment = fields['comment']

        if 'rating' in fields:
            item.rating = int(fields['rating'])

        if 'metadata' in fields:
            item.metadata.update(fields['metadata'])

        self._save_meta(item)

        with self._items_lock:
            self._items[feedback_id] = item

        return True

    def list_feedback(
        self,
        limit: int = 100,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        stage: Optional[str] = None,
    ) -> List[FeedbackItem]:
        """
        List feedback items with optional filters.

        Args:
            limit: Maximum number of items to return
            category: Filter by category
            severity: Filter by severity
            stage: Filter by pipeline stage

        Returns:
            List of FeedbackItem objects sorted by created_at descending
        """
        self._ensure_feedback_dir()

        items = []
        try:
            for feedback_id in os.listdir(self.FEEDBACK_DIR):
                item_dir = os.path.join(self.FEEDBACK_DIR, feedback_id)
                if not os.path.isdir(item_dir):
                    continue
                item = self.get_feedback(feedback_id)
                if not item:
                    continue

                # Apply filters
                if category is not None and item.category.value != category:
                    continue
                if severity is not None and item.severity.value != severity:
                    continue
                if stage is not None and item.stage.value != stage:
                    continue

                items.append(item)
        except FileNotFoundError:
            pass

        items.sort(key=lambda i: i.created_at, reverse=True)
        return items[:limit]
