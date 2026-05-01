"""
Report Agentservice
useLangChain + ZepimplementationReACTsimulationreport

function
1. according to simulation requirement andZepgraphinforeport
2. first plan directory structurethen generate by section
3. adoptReACTthoughtwith
4. supportwithdialoguein conversationcall
"""

import os
import json
import time
import re
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..config import Config
from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger
from ..utils.locale import get_reporting_language_instruction, t
from ..utils.language_integrity import assess_text_integrity, enforce_controlled_output, extract_entity_candidates
from ..profiles import ProfileManager, UserProfile
from .zep_tools import (
    ZepToolsService,
    SearchResult,
    InsightForgeResult,
    PanoramaResult,
    InterviewResult
)
from .data_validation import (
    DataValidationService,
    ValidationReport,
    DEFAULT_VALIDATION_THRESHOLDS,
)
from .bias_audit import (
    BiasAuditService,
    BiasReport,
)
from .quality_gates import (
    QualityGateService,
    QualityReport,
)

logger = get_logger('futuria.report_agent')


class ReportLogger:
    """
    Report Agent logger

    generate in report folder agent_log.jsonl log each detailed action
    count JSON objectcontains timestampaction typeetc
    """

    def __init__(self, report_id: str):
        """
        initializelogger

        Args:
            report_id: reportIDused to determine log file path
        """
        self.report_id = report_id
        self.log_file_path = os.path.join(
            Config.UPLOAD_FOLDER, 'reports', report_id, 'agent_log.jsonl'
        )
        self.start_time = datetime.now()
        self._ensure_log_file()

    def _ensure_log_file(self):
        """loginin"""
        log_dir = os.path.dirname(self.log_file_path)
        os.makedirs(log_dir, exist_ok=True)

    def _get_elapsed_time(self) -> float:
        """getfromstartin"""
        return (datetime.now() - self.start_time).total_seconds()

    def log(
        self,
        action: str,
        stage: str,
        details: Dict[str, Any],
        section_title: str = None,
        section_index: int = None
    ):
        """
        log one entry

        Args:
            action: action typesuch as 'start', 'tool_call', 'llm_response', 'section_complete' etc
            stage: phasesuch as 'planning', 'generating', 'completed'
            details: detailed content dictno truncation
            section_title: section title
            section_index: section
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": round(self._get_elapsed_time(), 2),
            "report_id": self.report_id,
            "action": action,
            "stage": stage,
            "section_title": section_title,
            "section_index": section_index,
            "details": details
        }

        #  JSONL
        with open(self.log_file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    def log_start(self, simulation_id: str, graph_id: str, simulation_requirement: str):
        """log report generation start"""
        self.log(
            action="report_start",
            stage="pending",
            details={
                "simulation_id": simulation_id,
                "graph_id": graph_id,
                "simulation_requirement": simulation_requirement,
                "provenance_version": "1.0",
                "message": t('report.taskStarted')
            }
        )

    def log_planning_start(self):
        """log outline planning start"""
        self.log(
            action="planning_start",
            stage="planning",
            details={"message": t('report.planningStart')}
        )

    def log_planning_context(self, context: Dict[str, Any]):
        """log context acquired during planning"""
        self.log(
            action="planning_context",
            stage="planning",
            details={
                "message": t('report.fetchSimContext'),
                "context": context
            }
        )

    def log_planning_complete(self, outline_dict: Dict[str, Any]):
        """recordoutline planning"""
        self.log(
            action="planning_complete",
            stage="planning",
            details={
                "message": t('report.planningComplete'),
                "outline": outline_dict
            }
        )

    def log_section_start(self, section_title: str, section_index: int):
        """recordsectionstart"""
        self.log(
            action="section_start",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={"message": t('report.sectionStart', title=section_title)}
        )

    def log_react_thought(self, section_title: str, section_index: int, iteration: int, thought: str):
        """record ReACT thought"""
        self.log(
            action="react_thought",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "iteration": iteration,
                "thought": thought,
                "message": t('report.reactThought', iteration=iteration)
            }
        )

    def log_tool_call(
        self,
        section_title: str,
        section_index: int,
        tool_name: str,
        parameters: Dict[str, Any],
        iteration: int,
        provenance_tag: str = None
    ):
        """recordcall"""
        self.log(
            action="tool_call",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "iteration": iteration,
                "tool_name": tool_name,
                "parameters": parameters,
                "provenance_tag": provenance_tag,
                "message": t('report.toolCall', toolName=tool_name)
            }
        )

    def log_tool_result(
        self,
        section_title: str,
        section_index: int,
        tool_name: str,
        result: str,
        iteration: int,
        provenance_tag: str = None
    ):
        """recordcallresultfull contentno truncation"""
        self.log(
            action="tool_result",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "iteration": iteration,
                "tool_name": tool_name,
                "result": result,  # resultno truncation
                "result_length": len(result),
                "provenance_tag": provenance_tag,
                "message": t('report.toolResult', toolName=tool_name)
            }
        )

    def log_llm_response(
        self,
        section_title: str,
        section_index: int,
        response: str,
        iteration: int,
        has_tool_calls: bool,
        has_final_answer: bool
    ):
        """record LLM full contentno truncation"""
        self.log(
            action="llm_response",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "iteration": iteration,
                "response": response,  # full responseno truncation
                "response_length": len(response),
                "has_tool_calls": has_tool_calls,
                "has_final_answer": has_final_answer,
                "message": t('report.llmResponse', hasToolCalls=has_tool_calls, hasFinalAnswer=has_final_answer)
            }
        )

    def log_section_content(
        self,
        section_title: str,
        section_index: int,
        content: str,
        tool_calls_count: int
    ):
        """recordsectionrecorddoes not mean section complete"""
        self.log(
            action="section_content",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "content": content,  # full contentno truncation
                "content_length": len(content),
                "tool_calls_count": tool_calls_count,
                "message": t('report.sectionContentDone', title=section_title)
            }
        )

    def log_section_full_complete(
        self,
        section_title: str,
        section_index: int,
        full_content: str
    ):
        """
        recordsection

        logcountsectionand get full content
        """
        self.log(
            action="section_complete",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "content": full_content,
                "content_length": len(full_content),
                "message": t('report.sectionComplete', title=section_title)
            }
        )

    def log_report_complete(self, total_sections: int, total_time_seconds: float):
        """recordreport"""
        self.log(
            action="report_complete",
            stage="completed",
            details={
                "total_sections": total_sections,
                "total_time_seconds": round(total_time_seconds, 2),
                "message": t('report.reportComplete')
            }
        )

    def log_error(self, error_message: str, stage: str, section_title: str = None):
        """record"""
        self.log(
            action="error",
            stage=stage,
            section_title=section_title,
            section_index=None,
            details={
                "error": error_message,
                "message": t('report.errorOccurred', error=error_message)
            }
        )


class ReportConsoleLogger:
    """
    Report Agent console logger

    console style logINFOWARNINGetcwrite to report folder console_log.txt
    logwith agent_log.jsonl differentis plain text console output
    """

    def __init__(self, report_id: str):
        """
        initializeconsole logger

        Args:
            report_id: reportIDused to determine log file path
        """
        self.report_id = report_id
        self.log_file_path = os.path.join(
            Config.UPLOAD_FOLDER, 'reports', report_id, 'console_log.txt'
        )
        self._ensure_log_file()
        self._file_handler = None
        self._setup_file_handler()

    def _ensure_log_file(self):
        """loginin"""
        log_dir = os.path.dirname(self.log_file_path)
        os.makedirs(log_dir, exist_ok=True)

    def _setup_file_handler(self):
        """write log to file simultaneously"""
        import logging

        #
        self._file_handler = logging.FileHandler(
            self.log_file_path,
            mode='a',
            encoding='utf-8'
        )
        self._file_handler.setLevel(logging.INFO)

        # usewithformat
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        self._file_handler.setFormatter(formatter)

        #  report_agent related logger
        loggers_to_attach = [
            'futuria.report_agent',
            'futuria.zep_tools',
        ]

        for logger_name in loggers_to_attach:
            target_logger = logging.getLogger(logger_name)
            # avoid duplicate add
            if self._file_handler not in target_logger.handlers:
                target_logger.addHandler(self._file_handler)

    def close(self):
        """from logger remove from"""
        import logging

        if self._file_handler:
            loggers_to_detach = [
                'futuria.report_agent',
                'futuria.zep_tools',
            ]

            for logger_name in loggers_to_detach:
                target_logger = logging.getLogger(logger_name)
                if self._file_handler in target_logger.handlers:
                    target_logger.removeHandler(self._file_handler)

            self._file_handler.close()
            self._file_handler = None

    def __del__(self):
        """ensure close file handler on destruct"""
        self.close()


class ReportStatus(str, Enum):
    """report"""
    PENDING = "pending"
    PLANNING = "planning"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ReportSection:
    """report section"""
    title: str
    content: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content
        }

    def to_markdown(self, level: int = 2) -> str:
        """convert toMarkdownformat"""
        md = f"{'#' * level} {self.title}\n\n"
        if self.content:
            md += f"{self.content}\n\n"
        return md


@dataclass
class ReportOutline:
    """report"""
    title: str
    summary: str
    sections: List[ReportSection]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "summary": self.summary,
            "sections": [s.to_dict() for s in self.sections]
        }

    def to_markdown(self) -> str:
        """convert toMarkdownformat"""
        md = f"# {self.title}\n\n"
        md += f"> {self.summary}\n\n"
        for section in self.sections:
            md += section.to_markdown()
        return md


@dataclass
class Report:
    """report"""
    report_id: str
    simulation_id: str
    graph_id: str
    simulation_requirement: str
    status: ReportStatus
    outline: Optional[ReportOutline] = None
    markdown_content: str = ""
    created_at: str = ""
    completed_at: str = ""
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "simulation_id": self.simulation_id,
            "graph_id": self.graph_id,
            "simulation_requirement": self.simulation_requirement,
            "status": self.status.value,
            "outline": self.outline.to_dict() if self.outline else None,
            "markdown_content": self.markdown_content,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "error": self.error
        }


# ═══════════════════════════════════════════════════════════════
# Prompt template constants
# ═══════════════════════════════════════════════════════════════

# ── tool description ──

TOOL_DESC_INSIGHT_FORGE = """[Deep Search - High Signal Retrieval]
Use this tool when a chapter needs multi-angle evidence instead of a single fact lookup. It will:
1. Break the question into focused sub-questions
2. Search the simulation graph across multiple dimensions
3. Combine semantic facts, entity insights, and relationship chains
4. Return the richest available context for report writing

[Best Use Cases]
- Deep analysis of a theme or conflict
- Chapters that need multiple supporting angles
- Cases where simple search is too shallow

[Returned Content]
- Directly quotable facts
- Central entity insights
- Relationship-chain analysis"""

TOOL_DESC_PANORAMA_SEARCH = """[Panorama Search - Full Situation View]
Use this tool to get the broadest available view of the simulated future. It will:
1. Gather relevant nodes and relationships
2. Separate active facts from historical or expired facts
3. Show how the situation evolved over time

[Best Use Cases]
- Understanding the full event arc
- Comparing current and historical states
- Getting a broad map before writing conclusions

[Returned Content]
- Active facts
- Historical or expired facts
- Involved entities"""

TOOL_DESC_QUICK_SEARCH = """[Quick Search - Direct Fact Lookup]
Use this lightweight tool for specific and direct fact checks.

[Best Use Cases]
- Verify one concrete claim
- Retrieve a small set of directly relevant facts
- Resolve a narrow uncertainty quickly

[Returned Content]
- The most relevant facts for the query"""

TOOL_DESC_INTERVIEW_AGENTS = """[Interview Agents - First-Person Simulation Responses]
Use this tool to call the OASIS interview API and gather direct answers from simulated agents. This is not an LLM roleplay shortcut. It queries the running simulation for first-person responses.

[Best Use Cases]
- Capture perspective differences across roles
- Add first-person evidence to a chapter
- Compare reactions from different simulated groups

[Returned Content]
- Agent identity and role
- Interview answers from the available platforms
- Quotable excerpts
- A short comparison of viewpoints

[Important]
The OASIS simulation environment must be running for this tool to work."""



# ── outline planning prompt ──

PLAN_SYSTEM_PROMPT = """\
You are writing a future-prediction report about a simulated world. The simulation is a rehearsal of a possible future, not a commentary on the current real world.
Write the entire outline in Portuguese brasileiro (pt-BR), including the title, summary, and all section titles.

