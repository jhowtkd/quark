"""
Output Quality Gates Service

Post-generation quality checks for economy reports:
- Language consistency (no mid-document switching)
- Known Limitations section auto-append
- Numeric consistency within report
- Self-contradiction and unsupported valuation detection

Requirements: QUAL-01, QUAL-02, QUAL-03, QUAL-04
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum

from ..utils.logger import get_logger

logger = get_logger('futuria.quality_gates')


class GateSeverity(str, Enum):
    """Severidade de um finding de quality gate."""
    INFO = "info"
    WARNING = "warning"
    BLOCKING = "blocking"


# =============================================================================
# PALAVRAS FUNCIONAIS PARA DETECCAO DE IDIOMA
# =============================================================================

PORTUGUESE_FUNCTION_WORDS = frozenset({
    "de", "do", "da", "dos", "das", "o", "a", "os", "as", "e", "em", "para",
    "por", "com", "sem", "sob", "sobre", "entre", "durante", "apos", "após",
    "antes", "mais", "menos", "muito", "pouco", "como", "quando", "onde",
    "que", "qual", "quem", "cujo", "cuja", "cujos", "cujas", "um", "uma",
    "uns", "umas", "este", "esta", "estes", "estas", "esse", "essa", "esses",
    "essas", "aquele", "aquela", "aqueles", "aquelas", "meu", "minha", "meus",
    "minhas", "teu", "tua", "teus", "tuas", "seu", "sua", "seus", "suas",
    "nosso", "nossa", "nossos", "nossas", "vosso", "vossa", "vossos", "vossas",
    "mas", "ou", "nem", "também", "tambem", "já", "ja", "ainda", "só", "so",
    "mesmo", "mesma", "mesmos", "mesmas", "outro", "outra", "outros", "outras",
    "tal", "tais", "qualquer", "quaisquer", "todo", "toda", "todos", "todas",
    "cada", "algum", "alguma", "alguns", "algumas", "nenhum", "nenhuma",
    "muitos", "muitas", "poucos", "poucas", "varios", "vários", "várias", "varias",
})

ENGLISH_FUNCTION_WORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "for", "with",
    "on", "at", "by", "from", "as", "into", "through", "during", "before",
    "after", "above", "below", "between", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "each",
    "few", "more", "most", "other", "some", "such", "no", "nor", "not",
    "only", "own", "same", "so", "than", "too", "very", "can", "will", "just",
    "should", "now", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "doing", "it", "its", "this",
    "that", "these", "those", "i", "you", "he", "she", "we", "they", "them",
    "their", "what", "which", "who", "whom", "whose", "if", "because",
    "while", "about", "against", "until", "since", "up", "down", "out",
    "over", "off", "both", "any", "many", "much", "little", "less", "least",
})


# =============================================================================
# PADROES DE EXTRACAO DE METRICAS
# =============================================================================

NUMERIC_PATTERN = re.compile(
    r"(?:US\$\s*[\d,.]+|\d+[,.)]?\d*\s*(?:%|bilh[oõ]es|milh[oõ]es|mil)|\b20\d{2}\b|Q[1-4]\s+20\d{2})",
    re.IGNORECASE,
)

METRIC_TYPE_PATTERNS = [
    (re.compile(r"(?:receita|revenue|faturamento)", re.IGNORECASE), "receita"),
    (re.compile(r"(?:eps|lucro\s+por\s+a[cç][aã]o)", re.IGNORECASE), "eps"),
    (re.compile(r"(?:margem\s+bruta|gross\s+margin)", re.IGNORECASE), "margem_bruta"),
    (re.compile(r"(?:margem\s+operacional|operating\s+margin)", re.IGNORECASE), "margem_operacional"),
    (re.compile(r"(?:margem\s+l[ií]quida|net\s+margin|profit\s+margin)", re.IGNORECASE), "margem_liquida"),
    (re.compile(r"(?:capex|capital\s+expenditure)", re.IGNORECASE), "capex"),
    (re.compile(r"(?:fcf|free\s+cash\s+flow)", re.IGNORECASE), "fcf"),
    (re.compile(r"(?:deliveries|entregas|vehicle\s+deliveries)", re.IGNORECASE), "entregas"),
]


# =============================================================================
# DATACLASSES
# =============================================================================

@dataclass
class QualityGateResult:
    """Resultado de um quality gate individual."""
    gate_name: str
    passed: bool
    findings: List[str] = field(default_factory=list)
    severity: GateSeverity = GateSeverity.INFO

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate_name": self.gate_name,
            "passed": self.passed,
            "findings": self.findings,
            "severity": self.severity.value,
        }


@dataclass
class QualityReport:
    """Relatorio completo dos quality gates."""
    overall_passed: bool = True
    gates: List[QualityGateResult] = field(default_factory=list)
    modified_content: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_passed": self.overall_passed,
            "gates": [g.to_dict() for g in self.gates],
            "content_modified": self.modified_content is not None,
        }


# =============================================================================
# QUALITY GATE SERVICE
# =============================================================================

class QualityGateService:
    """
    Servico de quality gates pos-geracao para relatorios de economia.

    Executa quatro verificacoes:
    1. Consistencia de idioma (QUAL-01)
    2. Secao de Limitacoes Conhecidas (QUAL-02)
    3. Consistencia numerica (QUAL-03)
    4. Auto-contradicao (QUAL-04)
    """

    def __init__(self):
        self.pt_pattern = self._build_word_pattern(PORTUGUESE_FUNCTION_WORDS)
        self.en_pattern = self._build_word_pattern(ENGLISH_FUNCTION_WORDS)

    @staticmethod
    def _build_word_pattern(words: frozenset) -> re.Pattern:
        escaped = [re.escape(w) for w in sorted(words, key=len, reverse=True)]
        return re.compile(r"\b(?:" + "|".join(escaped) + r")\b", re.IGNORECASE)

    def run_gates(
        self,
        report_content: str,
        validation_report: Optional[Any] = None,
        bias_report: Optional[Any] = None,
    ) -> QualityReport:
        """
        Executa todos os quality gates sobre o conteudo do relatorio.

        Args:
            report_content: Markdown completo do relatorio.
            validation_report: ValidationReport da Phase 9 (opcional).
            bias_report: BiasReport da Phase 11 (opcional).

        Returns:
            QualityReport com resultados de todos os gates.
        """
        gates: List[QualityGateResult] = []
        modified_content = report_content

        # Structural Gate 1: Relatorio nao vazio
        gates.append(self._check_not_empty(modified_content))

        # Structural Gate 2: Titulo presente
        gates.append(self._check_has_title(modified_content))

        # Structural Gate 3: Corpo minimo
        gates.append(self._check_has_body(modified_content))

        # Structural Gate 4: Conclusoes presentes
        gates.append(self._check_has_conclusions(modified_content))

        # Gate 5: Consistencia de idioma
        lang_result = self._check_language_consistency(modified_content)
        gates.append(lang_result)

        # Gate 6: Limitacoes Conhecidas (pode modificar conteudo)
        modified_content, limitations_result = self._ensure_known_limitations(
            modified_content, validation_report, bias_report
        )
        gates.append(limitations_result)

        # Gate 7: Consistencia numerica
        numeric_result = self._check_numeric_consistency(modified_content)
        gates.append(numeric_result)

        # Gate 8: Auto-contradicao
        contradiction_result = self._check_self_contradictions(modified_content)
        gates.append(contradiction_result)

        overall_passed = all(g.passed for g in gates)

        report = QualityReport(
            overall_passed=overall_passed,
            gates=gates,
            modified_content=modified_content if modified_content != report_content else None,
        )

        logger.info(
            f"[QualityGates] Overall={report.overall_passed}, "
            f"gates={len(report.gates)}, modified={report.modified_content is not None}"
        )
        return report

    def _check_not_empty(self, text: str) -> QualityGateResult:
        """
        Verifica se o relatorio nao esta vazio ou com conteudo insignificante.
        """
        if len(text.strip()) < 50:
            return QualityGateResult(
                gate_name="not_empty",
                passed=False,
                findings=["Relatorio vazio ou com conteudo insignificante (menos de 50 caracteres)."],
                severity=GateSeverity.BLOCKING,
            )
        return QualityGateResult(
            gate_name="not_empty",
            passed=True,
            findings=["Relatorio contem conteudo suficiente."],
            severity=GateSeverity.INFO,
        )

    def _check_has_title(self, text: str) -> QualityGateResult:
        """
        Verifica se o relatorio possui um titulo principal de nivel 1.
        """
        if not re.search(r"^#\s+.+", text, re.MULTILINE):
            return QualityGateResult(
                gate_name="has_title",
                passed=False,
                findings=["Titulo principal ausente. O relatorio deve comecar com um titulo de nivel 1."],
                severity=GateSeverity.BLOCKING,
            )
        return QualityGateResult(
            gate_name="has_title",
            passed=True,
            findings=["Titulo principal presente."],
            severity=GateSeverity.INFO,
        )

    def _check_has_body(self, text: str) -> QualityGateResult:
        """
        Verifica se o corpo do relatorio possui tamanho minimo.
        """
        if len(text.strip()) < 500:
            return QualityGateResult(
                gate_name="has_body",
                passed=False,
                findings=["Corpo do relatorio muito curto (menos de 500 caracteres)."],
                severity=GateSeverity.BLOCKING,
            )
        return QualityGateResult(
            gate_name="has_body",
            passed=True,
            findings=["Corpo do relatorio com tamanho adequado."],
            severity=GateSeverity.INFO,
        )

    def _check_has_conclusions(self, text: str) -> QualityGateResult:
        """
        Verifica se o relatorio possui uma secao de conclusoes ou sintese.
        """
        if not re.search(
            r"#{1,3}\s*(conclus|conclusion|consideracoes finais|sintese)",
            text,
            re.IGNORECASE,
        ):
            return QualityGateResult(
                gate_name="has_conclusions",
                passed=False,
                findings=["Secao de conclusoes ou sintese nao detectada."],
                severity=GateSeverity.WARNING,
            )
        return QualityGateResult(
            gate_name="has_conclusions",
            passed=True,
            findings=["Secao de conclusoes detectada."],
            severity=GateSeverity.INFO,
        )

    def _check_language_consistency(self, text: str) -> QualityGateResult:
        """
        Verifica se o relatorio mantem um unico idioma do inicio ao fim.

        Divide o texto em 3 partes iguais e compara o perfil linguistico.
        """
        # Remove markdown formatting para analise
        clean = re.sub(r"[#*|\-_>`\[\](){}]", "", text)
        clean = re.sub(r"\s+", " ", clean).strip()

        if len(clean) < 200:
            return QualityGateResult(
                gate_name="language_consistency",
                passed=True,
                findings=["Texto muito curto para analise de idioma."],
            )

        chunk_size = max(1, len(clean) // 3)
        chunks = [clean[i:i + chunk_size] for i in range(0, len(clean), chunk_size)]

        chunk_langs: List[str] = []
        for chunk in chunks[:3]:
            pt_count = len(self.pt_pattern.findall(chunk))
            en_count = len(self.en_pattern.findall(chunk))
            total_words = len(chunk.split())
            if total_words < 10:
                chunk_langs.append("unknown")
                continue

            pt_density = pt_count / total_words
            en_density = en_count / total_words

            if pt_density > en_density * 2:
                chunk_langs.append("pt")
            elif en_density > pt_density * 2:
                chunk_langs.append("en")
            else:
                chunk_langs.append("mixed")

        # Determina idioma majoritario
        non_mixed = [l for l in chunk_langs if l != "mixed" and l != "unknown"]
        if not non_mixed:
            return QualityGateResult(
                gate_name="language_consistency",
                passed=True,
                findings=["Perfil linguistico misto ou inconclusivo."],
            )

        majority = max(set(non_mixed), key=non_mixed.count)
        inconsistencies = []
        for i, lang in enumerate(chunk_langs):
            if lang not in (majority, "mixed", "unknown"):
                inconsistencies.append(f"Parte {i+1} detectada como {lang} (majoritario: {majority})")

        passed = len(inconsistencies) == 0

        return QualityGateResult(
            gate_name="language_consistency",
            passed=passed,
            findings=inconsistencies or [f"Idioma consistente: {majority}"],
            severity=GateSeverity.WARNING if not passed else GateSeverity.INFO,
        )

    def _ensure_known_limitations(
        self,
        text: str,
        validation_report: Optional[Any],
        bias_report: Optional[Any],
    ) -> tuple[str, QualityGateResult]:
        """
        Garante que o relatorio possui uma secao de Limitacoes Conhecidas.
        Se nao existir, sintetiza uma a partir dos relatorios de validacao e vies.
        """
        # Verifica se ja existe
        has_limitations = bool(re.search(
            r"#{1,3}\s*(?:limitacoes conhecidas|known limitations|limitações conhecidas)",
            text,
            re.IGNORECASE,
        ))

        if has_limitations:
            return text, QualityGateResult(
                gate_name="known_limitations",
                passed=True,
                findings=["Secao de Limitacoes Conhecidas presente."],
            )

        # Sintetiza conteudo
        lines: List[str] = [
            "",
            "## Limitacoes Conhecidas",
            "",
            "Este relatorio foi gerado a partir de uma simulacao de cenario futuro. "
            "As seguintes limitacoes devem ser consideradas na interpretacao dos resultados:",
            "",
        ]

        findings: List[str] = ["Secao de Limitacoes Conhecidas ausente — adicionada automaticamente."]

        # Dados da validacao
        if validation_report:
            if getattr(validation_report, 'discrepancies', None):
                lines.append("- **Inconsistencias detectadas nos dados:**")
                for disc in validation_report.discrepancies[:5]:
                    msg = getattr(disc, 'message', str(disc))
                    lines.append(f"  - {msg}")
                lines.append("")

            if getattr(validation_report, 'gaap_non_gaap_notes', None):
                lines.append("- **Distincao GAAP/non-GAAP:**")
                for note in validation_report.gaap_non_gaap_notes[:3]:
                    lines.append(f"  - {note}")
                lines.append("")

            if getattr(validation_report, 'metrics', None) and not validation_report.metrics:
                lines.append("- **Poucas metricas financeiras extraiveis:** A simulacao nao forneceu dados numericos suficientes para validacao completa.")
                lines.append("")

        # Dados do bias audit
        if bias_report:
            if getattr(bias_report, 'warnings', None):
                lines.append("- **Alertas de neutralidade:**")
                for warning in bias_report.warnings[:5]:
                    lines.append(f"  - {warning}")
                lines.append("")

        # Fallback generico se nao houver findings especificos
        if len(lines) <= 6:
            lines.extend([
                "- **Natureza simulada:** Os dados apresentados refletem um cenario futuro simulado, nao necessariamente resultados reais ou previsoes garantidas.",
                "- **Fontes de dados:** Algumas informacoes podem ser projecoes ou inferencias do modelo (🔮) quando dados verificados (📊) nao estao disponiveis.",
                "- **Atualidade:** O cenario simulado pode nao refletir eventos ou dados publicados apos a data de geracao.",
                "",
            ])

        limitations_section = "\n".join(lines)
        new_text = text.rstrip() + "\n" + limitations_section

        return new_text, QualityGateResult(
            gate_name="known_limitations",
            passed=True,  # Passa porque corrigimos
            findings=findings,
            severity=GateSeverity.INFO,
        )

    def _check_numeric_consistency(self, text: str) -> QualityGateResult:
        """
        Extrai metricas do texto e verifica se a mesma metrica+periodo
        aparece com valores diferentes.
        """
        findings: List[str] = []

        # Extrai pares (metric_type, period, valor, contexto)
        extracted: List[tuple[str, str, float, str]] = []

        # Analisa paragrafo por paragrafo
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 20]
        for para in paragraphs:
            # Determina tipo de metrica
            metric_type = ""
            for pattern, mtype in METRIC_TYPE_PATTERNS:
                if pattern.search(para):
                    metric_type = mtype
                    break

            if not metric_type:
                continue

            # Extrai periodo
            period = ""
            m = re.search(r"\b(20\d{2}|Q[1-4]\s+20\d{2})\b", para)
            if m:
                period = m.group(1)

            # Extrai valores numericos
            for num_match in NUMERIC_PATTERN.finditer(para):
                val_str = num_match.group()
                # Tenta extrair numero
                num_only = re.search(r"[\d.,]+", val_str)
                if not num_only:
                    continue
                try:
                    value = self._parse_number(num_only.group())
                except ValueError:
                    continue

                extracted.append((metric_type, period, value, para[:60]))

        # Agrupa por metric_type + periodo
        grouped: Dict[str, List[float]] = {}
        for mtype, period, value, _ in extracted:
            key = f"{mtype}:{period}" if period else mtype
            grouped.setdefault(key, []).append(value)

        # Verifica inconsistencias
        for key, values in grouped.items():
            if len(values) > 1:
                unique_values = sorted(set(values))
                if len(unique_values) > 1:
                    findings.append(
                        f"Inconsistencia numerica em '{key}': valores {unique_values}"
                    )

        passed = len(findings) == 0

        return QualityGateResult(
            gate_name="numeric_consistency",
            passed=passed,
            findings=findings or ["Nenhuma inconsistencia numerica detectada."],
            severity=GateSeverity.WARNING if not passed else GateSeverity.INFO,
        )

    def _check_self_contradictions(self, text: str) -> QualityGateResult:
        """
        Detecta conclusoes de avaliacao nao suportadas e contradicoes leves.
        """
        findings: List[str] = []

        # Padroes de conclusao de avaliacao nao suportada
        unsupported_patterns = [
            (re.compile(r"(?:preco-alvo|preço-alvo|target price)[^\d]{0,20}?[\d.,]+", re.IGNORECASE),
             "preco-alvo declarado sem metodologia explicita"),
            (re.compile(r"(?:valor justo|fair value)[^\d]{0,20}?[\d.,]+", re.IGNORECASE),
             "valor justo declarado sem metodologia explicita"),
            (re.compile(r"(?:recomendacao|recomendação)\s+(?:de\s+)?(?:compra|venda|strong buy|strong sell)", re.IGNORECASE),
             "recomendacao de investimento declarada — os relatorios apresentam analise, nao aconselhamento de investimento"),
            (re.compile(r"(?:nota\s+de\s+investimento|rating)[^a-zA-Z]{0,5}?(?:A|B|C|AAA|BB|overweight|underweight)", re.IGNORECASE),
             "nota de investimento/rating declarado sem metodologia explicita"),
        ]

        for pattern, message in unsupported_patterns:
            if pattern.search(text):
                findings.append(message)

        # Verifica se a secao de Limitacoes Conhecidas existe (ja garantido pelo gate anterior, mas verificamos)
        has_limitations = bool(re.search(
            r"#{1,3}\s*(?:limitacoes conhecidas|known limitations|limitações conhecidas)",
            text,
            re.IGNORECASE,
        ))
        if not has_limitations:
            findings.append("Secao de Limitacoes Conhecidas ausente — risco de conclusoes nao contextualizadas.")

        passed = len(findings) == 0

        return QualityGateResult(
            gate_name="self_contradiction",
            passed=passed,
            findings=findings or ["Nenhuma contradicao ou conclusao nao suportada detectada."],
            severity=GateSeverity.WARNING if not passed else GateSeverity.INFO,
        )

    def _check_simulation_agent_coverage(
        self,
        validation_result: Dict[str, Any]
    ) -> QualityGateResult:
        """
        Verifica cobertura de agentes na simulacao.

        - Bloqueante se coverage_ratio < 0.80
        - Warning se 0.80 <= coverage_ratio < 0.90
        - Passa se coverage_ratio >= 0.90 e spurious_count == 0
        """
        coverage_ratio = validation_result.get("coverage_ratio", 0.0)
        spurious_count = validation_result.get("spurious_count", 0)

        if coverage_ratio < 0.80:
            return QualityGateResult(
                gate_name="simulation_agent_coverage",
                passed=False,
                findings=[
                    f"Cobertura de agentes muito baixa: {coverage_ratio:.2%} "
                    f"(minimo 80%). "
                    f"Missing: {validation_result.get('missing_count', 0)}, "
                    f"Spurious: {spurious_count}"
                ],
                severity=GateSeverity.BLOCKING,
            )

        if coverage_ratio < 0.90:
            return QualityGateResult(
                gate_name="simulation_agent_coverage",
                passed=False,
                findings=[
                    f"Cobertura de agentes abaixo do ideal: {coverage_ratio:.2%} "
                    f"(esperado >= 90%). "
                    f"Missing: {validation_result.get('missing_count', 0)}, "
                    f"Spurious: {spurious_count}"
                ],
                severity=GateSeverity.WARNING,
            )

        if spurious_count > 0:
            return QualityGateResult(
                gate_name="simulation_agent_coverage",
                passed=False,
                findings=[
                    f"Cobertura adequada ({coverage_ratio:.2%}), mas "
                    f"agentes espurios detectados: {spurious_count}"
                ],
                severity=GateSeverity.WARNING,
            )

        return QualityGateResult(
            gate_name="simulation_agent_coverage",
            passed=True,
            findings=[
                f"Cobertura de agentes satisfatoria: {coverage_ratio:.2%}"
            ],
            severity=GateSeverity.INFO,
        )

    def run_simulation_gates(self, validation_result: Dict[str, Any]) -> QualityReport:
        """
        Executa quality gates especificos de simulacao.

        Args:
            validation_result: Resultado da validacao IO de agentes.

        Returns:
            QualityReport com resultados dos gates.
        """
        gates: List[QualityGateResult] = []

        gates.append(self._check_simulation_agent_coverage(validation_result))

        overall_passed = all(g.passed for g in gates)

        report = QualityReport(
            overall_passed=overall_passed,
            gates=gates,
        )

        logger.info(
            f"[QualityGates] Simulation overall={report.overall_passed}, "
            f"gates={len(report.gates)}"
        )
        return report

    @staticmethod
    def _parse_number(value_str: str) -> float:
        """Converte string numerica para float."""
        cleaned = value_str.strip().replace(" ", "")
        if "," in cleaned and "." in cleaned:
            if cleaned.rfind(",") > cleaned.rfind("."):
                cleaned = cleaned.replace(".", "").replace(",", ".")
            else:
                cleaned = cleaned.replace(",", "")
        elif "," in cleaned:
            parts = cleaned.split(",")
            if len(parts) == 2 and len(parts[1]) <= 2:
                cleaned = cleaned.replace(",", ".")
            else:
                cleaned = cleaned.replace(",", "")
        return float(cleaned)


# Re-exportar
__all__ = [
    "QualityGateService",
    "QualityReport",
    "QualityGateResult",
    "GateSeverity",
]
