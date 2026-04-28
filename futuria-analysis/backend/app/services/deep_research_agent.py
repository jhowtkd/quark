"""
Deep Research Agent — LangGraph-based research pipeline.

Phases: search -> extract -> summarize -> format_sources -> END
Each phase calls external services (connectors, LLM) and writes structured
markdown artifacts to disk on success. Failures are logged at INFO level
and leave the draft.md unwritten (fail-closed).
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Dict, Any, List, Literal, TypedDict, Optional

from langgraph.graph import StateGraph, END

from ..connectors.fallback_router import ConnectorFallbackRouter
from ..profiles import ProfileManager, UserProfile
from ..utils.llm_client import LLMClient
from ..models.research_run import ResearchRunManager, ResearchRunStatus

logger = logging.getLogger(__name__)


# ─── State ────────────────────────────────────────────────────────────────────

class ResearchState(TypedDict, total=False):
    """Shared state threaded through the research graph nodes."""
    query: str
    profile: str  # User profile for research focus
    graph_id: str  # Zep graph ID for health check
    search_results: List[Dict[str, Any]]
    claims: str
    summary: str
    sources: str
    status: str          # 'searching' | 'extracting' | 'summarizing' | 'completed' | 'failed'
    error: str
    retry_count: int
    connector_used: str  # Set on success for observability
    fallback_used: bool  # Whether external search fallback was triggered


# ─── Node implementations ─────────────────────────────────────────────────────

def search_node(state: ResearchState) -> Dict[str, Any]:
    """
    Phase 1 — Discovery & Extraction via ConnectorFallbackRouter.

    Checks graph health first. If graph is empty/sparse, uses external search immediately.
    If graph is healthy, attempts graph search then supplements with external search.

    Logs each connector attempt at INFO level for observability.
    Sets connector_used in state on success.
    """
    query = state["query"]
    profile = state.get("profile", "generico")
    graph_id = state.get("graph_id", "")

    # Apply profile-specific research suffix
    try:
        config = ProfileManager.get_profile_or_default(profile)
        suffix = getattr(config, 'deep_research_prompt_suffix', '')
        if suffix:
            query = f"{query}\n{suffix}"
    except Exception as e:
        logger.debug(f"[research] Could not apply profile suffix: {e}")

    logger.info(f"[research] Phase=searching query={query!r} profile={profile} graph_id={graph_id}")

    all_results: List[Dict[str, Any]] = []
    fallback_used = False
    connector_used = "none"

    # ── Graph health check and graph search ──
    if graph_id:
        try:
            from .zep_tools import ZepToolsService
            zep = ZepToolsService()
            health = zep.check_graph_health(graph_id)
            health_status = health.get("status", "unknown")
            logger.info(f"[research] Graph health={health_status} nodes={health.get('node_count')} facts={health.get('facts_count')}")

            if health_status == "healthy":
                # Try graph search as primary source
                graph_search = zep.search_graph(graph_id, state["query"], limit=15, scope="edges")
                if graph_search.facts:
                    for fact in graph_search.facts[:10]:
                        all_results.append({
                            "url": f"zep://graph/{graph_id}",
                            "content": fact,
                            "title": "Zep Graph Fact",
                        })
                    logger.info(f"[research] Graph search returned {len(graph_search.facts)} facts")
                else:
                    logger.info("[research] Graph healthy but no relevant facts for query")
            elif health_status in ("empty", "no_facts", "sparse"):
                logger.info(f"[research] Graph {health_status}, will rely on external search")
                fallback_used = True
        except Exception as e:
            logger.warning(f"[research] Graph health check/search failed: {e}")
            fallback_used = True

    # ── External search (fallback or supplement) ──
    try:
        router = ConnectorFallbackRouter()
        result = router.search(query)

        if result.success and result.results:
            all_results.extend(result.results)
            connector_used = result.source
            logger.info(f"[research] External search success connector={result.source} results={len(result.results)}")
        else:
            error_msg = result.error or "No results returned"
            logger.warning(f"[research] External search failed: {error_msg}")
            if not all_results:
                return {
                    "search_results": [],
                    "status": "failed",
                    "error": error_msg,
                    "connector_used": "none",
                    "fallback_used": True,
                }
    except Exception as e:
        logger.warning(f"[research] External search exception: {e}")
        if not all_results:
            return {
                "search_results": [],
                "status": "failed",
                "error": str(e),
                "connector_used": "none",
                "fallback_used": True,
            }

    logger.info(f"[research] Phase=searching status=success total_results={len(all_results)} fallback={fallback_used}")
    return {
        "search_results": all_results,
        "status": "extracting",
        "connector_used": connector_used,
        "fallback_used": fallback_used,
    }


def extract_node(state: ResearchState) -> Dict[str, Any]:
    """
    Phase 2 — Extract key claims from search results via LLM.

    Prompts the LLM to produce 3-5 numbered claims with inline citations.
    Applies profile-specific rules to ensure factual, actionable output.
    No user query or content is logged — only phase name and short error strings.
    """
    results = state.get("search_results", [])
    profile = state.get("profile", "generico")
    logger.info("[research] Phase=extracting")

    if not results:
        return {"status": "failed", "error": "No search results to extract from"}

    # Build a concise context string from search results (url + content snippet)
    context_parts = []
    for i, item in enumerate(results[:5], start=1):
        url = item.get("url", "")
        content = item.get("content", "")
        snippet = content[:600].replace("\n", " ").strip() if content else ""
        context_parts.append(f"[{i}] URL: {url}\n{snippet}\n")

    context_str = "\n\n".join(context_parts)

    # Apply profile rules to extraction prompt
    profile_rules = ""
    try:
        config = ProfileManager.get_profile_or_default(profile)
        max_words = getattr(config, 'max_words_per_sentence', 25)
        profile_rules = (
            f"\nProfile: {profile}. Rules:\n"
            f"- Max {max_words} words per sentence\n"
            f"- No poetic adjectives, metaphors, or figurative language\n"
            f"- Every claim must cite a source\n"
            f"- Use numeric notation (1,5% not 'um virgula cinco')\n"
            f"- If insufficient data, write 'Dados insuficientes' for that claim\n"
        )
    except Exception:
        pass

    messages = [
        {
            "role": "system",
            "content": (
                "You are a research assistant. Based on the provided sources, "
                "extract 3-5 key factual claims. For each claim, include a citation "
                "in brackets like [N] where N is the source number. "
                "Return ONLY the numbered list of claims, no preamble or explanation."
                f"{profile_rules}"
            ),
        },
        {
            "role": "user",
            "content": f"Sources:\n{context_str}\n\nExtract the key claims:",
        },
    ]

    try:
        llm = LLMClient()
        raw_claims = llm.chat(messages, temperature=0.3, max_tokens=1024)
        claims_text = raw_claims.strip()

        if not claims_text:
            raise ValueError("LLM returned empty claims")

        logger.info("[research] Phase=extracting status=success")
        return {"claims": claims_text, "status": "summarizing", "fallback_used": state.get("fallback_used", False)}

    except Exception as e:
        logger.warning(f"[research] Phase=extracting status=failed error={str(e)[:80]}")
        return {"status": "failed", "error": f"Extraction failed: {str(e)[:120]}", "fallback_used": state.get("fallback_used", False)}


def summarize_node(state: ResearchState) -> Dict[str, Any]:
    """
    Phase 3 — Write the Summary section via LLM.

    Produces a 2-4 paragraph overview based on the claims.
    Applies profile rules for language and structure.
    No user query or artifact content logged.
    """
    claims = state.get("claims", "")
    profile = state.get("profile", "generico")
    logger.info("[research] Phase=summarizing")

    if not claims:
        return {"status": "failed", "error": "No claims to summarize"}

    # Apply profile rules to summary prompt
    profile_rules = ""
    try:
        config = ProfileManager.get_profile_or_default(profile)
        max_words = getattr(config, 'max_words_per_sentence', 25)
        profile_rules = (
            f"\nProfile: {profile}. Rules:\n"
            f"- Max {max_words} words per sentence\n"
            f"- No poetic adjectives, metaphors, or figurative language\n"
            f"- Every factual claim must cite a source using [N] notation\n"
            f"- Use numeric notation (1,5% not 'um virgula cinco')\n"
            f"- If insufficient data, write 'Nao possuo informacoes suficientes' explicitly\n"
        )
    except Exception:
        pass

    messages = [
        {
            "role": "system",
            "content": (
                "You are a research report writer. Based on the claims provided, "
                "write a 2-4 paragraph neutral overview of the topic. "
                "Use the citations [N] from the claims. "
                "Return ONLY the summary text, no headings or labels."
                f"{profile_rules}"
            ),
        },
        {
            "role": "user",
            "content": f"Claims:\n{claims}\n\nWrite the summary:",
        },
    ]

    try:
        llm = LLMClient()
        summary_text = llm.chat(messages, temperature=0.4, max_tokens=2048).strip()

        if not summary_text:
            raise ValueError("LLM returned empty summary")

        logger.info("[research] Phase=summarizing status=success")
        return {"summary": summary_text, "status": "formatting", "fallback_used": state.get("fallback_used", False)}

    except Exception as e:
        logger.warning(f"[research] Phase=summarizing status=failed error={str(e)[:80]}")
        return {"status": "failed", "error": f"Summarization failed: {str(e)[:120]}", "fallback_used": state.get("fallback_used", False)}


def sources_node(state: ResearchState) -> Dict[str, Any]:
    """
    Phase 4 — Format the Sources list from search results.

    Returns a bulleted markdown list of sources with number, title, URL, and date.
    """
    results = state.get("search_results", [])
    logger.info("[research] Phase=formatting sources")

    if not results:
        return {"status": "failed", "error": "No search results to format as sources"}

    today = datetime.now().strftime("%Y-%m-%d")
    source_lines: List[str] = []

    for i, item in enumerate(results[:10], start=1):
        url = item.get("url", "")
        title = item.get("title", "")
        # Clean up title — use URL path as fallback title
        if not title or title == url:
            title = url.split("/")[-1].replace("-", " ").replace("_", " ").strip()
            if not title:
                title = url

        source_lines.append(f"- [{i}] {title} — {url} (accessed {today})")

    formatted_sources = "\n".join(source_lines)

    logger.info(f"[research] Phase=formatting sources status=completed source_count={len(source_lines)} fallback={state.get('fallback_used', False)}")
    return {"sources": formatted_sources, "status": "completed", "fallback_used": state.get("fallback_used", False)}


# ─── Graph builder ─────────────────────────────────────────────────────────────

def _build_graph() -> StateGraph:
    """
    Construct the research pipeline graph.

    Edges:
      search_node  -> extract_node  (if results present)
      search_node  -> END           (if no results)
      extract_node -> summarize_node
      summarize_node -> sources_node
      sources_node  -> END
      Any node can return status='failed' -> END
    """
    g = StateGraph(ResearchState)

    g.add_node("search_node", search_node)
    g.add_node("extract_node", extract_node)
    g.add_node("summarize_node", summarize_node)
    g.add_node("sources_node", sources_node)

    def route_after_search(state: ResearchState) -> Literal["extract_node", "__end__"]:
        if state.get("search_results"):
            return "extract_node"
        return END

    g.set_entry_point("search_node")
    g.add_conditional_edges(
        "search_node",
        route_after_search,
        {
            "extract_node": "extract_node",
            END: END,
        },
    )
    g.add_conditional_edges(
        "extract_node",
        lambda s: "summarize_node" if s.get("status") != "failed" else END,
    )
    g.add_conditional_edges(
        "summarize_node",
        lambda s: "sources_node" if s.get("status") != "failed" else END,
    )
    g.add_edge("sources_node", END)

    return g


# Singleton compiled graph
_COMPILED_GRAPH = None


def compile_research_graph():
    """
    Return a cached compiled LangGraph.

    Returns:
        CompiledGraph ready for .invoke()
    """
    global _COMPILED_GRAPH
    if _COMPILED_GRAPH is None:
        _COMPILED_GRAPH = _build_graph().compile()
    return _COMPILED_GRAPH


# ─── Artifact validation ───────────────────────────────────────────────────────

def validate_artifact(
    markdown_content: str,
    run_id: str,
) -> bool:
    """
    Check that a draft.md has non-empty Summary, Claims, and Sources sections.

    Returns True if valid; on failure, marks the run as FAILED in the DB.
    """
    sections = ["Summary", "Claims", "Sources"]
    missing = []

    for section in sections:
        pattern = rf"(?i)^##\s+{section}\s*$"
        # Check the section exists and has content after it
        match = re.search(pattern, markdown_content, re.MULTILINE)
        if not match:
            missing.append(section)
            continue

        # Find the next heading or end of file
        start = match.end()
        next_heading = re.search(r"\n##\s+", markdown_content[start:])
        section_body = (
            markdown_content[
                start : start + next_heading.start() if next_heading else None
            ]
            .strip()
        )
        if not section_body:
            missing.append(section)

    if missing:
        logger.warning(
            f"[research] Artifact validation failed for run={run_id} "
            f"missing_sections={missing}"
        )
        ResearchRunManager().fail_run(run_id, error=f"Missing sections: {', '.join(missing)}")
        return False

    return True


# ─── Artifact writer ──────────────────────────────────────────────────────────

def write_draft(
    run_id: str,
    query: str,
    summary: str,
    claims: str,
    sources: str,
    connector_used: str,
) -> str:
    """
    Render the structured markdown artifact to disk.

    Returns the path to the written draft.md file.
    Raises on I/O errors.
    """
    draft_path = ResearchRunManager._get_draft_path(run_id)

    markdown = f"""# Deep Research: {query}

