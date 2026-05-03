"""
Triage service for feedback classification and backlog generation.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from ..models.feedback import FeedbackManager, FeedbackSeverity, FeedbackCategory
from ..config import Config


class TriageService:
    """Service for classifying feedback and generating backlog items."""

    def classify_feedback(self, feedback_id: str, severity: str, notes: str = "") -> bool:
        """
        Manually classify a feedback item by severity.

        Args:
            feedback_id: Feedback item ID
            severity: One of FeedbackSeverity values (not 'untriaged')
            notes: Optional triage notes

        Returns:
            True if classified successfully
        """
        # Validate severity
        try:
            sev = FeedbackSeverity(severity)
        except ValueError:
            return False

        if sev == FeedbackSeverity.UNTRIAGED:
            return False

        converted = sev in (FeedbackSeverity.P0, FeedbackSeverity.P1)

        manager = FeedbackManager()
        return manager.update_feedback(
            feedback_id,
            severity=severity,
            triage_notes=notes,
            converted_to_backlog=converted,
        )

    def auto_classify(self) -> List[str]:
        """
        Automatically classify untriaged feedback using heuristics.

        Heuristics:
          - rating == 1 and category == "bug" -> P0
          - rating == 2 and category == "bug" -> P1
          - rating <= 3 and category == "ux_confusion" -> P2
          - category == "suggestion" -> P3
          - rating >= 4 -> P3 (positive feedback, implicit suggestion)

        Returns:
            List of feedback_ids that were auto-classified
        """
        manager = FeedbackManager()
        items = manager.list_feedback(limit=10000, severity="untriaged")
        classified: List[str] = []

        for item in items:
            new_severity = None

            if item.rating == 1 and item.category == FeedbackCategory.BUG:
                new_severity = FeedbackSeverity.P0
            elif item.rating == 2 and item.category == FeedbackCategory.BUG:
                new_severity = FeedbackSeverity.P1
            elif item.rating <= 3 and item.category == FeedbackCategory.UX_CONFUSION:
                new_severity = FeedbackSeverity.P2
            elif item.category == FeedbackCategory.SUGGESTION:
                new_severity = FeedbackSeverity.P3
            elif item.rating >= 4:
                new_severity = FeedbackSeverity.P3
            else:
                # Default: rating 3 bug -> P2
                new_severity = FeedbackSeverity.P2

            converted = new_severity in (FeedbackSeverity.P0, FeedbackSeverity.P1)
            manager.update_feedback(
                item.feedback_id,
                severity=new_severity.value,
                triage_notes="Auto-classificado por heuristica",
            )
            classified.append(item.feedback_id)

        return classified

    def get_weekly_summary(self, since_iso_date: str) -> Dict[str, Any]:
        """
        Generate a weekly summary of feedback.

        Args:
            since_iso_date: ISO date string for period start

        Returns:
            Summary dictionary with counts and averages
        """
        manager = FeedbackManager()
        items = manager.list_feedback(limit=10000)

        # Filter by date if provided
        if since_iso_date:
            items = [i for i in items if i.created_at >= since_iso_date]

        total = len(items)
        by_severity = {"p0": 0, "p1": 0, "p2": 0, "p3": 0, "untriaged": 0}
        by_category = {"bug": 0, "ux_confusion": 0, "suggestion": 0}
        converted_to_backlog = 0
        rating_sum = 0
        stage_counts: Dict[str, int] = {}

        for item in items:
            by_severity[item.severity.value] += 1
            by_category[item.category.value] += 1
            if item.converted_to_backlog:
                converted_to_backlog += 1
            rating_sum += item.rating
            stage_counts[item.stage.value] = stage_counts.get(item.stage.value, 0) + 1

        avg_rating = round(rating_sum / total, 1) if total > 0 else 0.0
        top_stages = sorted(stage_counts.keys(), key=lambda s: stage_counts[s], reverse=True)

        return {
            "period_start": since_iso_date,
            "period_end": datetime.now().isoformat(),
            "total_new": total,
            "by_severity": by_severity,
            "by_category": by_category,
            "converted_to_backlog": converted_to_backlog,
            "avg_rating": avg_rating,
            "top_stages": top_stages,
        }

    def generate_backlog_items(self) -> List[Dict[str, Any]]:
        """
        Convert P0/P1 feedback items into backlog entries.

        Returns:
            List of created backlog items
        """
        manager = FeedbackManager()
        items = manager.list_feedback(limit=10000)

        backlog_items: List[Dict[str, Any]] = []
        backlog_dir = os.path.join(FeedbackManager.FEEDBACK_DIR, 'backlog')
        os.makedirs(backlog_dir, exist_ok=True)

        today = datetime.now().strftime('%Y-%m-%d')
        backlog_path = os.path.join(backlog_dir, f'backlog-{today}.jsonl')

        for item in items:
            if item.severity not in (FeedbackSeverity.P0, FeedbackSeverity.P1):
                continue
            if item.converted_to_backlog:
                continue

            backlog_item = {
                "backlog_id": f"bl_{item.feedback_id}",
                "feedback_id": item.feedback_id,
                "severity": item.severity.value,
                "title": f"[{item.severity.value.upper()}] {item.category.value}: {item.comment[:60]}...",
                "description": item.comment,
                "stage": item.stage.value,
                "simulation_id": item.simulation_id,
                "report_id": item.report_id,
                "created_at": item.created_at,
                "source": "beta-feedback",
            }
            backlog_items.append(backlog_item)

            # Mark as converted
            manager.update_feedback(item.feedback_id, converted_to_backlog=True)

        # Append to JSONL file
        if backlog_items:
            with open(backlog_path, 'a', encoding='utf-8') as f:
                for bi in backlog_items:
                    f.write(json.dumps(bi, ensure_ascii=False) + '\n')

        return backlog_items