[Core Task]
Design a concise report outline that explains:
1. What happened in the simulated future under the stated conditions
2. How different agent groups reacted and behaved
3. Which future trends, risks, and opportunities emerged

[Output Rules]
- Return valid JSON only
- Create between 2 and 5 sections
- Keep the outline concise and evidence-oriented
- Choose section titles that fit the simulation results rather than a fixed template
- Sentences max 25 words
- No poetic language, metaphors, or figurative expressions
- Use numeric notation for all numbers

Return JSON in this shape:
{
  "title": "Report title",
  "summary": "One-sentence summary of the main predicted finding",
  "sections": [
    {
      "title": "Section title",
      "description": "What this section covers"
    }
  ]
}"""

PLAN_USER_PROMPT_TEMPLATE = """\
[Simulation Requirement]
{simulation_requirement}

[Simulation Scale]
- Total participating entities: {total_nodes}
- Total generated relationships: {total_edges}
- Entity types present: {entity_types}
- Active agents: {total_entities}

[Sample Predicted Facts]
{related_facts_json}

Design the report structure that best explains the simulated future. Keep it concise, evidence-oriented, and limited to 2-5 sections."""

# ── section prompt ──

SECTION_SYSTEM_PROMPT_TEMPLATE = """\
You are writing one chapter of a future-prediction report about a simulated world.
Write this chapter entirely in Portuguese brasileiro (pt-BR), including the title, summary, headings, labels, and narrative text.

Report title: {report_title}
Report summary: {report_summary}
Simulation requirement: {simulation_requirement}
Current section: {section_title}

[Core Rules]
- Treat the simulation as a rehearsal of the future
- Use only evidence gathered from the simulation tools
- Do not inject outside knowledge
- Every chapter must use tools at least 3 times and at most 5 times
- Translate quoted source material into the report language before using it in the final answer
- If evidence is insufficient, say so plainly: "Nao possuo informacoes suficientes"

[HARD LANGUAGE RULES - VIOLATION IS AN ERROR]
- Maximum 25 words per sentence
- Prohibit poetic adjectives, metaphors, or figurative language
- Every factual claim must have an identifiable source
- Use numeric notation: 1,5% instead of "um virgula cinco"
- Never invent data; declare insufficiency explicitly
- Never use Chinese, Japanese, or Korean scripts
- Tables must be structured with headers and data rows only
- No emotional or superlative adjectives

[Formatting Rules]
- Do not add Markdown headings inside the chapter
- Do not repeat the section title at the top of the content
- Use bold text, lists, and block quotes to structure the chapter
- Quotes must be in their own paragraph

[Tooling]
{tools_description}

[Response Contract]
Each response may do exactly one of these:
1. Call one tool using XML format: <tool_call>{{"name": "tool_name", "parameters": {{"param": "value"}}}}</tool_call>
2. Start with "Final Answer:" and write the final chapter content

IMPORTANT: Use <tool_call> with JSON inside. Do NOT use <tool_name> or <parameters> tags - they will be ignored.
"""

SECTION_USER_PROMPT_TEMPLATE = """\
Previously completed chapters (read carefully to avoid repetition):
{previous_content}

Current task: write the section "{section_title}".

Before producing the final chapter, think about what information is still needed, call tools to gather it, and only then produce the final answer as plain body text with no heading."""

# ── ReACT loop ──

REACT_OBSERVATION_TEMPLATE = """\
Observation (tool result)

=== Tool: {tool_name} ===
{result}

Tool calls used: {tool_calls_count}/{max_tool_calls} (already used: {used_tools_str}){unused_hint}
- If the evidence is sufficient, start with "Final Answer:" and write the chapter
- If more evidence is needed, call one additional tool
"""

REACT_INSUFFICIENT_TOOLS_MSG = (
    "You have called tools only {tool_calls_count} times, but at least {min_tool_calls} calls are required before the final answer. "
    "Call more tools and gather more simulation evidence first.{unused_hint}"
)

REACT_INSUFFICIENT_TOOLS_MSG_ALT = (
    "Only {tool_calls_count} tool calls have been made so far; at least {min_tool_calls} are required. "
    "Call more tools and gather more simulation evidence.{unused_hint}"
)

REACT_TOOL_LIMIT_MSG = (
    "The tool-call limit has been reached ({tool_calls_count}/{max_tool_calls}). "
    "Produce the chapter immediately, starting with Final Answer:, using only the evidence already gathered."
)

REACT_UNUSED_TOOLS_HINT = (
    "\nYou have not used these tools yet: {unused_list}. "
    "Use different tools if the chapter still lacks multiple perspectives."
)

REACT_FORCE_FINAL_MSG = (
    "The tool-call limit has been reached. Produce the chapter now, starting with Final Answer:."
)

# ═══════════════════════════════════════════════════════════════
# Language Guard - Protection against script contamination
# ═══════════════════════════════════════════════════════════════


def _contains_forbidden_language(text: str) -> bool:
    """Return True when the text contains forbidden scripts for controlled output."""
    return not assess_text_integrity(text).ok


# ── Chat prompt ──

CHAT_SYSTEM_PROMPT_TEMPLATE = """\
You are a concise simulation-report assistant.
Answer in Portuguese brasileiro (pt-BR) unless the user explicitly requests another language.

[Context]
Simulation requirement: {simulation_requirement}

[Generated report content]
{report_content}

[Rules]
1. Prefer answers grounded in the generated report content
2. Be direct and concise
3. Call tools only when the report content is insufficient
4. Keep the answer well structured and easy to verify

[Available tools]
{tools_description}

[Tool-call format]
<tool_call>
{{"name": "tool_name", "parameters": {{"parameter_name": "value"}}}}
</tool_call>

