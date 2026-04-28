from app.services.zep_tools import ZepToolsService
from app.utils.locale import set_locale, t


class _FakeSearchResults:
    edges = []
    nodes = []


class _FakeGraphClient:
    def __init__(self) -> None:
        self.last_query = None

    def search(self, *, graph_id: str, query: str, limit: int, scope: str, reranker: str):
        self.last_query = query
        return _FakeSearchResults()


class _FakeClient:
    def __init__(self) -> None:
        self.graph = _FakeGraphClient()


def test_reporting_console_messages_are_plain_portuguese() -> None:
    set_locale("pt")

    assert t("report.startPlanningOutline") == "Planejando a estrutura geral do relatório..."
    assert t("report.reportSaved", reportId="report_123") == "Relatório salvo: report_123"
    assert t("console.zepAllRetriesFailed", operation="busca", retries=3, error="boom") == (
        "Falha ao consultar o Zep após 3 tentativas em busca: boom"
    )


def test_search_graph_truncates_query_before_sending_to_zep() -> None:
    service = object.__new__(ZepToolsService)
    service.client = _FakeClient()
    service.MAX_RETRIES = 1
    service.RETRY_DELAY = 0

    long_query = "A" * 450
    result = service.search_graph("graph_123", long_query, limit=5, scope="edges")

    assert service.client.graph.last_query is not None
    assert len(service.client.graph.last_query) <= 400
    assert result.query == service.client.graph.last_query
