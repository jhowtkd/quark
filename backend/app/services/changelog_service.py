"""
Changelog service for generating beta changelog markdown files.
"""

import os
from datetime import datetime
from typing import Dict, Any, List, Optional

from ..models.feedback import FeedbackManager, FeedbackSeverity


class ChangelogService:
    """Service for generating beta changelog markdown reports."""

    def generate_changelog(self, since_iso_date: str, output_path: str) -> str:
        """
        Generate a changelog markdown file from feedback since a given date.

        Args:
            since_iso_date: ISO date string for period start
            output_path: Full path where the markdown file will be saved

        Returns:
            Absolute path to the generated file
        """
        manager = FeedbackManager()
        items = manager.list_feedback(limit=10000)

        if since_iso_date:
            items = [i for i in items if i.created_at >= since_iso_date]

        # Group by severity
        p0_p1_items = [i for i in items if i.severity in (FeedbackSeverity.P0, FeedbackSeverity.P1)]
        p2_p3_items = [i for i in items if i.severity in (FeedbackSeverity.P2, FeedbackSeverity.P3)]
        untriaged_items = [i for i in items if i.severity == FeedbackSeverity.UNTRIAGED]

        total = len(items)
        rating_sum = sum(i.rating for i in items)
        avg_rating = round(rating_sum / total, 1) if total > 0 else 0.0

        today = datetime.now().strftime('%Y-%m-%d')
        period_start = since_iso_date or today

        lines = [
            f"# Changelog Beta — {period_start} a {today}",
            "",
            "## Resumo",
            f"- Total de feedbacks: {total}",
            f"- Media de satisfacao: {avg_rating}/5",
            f"- Itens criticos (P0): {len([i for i in items if i.severity == FeedbackSeverity.P0])}",
            f"- Itens graves (P1): {len([i for i in items if i.severity == FeedbackSeverity.P1])}",
            "",
            "## Correcoes e Melhorias (P0/P1)",
        ]

        if p0_p1_items:
            for item in p0_p1_items:
                lines.append(
                    f"- [{item.severity.value.upper()}] [{item.stage.value}] {item.category.value}: {item.comment[:80]} ({item.feedback_id})"
                )
        else:
            lines.append("- Nenhum item P0/P1 neste periodo.")

        lines.extend([
            "",
            "## Ajustes e Sugestoes (P2/P3)",
        ])

        if p2_p3_items:
            for item in p2_p3_items:
                lines.append(
                    f"- [{item.severity.value.upper()}] [{item.stage.value}] {item.category.value}: {item.comment[:80]} ({item.feedback_id})"
                )
        else:
            lines.append("- Nenhum item P2/P3 neste periodo.")

        lines.extend([
            "",
            "## Conhecidos — Em investigacao",
        ])

        if untriaged_items:
            for item in untriaged_items:
                lines.append(
                    f"- [untriaged] [{item.stage.value}] {item.category.value}: {item.comment[:80]} ({item.feedback_id})"
                )
        else:
            lines.append("- Nenhum item nao classificado.")

        lines.extend([
            "",
            "## Agradecimentos",
            "Agradecimento aos testers que enviaram feedback.",
            "",
        ])

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        return os.path.abspath(output_path)