[Answer style]
- Concise and direct
- Use block quotes for key cited material
- Lead with the conclusion, then explain briefly
- Preserve entity names exactly; never substitute a person or organization with a different proper noun
"""

CHAT_OBSERVATION_SUFFIX = "\n\nResponda de forma concisa em português brasileiro."


# ═══════════════════════════════════════════════════════════════
# ReportAgent main class
# ═══════════════════════════════════════════════════════════════


class ReportAgent:
    """
    Report Agent - simulationreportAgent

    adoptReACTReasoning + Acting
    1. phaseanalyze simulation requirementplan report directory structure
    2. phasesectionsectioncallgetinfo
    3. phasecheck content completeness and accuracy
    """

    # callcountsection
    MAX_TOOL_CALLS_PER_SECTION = 5

    # max reflection rounds
    MAX_REFLECTION_ROUNDS = 3

    # dialoguecall
    MAX_TOOL_CALLS_PER_CHAT = 2

    def __init__(
        self,
        graph_id: str,
        simulation_id: str,
        simulation_requirement: str,
        llm_client: Optional[LLMClient] = None,
        zep_tools: Optional[ZepToolsService] = None,
        observability_client: Optional[Any] = None,
        profile: str = "generico",
    ):
        """
        initializeReport Agent

        Args:
            graph_id: graphID
            simulation_id: simulationID
            simulation_requirement: simulation
            llm_client: LLMclient
            zep_tools: Zepservice
            observability_client: Langfuse observability client (optional, from app.observability).
            profile: User profile for report generation (marketing, direito, economia, saude, generico)
        """
        self.graph_id = graph_id
        self.simulation_id = simulation_id
        self.simulation_requirement = simulation_requirement

        self.llm = llm_client or LLMClient()
        self.zep_tools = zep_tools or ZepToolsService()
        self.observability_client = observability_client

        # Profile configuration
        self.profile_name = profile or "generico"
        self.profile_manager = ProfileManager()
        self._apply_profile_config(self.profile_name)

        # tool definition
        self.tools = self._define_tools()

        # loggerin generate_report initialize in
        self.report_logger: Optional[ReportLogger] = None
        # console loggerin generate_report initialize in
        self.console_logger: Optional[ReportConsoleLogger] = None

        # Provenance capability version (immutable per agent instance)
        self.provenance_version = "1.0"

        logger.info(t('report.agentInitDone', graphId=graph_id, simulationId=simulation_id))

    def _apply_profile_config(self, profile_name: str) -> None:
        """Aplica configuracao de perfil ao ReportAgent."""
        try:
            config = self.profile_manager.get_profile_or_default(profile_name)
            config.apply_to_report_agent(self)
            logger.info(f"[ReportAgent] Profile applied: {config.profile_type.value} "
                       f"(temp={config.report_temperature}, max_words={config.max_words_per_sentence})")
        except Exception as e:
            logger.warning(f"[ReportAgent] Failed to apply profile '{profile_name}': {e}. Using defaults.")
            # Default hard rules fallback
            self.system_prompt = ""
            self.section_prompt = ""
            self.temperature = 0.3
            self.max_reflection_rounds = 2
            self.max_words_per_sentence = 25
            self.forbidden_scripts = ['zh', 'ja', 'ko']
            self.entity_type_weights = {}
            self.profile_type = "generico"

    def _get_profile_section_prompt(self, section_title: str) -> str:
        """Retorna o section_prompt especifico do perfil, se configurado."""
        section_prompt = getattr(self, 'section_prompt', None)
        if section_prompt:
            # Suporta formatacao dinamica com o titulo da secao
            if "{section_title}" in section_prompt:
                try:
                    section_prompt = section_prompt.format(section_title=section_title)
                except Exception:
                    pass
            return f"\n\n[Profile-Specific Section Guidance]\n{section_prompt}\n"
        return ""

    def _validate_output_against_profile(self, text: str, context_label: str = "output") -> str:
        """Valida saida contra regras do perfil (forbidden scripts, word count)."""
        forbidden = getattr(self, 'forbidden_scripts', ['zh', 'ja', 'ko'])
        max_words = getattr(self, 'max_words_per_sentence', 25)

        # Check forbidden scripts
        integrity = assess_text_integrity(text)
        if integrity.forbidden_categories:
            for cat in integrity.forbidden_categories:
                if cat in forbidden:
                    logger.error(f"[ReportAgent] Forbidden script '{cat}' detected in {context_label}")
                    # Try to sanitize
                    safe_text, _ = enforce_controlled_output(text, fallback_text="[Conteudo removido por politica de idioma]")
                    text = safe_text

        # Check word count per sentence (soft warning, not blocking)
        sentences = re.split(r'[.!?\n]+', text)
        long_sentences = [s for s in sentences if len(s.split()) > max_words]
        if long_sentences:
            logger.warning(f"[ReportAgent] {len(long_sentences)} sentences exceed {max_words} words in {context_label}")

        return text

    def _trigger_fallback_search(
        self,
        query: str,
        section_title: str,
        section_index: int,
    ) -> str:
        """
        Aciona busca externa via fallback router quando o grafo Zep esta vazio.
        Retorna resultados formatados para inclusao no contexto da secao.
        """
        try:
            from ..connectors.fallback_router import ConnectorFallbackRouter
            router = ConnectorFallbackRouter()
            result = router.search(query)

            if not result.success or not result.results:
                logger.warning(f"[ReportAgent] Fallback search returned no results for query: {query[:50]}")
                if self.report_logger:
                    self.report_logger.log(
                        action="fallback_search_empty",
                        stage="generating",
                        section_title=section_title,
                        section_index=section_index,
                        details={"query": query, "status": "no_results"}
                    )
                return ""

            # Format results for report context
            formatted_lines = ["\n### Fontes Externas (busca complementar) 📊\n"]
            for i, item in enumerate(result.results[:5], 1):
                url = item.get("url", "")
                content = item.get("content", "")
                snippet = content[:400].replace("\n", " ").strip() if content else ""
                formatted_lines.append(
                    f"Fonte: [{url}] | Data: {datetime.now().strftime('%Y-%m-%d')} | "
                    f"Proveniencia: fonte externa | "
                    f"Conteudo: {snippet}"
                )

            fallback_text = "\n".join(formatted_lines)
            logger.info(f"[ReportAgent] Fallback search succeeded: {len(result.results)} results for query: {query[:50]}")

            if self.report_logger:
                self.report_logger.log(
                    action="fallback_search_success",
                    stage="generating",
                    section_title=section_title,
                    section_index=section_index,
                    details={
                        "query": query,
                        "provenance_tag": "📊 Fato — fonte externa",
                        "source_urls": [item.get("url", "") for item in result.results[:5]],
                        "result_count": len(result.results),
                        "connector": result.source,
                        "status": "success"
                    }
                )

            return fallback_text

        except Exception as e:
            logger.error(f"[ReportAgent] Fallback search failed: {e}")
            if self.report_logger:
                self.report_logger.log(
                    action="fallback_search_error",
                    stage="generating",
                    section_title=section_title,
                    section_index=section_index,
                    details={"query": query, "error": str(e)}
                )
            return ""

    def _controlled_entity_source(self, report_content: str = "") -> str:
        parts = [self.simulation_requirement or "", report_content or ""]
        return "\n\n".join(part for part in parts if part)

    def _validate_persisted_output(
        self,
        text: str,
        *,
        expected_entities: List[str] | None = None,
        allowed_entity_source: str = "",
        context_label: str,
    ) -> str:
        result = assess_text_integrity(
            text,
            expected_entities=expected_entities,
            allowed_entities=extract_entity_candidates(self._controlled_entity_source(allowed_entity_source)),
        )
        if result.ok:
            return text

        problems: list[str] = []
        if result.forbidden_categories:
            problems.append(f"forbidden_scripts={','.join(result.forbidden_categories)}")
        if result.missing_entities:
            problems.append(f"missing_entities={','.join(result.missing_entities)}")
        if result.suspect_terms:
            problems.append(f"suspect_terms={','.join(result.suspect_terms)}")
        if result.entity_drift:
            problems.append(f"entity_drift={','.join(result.entity_drift)}")

        problem_summary = "; ".join(problems) or "unknown_integrity_failure"
        logger.error(f"Reporting integrity rejection in {context_label}: {problem_summary}")

        # Sanitize instead of reject: strip forbidden scripts and drifted entities
        # rather than failing the whole report. Only missing_entities fails hard
        # since that's a structural requirement.
        if result.forbidden_categories or result.entity_drift:
            fallback_msg = (
                " [content removed by language policy: check report integrity] "
            )
            # Include the unvalidated text itself as allowed entity source so that
            # self-referential entities (e.g. section title appearing in the section
            # body) don't appear as drift during sanitization.
            combined_source = (
                allowed_entity_source + "\n\n" + text
                if allowed_entity_source else text
            )
            safe_text, sanitize_result = enforce_controlled_output(
                text,
                fallback_text=fallback_msg,
                allowed_entity_source=combined_source,
            )
            if sanitize_result.ok:
                logger.warning(
                    f"Reporting language policy sanitized {context_label} "
                    f"(removed: {problem_summary})."
                )
                return safe_text
            # If even sanitization failed, fall through to reject

        raise ValueError(f"Reporting language policy rejected {context_label}: {problem_summary}")

    def _sanitize_chat_response(self, response: str, report_content: str) -> str:
        fallback = "Response blocked by reporting language policy. Please regenerate the report context and retry."
        # Chat mode: only check forbidden scripts / suspect terms, skip entity-drift
        # because users may ask open-ended questions whose answers mention entities
        # not present in the original report.
        safe_text, result = enforce_controlled_output(
            response,
            fallback_text=fallback,
            allowed_entity_source=None,
        )
        if not result.ok:
            problems: list[str] = []
            if result.forbidden_categories:
                problems.append(f"forbidden_scripts={','.join(result.forbidden_categories)}")
            if result.suspect_terms:
                problems.append(f"suspect_terms={','.join(result.suspect_terms)}")
            if result.entity_drift:
                problems.append(f"entity_drift={','.join(result.entity_drift)}")
            logger.error("Reporting chat response blocked: " + ("; ".join(problems) or "unknown_integrity_failure"))
        return safe_text

    def _generate_with_language_guard(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.5,
        max_tokens: int = 4096,
        max_retries: int = 2,
        json_mode: bool = False,
        observation: Optional[Any] = None,
        generation_name: Optional[str] = None,
    ) -> Optional[str]:
        """
        Chama o LLM com proteção contra alucinação de idioma.
        Se detectar chinês/japonês/coreano/cirílico, faz retry com correção.
        """
        lang_enforcement = (
            "\n\nCORREÇÃO IMEDIATA - IDIOMA\n"
            "Your previous response contained forbidden script characters. "
            "This is strictly forbidden. Rewrite everything in English. "
            "Do not use non-Latin scripts or mixed-language output."
        )

        for attempt in range(max_retries + 1):
            if json_mode:
                # plan_outline usa chat_json; não podemos interceptar a string bruta,
                # então aplicamos guarda no nível das mensagens e validamos o JSON serializado
                import json as _json
                response = self.llm.chat_json(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    observation=observation,
                    generation_name=generation_name,
                )
                raw_text = _json.dumps(response, ensure_ascii=False)
                if not _contains_forbidden_language(raw_text):
                    return raw_text  # retorna string para compatibilidade; quem chama faz parse
                logger.warning(f"[LanguageGuard] JSON com idioma proibido detectado (tentativa {attempt + 1})")
            else:
                response = self.llm.chat(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    observation=observation,
                    generation_name=generation_name,
                )
                if response is None:
                    return None
                if not _contains_forbidden_language(response):
                    return response
                logger.warning(f"[LanguageGuard] Texto com idioma proibido detectado (tentativa {attempt + 1})")

            # Retry: adiciona mensagem de correção
            if attempt < max_retries:
                messages.append({"role": "assistant", "content": response if not json_mode else raw_text})
                messages.append({"role": "user", "content": lang_enforcement})

        # Última tentativa falhou, retorna mesmo assim (fallback)
        return response if not json_mode else raw_text

    def _define_tools(self) -> Dict[str, Dict[str, Any]]:
        """available tools"""
        return {
            "insight_forge": {
                "name": "insight_forge",
                "description": TOOL_DESC_INSIGHT_FORGE,
                "parameters": {
                    "query": "Pergunta que deseja analisar em profundidade",
                    "report_context": "Contexto do capitulo atual do relatorio (opcional, ajuda a gerar sub-perguntas mais precisas)"
                }
            },
            "panorama_search": {
                "name": "panorama_search",
                "description": TOOL_DESC_PANORAMA_SEARCH,
                "parameters": {
                    "query": "Consulta de busca para ordenacao por relevancia",
                    "include_expired": "Se deve incluir conteudo expirado/historico (padrao True)"
                }
            },
            "quick_search": {
                "name": "quick_search",
                "description": TOOL_DESC_QUICK_SEARCH,
                "parameters": {
                    "query": "String de consulta de busca",
                    "limit": "Numero de resultados a retornar (opcional, padrao 10)"
                }
            },
            "interview_agents": {
                "name": "interview_agents",
                "description": TOOL_DESC_INTERVIEW_AGENTS,
                "parameters": {
                    "interview_topic": "Tema da entrevista ou descricao da necessidade (ex: opniao dos estudantes sobre o evento X)",
                    "max_agents": "Numero maximo de Agentes para entrevista (opcional, padrao 5, max 10)"
                }
            }
        }

    def _execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        report_context: str = "",
        observation: Optional[Any] = None,
    ) -> str:
        """
        call

        Args:
            tool_name:
            parameters: parameters
            report_context: reportInsightForge
            observation: Optional Langfuse span for tool-call tracing (optional).

        Returns:
            resultformat
        """
        logger.info(t('report.executingTool', toolName=tool_name, params=parameters))

        provenance = {
            "source": tool_name,
            "tool_name": tool_name,
            "query": parameters.get("query", ""),
            "retrieved_at": datetime.now().isoformat(),
            "connector_name": "zep_graph"
        }

        try:
            if tool_name == "insight_forge":
                query = parameters.get("query", "")
                ctx = parameters.get("report_context", "") or report_context
                result = self.zep_tools.insight_forge(
                    graph_id=self.graph_id,
                    query=query,
                    simulation_requirement=self.simulation_requirement,
                    report_context=ctx
                )
                result.provenance = provenance
                text_result = result.to_text()
                if "No facts or nodes found" in text_result or "Não foi possível encontrar" in text_result or len(text_result) < 50:
                    fallback_result = self._trigger_fallback_search(query)
                    if fallback_result:
                        return f"[Zep Graph Empty] Externa Search Result:\n{fallback_result}"
                return text_result

            elif tool_name == "panorama_search":
                # broad search - get overview
                query = parameters.get("query", "")
                include_expired = parameters.get("include_expired", True)
                if isinstance(include_expired, str):
                    include_expired = include_expired.lower() in ['true', '1', 'yes']
                result = self.zep_tools.panorama_search(
                    graph_id=self.graph_id,
                    query=query,
                    include_expired=include_expired
                )
                result.provenance = provenance
                return result.to_text()

            elif tool_name == "quick_search":
                # simple search -
                query = parameters.get("query", "")
                limit = parameters.get("limit", 10)
                if isinstance(limit, str):
                    limit = int(limit)
                result = self.zep_tools.quick_search(
                    graph_id=self.graph_id,
                    query=query,
                    limit=limit
                )
                result.provenance = provenance
                return result.to_text()

            elif tool_name == "interview_agents":
                # deep interview - callOASISinterviewAPIgetsimulationAgentanswerdual platform
                interview_topic = parameters.get("interview_topic", parameters.get("query", ""))
                max_agents = parameters.get("max_agents", 5)
                if isinstance(max_agents, str):
                    max_agents = int(max_agents)
                max_agents = min(max_agents, 10)
                result = self.zep_tools.interview_agents(
                    simulation_id=self.simulation_id,
                    interview_requirement=interview_topic,
                    simulation_requirement=self.simulation_requirement,
                    max_agents=max_agents
                )
                result.provenance = provenance
                return result.to_text()

            # ========== backward compatible old toolsredirect to ==========

            elif tool_name == "search_graph":
                # redirect to quick_search
                logger.info(t('report.redirectToQuickSearch'))
                return self._execute_tool("quick_search", parameters, report_context)

            elif tool_name == "get_graph_statistics":
                result = self.zep_tools.get_graph_statistics(self.graph_id)
                return json.dumps(result, ensure_ascii=False, indent=2)

            elif tool_name == "get_entity_summary":
                entity_name = parameters.get("entity_name", "")
                result = self.zep_tools.get_entity_summary(
                    graph_id=self.graph_id,
                    entity_name=entity_name
                )
                return json.dumps(result, ensure_ascii=False, indent=2)

            elif tool_name == "get_simulation_context":
                # redirect to insight_forge
                logger.info(t('report.redirectToInsightForge'))
                query = parameters.get("query", self.simulation_requirement)
                return self._execute_tool("insight_forge", {"query": query}, report_context)

            elif tool_name == "get_entities_by_type":
                entity_type = parameters.get("entity_type", "")
                nodes = self.zep_tools.get_entities_by_type(
                    graph_id=self.graph_id,
                    entity_type=entity_type
                )
                result = [n.to_dict() for n in nodes]
                return json.dumps(result, ensure_ascii=False, indent=2)

            else:
                return f"unknown tool: {tool_name}. Use one of: insight_forge, panorama_search, quick_search, interview_agents"

        except Exception as e:
            logger.error(t('report.toolExecFailed', toolName=tool_name, error=str(e)))
            return f"tool execution failed: {str(e)}"

    # valid tool names setused for bare JSON validate in fallback parsing
    VALID_TOOL_NAMES = {"insight_forge", "panorama_search", "quick_search", "interview_agents"}

    def _parse_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """
        fromLLMparse tool call from response

        supportformatby priority
        1. <tool_call>{JSON}</tool_call>
        2. bare JSON (full response is a single JSON object)
        3. JSON objects embedded anywhere in text
        """
        tool_calls = []
        seen: set[tuple[str, str]] = set()  # deduplicate by (name, params_json)

        def add_tool(data: Dict[str, Any]) -> None:
            try:
                tool_name = data.get("name") or data.get("tool") or data.get("tool_name")
                if not tool_name:
                    return
                params = data.get("parameters") or data.get("params") or {}
                key = (str(tool_name), json.dumps(params, sort_keys=True))
            except Exception:
                return
            if key not in seen and self._is_valid_tool_call(data):
                seen.add(key)
                tool_calls.append(data)

        # ── format1: <tool_call>...</tool_call> ──
        # Strip wrapper tags first to avoid regex issues with nested braces.
        clean = re.sub(r'</tool_call>\s*<tool_call>', '', response)  # merge consecutive
        for m in re.finditer(r'<tool_call>', clean):
            start = m.end()
            end = clean.find('</tool_call>', start)
            if end == -1:
                break
            raw = clean[start:end].strip()
            for inner in [raw, re.sub(r'^<tool_call>\s*', '', raw), re.sub(r'\s*</tool_call>$', '', raw)]:
                try:
                    data = json.loads(inner)
                    add_tool(data)
                    break
                except json.JSONDecodeError:
                    pass

        stripped = response.strip()

        # ── format3: XML-style tool calls (<tool_name>...</tool_name>) ──
        # Handles model output that wraps tool calls in XML-like tags instead of JSON.
        no_think = re.sub(r'^.*?\s*', '', stripped, flags=re.DOTALL).strip()
        for name_m in re.finditer(r'<tool_name>\s*(\w+)\s*</tool_name>', no_think):
            tool_name = name_m.group(1)
            # Find the parameters block that follows this tool_name tag
            after_tool_name = no_think[name_m.end():]
            # Look for <parameters>...</parameters> or <params>...</params>
            params_m = re.search(r'<(?:parameters?|params)>\s*(\{[^}]*(?:\{[^}]*\}[^}]*)*\})\s*</(?:parameters?|params)>', after_tool_name, re.DOTALL)
            if params_m:
                try:
                    params = json.loads(params_m.group(1))
                    add_tool({"name": tool_name, "parameters": params})
                    continue
                except json.JSONDecodeError:
                    pass
            # Try bare JSON object after tool_name
            bare_m = re.search(r'<parameters?\s*>\s*(\{.*?\})\s*</parameters?>', after_tool_name, re.DOTALL)
            if bare_m:
                try:
                    params = json.loads(bare_m.group(1))
                    add_tool({"name": tool_name, "parameters": params})
                except json.JSONDecodeError:
                    pass

        if tool_calls:
            return tool_calls

        # ── format2: bare JSON (response is exactly one JSON object) ──
        if stripped.startswith('{') and stripped.endswith('}'):
            try:
                data = json.loads(stripped)
                add_tool(data)
                if tool_calls:
                    return tool_calls
            except json.JSONDecodeError:
                pass

        # ── format3: find all JSON objects anywhere in the response ──
        # Handles responses that contain JSON after <think>/ or other text.
        json_objects: list[tuple[int, dict]] = []
        # Find all {...} sequences that are valid JSON
        for m in re.finditer(r'\{[^{}]*"name"\s*:[^}]+\}', stripped):
            try:
                obj = json.loads(m.group())
                json_objects.append((m.start(), obj))
            except json.JSONDecodeError:
                pass
        for m in re.finditer(r'\{[^{}]*"tool"\s*:[^}]+\}', stripped):
            try:
                obj = json.loads(m.group())
                json_objects.append((m.start(), obj))
            except json.JSONDecodeError:
                pass
        for _, obj in sorted(json_objects, key=lambda x: x[0]):
            add_tool(obj)

        return tool_calls

    def _is_valid_tool_call(self, data: dict) -> bool:
        """validate parsed JSON call"""
        tool_name = data.get("name") or data.get("tool") or data.get("tool_name")
        if not tool_name:
            return False

        # ── fuzzy match for common typos in tool names ──
        def fuzzy_match(name: str) -> str | None:
            """Return canonical tool name if Levenshtein distance <= 2, else None."""
            name_lc = name.casefold()
            for valid in self.VALID_TOOL_NAMES:
                if valid.casefold() == name_lc:
                    return valid
                if len(name_lc) >= 4 and len(valid) >= 4:
                    # Allow single-character insertion/deletion/substitution
                    if self._levenshtein_dist(name_lc, valid.casefold()) <= 2:
                        return valid
            return None

        canonical = fuzzy_match(tool_name)
        if not canonical:
            return False

        # normalize key names name / parameters
        data["name"] = canonical
        if "params" in data and "parameters" not in data:
            data["parameters"] = data.pop("params")
        if "tool" in data:
            del data["tool"]
        if "tool_name" in data:
            del data["tool_name"]
        return True

    @staticmethod
    def _levenshtein_dist(a: str, b: str) -> int:
        """Simple Levenshtein distance for fuzzy tool-name matching."""
        if len(a) > len(b):
            a, b = b, a
        if not a:
            return len(b)
        previous_row = list(range(len(b) + 1))
        for i, ca in enumerate(a):
            current_row = [i + 1]
            for j, cb in enumerate(b):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (ca != cb)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

    def _get_tools_description(self) -> str:
        """tool description"""
        desc_parts = ["available tools"]
        for name, tool in self.tools.items():
            params_desc = ", ".join([f"{k}: {v}" for k, v in tool["parameters"].items()])
            desc_parts.append(f"- {name}: {tool['description']}")
            if params_desc:
                desc_parts.append(f"  parameters: {params_desc}")
        return "\n".join(desc_parts)

    def plan_outline(
        self,
        progress_callback: Optional[Callable] = None,
        observability_client: Optional[Any] = None,
    ) -> ReportOutline:
        """
        plan report outline

        useLLManalyze simulation requirementplan report directory structure

        Args:
            progress_callback: progress callback
            observability_client: Langfuse observation to use for planning span (optional).

        Returns:
            ReportOutline: report
        """
        logger.info(t('report.startPlanningOutline'))

        if progress_callback:
            progress_callback("planning", 0, t('progress.analyzingRequirements'))

        # getsimulation
        context = self.zep_tools.get_simulation_context(
            graph_id=self.graph_id,
            simulation_requirement=self.simulation_requirement
        )

        if progress_callback:
            progress_callback("planning", 30, t('progress.generatingOutline'))

        system_prompt = f"{PLAN_SYSTEM_PROMPT}\n\n{get_reporting_language_instruction()}"
        # Apply profile-specific system prompt if configured
        profile_system = getattr(self, 'system_prompt', None)
        if profile_system:
            system_prompt = f"{profile_system}\n\n{system_prompt}"
        # Apply profile-specific outline prompt if configured (Phase 10)
        outline_prompt = getattr(self, 'outline_system_prompt', None)
        if outline_prompt:
            system_prompt = f"{outline_prompt}\n\n{system_prompt}"

        user_prompt = PLAN_USER_PROMPT_TEMPLATE.format(
            simulation_requirement=self.simulation_requirement,
            total_nodes=context.get('graph_statistics', {}).get('total_nodes', 0),
            total_edges=context.get('graph_statistics', {}).get('total_edges', 0),
            entity_types=list(context.get('graph_statistics', {}).get('entity_types', {}).keys()),
            total_entities=context.get('total_entities', 0),
            related_facts_json=json.dumps(context.get('related_facts', [])[:10], ensure_ascii=False, indent=2),
        )

        # Wrap planning LLM call in an observability span
        planning_obs = observability_client or self.observability_client
        planning_span = None
        if planning_obs is not None:
            planning_span = planning_obs.start_span(
                name="report_planning",
                metadata={
                    "graph_id": self.graph_id,
                    "simulation_id": self.simulation_id,
                },
            )

        try:
            raw_response = self._generate_with_language_guard(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                json_mode=True,
                observation=planning_span,
                generation_name="outline_planning",
            )

            import json as _json
            response = _json.loads(raw_response) if isinstance(raw_response, str) else raw_response

            if progress_callback:
                progress_callback("planning", 80, t('progress.parsingOutline'))

            # parse outline
            sections = []
            for section_data in response.get("sections", []):
                sections.append(ReportSection(
                    title=section_data.get("title", ""),
                    content=""
                ))

            outline = ReportOutline(
                title=response.get("title", "Simulation Analysis Report"),
                summary=response.get("summary", ""),
                sections=sections
            )

            if progress_callback:
                progress_callback("planning", 100, t('progress.outlinePlanComplete'))

            logger.info(t('report.outlinePlanDone', count=len(sections)))

            if planning_span is not None:
                planning_span.update(output={"title": outline.title, "sections": [s.title for s in outline.sections]})
                planning_span.end()

            return outline

        except Exception as e:
            logger.error(t('report.outlinePlanFailed', error=str(e)))

            if planning_span is not None:
                planning_span.update(status_message=f"error: {str(e)}", output="")
                planning_span.end()
            # Fallback outline: usar estrutura due-diligence se o perfil exigir
            if getattr(self, 'outline_system_prompt', None):
                return ReportOutline(
                    title="Análise de Due Diligence",
                    summary="Avaliação estruturada do cenário econômico simulado",
                    sections=[
                        ReportSection(title="Tese Principal"),
                        ReportSection(title="Evidências Verificadas"),
                        ReportSection(title="Fragilidades e Riscos"),
                        ReportSection(title="Premissas Explícitas"),
                        ReportSection(title="Cenários (Bear / Base / Bull)")
                    ]
                )
            # Fallback generico
            return ReportOutline(
                title="Relatório de Predição Futura",
                summary="Análise de tendências futuras e riscos com base na simulação",
                sections=[
                    ReportSection(title="Cenários de Predição e Principais Achados"),
                    ReportSection(title="Análise de Comportamento Coletivo"),
                    ReportSection(title="Perspectivas de Tendência e Alertas de Risco")
                ]
            )

    def _generate_section_react(
        self,
        section: ReportSection,
        outline: ReportOutline,
        previous_sections: List[str],
        progress_callback: Optional[Callable] = None,
        section_index: int = 0,
        observation: Optional[Any] = None,
    ) -> str:
        """
        useReACTcountsection

        ReACTloop
        1. Thoughtthought- analyze what info needed
        2. Actionaction- callgetinfo
        3. Observationobservation- result
        4. repeat until info sufficient or max reached
        5. Final Answerfinal answer- section

        Args:
            section: section to generate
            outline: complete outline
            previous_sections: previous sections contentused to maintain coherence
            progress_callback: progress callback
            section_index: sectionlogrecord
            observation: Langfuse span to use for this section's generation (optional).

        Returns:
            sectionMarkdownformat
        """
        logger.info(t('report.reactGenerateSection', title=section.title))

        # recordsectionstartlog
        if self.report_logger:
            self.report_logger.log_section_start(section.title, section_index)

        system_prompt = SECTION_SYSTEM_PROMPT_TEMPLATE.format(
            report_title=outline.title,
            report_summary=outline.summary,
            simulation_requirement=self.simulation_requirement,
            section_title=section.title,
            tools_description=self._get_tools_description(),
        )
        # Add profile-specific section guidance
        system_prompt += self._get_profile_section_prompt(section.title)

        # Inject validation context (Phase 9)
        if getattr(self, 'validation_report', None):
            validation_context = (
                "\n\n[Contexto de Validacao de Dados]\n"
                f"{self.validation_report.summary_text}\n"
                "\nRegras de narrativa baseadas na validacao:\n"
                "- Use a confianca indicada ao descrever cada metrica (alta=afirmativa, media=condicional, baixa=especulativa).\n"
                "- Se houver discrepancias de BLOQUEIO, nao apresente o dado como fato consolidado.\n"
                "- Se houver notas GAAP/non-GAAP, distingua explicitamente no texto.\n"
            )
            system_prompt += validation_context

        system_prompt = f"{system_prompt}\n\n{get_reporting_language_instruction()}"

        # Determine temperature: profile override or default
        generation_temp = getattr(self, 'temperature', 0.5)
        max_reflection = getattr(self, 'max_reflection_rounds', 3)

        # Check graph health before starting ReACT loop
        graph_health = self.zep_tools.check_graph_health(self.graph_id)
        health_status = graph_health.get("status", "unknown")
        if health_status in ("empty", "no_facts", "sparse"):
            logger.warning(f"[ReportAgent] Graph health '{health_status}' for section '{section.title}'. Pre-loading fallback sources.")
            fallback_preload = self._trigger_fallback_search(
                query=f"{section.title} {self.simulation_requirement}",
                section_title=section.title,
                section_index=section_index,
            )
            if fallback_preload:
                # Inject fallback sources as system context
                system_prompt += f"\n\n[Contexto Pre-carregado - Grafo {health_status}]\n{fallback_preload}\n"

        # prompt - countsection4000
        if previous_sections:
            previous_parts = []
            for sec in previous_sections:
                # countsection4000
                truncated = sec[:4000] + "..." if len(sec) > 4000 else sec
                previous_parts.append(truncated)
            previous_content = "\n\n---\n\n".join(previous_parts)
        else:
            previous_content = "(this is the first section)"

        user_prompt = SECTION_USER_PROMPT_TEMPLATE.format(
            previous_content=previous_content,
            section_title=section.title,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # ReACT loop
        tool_calls_count = 0
        max_iterations = 8  # max iteration rounds
        min_tool_calls = 3  # call
        conflict_retries = 0  # tool call andFinal Answerconsecutive conflicts at same time
        used_tools = set()  # recordcall
        all_tools = {"insight_forge", "panorama_search", "quick_search", "interview_agents"}

        # reportInsightForgesub-question generation
        report_context = f"section title: {section.title}\nsimulation: {self.simulation_requirement}"

        for iteration in range(max_iterations):
            if progress_callback:
                progress_callback(
                    "generating",
                    int((iteration / max_iterations) * 100),
                    t('progress.deepSearchAndWrite', current=tool_calls_count, max=self.MAX_TOOL_CALLS_PER_SECTION)
                )

            # callLLM (com proteção de idioma)
            response = self._generate_with_language_guard(
                messages=messages,
                temperature=generation_temp,
                max_tokens=4096,
                observation=observation,
                generation_name=f"section_{section.title[:30]}",
            )

            # check LLM return if NoneAPI is empty
            if response is None:
                logger.warning(t('report.sectionIterNone', title=section.title, iteration=iteration + 1))
                # if still have iterationsadd message and retry
                if iteration < max_iterations - 1:
                    messages.append({"role": "assistant", "content": "(response is empty)"})
                    messages.append({"role": "user", "content": "Please continue generating content."})
                    continue
                # last iteration also returns Noneloop
                break

            logger.debug(f"LLM: {response[:200]}...")

            # parse onceresult
            tool_calls = self._parse_tool_calls(response)
            has_tool_calls = bool(tool_calls)
            has_final_answer = "Final Answer:" in response

            # ── conflict handlingLLM outputcalland Final Answer ──
            if has_tool_calls and has_final_answer:
                conflict_retries += 1
                logger.warning(
                    t('report.sectionConflict', title=section.title, iteration=iteration+1, conflictCount=conflict_retries)
                )

                if conflict_retries <= 2:
                    # discard this responserequire LLM reply again
                    messages.append({"role": "assistant", "content": response})
                    messages.append({
                        "role": "user",
                        "content": (
                            "format errorinreplycalland Final Answer\n"
                            "each reply can only do one of two things\n"
                            "- output one <tool_call> JSON block with no other content\n"
                            "- output final content starting with 'Final Answer:' with no <tool_call>\n"
                            "please reply againonly do one thing"
                        ),
                    })
                    continue
                else:
                    # third timedegrade handlingtruncate to first tool call
                    logger.warning(
                        t('report.sectionConflictDowngrade', title=section.title, conflictCount=conflict_retries)
                    )
                    first_tool_end = response.find('</tool_call>')
                    if first_tool_end != -1:
                        response = response[:first_tool_end + len('</tool_call>')]
                        tool_calls = self._parse_tool_calls(response)
                        has_tool_calls = bool(tool_calls)
                    has_final_answer = False
                    conflict_retries = 0

            # record LLM response log
            if self.report_logger:
                self.report_logger.log_llm_response(
                    section_title=section.title,
                    section_index=section_index,
                    response=response,
                    iteration=iteration + 1,
                    has_tool_calls=has_tool_calls,
                    has_final_answer=has_final_answer
                )

            # ── situation1LLM output Final Answer ──
            if has_final_answer:
                # callrequire
                if tool_calls_count < min_tool_calls:
                    messages.append({"role": "assistant", "content": response})
                    unused_tools = all_tools - used_tools
                    unused_hint = f"userecommend using them: {', '.join(unused_tools)}" if unused_tools else ""
                    messages.append({
                        "role": "user",
                        "content": REACT_INSUFFICIENT_TOOLS_MSG.format(
                            tool_calls_count=tool_calls_count,
                            min_tool_calls=min_tool_calls,
                            unused_hint=unused_hint,
                        ),
                    })
                    continue

                # normal end
                final_answer = response.split("Final Answer:")[-1].strip()
                # Apply profile output validation
                final_answer = self._validate_output_against_profile(final_answer, context_label=f"section_{section_index}_final")
                logger.info(t('report.sectionGenDone', title=section.title, count=tool_calls_count))

                if self.report_logger:
                    self.report_logger.log_section_content(
                        section_title=section.title,
                        section_index=section_index,
                        content=final_answer,
                        tool_calls_count=tool_calls_count
                    )
                return final_answer

            # ── situation2LLM call ──
            if has_tool_calls:
                # tool quota exhausted → explicitly informrequired output Final Answer
                if tool_calls_count >= self.MAX_TOOL_CALLS_PER_SECTION:
                    messages.append({"role": "assistant", "content": response})
                    messages.append({
                        "role": "user",
                        "content": REACT_TOOL_LIMIT_MSG.format(
                            tool_calls_count=tool_calls_count,
                            max_tool_calls=self.MAX_TOOL_CALLS_PER_SECTION,
                        ),
                    })
                    continue

                # sectioncountcall
                call = tool_calls[0]
                if len(tool_calls) > 1:
                    logger.info(t('report.multiToolOnlyFirst', total=len(tool_calls), toolName=call['name']))

                # Determine provenance tag based on tool
                if call["name"] == "interview_agents":
                    _provenance_tag = "📊 Fato — entrevista com agentes"
                else:
                    _provenance_tag = "📊 Fato — extraído da base de conhecimento"

                if self.report_logger:
                    self.report_logger.log_tool_call(
                        section_title=section.title,
                        section_index=section_index,
                        tool_name=call["name"],
                        parameters=call.get("parameters", {}),
                        iteration=iteration + 1,
                        provenance_tag=_provenance_tag
                    )

                # Wrap tool execution in an observability span
                tool_span = None
                if observation is not None:
                    tool_span = observation.start_span(
                        name=f"tool_{call['name']}",
                        metadata={
                            "section_title": section.title,
                            "section_index": section_index,
                            "tool_name": call["name"],
                            "iteration": iteration + 1,
                        },
                    )
                    tool_span.update(
                        input={
                            "tool_name": call["name"],
                            "parameters": call.get("parameters", {}),
                        }
                    )

                try:
                    result = self._execute_tool(
                        call["name"],
                        call.get("parameters", {}),
                        report_context=report_context,
                        observation=observation,
                    )
                finally:
                    if tool_span is not None:
                        tool_span.update(output={"result_length": len(result)})
                        tool_span.end()

                if self.report_logger:
                    self.report_logger.log_tool_result(
                        section_title=section.title,
                        section_index=section_index,
                        tool_name=call["name"],
                        result=result,
                        iteration=iteration + 1,
                        provenance_tag=_provenance_tag
                    )

                # ── Fallback detection: if graph returns empty, trigger external search ──
                # Detect empty graph results (0 facts, 0 entities mentioned)
                is_empty_result = (
                    "0 related items" in result
                    or "Found 0" in result
                    or "no facts" in result.lower()
                    or ("total_facts: 0" in result.lower())
                    or (len(result.strip()) < 100 and "0" in result and "related" in result.lower())
                )
                if is_empty_result and call["name"] in {"insight_forge", "panorama_search", "quick_search"}:
                    query_for_fallback = call.get("parameters", {}).get("query", section.title)
                    fallback_text = self._trigger_fallback_search(
                        query=query_for_fallback,
                        section_title=section.title,
                        section_index=section_index,
                    )
                    if fallback_text:
                        result += f"\n\n{fallback_text}"
                        logger.info(f"[ReportAgent] Appended fallback sources to tool result for section '{section.title}'")

                tool_calls_count += 1
                used_tools.add(call['name'])

                # use
                unused_tools = all_tools - used_tools
                unused_hint = ""
                if unused_tools and tool_calls_count < self.MAX_TOOL_CALLS_PER_SECTION:
                    unused_hint = REACT_UNUSED_TOOLS_HINT.format(unused_list="".join(unused_tools))

                messages.append({"role": "assistant", "content": response})
                messages.append({
                    "role": "user",
                    "content": REACT_OBSERVATION_TEMPLATE.format(
                        tool_name=call["name"],
                        result=result,
                        tool_calls_count=tool_calls_count,
                        max_tool_calls=self.MAX_TOOL_CALLS_PER_SECTION,
                        used_tools_str=", ".join(used_tools),
                        unused_hint=unused_hint,
                    ),
                })
                continue

            # ── situation3callalso not Final Answer ──
            messages.append({"role": "assistant", "content": response})
            logger.warning(
                f"[ReportAgent] Section '{section.title}' iteration {iteration+1}: "
                f"response has no tool_call and no Final Answer (len={len(response)}). "
                f"Preview: {response[:150]!r}"
            )

            if tool_calls_count < min_tool_calls:
                # callrecommend unused tools
                unused_tools = all_tools - used_tools
                unused_hint = f"userecommend using them: {', '.join(unused_tools)}" if unused_tools else ""

                messages.append({
                    "role": "user",
                    "content": REACT_INSUFFICIENT_TOOLS_MSG_ALT.format(
                        tool_calls_count=tool_calls_count,
                        min_tool_calls=min_tool_calls,
                        unused_hint=unused_hint,
                    ),
                })
                continue

            # callLLM output "Final Answer:" prefix
            # directly use this content as final answerno longer idle
            logger.info(t('report.sectionNoPrefix', title=section.title, count=tool_calls_count))
            final_answer = response.strip()

            if self.report_logger:
                self.report_logger.log_section_content(
                    section_title=section.title,
                    section_index=section_index,
                    content=final_answer,
                    tool_calls_count=tool_calls_count
                )
            return final_answer

        # max iterations reachedforce generate content
        logger.warning(t('report.sectionMaxIter', title=section.title))
        messages.append({"role": "user", "content": REACT_FORCE_FINAL_MSG})

        response = self._generate_with_language_guard(
            messages=messages,
            temperature=generation_temp,
            max_tokens=4096
        )

        # check LLM return if None
        if response is None:
            logger.error(t('report.sectionForceFailed', title=section.title))
            final_answer = t('report.sectionGenFailedContent')
        elif "Final Answer:" in response:
            final_answer = response.split("Final Answer:")[-1].strip()
        else:
            final_answer = response

        # Apply profile output validation
        final_answer = self._validate_output_against_profile(final_answer, context_label=f"section_{section_index}_forced")

        # recordsectionlog
        if self.report_logger:
            self.report_logger.log_section_content(
                section_title=section.title,
                section_index=section_index,
                content=final_answer,
                tool_calls_count=tool_calls_count
            )

        return final_answer

    def generate_report(
        self,
        progress_callback: Optional[Callable[[str, int, str], None]] = None,
        report_id: Optional[str] = None
    ) -> Report:
        """
        generate full reportsection

        save each section immediately after generationetccountreport
        file structure
        reports/{report_id}/
            meta.json       - report metadata
            outline.json    - report
            progress.json   - generation progress
            section_01.md   - section1section
            section_02.md   - section2section
            ...
            full_report.md  - report

        Args:
            progress_callback: progress callback (stage, progress, message)
            report_id: reportIDsuch asauto generate

        Returns:
            Report: report
        """
        import uuid

        # such as report_idauto generate
        if not report_id:
            report_id = f"report_{uuid.uuid4().hex[:12]}"
        start_time = datetime.now()

        report = Report(
            report_id=report_id,
            simulation_id=self.simulation_id,
            graph_id=self.graph_id,
            simulation_requirement=self.simulation_requirement,
            status=ReportStatus.PENDING,
            created_at=datetime.now().isoformat()
        )

        # section titleused for progress tracking
        completed_section_titles = []

        try:
            # initializecreate report folder and save initial state
            ReportManager._ensure_report_folder(report_id)

            # Defensive: ensure we don't generate partial-provenance reports
            # Old in-flight reports use old code and finish without provenance (displayed as-is)
            # New reports always run provenance when profile.require_provenance is True
            if getattr(self, 'require_provenance', False) and not hasattr(self, 'provenance_version'):
                raise RuntimeError("Provenance support incomplete: agent missing provenance_version")

            # Data Validation Pipeline (Phase 9)
            # Executa apos o planejamento e antes da geracao das secoes
            self.validation_report: Optional[ValidationReport] = None
            if getattr(self, 'require_validation', False):
                try:
                    validation_svc = DataValidationService(
                        thresholds=getattr(self, 'validation_thresholds', None)
                    )
                    # Reutiliza o contexto da simulacao ja obtido durante o planejamento
                    sim_context = self.zep_tools.get_simulation_context(
                        graph_id=self.graph_id,
                        simulation_requirement=self.simulation_requirement
                    )
                    self.validation_report = validation_svc.validate(
                        simulation_requirement=self.simulation_requirement,
                        context=sim_context,
                    )
                    logger.info(
                        f"[ReportAgent] Validacao concluida: "
                        f"{len(self.validation_report.metrics)} metricas, "
                        f"confianca={self.validation_report.confidence_level.value}"
                    )
                except Exception as e:
                    logger.warning(f"[ReportAgent] Validacao de dados falhou (continuando): {e}")
                    self.validation_report = None

            # initializeloggerstructured log agent_log.jsonl
            self.report_logger = ReportLogger(report_id)
            self.report_logger.log_start(
                simulation_id=self.simulation_id,
                graph_id=self.graph_id,
                simulation_requirement=self.simulation_requirement
            )

            # initializeconsole loggerconsole_log.txt
            self.console_logger = ReportConsoleLogger(report_id)

            ReportManager.update_progress(
                report_id, "pending", 0, t('progress.initReport'),
                completed_sections=[]
            )
            ReportManager.save_report(report)

            # phase1: planning outline
            report.status = ReportStatus.PLANNING
            ReportManager.update_progress(
                report_id, "planning", 5, t('progress.startPlanningOutline'),
                completed_sections=[]
            )

            # recordstartlog
            self.report_logger.log_planning_start()

            # Log do resultado da validacao
            if self.report_logger and self.validation_report:
                self.report_logger.log(
                    action="data_validation",
                    stage="planning",
                    details={
                        "metrics_count": len(self.validation_report.metrics),
                        "discrepancies_count": len(self.validation_report.discrepancies),
                        "confidence_level": self.validation_report.confidence_level.value,
                        "is_valid": self.validation_report.is_valid,
                        "requires_override": self.validation_report.requires_override,
                        "gaap_notes": self.validation_report.gaap_non_gaap_notes,
                        "metrics": [m.to_dict() for m in self.validation_report.metrics],
                        "discrepancies": [d.to_dict() for d in self.validation_report.discrepancies],
                    }
                )

            if progress_callback:
                progress_callback("planning", 0, t('progress.startPlanningOutline'))

            # Create root Langfuse trace for this report generation
            root_trace = None
            if self.observability_client is not None:
                root_trace = self.observability_client.start_report_trace(
                    name="report_generation",
                    session_id=report_id,
                    metadata={
                        "report_id": report_id,
                        "graph_id": self.graph_id,
                        "simulation_id": self.simulation_id,
                        "simulation_requirement": self.simulation_requirement,
                    },
                )
                root_trace.update(
                    input={
                        "report_id": report_id,
                        "simulation_id": self.simulation_id,
                        "graph_id": self.graph_id,
                    }
                )

            outline = self.plan_outline(
                progress_callback=lambda stage, prog, msg:
                    progress_callback(stage, prog // 5, msg) if progress_callback else None,
                observability_client=root_trace,
            )
            report.outline = outline

            # recordlog
            self.report_logger.log_planning_complete(outline.to_dict())

            # save outline to file
            ReportManager.save_outline(report_id, outline)
            ReportManager.update_progress(
                report_id, "planning", 15, t('progress.outlineDone', count=len(outline.sections)),
                completed_sections=[]
            )
            ReportManager.save_report(report)

            logger.info(t('report.outlineSavedToFile', reportId=report_id))

            # phase2: sectionsection
            report.status = ReportStatus.GENERATING

            total_sections = len(outline.sections)
            generated_sections = []  #

            for i, section in enumerate(outline.sections):
                section_num = i + 1
                base_progress = 20 + int((i / total_sections) * 70)

                # update progress
                ReportManager.update_progress(
                    report_id, "generating", base_progress,
                    t('progress.generatingSection', title=section.title, current=section_num, total=total_sections),
                    current_section=section.title,
                    completed_sections=completed_section_titles
                )

                if progress_callback:
                    progress_callback(
                        "generating",
                        base_progress,
                        t('progress.generatingSection', title=section.title, current=section_num, total=total_sections)
                    )

                # Open a section span for observability
                section_span = None
                if root_trace is not None:
                    section_span = root_trace.start_span(
                        name=f"section_{section.title[:30]}",
                        metadata={
                            "section_num": section_num,
                            "total_sections": total_sections,
                            "graph_id": self.graph_id,
                        },
                    )
                    section_span.update(
                        input={"title": section.title, "section_num": section_num},
                    )

                # section
                section_content = self._generate_section_react(
                    section=section,
                    outline=outline,
                    previous_sections=generated_sections,
                    progress_callback=lambda stage, prog, msg:
                        progress_callback(
                            stage,
                            base_progress + int(prog * 0.7 / total_sections),
                            msg
                        ) if progress_callback else None,
                    section_index=section_num,
                    observation=section_span,
                )

                section_content = self._validate_persisted_output(
                    section_content,
                    allowed_entity_source="\n\n".join(generated_sections),
                    context_label=f"section_{section_num:02d}",
                )
                section.content = section_content
                generated_sections.append(f"## {section.title}\n\n{section_content}")

                if section_span is not None:
                    section_span.update(output={"content_length": len(section_content)})
                    section_span.end()

                # save section
                ReportManager.save_section(report_id, section_num, section)
                completed_section_titles.append(section.title)

                # recordsectionlog
                full_section_content = f"## {section.title}\n\n{section_content}"

                if self.report_logger:
                    self.report_logger.log_section_full_complete(
                        section_title=section.title,
                        section_index=section_num,
                        full_content=full_section_content.strip()
                    )

                logger.info(t('report.sectionSaved', reportId=report_id, sectionNum=f"{section_num:02d}"))

                # update progress
                ReportManager.update_progress(
                    report_id, "generating",
                    base_progress + int(70 / total_sections),
                    t('progress.sectionDone', title=section.title),
                    current_section=None,
                    completed_sections=completed_section_titles
                )

            # Bias Audit (Phase 11) — after sections, before assembly
            self.bias_report: Optional[BiasReport] = None
            if getattr(self, 'require_bias_audit', False):
                try:
                    audit_svc = BiasAuditService()
                    self.bias_report = audit_svc.audit_sections(generated_sections)
                    logger.info(
                        f"[ReportAgent] Bias audit: score={self.bias_report.bias_score}, "
                        f"balanced={self.bias_report.is_balanced}"
                    )
                    if self.report_logger:
                        self.report_logger.log(
                            action="bias_audit",
                            stage="generating",
                            details={
                                "bias_score": self.bias_report.bias_score,
                                "is_balanced": self.bias_report.is_balanced,
                                "warnings_count": len(self.bias_report.warnings),
                                "warnings": self.bias_report.warnings[:10],
                                "dimensions": {
                                    k: v.to_dict() for k, v in self.bias_report.dimensions.items()
                                },
                            }
                        )
                except Exception as e:
                    logger.warning(f"[ReportAgent] Bias audit falhou (continuando): {e}")
                    self.bias_report = None

            # phase3: assemble full report
            if progress_callback:
                progress_callback("generating", 95, t('progress.assemblingReport'))

            ReportManager.update_progress(
                report_id, "generating", 95, t('progress.assemblingReport'),
                completed_sections=completed_section_titles
            )

            # useReportManagerassemble full report
            report.markdown_content = ReportManager.assemble_full_report(report_id, outline)

            # Log provenance validation result via agent logger
            _is_valid, _warnings = ReportManager._validate_provenance_tags(report.markdown_content)
            if self.report_logger:
                self.report_logger.log(
                    action="provenance_validation",
                    stage="generating",
                    details={
                        "is_valid": _is_valid,
                        "warning_count": len(_warnings),
                        "warnings": _warnings[:20]
                    }
                )

            # Langfuse observability score for provenance coverage
            coverage_score = 1.0 if _is_valid else max(0.0, 1.0 - (len(_warnings) / 20.0))
            if hasattr(self, 'observability_client') and self.observability_client:
                self.observability_client.score(
                    trace_id=report_id,
                    name="provenance_coverage",
                    value=coverage_score,
                    comment=f"{len(_warnings)} untagged claims" if _warnings else "All claims tagged"
                )

            # Full report entity_drift: include report title/summary in allowed_entity_source
            # so section-crossing titles don't appear as drift
            full_report_allowed = (
                f"# {outline.title}\n\n> {outline.summary}\n\n"
                + "\n\n".join(generated_sections)
            )
            report.markdown_content = self._validate_persisted_output(
                report.markdown_content,
                allowed_entity_source=full_report_allowed,
                context_label="full_report",
            )
            # Apply profile validation to full report
            report.markdown_content = self._validate_output_against_profile(
                report.markdown_content,
                context_label="full_report",
            )

            # Quality Gates (Phase 12) — after assembly, before completion
            self.quality_report: Optional[QualityReport] = None
            if getattr(self, 'require_quality_gates', False):
                try:
                    gate_svc = QualityGateService()
                    self.quality_report = gate_svc.run_gates(
                        report_content=report.markdown_content,
                        validation_report=self.validation_report,
                        bias_report=self.bias_report,
                    )
                    # Aplica modificacoes se houver (ex: adicao de Limitacoes Conhecidas)
                    if self.quality_report.modified_content:
                        report.markdown_content = self.quality_report.modified_content
                        # Re-salva o full_report.md com o conteudo atualizado
                        full_path = ReportManager._get_report_markdown_path(report_id)
                        with open(full_path, 'w', encoding='utf-8') as f:
                            f.write(report.markdown_content)
                        logger.info(f"[ReportAgent] Quality gates modificaram o relatorio: {report_id}")

                    if self.report_logger:
                        self.report_logger.log(
                            action="quality_gates",
                            stage="generating",
                            details={
                                "overall_passed": self.quality_report.overall_passed,
                                "gates": [g.to_dict() for g in self.quality_report.gates],
                                "content_modified": self.quality_report.modified_content is not None,
                            }
                        )
                    logger.info(
                        f"[ReportAgent] Quality gates: passed={self.quality_report.overall_passed}, "
                        f"gates={len(self.quality_report.gates)}"
                    )
                except Exception as e:
                    logger.warning(f"[ReportAgent] Quality gates falharam (continuando): {e}")
                    self.quality_report = None

            report.status = ReportStatus.COMPLETED
            report.completed_at = datetime.now().isoformat()

            # calculate total time
            total_time_seconds = (datetime.now() - start_time).total_seconds()

            # recordreportlog
            if self.report_logger:
                self.report_logger.log_report_complete(
                    total_sections=total_sections,
                    total_time_seconds=total_time_seconds
                )

            # save final report
            extra_meta = {
                "provenance_version": "1.0",
                "profile_type": getattr(self, 'profile_type', 'generico'),
                "provenance_enabled": getattr(self, 'require_provenance', False),
                "validation_enabled": getattr(self, 'require_validation', False),
                "bias_audit_enabled": getattr(self, 'require_bias_audit', False),
            }
            if self.validation_report:
                extra_meta["validation_report"] = self.validation_report.to_dict()
            if self.bias_report:
                extra_meta["bias_audit_report"] = self.bias_report.to_dict()
            if self.quality_report:
                extra_meta["quality_gates_report"] = self.quality_report.to_dict()
            ReportManager.save_report(report, extra_meta=extra_meta)
            ReportManager.update_progress(
                report_id, "completed", 100, t('progress.reportComplete'),
                completed_sections=completed_section_titles
            )

            if progress_callback:
                progress_callback("completed", 100, t('progress.reportComplete'))

            logger.info(t('report.reportGenDone', reportId=report_id))

            # console logger
            if self.console_logger:
                self.console_logger.close()
                self.console_logger = None

            if root_trace is not None:
                root_trace.update(output={"report_id": report_id, "status": report.status.value})
                root_trace.end()

            return report

        except Exception as e:
            logger.error(t('report.reportGenFailed', error=str(e)))
            report.status = ReportStatus.FAILED
            report.error = str(e)

            # log error
            if self.report_logger:
                self.report_logger.log_error(str(e), "failed")

            # save failure status
            try:
                ReportManager.save_report(report)
                ReportManager.update_progress(
                    report_id, "failed", -1, t('progress.reportFailed', error=str(e)),
                    completed_sections=completed_section_titles
                )
            except Exception:
                pass  # ignore save failure errors

            # console logger
            if self.console_logger:
                self.console_logger.close()
                self.console_logger = None

            if root_trace is not None:
                root_trace.update(status_message=f"error: {str(e)}", output="")
                root_trace.end()

            return report

    def chat(
        self,
        message: str,
        chat_history: List[Dict[str, str]] = None,
        observability_client: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        withReport Agentdialogue

        in conversationAgentcan autonomously call search tools to answer questions

        Args:
            message:
            chat_history: dialogue
            observability_client: Optional Langfuse observation for chat tracing (optional).
            
        Returns:
            {
                "response": "Agentreply",
                "tool_calls": [called tools list],
                "sources": [info]
            }
        """
        logger.info(t('report.agentChat', message=message[:50]))

        # Create a chat trace span
        obs = observability_client or self.observability_client
        chat_span = None
        if obs is not None:
            chat_span = obs.start_report_trace(
                name="chat_session",
                session_id=self.simulation_id,
                metadata={
                    "graph_id": self.graph_id,
                    "simulation_id": self.simulation_id,
                    "message_length": len(message),
                },
            )
            chat_span.update(input={"message": message[:500]})

        chat_history = chat_history or []

        # getreport
        report_content = ""
        try:
            report = ReportManager.get_report_by_simulation(self.simulation_id)
            if report and report.markdown_content:
                # reportavoid context too long
                report_content = report.markdown_content[:15000]
                if len(report.markdown_content) > 15000:
                    report_content += "\n\n... [report content truncated] ..."
        except Exception as e:
            logger.warning(t('report.fetchReportFailed', error=e))

        system_prompt = CHAT_SYSTEM_PROMPT_TEMPLATE.format(
            simulation_requirement=self.simulation_requirement,
            report_content=report_content if report_content else "(no report available yet)",
            tools_description=self._get_tools_description(),
        )
        # Apply profile hard rules to chat
        profile_system = getattr(self, 'system_prompt', None)
        if profile_system:
            system_prompt = f"{profile_system}\n\n{system_prompt}"
        system_prompt = f"{system_prompt}\n\n{get_reporting_language_instruction()}"

        #
        messages = [{"role": "system", "content": system_prompt}]

        # add history
        for h in chat_history[-10:]:  #
            messages.append(h)

        # add user message
        messages.append({
            "role": "user",
            "content": message
        })

        # ReACTloopsimplified
        tool_calls_made = []
        max_iterations = 2  # reduce iteration rounds

        for iteration in range(max_iterations):
            chat_temp = getattr(self, 'temperature', 0.5)
            response = self._generate_with_language_guard(
                messages=messages,
                temperature=chat_temp,
                observation=chat_span,
                generation_name="chat_turn",
            )

            # parse tool call
            tool_calls = self._parse_tool_calls(response)

            if not tool_calls:
                # calldirectly return response
                clean_response = re.sub(r'<tool_call>.*?</tool_call>', '', response, flags=re.DOTALL)
                clean_response = re.sub(r'\[TOOL_CALL\].*?\)', '', clean_response)
                clean_response = self._sanitize_chat_response(clean_response.strip(), report_content)

                if chat_span is not None:
                    integrity_result = assess_text_integrity(clean_response)
                    chat_span.update(
                        output={
                            "response": clean_response[:500] if clean_response else "",
                            "tool_calls_count": len(tool_calls_made),
                            "integrity_ok": integrity_result.ok,
                            "forbidden_categories": list(integrity_result.forbidden_categories),
                        }
                    )
                    chat_span.end()

                return {
                    "response": clean_response,
                    "tool_calls": tool_calls_made,
                    "sources": [tc.get("parameters", {}).get("query", "") for tc in tool_calls_made]
                }

            # calllimit count
            tool_results = []
            for call in tool_calls[:1]:  # max per round1call
                if len(tool_calls_made) >= self.MAX_TOOL_CALLS_PER_CHAT:
                    break
                result = self._execute_tool(call["name"], call.get("parameters", {}))
                tool_results.append({
                    "tool": call["name"],
                    "result": result[:1500]  # result
                })
                tool_calls_made.append(call)

            # add result to message
            messages.append({"role": "assistant", "content": response})
            observation = "\n".join([f"[{r['tool']}result]\n{r['result']}" for r in tool_results])
            messages.append({
                "role": "user",
                "content": observation + CHAT_OBSERVATION_SUFFIX
            })

        # reached max iterationget
        chat_temp = getattr(self, 'temperature', 0.5)
        final_response = self._generate_with_language_guard(
            messages=messages,
            temperature=chat_temp,
            observation=chat_span,
            generation_name="chat_final",
        )

        # clean response
        clean_response = re.sub(r'<tool_call>.*?</tool_call>', '', final_response, flags=re.DOTALL)
        clean_response = re.sub(r'\[TOOL_CALL\].*?\)', '', clean_response)
        clean_response = self._sanitize_chat_response(clean_response.strip(), report_content)

        if chat_span is not None:
            integrity_result = assess_text_integrity(clean_response)
            chat_span.update(
                output={
                    "response": clean_response[:500] if clean_response else "",
                    "tool_calls_count": len(tool_calls_made),
                    "integrity_ok": integrity_result.ok,
                    "forbidden_categories": list(integrity_result.forbidden_categories),
                }
            )
            chat_span.end()

        return {
            "response": clean_response,
            "tool_calls": tool_calls_made,
            "sources": [tc.get("parameters", {}).get("query", "") for tc in tool_calls_made]
        }


