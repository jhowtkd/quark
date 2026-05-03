#!/usr/bin/env python3
"""
Onboarding fixture runner for FUTUR.IA.

Loads the onboarding_saude_fixture.json, runs the pipeline up to Step4
(report generation) using mocked/injected services, and verifies expected outputs.

Usage:
    python scripts/run_onboarding_fixture.py
    python scripts/run_onboarding_fixture.py --dry-run
"""

import argparse
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── ensure backend imports work ──
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))


# ═══════════════════════════════════════════════════════════════
# Mock services
# ═══════════════════════════════════════════════════════════════

class MockLLMClient:
    """Mock LLMClient returning controlled responses for report generation."""

    def __init__(
        self,
        responses: Optional[List[str]] = None,
        json_responses: Optional[List[Dict[str, Any]]] = None,
        default_response: str = "mock response",
        default_json_response: Optional[Dict[str, Any]] = None,
    ):
        self.responses = responses or []
        self.json_responses = json_responses or []
        self.default_response = default_response
        self.default_json_response = default_json_response or {"mock": "response"}
        self.call_count = 0
        self.chat_calls: List[dict] = []
        self.chat_json_calls: List[dict] = []

    def chat(
        self,
        messages=None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None,
        observation: Any = None,
        generation_name: Optional[str] = None,
        generation_metadata: Optional[dict] = None,
    ) -> str:
        self.call_count += 1
        self.chat_calls.append(
            {
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "response_format": response_format,
            }
        )
        if self.responses:
            idx = min(self.call_count - 1, len(self.responses) - 1)
            return self.responses[idx]
        return self.default_response

    def chat_json(
        self,
        messages=None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        observation: Any = None,
        generation_name: Optional[str] = None,
        generation_metadata: Optional[dict] = None,
    ) -> Dict[str, Any]:
        self.call_count += 1
        self.chat_json_calls.append(
            {
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        )
        if self.json_responses:
            idx = min(self.call_count - 1, len(self.json_responses) - 1)
            return self.json_responses[idx]
        return self.default_json_response


class MockZepToolsService:
    """Mock ZepToolsService avoiding external API calls."""

    def __init__(self):
        self.search_calls: List[dict] = []

    def check_graph_health(self, graph_id: str) -> Dict[str, Any]:
        return {"status": "healthy", "graph_id": graph_id}

    def get_all_nodes(self, graph_id: str):
        from app.services.zep_tools import NodeInfo
        return [
            NodeInfo(
                uuid="n1",
                name="Secretaria de Saude",
                labels=["Entity", "Organization"],
                summary="Secretaria Municipal de Saude de Sao Paulo",
            ),
            NodeInfo(
                uuid="n2",
                name="Biotech Futura",
                labels=["Entity", "Company"],
                summary="Laboratorio farmaceutico ficticio",
            ),
        ]

    def get_all_edges(self, graph_id: str, include_temporal: bool = True):
        return []

    def get_node_detail(self, node_uuid: str):
        return None

    def get_node_edges(self, graph_id: str, node_uuid: str):
        return []

    def get_entities_by_type(self, graph_id: str, entity_type: str):
        return []

    def get_graph_statistics(self, graph_id: str) -> Dict[str, Any]:
        return {
            "total_nodes": 2,
            "total_edges": 1,
            "entity_types": {"Organization": 1, "Company": 1},
        }

    def search_graph(self, graph_id: str, query: str, limit: int = 10, scope: str = "edges"):
        from app.services.zep_tools import SearchResult
        self.search_calls.append(
            {"graph_id": graph_id, "query": query, "limit": limit, "scope": scope}
        )
        return SearchResult(
            facts=[
                "A Secretaria de Saude lancou a Campanha Vacina para Todos em janeiro de 2026.",
                "A campanha planeja vacinar 85% da populacao adulta ate marco de 2026.",
            ],
            entities=["Secretaria de Saude", "Biotech Futura"],
            relationships=[],
        )

    def _local_search(self, graph_id: str, query: str, limit: int = 10, scope: str = "edges"):
        return self.search_graph(graph_id, query, limit, scope)

    def insight_forge(self, graph_id: str, query: str, simulation_requirement: str, report_context: str = "", max_sub_queries: int = 5, observation: Any = None):
        from app.services.zep_tools import InsightForgeResult
        return InsightForgeResult(
            facts=[
                "Fato 1: A campanha de vacinacao ficticia foi bem recebida pela comunidade medica.",
                "Fato 2: Grupos antivacina organizaram protestos nas redes sociais.",
            ],
            central_entities=["Secretaria de Saude", "Biotech Futura"],
            relationship_chains=["Secretaria de Saude -> contrata -> Biotech Futura"],
            analysis="A simulacao mostra reacao mista da comunidade.",
        )

    def _generate_sub_queries(self, query: str, simulation_requirement: str, report_context: str = "", max_queries: int = 5, observation: Any = None):
        return [f"subquery {i}" for i in range(1, max_queries + 1)]

    def panorama_search(self, graph_id: str, query: str, include_expired: bool = True, limit: int = 50):
        from app.services.zep_tools import PanoramaResult
        return PanoramaResult(
            active_facts=["A campanha atingiu 60% da meta de vacinacao."],
            historical_facts=["Lancamento ocorreu em janeiro de 2026."],
            involved_entities=["Secretaria de Saude", "Biotech Futura"],
            timeline="Janeiro: lancamento. Fevereiro: primeiro relatorio.",
        )

    def quick_search(self, graph_id: str, query: str, limit: int = 10):
        from app.services.zep_tools import SearchResult
        return SearchResult(
            facts=["Resultado rapido para: " + query],
            entities=[],
            relationships=[],
        )

    def get_simulation_context(self, graph_id: str, simulation_requirement: str, limit: int = 30) -> Dict[str, Any]:
        stats = self.get_graph_statistics(graph_id)
        return {
            "simulation_requirement": simulation_requirement,
            "related_facts": [
                "A Secretaria de Saude lancou a Campanha Vacina para Todos.",
                "A campanha usa o chatbot DoutorVirtual para agendamentos.",
            ],
            "graph_statistics": stats,
            "entities": [
                {"name": "Secretaria de Saude", "type": "Organization", "summary": "Secretaria Municipal de Saude"},
                {"name": "Biotech Futura", "type": "Company", "summary": "Laboratorio farmaceutico"},
            ],
            "total_entities": 2,
        }

    def get_entity_summary(self, graph_id: str, entity_name: str) -> Dict[str, Any]:
        return {"entity_name": entity_name, "entity_info": None, "related_facts": [], "related_edges": [], "total_relations": 0}

    def interview_agents(self, simulation_id: str, interview_requirement: str, simulation_requirement: str = "", max_agents: int = 5, custom_questions: None = None):
        from app.services.zep_tools import InterviewResult
        return InterviewResult(
            agents=[
                {"name": "DrSilva", "role": "Medico", "platform": "twitter", "answer": "A campanha e bem-vinda, mas precisa de mais postos."},
                {"name": "AnaSaude", "role": "Influencer", "platform": "twitter", "answer": "Vacinem-se! A gripe X-42 e perigosa."},
            ],
            comparison="Medicos apoiam, mas alertam para logistica. Influenciadores sao entusiasticos.",
        )


# ═══════════════════════════════════════════════════════════════
# Runner
# ═══════════════════════════════════════════════════════════════

def validate_fixture(fixture_path: Path) -> Dict[str, Any]:
    """Load and validate the fixture JSON."""
    with open(fixture_path, "r", encoding="utf-8") as f:
        fixture = json.load(f)

    required_top = {"input_text", "ontology_config", "simulation_config", "expected_outputs"}
    missing = required_top - set(fixture.keys())
    if missing:
        raise ValueError(f"Fixture missing top-level keys: {missing}")

    sim_cfg = fixture["simulation_config"]
    for key in ("maxRounds", "minutesPerRound", "platforms", "echo_chamber_strength"):
        if key not in sim_cfg:
            raise ValueError(f"simulation_config missing key: {key}")

    exp = fixture["expected_outputs"]
    for key in ("report", "simulated_hours"):
        if key not in exp:
            raise ValueError(f"expected_outputs missing key: {key}")

    return fixture


def build_mock_llm_responses() -> tuple[list[Dict[str, Any]], list[str]]:
    """Return (json_responses, text_responses) for the mocked LLM."""
    outline_json = {
        "title": "Relatorio da Campanha Vacina para Todos - 2026",
        "summary": "A simulacao da campanha de vacinacao ficticia mostra adesao majoritaria, mas resistencia organizada de grupos antivacina.",
        "sections": [
            {"title": "Cenario de Lancamento e Adesao Inicial", "description": "Como foi o lancamento e a primeira adesao do publico."},
            {"title": "Reacao da Comunidade Medica", "description": "Posicionamento de endocrinologistas e outros profissionais."},
            {"title": "Impacto nas Redes Sociais", "description": "Dinamica de discurso no Twitter durante a simulacao."},
            {"title": "Conclusoes e Recomendacoes", "description": "Sintese dos achados e proximos passos sugeridos."},
        ],
    }

    section_contents = [
        "Final Answer: O lancamento da Campanha Vacina para Todos em janeiro de 2026 contou com 120 postos volantes e um chatbot de agendamento. A adesao inicial foi positiva, com filas nos primeiros dias. A parceria com farmacias populares ampliou o alcance, mas a falta de refrigeracao em alguns postos gerou filas e descontentamento.",
        "Final Answer: A comunidade medica, representada por endocrinologistas e enfermeiros, reagiu de forma favoravel. O concurso para 300 enfermeiros temporarios foi visto como necessario. Alguns medicos alertaram para a logistica de distribuicao das 500 mil doses da Biotech Futura.",
        "Final Answer: No Twitter, a simulacao mostrou eco de 0,3 de camaras de reverb. Influenciadores de saude promoveram a campanha com hashtags positivas. Grupos antivacina organizaram threads de desinformacao, mas tiveram alcance limitado devido ao engajamento majoritario favoravel.",
        "Final Answer: A simulacao indica que a campanha atingira a meta de 85% de vacinacao se os desafios logisticos forem resolvidos. Recomenda-se reforcar a refrigeracao dos postos volantes e ampliar o chatbot DoutorVirtual para outras plataformas. O monitoramento de discurso antivacina deve continuar.",
    ]

    json_responses = [outline_json]
    text_responses = section_contents
    return json_responses, text_responses


def run_pipeline(fixture: Dict[str, Any]) -> Dict[str, Any]:
    """Run the pipeline up to Step4 (report generation) with mocked services."""
    from app.services.report_agent import ReportAgent, ReportStatus
    from app.config import Config

    # Use a temporary uploads directory so we don't pollute the real one
    original_upload_folder = getattr(Config, "UPLOAD_FOLDER", None)
    tmpdir = tempfile.mkdtemp(prefix="onboarding_fixture_")
    Config.UPLOAD_FOLDER = tmpdir

    try:
        json_responses, text_responses = build_mock_llm_responses()
        mock_llm = MockLLMClient(
            json_responses=json_responses,
            responses=text_responses,
            default_response="Final Answer: Resposta padrao da secao simulada.",
        )
        mock_zep = MockZepToolsService()

        agent = ReportAgent(
            graph_id="graph_onboarding_test",
            simulation_id="sim_onboarding_test",
            simulation_requirement=(
                "Simular a reacao da comunidade medica e do publico geral a campanha "
                "de vacinacao ficticia Vacina para Todos em 2026."
            ),
            llm_client=mock_llm,
            zep_tools=mock_zep,
            profile="saude",
            debug_mode=True,
        )

        report = agent.generate_report(
            progress_callback=lambda stage, prog, msg: print(f"  [{stage}] {prog}% - {msg}"),
            report_id="report_onboarding_test",
        )

        result = {
            "report_status": report.status.value if hasattr(report.status, "value") else str(report.status),
            "report_title": report.outline.title if report.outline else "",
            "report_summary": report.outline.summary if report.outline else "",
            "report_body": report.markdown_content or "",
            "section_count": len(report.outline.sections) if report.outline else 0,
            "section_titles": [s.title for s in report.outline.sections] if report.outline else [],
            "has_conclusions": any(
                "conclus" in s.title.lower() or "conclusion" in s.title.lower()
                for s in (report.outline.sections if report.outline else [])
            ),
            "simulated_hours": fixture["simulation_config"]["maxRounds"] * fixture["simulation_config"]["minutesPerRound"] / 60.0,
        }
        return result

    finally:
        if original_upload_folder is not None:
            Config.UPLOAD_FOLDER = original_upload_folder
        shutil.rmtree(tmpdir, ignore_errors=True)


def verify_outputs(result: Dict[str, Any], expected: Dict[str, Any]) -> List[str]:
    """Verify actual outputs against expected_outputs. Returns list of errors."""
    errors: List[str] = []
    report_exp = expected.get("report", {})

    if report_exp.get("must_have_title") and not result.get("report_title"):
        errors.append("Report missing title")
    if report_exp.get("must_have_summary") and not result.get("report_summary"):
        errors.append("Report missing summary")
    if report_exp.get("must_have_body") and not result.get("report_body"):
        errors.append("Report missing body")
    if report_exp.get("must_have_conclusions") and not result.get("has_conclusions"):
        errors.append("Report missing conclusions section")

    threshold = expected.get("simulated_hours", 0)
    if result.get("simulated_hours", 0) <= threshold:
        errors.append(
            f"simulated_hours ({result.get('simulated_hours')}) must be > threshold ({threshold})"
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Run onboarding fixture pipeline.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate fixture JSON without running the pipeline.",
    )
    args = parser.parse_args()

    fixture_path = PROJECT_ROOT / "backend" / "tests" / "fixtures" / "onboarding_saude_fixture.json"

    print(f"Loading fixture: {fixture_path}")
    try:
        fixture = validate_fixture(fixture_path)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Fixture validation FAILED: {e}")
        return 1

    print("Fixture JSON is valid.")

    if args.dry_run:
        print("Dry-run mode: skipping pipeline execution.")
        return 0

    print("Running pipeline up to Step4 (report generation) with mocked services...")
    try:
        result = run_pipeline(fixture)
    except Exception as e:
        print(f"Pipeline execution FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("\nPipeline result:")
    print(f"  Status        : {result['report_status']}")
    print(f"  Title         : {result['report_title']}")
    print(f"  Summary       : {result['report_summary'][:100]}...")
    print(f"  Sections      : {result['section_count']}")
    print(f"  Section titles: {result['section_titles']}")
    print(f"  Has conclusions: {result['has_conclusions']}")
    print(f"  Simulated hours: {result['simulated_hours']}")

    errors = verify_outputs(result, fixture["expected_outputs"])
    if errors:
        print("\nVerification FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("\nAll verifications passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
