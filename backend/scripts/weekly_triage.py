#!/usr/bin/env python3
"""
Script CLI de triagem semanal de feedback.

Uso:
    cd backend && uv run python -m scripts.weekly_triage --since 2026-04-24 --auto-classify --generate-backlog --generate-changelog
    cd backend && uv run python -m scripts.weekly_triage --since 2026-04-24 --dry-run
"""

import argparse
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.triage_service import TriageService
from app.services.changelog_service import ChangelogService
from app.models.feedback import FeedbackManager


def main():
    parser = argparse.ArgumentParser(description="Triagem semanal de feedback beta")
    parser.add_argument("--since", required=True, help="Data de inicio do periodo (YYYY-MM-DD)")
    parser.add_argument("--auto-classify", action="store_true", help="Executar heuristica de auto-classificacao")
    parser.add_argument("--generate-backlog", action="store_true", help="Converter P0/P1 em backlog")
    parser.add_argument("--generate-changelog", action="store_true", help="Gerar changelog markdown")
    parser.add_argument("--changelog-dir", default="../docs/changelogs", help="Diretorio para salvar changelogs")
    parser.add_argument("--dry-run", action="store_true", help="Simula sem persistir")

    args = parser.parse_args()

    since_iso = f"{args.since}T00:00:00"
    today = datetime.now().strftime('%Y-%m-%d')

    print(f"[TRIAGEM SEMANAL] Periodo: {args.since} a {today}")

    if args.dry_run:
        print("[DRY-RUN] Nenhuma alteracao sera persistida.")

    triage_service = TriageService()
    changelog_service = ChangelogService()

    # Auto-classify
    if args.auto_classify:
        if args.dry_run:
            # Simulate count without persisting
            manager = FeedbackManager()
            untriaged = manager.list_feedback(limit=10000, severity="untriaged")
            print(f"[AUTO] {len(untriaged)} feedbacks seriam classificados (dry-run)")
        else:
            classified = triage_service.auto_classify()
            # Count by severity
            manager = FeedbackManager()
            items = [manager.get_feedback(fid) for fid in classified]
            counts = {"p0": 0, "p1": 0, "p2": 0, "p3": 0}
            for item in items:
                if item:
                    counts[item.severity.value] += 1
            print(
                f"[AUTO] {len(classified)} feedbacks classificados: "
                f"P0={counts['p0']}, P1={counts['p1']}, P2={counts['p2']}, P3={counts['p3']}"
            )

    # Generate backlog
    if args.generate_backlog:
        if args.dry_run:
            manager = FeedbackManager()
            p0_p1 = [
                i for i in manager.list_feedback(limit=10000)
                if i.severity.value in ("p0", "p1") and not i.converted_to_backlog
            ]
            print(f"[BACKLOG] {len(p0_p1)} itens seriam convertidos (dry-run)")
        else:
            items = triage_service.generate_backlog_items()
            backlog_dir = os.path.join(FeedbackManager.FEEDBACK_DIR, 'backlog')
            backlog_path = os.path.join(backlog_dir, f'backlog-{today}.jsonl')
            print(f"[BACKLOG] {len(items)} itens convertidos -> {backlog_path}")

    # Generate changelog
    if args.generate_changelog:
        changelog_filename = f"beta-{today}.md"
        output_path = os.path.join(args.changelog_dir, changelog_filename)
        if args.dry_run:
            print(f"[CHANGELOG] Seria gerado -> {output_path} (dry-run)")
        else:
            path = changelog_service.generate_changelog(since_iso, output_path)
            print(f"[CHANGELOG] Gerado -> {path}")


if __name__ == "__main__":
    main()