class ReportManager:
    """
    report

    reportand

    file structureoutput by section
    reports/
      {report_id}/
        meta.json          - report metadataand
        outline.json       - report
        progress.json      - generation progress
        section_01.md      - section1section
        section_02.md      - section2section
        ...
        full_report.md     - report
    """

    # report storage directory
    REPORTS_DIR = os.path.join(Config.UPLOAD_FOLDER, 'reports')

    @classmethod
    def _ensure_reports_dir(cls):
        """reportin"""
        os.makedirs(cls.REPORTS_DIR, exist_ok=True)

    @classmethod
    def _get_report_folder(cls, report_id: str) -> str:
        """getreportfolder"""
        return os.path.join(cls.REPORTS_DIR, report_id)

    @classmethod
    def _ensure_report_folder(cls, report_id: str) -> str:
        """ensure report folder exists and return path"""
        folder = cls._get_report_folder(report_id)
        os.makedirs(folder, exist_ok=True)
        return folder

    @classmethod
    def _get_report_path(cls, report_id: str) -> str:
        """getreport metadatafile path"""
        return os.path.join(cls._get_report_folder(report_id), "meta.json")

    @classmethod
    def _get_report_markdown_path(cls, report_id: str) -> str:
        """getreportMarkdownfile path"""
        return os.path.join(cls._get_report_folder(report_id), "full_report.md")

    @classmethod
    def _get_outline_path(cls, report_id: str) -> str:
        """get outline file path"""
        return os.path.join(cls._get_report_folder(report_id), "outline.json")

    @classmethod
    def _get_progress_path(cls, report_id: str) -> str:
        """get progress file path"""
        return os.path.join(cls._get_report_folder(report_id), "progress.json")

    @classmethod
    def _get_section_path(cls, report_id: str, section_index: int) -> str:
        """get sectionMarkdownfile path"""
        return os.path.join(cls._get_report_folder(report_id), f"section_{section_index:02d}.md")

    @classmethod
    def _get_agent_log_path(cls, report_id: str) -> str:
        """get Agent logfile path"""
        return os.path.join(cls._get_report_folder(report_id), "agent_log.jsonl")

    @classmethod
    def _get_console_log_path(cls, report_id: str) -> str:
        """get console log file path"""
        return os.path.join(cls._get_report_folder(report_id), "console_log.txt")

    @classmethod
    def get_console_log(cls, report_id: str, from_line: int = 0) -> Dict[str, Any]:
        """
        get console log content

        reportlogINFOWARNINGetc
        with agent_log.jsonl structured logdifferent

        Args:
            report_id: reportID
            from_line: fromsectionstartreadused for incremental get0 fromstart

        Returns:
            {
                "logs": [log line list],
                "total_lines": total lines,
                "from_line": start line number,
                "has_more": any more logs
            }
        """
        log_path = cls._get_console_log_path(report_id)

        if not os.path.exists(log_path):
            return {
                "logs": [],
                "total_lines": 0,
                "from_line": 0,
                "has_more": False
            }

        logs = []
        total_lines = 0

        with open(log_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                total_lines = i + 1
                if i >= from_line:
                    # logremove trailing newline
                    logs.append(line.rstrip('\n\r'))

        return {
            "logs": logs,
            "total_lines": total_lines,
            "from_line": from_line,
            "has_more": False  # reached end
        }

    @classmethod
    def get_console_log_stream(cls, report_id: str) -> List[str]:
        """
        getlogget

        Args:
            report_id: reportID

        Returns:
            log line list
        """
        result = cls.get_console_log(report_id, from_line=0)
        return result["logs"]

    @classmethod
    def get_agent_log(cls, report_id: str, from_line: int = 0) -> Dict[str, Any]:
        """
        get Agent log

        Args:
            report_id: reportID
            from_line: fromsectionstartreadused for incremental get0 fromstart

        Returns:
            {
                "logs": [log entry list],
                "total_lines": total lines,
                "from_line": start line number,
                "has_more": any more logs
            }
        """
        log_path = cls._get_agent_log_path(report_id)

        if not os.path.exists(log_path):
            return {
                "logs": [],
                "total_lines": 0,
                "from_line": 0,
                "has_more": False
            }

        logs = []
        total_lines = 0

        with open(log_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                total_lines = i + 1
                if i >= from_line:
                    try:
                        log_entry = json.loads(line.strip())
                        logs.append(log_entry)
                    except json.JSONDecodeError:
                        # skip lines that fail to parse
                        continue

        return {
            "logs": logs,
            "total_lines": total_lines,
            "from_line": from_line,
            "has_more": False  # reached end
        }

    @classmethod
    def get_agent_log_stream(cls, report_id: str) -> List[Dict[str, Any]]:
        """
        get Agent logused to get all at once

        Args:
            report_id: reportID

        Returns:
            log entry list
        """
        result = cls.get_agent_log(report_id, from_line=0)
        return result["logs"]

    @classmethod
    def save_outline(cls, report_id: str, outline: ReportOutline) -> None:
        """
        report

        call immediately after planning phase
        """
        cls._ensure_report_folder(report_id)

        with open(cls._get_outline_path(report_id), 'w', encoding='utf-8') as f:
            json.dump(outline.to_dict(), f, ensure_ascii=False, indent=2)

        logger.info(t('report.outlineSaved', reportId=report_id))

    @classmethod
    def save_section(
        cls,
        report_id: str,
        section_index: int,
        section: ReportSection
    ) -> str:
        """
        save single section

        incountsectioncallimplementationoutput by section

        Args:
            report_id: reportID
            section_index: sectionfrom1start
            section: sectionobject

        Returns:
            saved file path
        """
        cls._ensure_report_folder(report_id)

        # build sectionMarkdown - clean possible duplicate titles
        cleaned_content = cls._clean_section_content(section.content, section.title)
        md_content = f"## {section.title}\n\n"
        if cleaned_content:
            md_content += f"{cleaned_content}\n\n"

        # save file
        file_suffix = f"section_{section_index:02d}.md"
        file_path = os.path.join(cls._get_report_folder(report_id), file_suffix)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        logger.info(t('report.sectionFileSaved', reportId=report_id, fileSuffix=file_suffix))
        return file_path

    @classmethod
    def _clean_section_content(cls, content: str, section_title: str) -> str:
        """
        section

        1. beginningwithsection titleMarkdowntitle line
        2. convert all ### and belowconvert to bold

        Args:
            content: raw content
            section_title: section title

        Returns:
            cleaned content
        """
        import re

        if not content:
            return content

        content = content.strip()
        lines = content.split('\n')
        cleaned_lines = []
        skip_next_empty = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            # check ifMarkdowntitle line
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)

            if heading_match:
                level = len(heading_match.group(1))
                title_text = heading_match.group(2).strip()

                # check ifwithsection titleskip before5inline repetition
                if i < 5:
                    if title_text == section_title or title_text.replace(' ', '') == section_title.replace(' ', ''):
                        skip_next_empty = True
                        continue

                # convert all#, ##, ###, ####etcconvert to bold
                # section titlecontent should have no titles
                cleaned_lines.append(f"**{title_text}**")
                cleaned_lines.append("")  # add empty line
                continue

            # if previous line was skipped titleis emptyalso skip
            if skip_next_empty and stripped == '':
                skip_next_empty = False
                continue

            skip_next_empty = False
            cleaned_lines.append(line)

        # remove leading empty lines
        while cleaned_lines and cleaned_lines[0].strip() == '':
            cleaned_lines.pop(0)

        # beginning
        while cleaned_lines and cleaned_lines[0].strip() in ['---', '***', '___']:
            cleaned_lines.pop(0)
            # also remove empty line after separator
            while cleaned_lines and cleaned_lines[0].strip() == '':
                cleaned_lines.pop(0)

        return '\n'.join(cleaned_lines)

    @classmethod
    def update_progress(
        cls,
        report_id: str,
        status: str,
        progress: int,
        message: str,
        current_section: str = None,
        completed_sections: List[str] = None
    ) -> None:
        """
        reportgeneration progress

        frontend can readprogress.jsonget
        """
        cls._ensure_report_folder(report_id)

        progress_data = {
            "status": status,
            "progress": progress,
            "message": message,
            "current_section": current_section,
            "completed_sections": completed_sections or [],
            "updated_at": datetime.now().isoformat()
        }

        with open(cls._get_progress_path(report_id), 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)

    @classmethod
    def get_progress(cls, report_id: str) -> Optional[Dict[str, Any]]:
        """getreportgeneration progress"""
        path = cls._get_progress_path(report_id)

        if not os.path.exists(path):
            return None

        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @classmethod
    def get_generated_sections(cls, report_id: str) -> List[Dict[str, Any]]:
        """
        getsection

        sectioninfo
        """
        folder = cls._get_report_folder(report_id)

        if not os.path.exists(folder):
            return []

        sections = []
        for filename in sorted(os.listdir(folder)):
            if filename.startswith('section_') and filename.endswith('.md'):
                file_path = os.path.join(folder, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # fromsection
                parts = filename.replace('.md', '').split('_')
                section_index = int(parts[1])

                sections.append({
                    "filename": filename,
                    "section_index": section_index,
                    "content": content
                })

        return sections

    @classmethod
    def assemble_full_report(cls, report_id: str, outline: ReportOutline, save: bool = True) -> str:
        """
        assemble full report

        fromsectionassemble full report
        """
        folder = cls._get_report_folder(report_id)

        # build report header
        md_content = f"# {outline.title}\n\n"
        md_content += f"> {outline.summary}\n\n"
        md_content += f"---\n\n"

        # readsection
        sections = cls.get_generated_sections(report_id)
        for section_info in sections:
            md_content += section_info["content"]

        # post-processcountreport
        md_content = cls._post_process_report(md_content, outline)

        # Validate provenance tags
        is_valid, warnings = cls._validate_provenance_tags(md_content)
        if not is_valid:
            logger.warning(f"[Provenance] Report {report_id} has {len(warnings)} untagged claims")
            for w in warnings[:10]:  # Log first 10
                logger.warning(f"[Provenance] {w}")
            # Write warnings to a sidecar file for debugging
            warn_path = os.path.join(folder, 'provenance_warnings.txt')
            with open(warn_path, 'w', encoding='utf-8') as f:
                f.write(f"# Provenance Warnings for {report_id}\n\n")
                for w in warnings:
                    f.write(f"- {w}\n")

        if save:
            # save completereport
            full_path = cls._get_report_markdown_path(report_id)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(md_content)

            logger.info(t('report.fullReportAssembled', reportId=report_id))
        return md_content

    @classmethod
    def _post_process_report(cls, content: str, outline: ReportOutline) -> str:
        """
        post-process report content

        1. remove duplicate titles
        2. report(#)andsection title(##)remove other level titles(###, ####etc)
        3. clean extra empty lines and separators

        Args:
            content: report
            outline: report

        Returns:
            processed content
        """
        import re

        lines = content.split('\n')
        processed_lines = []
        prev_was_heading = False

        # section title
        section_titles = set()
        for section in outline.sections:
            section_titles.add(section.title)

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # check iftitle line
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)

            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()

                # check ifin consecutive5
                is_duplicate = False
                for j in range(max(0, len(processed_lines) - 5), len(processed_lines)):
                    prev_line = processed_lines[j].strip()
                    prev_match = re.match(r'^(#{1,6})\s+(.+)$', prev_line)
                    if prev_match:
                        prev_title = prev_match.group(2).strip()
                        if prev_title == title:
                            is_duplicate = True
                            break

                if is_duplicate:
                    # skip duplicate title and following empty line
                    i += 1
                    while i < len(lines) and lines[i].strip() == '':
                        i += 1
                    continue

                # title hierarchy processing
                # - # (level=1) report
                # - ## (level=2) section title
                # - ### and below (level>=3) convert to bold

                if level == 1:
                    if title == outline.title:
                        # report
                        processed_lines.append(line)
                        prev_was_heading = True
                    elif title in section_titles:
                        # section titleuse#corrected to##
                        processed_lines.append(f"## {title}")
                        prev_was_heading = True
                    else:
                        # other level 1 titles to bold
                        processed_lines.append(f"**{title}**")
                        processed_lines.append("")
                        prev_was_heading = False
                elif level == 2:
                    if title in section_titles or title == outline.title:
                        # section title
                        processed_lines.append(line)
                        prev_was_heading = True
                    else:
                        # section
                        processed_lines.append(f"**{title}**")
                        processed_lines.append("")
                        prev_was_heading = False
                else:
                    # ### and belowconvert to bold
                    processed_lines.append(f"**{title}**")
                    processed_lines.append("")
                    prev_was_heading = False

                i += 1
                continue

            elif stripped == '---' and prev_was_heading:
                # skip separator right after title
                i += 1
                continue

            elif stripped == '' and prev_was_heading:
                # count
                if processed_lines and processed_lines[-1].strip() != '':
                    processed_lines.append(line)
                prev_was_heading = False

            else:
                processed_lines.append(line)
                prev_was_heading = False

            i += 1

        # clean multiple consecutive empty lineskeep at most2count
        result_lines = []
        empty_count = 0
        for line in processed_lines:
            if line.strip() == '':
                empty_count += 1
                if empty_count <= 2:
                    result_lines.append(line)
            else:
                empty_count = 0
                result_lines.append(line)

        return '\n'.join(result_lines)

    @classmethod
    def _validate_provenance_tags(cls, content: str) -> tuple[bool, list[str]]:
        """
        Validate that quantitative claims have provenance emoji tags.
        Returns (is_valid, warnings).
        """
        import re
        warnings = []
        # Pattern: numbers/money/percentages not followed by provenance emoji within same sentence
        # Look for numeric patterns: $X, X%, X bilhoes, X milhoes, dates like 2025, Q1 2026
        numeric_pattern = re.compile(
            r'(?:US\$\s*[\d,.]+|\d+[,.)]?\d*\s*(?:%|bilh(?:o|õ)es|milh(?:o|õ)es|mil)|\b20\d{2}\b|Q[1-4]\s+20\d{2})',
            re.IGNORECASE
        )
        # Split into sentences roughly
        sentences = re.split(r'[.!?\n]+', content)
        for sentence in sentences:
            if numeric_pattern.search(sentence) and not re.search(r'[📊🔮⚠️]', sentence):
                # Skip table rows and headers
                if sentence.strip().startswith('|') or sentence.strip().startswith('#'):
                    continue
                snippet = sentence.strip()[:80]
                warnings.append(f"Untagged numeric claim: {snippet}...")
        is_valid = len(warnings) == 0
        return is_valid, warnings

    @classmethod
    def save_report(cls, report: Report, extra_meta: Optional[Dict[str, Any]] = None) -> None:
        """report metadataandreport"""
        cls._ensure_report_folder(report.report_id)

        # infoJSON
        meta = report.to_dict()
        if extra_meta:
            meta.update(extra_meta)
        with open(cls._get_report_path(report.report_id), 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        # save outline
        if report.outline:
            cls.save_outline(report.report_id, report.outline)

        # save completeMarkdownreport
        if report.markdown_content:
            with open(cls._get_report_markdown_path(report.report_id), 'w', encoding='utf-8') as f:
                f.write(report.markdown_content)

        logger.info(t('report.reportSaved', reportId=report.report_id))

    @classmethod
    def get_report(cls, report_id: str) -> Optional[Report]:
        """getreport"""
        path = cls._get_report_path(report_id)

        if not os.path.exists(path):
            # compatible with old formatcheckinreportsfiles in directory
            old_path = os.path.join(cls.REPORTS_DIR, f"{report_id}.json")
            if os.path.exists(old_path):
                path = old_path
            else:
                return None

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # rebuildReportobject
        outline = None
        if data.get('outline'):
            outline_data = data['outline']
            sections = []
            for s in outline_data.get('sections', []):
                sections.append(ReportSection(
                    title=s['title'],
                    content=s.get('content', '')
                ))
            outline = ReportOutline(
                title=outline_data['title'],
                summary=outline_data['summary'],
                sections=sections
            )

        # such asmarkdown_contentis emptyfromfull_report.mdread
        markdown_content = data.get('markdown_content', '')
        if not markdown_content:
            full_report_path = cls._get_report_markdown_path(report_id)
            if os.path.exists(full_report_path):
                with open(full_report_path, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()

        return Report(
            report_id=data['report_id'],
            simulation_id=data['simulation_id'],
            graph_id=data['graph_id'],
            simulation_requirement=data['simulation_requirement'],
            status=ReportStatus(data['status']),
            outline=outline,
            markdown_content=markdown_content,
            created_at=data.get('created_at', ''),
            completed_at=data.get('completed_at', ''),
            error=data.get('error')
        )

    @classmethod
    def get_report_by_simulation(cls, simulation_id: str) -> Optional[Report]:
        """simulationIDgetreport"""
        cls._ensure_reports_dir()

        for item in os.listdir(cls.REPORTS_DIR):
            item_path = os.path.join(cls.REPORTS_DIR, item)
            # new formatfolder
            if os.path.isdir(item_path):
                report = cls.get_report(item)
                if report and report.simulation_id == simulation_id:
                    return report
            # compatible with old formatJSON
            elif item.endswith('.json'):
                report_id = item[:-5]
                report = cls.get_report(report_id)
                if report and report.simulation_id == simulation_id:
                    return report

        return None

    @classmethod
    def list_reports(cls, simulation_id: Optional[str] = None, limit: int = 50) -> List[Report]:
        """list reports"""
        cls._ensure_reports_dir()

        reports = []
        for item in os.listdir(cls.REPORTS_DIR):
            item_path = os.path.join(cls.REPORTS_DIR, item)
            # new formatfolder
            if os.path.isdir(item_path):
                report = cls.get_report(item)
                if report:
                    if simulation_id is None or report.simulation_id == simulation_id:
                        reports.append(report)
            # compatible with old formatJSON
            elif item.endswith('.json'):
                report_id = item[:-5]
                report = cls.get_report(report_id)
                if report:
                    if simulation_id is None or report.simulation_id == simulation_id:
                        reports.append(report)

        # by creation time desc
        reports.sort(key=lambda r: r.created_at, reverse=True)

        return reports[:limit]

    @classmethod
    def delete_report(cls, report_id: str) -> bool:
        """reportcountfolder"""
        import shutil

        folder_path = cls._get_report_folder(report_id)

        # new formatcountfolder
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            shutil.rmtree(folder_path)
            logger.info(t('report.reportFolderDeleted', reportId=report_id))
            return True

        # compatible with old format
        deleted = False
        old_json_path = os.path.join(cls.REPORTS_DIR, f"{report_id}.json")
        old_md_path = os.path.join(cls.REPORTS_DIR, f"{report_id}.md")

        if os.path.exists(old_json_path):
            os.remove(old_json_path)
            deleted = True
        if os.path.exists(old_md_path):
            os.remove(old_md_path)
            deleted = True

        return deleted
