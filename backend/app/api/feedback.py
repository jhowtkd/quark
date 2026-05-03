"""
Feedback API routes

Endpoints:
  POST   /api/feedback                — Create feedback
  GET    /api/feedback                 — List feedback with optional filters
  GET    /api/feedback/<feedback_id>   — Get single feedback
  PUT    /api/feedback/<feedback_id>   — Update feedback (severity, triage_notes, converted_to_backlog)
  GET    /api/feedback/stats/summary   — Summary stats for triage

Request/Response schema examples:

  POST /api/feedback
  Request:
    {
      "stage": "simulation",
      "category": "bug",
      "rating": 2,
      "comment": "Simulacao parou no round 45 sem erro visivel",
      "simulation_id": "sim_abc123",
      "report_id": null,
      "user_email": "tester@example.com"
    }
  Response (success):
    {
      "success": true,
      "data": {
        "feedback_id": "fb_a1b2c3d4e5f6",
        "created_at": "2026-05-01T14:36:00.000000"
      }
    }
  Response (validation error):
    {
      "success": false,
      "error": "Comentario obrigatorio para nota <= 3 (minimo 10 caracteres)"
    }

  GET /api/feedback?limit=50&category=bug&severity=untriaged&stage=simulation
  Response:
    {
      "success": true,
      "data": {
        "items": [ ... ],
        "count": 12
      }
    }

  GET /api/feedback/fb_a1b2c3d4e5f6
  Response:
    {
      "success": true,
      "data": { ...FeedbackItem... }
    }

  PUT /api/feedback/fb_a1b2c3d4e5f6
  Request:
    {
      "severity": "p0",
      "triage_notes": "Bloqueia simulacao de Saude",
      "converted_to_backlog": true
    }
  Response:
    {
      "success": true,
      "data": { "updated_at": "2026-05-01T15:00:00.000000" }
    }

  GET /api/feedback/stats/summary
  Response:
    {
      "success": true,
      "data": {
        "total": 42,
        "by_category": {"bug": 10, "ux_confusion": 15, "suggestion": 17},
        "by_stage": {"graph_build": 5, "env_setup": 3, "simulation": 18, "report": 10, "inspection": 6},
        "by_severity": {"untriaged": 30, "p0": 2, "p1": 5, "p2": 3, "p3": 2},
        "avg_rating": 3.4
      }
    }
"""

import os

from flask import request, jsonify

from ..models.feedback import (
    FeedbackManager,
    FeedbackItem,
    FeedbackCategory,
    FeedbackSeverity,
    PipelineStage,
)
from ..services.triage_service import TriageService
from ..services.changelog_service import ChangelogService
from ..utils.response import success_response, error_response

from . import feedback_bp


@feedback_bp.route('', methods=['POST'])
def create_feedback():
    """Create a new feedback item"""
    data = request.get_json(silent=True) or {}

    # Required fields
    stage = data.get('stage')
    category = data.get('category')
    rating = data.get('rating')
    comment = data.get('comment', '')

    if not stage:
        return error_response("Campo 'stage' e obrigatorio", 400)
    if not category:
        return error_response("Campo 'category' e obrigatorio", 400)
    if rating is None:
        return error_response("Campo 'rating' e obrigatorio", 400)

    # Validate enums
    try:
        PipelineStage(stage)
    except ValueError:
        return error_response(
            f"Stage invalido. Valores validos: {[s.value for s in PipelineStage]}", 400
        )

    try:
        FeedbackCategory(category)
    except ValueError:
        return error_response(
            f"Categoria invalida. Valores validos: {[c.value for c in FeedbackCategory]}", 400
        )

    # Validate rating range
    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            raise ValueError
    except (ValueError, TypeError):
        return error_response("Rating deve ser um inteiro entre 1 e 5", 400)

    # Validate comment for low ratings
    if rating <= 3 and (not comment or len(comment.strip()) < 10):
        return error_response(
            "Comentario obrigatorio para nota <= 3 (minimo 10 caracteres)", 400
        )

    manager = FeedbackManager()
    item = manager.create_feedback(data)

    return success_response(
        data={
            "feedback_id": item.feedback_id,
            "created_at": item.created_at,
        },
        message="Feedback registrado com sucesso",
    )


@feedback_bp.route('', methods=['GET'])
def list_feedback():
    """List feedback items with optional filters"""
    limit = request.args.get('limit', 100, type=int)
    category = request.args.get('category') or None
    severity = request.args.get('severity') or None
    stage = request.args.get('stage') or None

    manager = FeedbackManager()
    items = manager.list_feedback(
        limit=limit,
        category=category,
        severity=severity,
        stage=stage,
    )

    return success_response(
        data={
            "items": [item.to_dict() for item in items],
            "count": len(items),
        }
    )


@feedback_bp.route('/<feedback_id>', methods=['GET'])
def get_feedback(feedback_id):
    """Get a single feedback item by ID"""
    manager = FeedbackManager()
    item = manager.get_feedback(feedback_id)

    if not item:
        return error_response("Feedback nao encontrado", 404)

    return success_response(data=item.to_dict())