## Summary
{summary}

## Claims
{claims}

## Sources
{sources}

---
*Research generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} via {connector_used}*
"""
    with open(draft_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    logger.info(f"[research] Draft written run={run_id} path={draft_path} "
                f"connector={connector_used}")
    return draft_path


# ─── Public API ──────────────────────────────────────────────────────────────

def run_deep_research(
    query: str,
    run_id: str,
    profile: str = "generico",
    graph_id: str = "",
) -> Dict[str, Any]:
    """
    Execute the full deep research pipeline with profile and graph awareness.

    Args:
        query: Research query
        run_id: Research run identifier
        profile: User profile (marketing, direito, economia, saude, generico)
        graph_id: Zep graph ID for health check and graph search

    Returns:
        Dict with 'draft_path', 'status', 'connector_used', 'fallback_used'
    """
    graph = compile_research_graph()
    initial_state: ResearchState = {
        "query": query,
        "profile": profile,
        "graph_id": graph_id,
        "search_results": [],
        "status": "searching",
        "retry_count": 0,
        "connector_used": "none",
        "fallback_used": False,
    }

    result = graph.invoke(initial_state)

    if result.get("status") == "completed":
        draft_path = write_draft(
            run_id=run_id,
            query=query,
            summary=result.get("summary", ""),
            claims=result.get("claims", ""),
            sources=result.get("sources", ""),
            connector_used=result.get("connector_used", "none"),
        )
        is_valid = validate_artifact(
            open(draft_path, "r", encoding="utf-8").read(),
            run_id,
        )
        return {
            "draft_path": draft_path,
            "status": "completed" if is_valid else "validation_failed",
            "connector_used": result.get("connector_used", "none"),
            "fallback_used": result.get("fallback_used", False),
        }

    # Mark run as failed if pipeline did not complete
    error_msg = result.get("error", "Unknown error")
    ResearchRunManager().fail_run(run_id, error=error_msg)
    return {
        "draft_path": "",
        "status": "failed",
        "error": error_msg,
        "connector_used": result.get("connector_used", "none"),
        "fallback_used": result.get("fallback_used", False),
    }
