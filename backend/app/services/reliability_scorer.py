"""Reliability scoring for FUTUR.IA pipeline outputs."""

import re
from dataclasses import dataclass
from typing import Any, Dict, List

BETA_MIN_TOTAL = 0.75
BETA_MIN_PILLAR = 0.60


@dataclass
class ReliabilityReport:
    """Aggregated reliability assessment."""

    total_score: float
    pillar_scores: Dict[str, float]
    gates_passed: List[str]
    gates_failed: List[str]
    passed_beta: bool


class ReliabilityScorer:
    """Score pipeline snapshots across 4 pillars of reliability."""

    BETA_MIN_TOTAL = BETA_MIN_TOTAL
    BETA_MIN_PILLAR = BETA_MIN_PILLAR

    # ------------------------------------------------------------------
    # Public pillar scorers
    # ------------------------------------------------------------------

    def score_structural(self, snapshot: Dict[str, Any]) -> float:
        """Graph-structure pillar (0.0 – 1.0)."""
        graph = snapshot.get("graph", {})
        nodes = graph.get("nodes_count", 0)
        edges = graph.get("edges_count", 0)
        unknown = graph.get("unknown_count", 0)

        if nodes == 0:
            return 0.0

        unknown_rate = unknown / nodes
        unknown_penalty = min(1.0, unknown_rate / 0.25) * 0.5
        node_penalty = 0.0 if nodes >= 6 else 0.2
        edge_penalty = 0.0 if edges >= 4 else 0.2

        score = 1.0 - unknown_penalty - node_penalty - edge_penalty
        return max(0.0, min(1.0, score))

    def score_semantic(self, snapshot: Dict[str, Any]) -> float:
        """Simulation-depth pillar (0.0 – 1.0)."""
        sim = snapshot.get("simulation", {})
        hours = sim.get("simulated_hours", 0)
        actions = sim.get("total_actions", 0)
        rounds = sim.get("rounds_completed", 0)

        if hours == 0:
            return 0.0

        hours_score = min(1.0, hours / 4.0)
        actions_score = min(1.0, actions / 20.0)
        rounds_score = min(1.0, rounds / 8.0)

        score = (hours_score + actions_score + rounds_score) / 3.0
        return max(0.0, min(1.0, score))

    def score_content(self, snapshot: Dict[str, Any]) -> float:
        """Report-quality pillar (0.0 – 1.0).

        Combines structural completeness (sections, summary, word count,
        language) and integrity (empty report, thinking process).
        """
        report = snapshot.get("report", {})
        markdown = report.get("markdown_content", "")

        if not markdown or not markdown.strip():
            return 0.0

        # ---- integrity ----
        has_thinking = bool(
            re.search(
                r"<think>|</think>|thinking\s+process|chain\s+of\s+thought|"
                r"reasoning\s+process|racioc[ií]nio|passo\s+a\s+passo",
                markdown,
                re.IGNORECASE,
            )
        )

        if has_thinking:
            # Must stay below the 0.60 pillar minimum
            return 0.4

        # ---- structure ----
        sections = report.get("section_count", 0)
        has_summary = report.get("has_summary", False)
        has_conclusions = report.get("has_conclusions", False)
        words = report.get("estimated_word_count", 0)
        lang = report.get("language_detected", "")

        section_score = min(1.0, sections / 4.0)
        summary_score = 1.0 if has_summary else 0.0
        conclusions_score = 1.0 if has_conclusions else 0.0
        word_score = min(1.0, words / 800.0)
        lang_score = 1.0 if lang == "pt" else 0.5

        structure_score = (
            section_score + summary_score + conclusions_score + word_score + lang_score
        ) / 5.0

        return max(0.0, min(1.0, structure_score))

    # ------------------------------------------------------------------
    # Overall scorer
    # ------------------------------------------------------------------

    def score_reliability(self, snapshot: Dict[str, Any]) -> ReliabilityReport:
        """Compute total score and beta-gate verdict."""
        structural = self.score_structural(snapshot)
        semantic = self.score_semantic(snapshot)
        content = self.score_content(snapshot)
        completeness = self._score_completeness(snapshot)

        pillar_scores = {
            "structural": round(structural, 4),
            "semantic": round(semantic, 4),
            "content": round(content, 4),
            "completeness": round(completeness, 4),
        }

        total = round(sum(pillar_scores.values()) / 4.0, 4)

        gates_passed: List[str] = []
        gates_failed: List[str] = []

        if total >= self.BETA_MIN_TOTAL:
            gates_passed.append("total_score")
        else:
            gates_failed.append(f"total_score ({total:.2f} < {self.BETA_MIN_TOTAL})")

        for name, score in pillar_scores.items():
            if score >= self.BETA_MIN_PILLAR:
                gates_passed.append(f"{name}_pillar")
            else:
                gates_failed.append(
                    f"{name}_pillar ({score:.2f} < {self.BETA_MIN_PILLAR})"
                )

        passed_beta = len(gates_failed) == 0

        return ReliabilityReport(
            total_score=total,
            pillar_scores=pillar_scores,
            gates_passed=gates_passed,
            gates_failed=gates_failed,
            passed_beta=passed_beta,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _score_completeness(self, snapshot: Dict[str, Any]) -> float:
        """Check that all 3 pipeline stages produced output."""
        graph = snapshot.get("graph", {})
        sim = snapshot.get("simulation", {})
        report = snapshot.get("report", {})

        graph_ok = graph.get("nodes_count", 0) > 0 and graph.get("edges_count", 0) > 0
        sim_ok = sim.get("total_actions", 0) > 0 and sim.get("simulated_hours", 0) > 0
        report_ok = report.get("section_count", 0) > 0 and bool(
            report.get("markdown_content", "").strip()
        )

        score = (graph_ok + sim_ok + report_ok) / 3.0
        return max(0.0, min(1.0, score))