@feedback_bp.route('/<feedback_id>', methods=['PUT'])
def update_feedback(feedback_id):
    """Update feedback severity, triage_notes, or converted_to_backlog"""
    data = request.get_json(silent=True) or {}

    fields = {}
    if 'severity' in data:
        try:
            FeedbackSeverity(data['severity'])
            fields['severity'] = data['severity']
        except ValueError:
            return error_response(
                f"Severidade invalida. Valores validos: {[s.value for s in FeedbackSeverity]}",
                400,
            )

    if 'triage_notes' in data:
        fields['triage_notes'] = data['triage_notes']

    if 'converted_to_backlog' in data:
        fields['converted_to_backlog'] = data['converted_to_backlog']

    if not fields:
        return error_response("Nenhum campo valido para atualizacao", 400)

    manager = FeedbackManager()
    updated = manager.update_feedback(feedback_id, **fields)

    if not updated:
        return error_response("Feedback nao encontrado", 404)

    item = manager.get_feedback(feedback_id)
    return success_response(
        data={"updated_at": item.updated_at if item else None}
    )


@feedback_bp.route('/stats/summary', methods=['GET'])
def get_feedback_stats():
    """Get summary statistics for triage"""
    manager = FeedbackManager()
    items = manager.list_feedback(limit=10000)

    total = len(items)
    by_category = {c.value: 0 for c in FeedbackCategory}
    by_stage = {s.value: 0 for s in PipelineStage}
    by_severity = {s.value: 0 for s in FeedbackSeverity}
    rating_sum = 0

    for item in items:
        by_category[item.category.value] += 1
        by_stage[item.stage.value] += 1
        by_severity[item.severity.value] += 1
        rating_sum += item.rating

    avg_rating = round(rating_sum / total, 1) if total > 0 else 0.0

    return success_response(
        data={
            "total": total,
            "by_category": by_category,
            "by_stage": by_stage,
            "by_severity": by_severity,
            "avg_rating": avg_rating,
        }
    )


# ---------------------------------------------------------------------------
# Triage endpoints (39-02)
# ---------------------------------------------------------------------------

@feedback_bp.route('/<feedback_id>/triage', methods=['POST'])
def triage_feedback(feedback_id):
    """Manually classify feedback severity"""
    data = request.get_json(silent=True) or {}
    severity = data.get('severity')
    notes = data.get('notes', '')

    if not severity:
        return error_response("Campo 'severity' e obrigatorio", 400)

    service = TriageService()
    updated = service.classify_feedback(feedback_id, severity, notes)

    if not updated:
        return error_response("Feedback nao encontrado ou severidade invalida", 404)

    manager = FeedbackManager()
    item = manager.get_feedback(feedback_id)

    return success_response(
        data={
            "feedback_id": feedback_id,
            "severity": item.severity.value if item else severity,
            "converted_to_backlog": item.converted_to_backlog if item else False,
        }
    )


@feedback_bp.route('/triage/auto', methods=['POST'])
def auto_classify_feedback():
    """Run auto-classification heuristic on untriaged feedback"""
    service = TriageService()
    classified = service.auto_classify()

    return success_response(
        data={
            "classified": classified,
            "count": len(classified),
        }
    )


@feedback_bp.route('/triage/weekly-summary', methods=['GET'])
def weekly_summary():
    """Get weekly summary for triage dashboard"""
    since = request.args.get('since', '')
    if not since:
        return error_response("Parametro 'since' e obrigatorio (YYYY-MM-DD)", 400)

    service = TriageService()
    summary = service.get_weekly_summary(f"{since}T00:00:00")

    return success_response(data=summary)


@feedback_bp.route('/triage/generate-backlog', methods=['POST'])
def generate_backlog():
    """Convert P0/P1 feedback items to backlog JSONL"""
    service = TriageService()
    items = service.generate_backlog_items()

    return success_response(
        data={
            "items_created": len(items),
            "backlog_path": None,  # Determined by service internally
        }
    )


@feedback_bp.route('/triage/generate-changelog', methods=['POST'])
def generate_changelog():
    """Generate changelog markdown for a given period"""
    data = request.get_json(silent=True) or {}
    since = data.get('since')
    output_filename = data.get('output_filename')

    if not since:
        return error_response("Campo 'since' e obrigatorio", 400)

    if not output_filename:
        from datetime import datetime
        output_filename = f"beta-{datetime.now().strftime('%Y-%m-%d')}.md"

    output_path = os.path.join(
        os.path.dirname(__file__), '..', '..', 'docs', 'changelogs', output_filename
    )

    service = ChangelogService()
    path = service.generate_changelog(f"{since}T00:00:00", output_path)

    # Read preview
    preview = ""
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            preview = f.read(500)

    return success_response(
        data={
            "path": path,
            "content_preview": preview,
        }
    )


@feedback_bp.route('/triage/latest-changelog', methods=['GET'])
def latest_changelog():
    """Return the most recent changelog markdown file"""
    changelogs_dir = os.path.join(
        os.path.dirname(__file__), '..', '..', 'docs', 'changelogs'
    )

    if not os.path.exists(changelogs_dir):
        return success_response(data=None)

    files = [
        f for f in os.listdir(changelogs_dir)
        if f.startswith('beta-') and f.endswith('.md')
    ]

    if not files:
        return success_response(data=None), 200

    files.sort(reverse=True)
    latest_file = files[0]
    latest_path = os.path.join(changelogs_dir, latest_file)

    # Extract date from filename: beta-YYYY-MM-DD.md
    date_str = latest_file.replace('beta-', '').replace('.md', '')

    with open(latest_path, 'r', encoding='utf-8') as f:
        content = f.read()

    return success_response(
        data={
            "filename": latest_file,
            "date": date_str,
            "content": content,
        }
    )
