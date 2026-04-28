"""
Data Validation Service

Pre-generation validation pipeline for financial metrics in economy reports.
Extracts, cross-checks, and flags discrepancies in key financial figures
before narrative generation begins.

Requirements: VALID-01, VALID-02, VALID-03, VALID-04
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum

from ..utils.logger import get_logger

logger = get_logger('futuria.data_validation')


class ConfidenceLevel(str, Enum):
    """Nivel de confianca na validacao dos dados."""
    ALTA = "alta"
    MEDIA = "media"
    BAIXA = "baixa"


class DiscrepancySeverity(str, Enum):
    """Severidade de uma discrepancia detectada."""
    AVISO = "aviso"
    BLOQUEIO = "bloqueio"
    INFO = "info"


@dataclass
class MetricEntry:
    """Métrica financeira extraída do contexto da simulação."""
    name: str
    value: float
    unit: str = ""
    period: str = ""
    source: str = "simulacao"
    metric_type: str = ""  # ex: "receita", "eps", "margem", "capex", "fcf"
    is_gaap: Optional[bool] = None  # True=GAAP, False=non-GAAP, None=nao especificado

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "period": self.period,
            "source": self.source,
            "metric_type": self.metric_type,
            "is_gaap": self.is_gaap,
        }


@dataclass
class Discrepancy:
    """Discrepancia detectada entre metricas ou contra referencia."""
    metric_type: str
    severity: DiscrepancySeverity
    message: str
    expected_range: Optional[str] = None
    actual_value: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_type": self.metric_type,
            "severity": self.severity.value,
            "message": self.message,
            "expected_range": self.expected_range,
            "actual_value": self.actual_value,
        }


@dataclass
class ValidationReport:
    """Relatorio completo de validacao de dados financeiros."""
    metrics: List[MetricEntry] = field(default_factory=list)
    discrepancies: List[Discrepancy] = field(default_factory=list)
    confidence_level: ConfidenceLevel = ConfidenceLevel.ALTA
    gaap_non_gaap_notes: List[str] = field(default_factory=list)
    is_valid: bool = True
    requires_override: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metrics": [m.to_dict() for m in self.metrics],
            "discrepancies": [d.to_dict() for d in self.discrepancies],
            "confidence_level": self.confidence_level.value,
            "gaap_non_gaap_notes": self.gaap_non_gaap_notes,
            "is_valid": self.is_valid,
            "requires_override": self.requires_override,
        }

    @property
    def summary_text(self) -> str:
        """Retorna resumo em texto para injecao no prompt do LLM."""
        lines = [
            f"Nivel de confianca: {self.confidence_level.value.upper()}",
            f"Metricas validadas: {len(self.metrics)}",
            f"Discrepancias: {len(self.discrepancies)}",
        ]
        if self.discrepancies:
            lines.append("Alertas:")
            for d in self.discrepancies:
                lines.append(f"  - [{d.severity.value.upper()}] {d.metric_type}: {d.message}")
        if self.gaap_non_gaap_notes:
            lines.append("Notas GAAP/non-GAAP:")
            for note in self.gaap_non_gaap_notes:
                lines.append(f"  - {note}")
        return "\n".join(lines)


# =============================================================================
# PADROES DE EXTRACAO DE METRICAS
# =============================================================================

# Mapeamento de nomes de metricas para tipos canonicos
METRIC_NAME_MAP = {
    # Receita / Revenue
    "receita": "receita",
    "revenue": "receita",
    "faturamento": "receita",
    "net revenue": "receita",
    "total revenue": "receita",
    # EPS
    "eps": "eps",
    "lucro por acao": "eps",
    "earnings per share": "eps",
    "lucro/acao": "eps",
    # Margens
    "margem bruta": "margem_bruta",
    "gross margin": "margem_bruta",
    "margem operacional": "margem_operacional",
    "operating margin": "margem_operacional",
    "margem liquida": "margem_liquida",
    "net margin": "margem_liquida",
    "profit margin": "margem_liquida",
    # Capex
    "capex": "capex",
    "capital expenditure": "capex",
    "despesa de capital": "capex",
    "investimento em capex": "capex",
    # FCF
    "fcf": "fcf",
    "free cash flow": "fcf",
    "fluxo de caixa livre": "fcf",
    "free cash flow": "fcf",
    # EBITDA
    "ebitda": "ebitda",
    # Deliveries / Unidades
    "deliveries": "entregas",
    "entregas": "entregas",
    "unidades vendidas": "entregas",
    "vehicle deliveries": "entregas",
}

# Regex para extrair valores numericos com contexto
# Padrao: <metric_name> ... <valor> <unidade opcional>
METRIC_EXTRACTION_PATTERNS = [
    # Receita: "receita de 2025: US$ 94,8 bilhoes"
    re.compile(
        r"(?:receita|revenue|faturamento)[\s\w]*?\b(20\d{2}|Q[1-4]\s+20\d{2})\b[^\d]{0,30}?"
        r"(?:US\$\s*|R\$\s*|\$\s*)?([\d.,]+)\s*(bilh[oõ]es|milh[oõ]es|mil|billion|million|mn|bn)?",
        re.IGNORECASE,
    ),
    # EPS: "EPS GAAP de 0,45" ou "lucro por acao: $0.45"
    re.compile(
        r"(?:eps|lucro\s+por\s+a[cç][aã]o|earnings\s+per\s+share)[^\d]{0,20}?"
        r"(GAAP|non-GAAP|nao-GAAP|ajustado|adjusted)?[^\d]{0,20}?"
        r"(?:US\$\s*|R\$\s*|\$\s*)?([\d.,]+)",
        re.IGNORECASE,
    ),
    # Margens: "margem bruta de 18,5%"
    re.compile(
        r"(?:margem\s+(bruta|operacional|l[ií]quida)|"
        r"(gross|operating|net|profit)\s+margin)[^\d]{0,20}?"
        r"([\d.,]+)\s*%",
        re.IGNORECASE,
    ),
    # Capex: "capex de 15 milhoes"
    re.compile(
        r"(?:capex|capital\s+expenditure|despesa\s+de\s+capital)[^\d]{0,30}?"
        r"(?:US\$\s*|R\$\s*|\$\s*)?([\d.,]+)\s*(bilh[oõ]es|milh[oõ]es|mil|billion|million|mn|bn)?",
        re.IGNORECASE,
    ),
    # FCF: "free cash flow de 2,1 bilhoes"
    re.compile(
        r"(?:fcf|free\s+cash\s+flow|fluxo\s+de\s+caixa\s+livre)[^\d]{0,30}?"
        r"(?:US\$\s*|R\$\s*|\$\s*)?([\d.,]+)\s*(bilh[oõ]es|milh[oõ]es|mil|billion|million|mn|bn)?",
        re.IGNORECASE,
    ),
    # Entregas / Deliveries: "deliveries de 1,8 milhao"
    re.compile(
        r"(?:deliveries|entregas|unidades\s+vendidas|vehicle\s+deliveries)[^\d]{0,30}?"
        r"([\d.,]+)\s*(milh[oõ]es|mil|million|mn)?",
        re.IGNORECASE,
    ),
]


def _parse_number(value_str: str) -> float:
    """Converte string numerica brasileira/americana para float."""
    if not value_str:
        return 0.0
    # Remove espacos
    cleaned = value_str.strip().replace(" ", "")
    # Detecta formato: se tem virgula e ponto, o ultimo e o decimal
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            # formato brasileiro: 1.234,56
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            # formato americano: 1,234.56
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        # Pode ser decimal brasileiro (1,5) ou milhar americano sem decimal (1,234)
        parts = cleaned.split(",")
        if len(parts) == 2 and len(parts[1]) <= 2:
            # provavelmente decimal
            cleaned = cleaned.replace(",", ".")
        else:
            # milhar
            cleaned = cleaned.replace(",", "")
    return float(cleaned)


def _normalize_unit(unit_str: Optional[str]) -> str:
    """Normaliza unidades para formato canonico."""
    if not unit_str:
        return ""
    u = unit_str.strip().lower()
    if u in ("bilhoes", "bilhões", "billion", "bn"):
        return "bilhoes"
    if u in ("milhoes", "milhões", "million", "mn"):
        return "milhoes"
    if u in ("mil", "thousand"):
        return "mil"
    if "%" in u:
        return "%"
    return u


def _detect_gaap(context: str) -> Optional[bool]:
    """Detecta se o contexto menciona GAAP ou non-GAAP."""
    lowered = context.lower()
    if "non-gaap" in lowered or "nao-gaap" in lowered or "ajustado" in lowered or "adjusted" in lowered:
        return False
    if "gaap" in lowered:
        return True
    return None


# =============================================================================
# DEFAULT THRESHOLDS
# =============================================================================

DEFAULT_VALIDATION_THRESHOLDS = {
    "revenue_eps_fcf_warning": 0.15,
    "revenue_eps_fcf_block": 0.30,
    "margin_warning_pp": 5.0,
    "margin_block_pp": 10.0,
    "capex_warning": 0.20,
    "capex_block": 0.40,
}


# =============================================================================
# DATA VALIDATION SERVICE
# =============================================================================

class DataValidationService:
    """
    Servico de validacao de dados financeiros para relatorios de economia.

    Responsavel por:
    1. Extrair metricas financeiras do contexto da simulacao
    2. Validar consistencia estrutural (Tier 1)
    3. Validar contra dados de referencia (Tier 2)
    4. Detectar distincao GAAP vs non-GAAP
    5. Gerar relatorio de validacao para injecao no prompt do LLM
    """

    def __init__(self, thresholds: Optional[Dict[str, float]] = None):
        self.thresholds = thresholds or DEFAULT_VALIDATION_THRESHOLDS.copy()

    def extract_metrics(
        self,
        simulation_requirement: str,
        context: Dict[str, Any]
    ) -> List[MetricEntry]:
        """
        Extrai metricas financeiras do requisito de simulacao e do contexto.

        Args:
            simulation_requirement: Texto do requisito da simulacao.
            context: Dicionario com contexto do grafo (related_facts, etc.).

        Returns:
            Lista de MetricEntry extraidas.
        """
        metrics: List[MetricEntry] = []
        seen: set[str] = set()

        # Coleta todas as fontes de texto para analise
        text_sources: List[str] = [simulation_requirement or ""]

        related_facts = context.get("related_facts", [])
        if isinstance(related_facts, list):
            text_sources.extend(str(f) for f in related_facts)

        # Tambem busca em estatisticas do grafo (se houver metricas la)
        graph_stats = context.get("graph_statistics", {})
        if isinstance(graph_stats, dict):
            stats_text = json.dumps(graph_stats, ensure_ascii=False)
            text_sources.append(stats_text)

        for text in text_sources:
            for pattern in METRIC_EXTRACTION_PATTERNS:
                for match in pattern.finditer(text):
                    groups = match.groups()
                    if not groups:
                        continue

                    # Determina metric_type e valor com base no padrao
                    metric_type = self._resolve_metric_type(match, text)
                    if not metric_type:
                        continue

                    # Extrai valor numerico
                    value_str = self._extract_value_string(groups)
                    if not value_str:
                        continue

                    try:
                        value = _parse_number(value_str)
                    except ValueError:
                        continue

                    # Extrai periodo e unidade
                    period = self._extract_period(groups, text)
                    unit = self._extract_unit(groups)

                    # Detecta GAAP
                    is_gaap = _detect_gaap(text[match.start():match.end()])

                    # Evita duplicados exatos
                    key = f"{metric_type}:{value}:{unit}:{period}"
                    if key in seen:
                        continue
                    seen.add(key)

                    metrics.append(MetricEntry(
                        name=metric_type.replace("_", " ").title(),
                        value=value,
                        unit=unit,
                        period=period,
                        source="simulacao",
                        metric_type=metric_type,
                        is_gaap=is_gaap,
                    ))

        logger.info(f"[DataValidation] {len(metrics)} metricas extraidas")
        return metrics

    def _resolve_metric_type(self, match: re.Match, text: str) -> Optional[str]:
        """Resolve o tipo canonico da metrica a partir do match."""
        mt = match.group(0).lower()
        if "receita" in mt or "revenue" in mt or "faturamento" in mt:
            return "receita"
        if "eps" in mt or "lucro por acao" in mt or "earnings per share" in mt:
            return "eps"
        if "margem bruta" in mt or "gross margin" in mt:
            return "margem_bruta"
        if "margem operacional" in mt or "operating margin" in mt:
            return "margem_operacional"
        if "margem liquida" in mt or "net margin" in mt or "profit margin" in mt:
            return "margem_liquida"
        if "capex" in mt or "capital expenditure" in mt or "despesa de capital" in mt:
            return "capex"
        if "fcf" in mt or "free cash flow" in mt or "fluxo de caixa livre" in mt:
            return "fcf"
        if "deliveries" in mt or "entregas" in mt or "vehicle deliveries" in mt:
            return "entregas"
        return None

    def _extract_value_string(self, groups: tuple) -> Optional[str]:
        """Extrai a string do valor numerico dos grupos do match."""
        for g in groups:
            if g and re.match(r"^[\d.,]+$", str(g).strip()):
                return str(g).strip()
        return None

    def _extract_period(self, groups: tuple, text: str) -> str:
        """Extrai o periodo (ano ou trimestre) dos grupos ou do texto."""
        for g in groups:
            if g and re.match(r"^(20\d{2}|Q[1-4]\s+20\d{2})$", str(g).strip()):
                return str(g).strip()
        # Fallback: busca ano no texto
        m = re.search(r"\b(20\d{2})\b", text)
        if m:
            return m.group(1)
        return ""

    def _extract_unit(self, groups: tuple) -> str:
        """Extrai a unidade dos grupos do match."""
        for g in groups:
            if g and re.match(r"^(bilh[oõ]es|milh[oõ]es|mil|billion|million|mn|bn|%)$", str(g).strip(), re.IGNORECASE):
                return _normalize_unit(str(g))
        return ""

    def validate_structural(self, metrics: List[MetricEntry]) -> List[Discrepancy]:
        """
        Tier 1: Validacoes estruturais e matematicas.

        - Receita deve ser positiva
        - Margem bruta <= Margem operacional <= Margem liquida (aproximadamente)
        - Capex deve ser menor que receita
        - Margens devem estar entre 0% e 100%
        """
        discrepancies: List[Discrepancy] = []

        # Indexa metricas por tipo para acesso rapido
        by_type: Dict[str, List[MetricEntry]] = {}
        for m in metrics:
            by_type.setdefault(m.metric_type, []).append(m)

        # 1. Receita positiva
        for m in by_type.get("receita", []):
            if m.value <= 0:
                discrepancies.append(Discrepancy(
                    metric_type="receita",
                    severity=DiscrepancySeverity.BLOQUEIO,
                    message=f"Receita {m.period} nao pode ser zero ou negativa: {m.value}",
                    actual_value=m.value,
                ))

        # 2. Ordem das margens
        mb = self._best_metric(by_type.get("margem_bruta", []))
        mo = self._best_metric(by_type.get("margem_operacional", []))
        ml = self._best_metric(by_type.get("margem_liquida", []))

        if mb and mo and mb.value < mo.value:
            discrepancies.append(Discrepancy(
                metric_type="margem_bruta",
                severity=DiscrepancySeverity.AVISO,
                message=f"Margem bruta ({mb.value}%) menor que margem operacional ({mo.value}%). "
                        f"Verificar se ha itens extraordinarios ou reclassificacoes.",
                actual_value=mb.value,
            ))

        if mo and ml and mo.value < ml.value:
            discrepancies.append(Discrepancy(
                metric_type="margem_operacional",
                severity=DiscrepancySeverity.AVISO,
                message=f"Margem operacional ({mo.value}%) menor que margem liquida ({ml.value}%). "
                        f"Pode indicar ganhos nao operacionais significativos.",
                actual_value=mo.value,
            ))

        # 3. Margens fora do intervalo [0, 100]
        for mtype in ("margem_bruta", "margem_operacional", "margem_liquida"):
            for m in by_type.get(mtype, []):
                if m.value < 0 or m.value > 100:
                    discrepancies.append(Discrepancy(
                        metric_type=mtype,
                        severity=DiscrepancySeverity.BLOQUEIO,
                        message=f"Margem fora do intervalo valido [0%, 100%]: {m.value}%",
                        actual_value=m.value,
                    ))

        # 4. Capex menor que receita
        receita = self._best_metric(by_type.get("receita", []))
        capex = self._best_metric(by_type.get("capex", []))
        if receita and capex and capex.value > receita.value:
            discrepancies.append(Discrepancy(
                metric_type="capex",
                severity=DiscrepancySeverity.AVISO,
                message=f"Capex ({capex.value}) maior que receita ({receita.value}). "
                        f"Verificar unidades ou consistencia dos dados.",
                actual_value=capex.value,
            ))

        logger.info(f"[DataValidation] {len(discrepancies)} discrepancias estruturais")
        return discrepancies

    def validate_against_reference(
        self,
        metrics: List[MetricEntry],
        reference_facts: List[str]
    ) -> List[Discrepancy]:
        """
        Tier 2: Valida metricas contra fatos de referencia do grafo ou busca externa.

        Como nao temos API de dados em tempo real, usamos os proprios fatos
        do grafo como 'referencia'. Se houver multiplas mencoes da mesma metrica,
        verificamos consistencia interna.
        """
        discrepancies: List[Discrepancy] = []

        # Agrupa metricas por tipo e periodo
        grouped: Dict[str, List[MetricEntry]] = {}
        for m in metrics:
            key = f"{m.metric_type}:{m.period}"
            grouped.setdefault(key, []).append(m)

        # Verifica consistencia interna: multiplas mencoes do mesmo valor
        for key, entries in grouped.items():
            if len(entries) > 1:
                values = [e.value for e in entries]
                max_val = max(values)
                min_val = min(values)
                if max_val > 0:
                    deviation = (max_val - min_val) / max_val
                    mtype = entries[0].metric_type

                    # Determina threshold com base no tipo
                    if mtype.startswith("margem"):
                        # Para margens, usamos diferenca em pontos percentuais
                        diff_pp = abs(max_val - min_val)
                        warn_pp = self.thresholds.get("margin_warning_pp", 5.0)
                        block_pp = self.thresholds.get("margin_block_pp", 10.0)
                        if diff_pp >= block_pp:
                            sev = DiscrepancySeverity.BLOQUEIO
                        elif diff_pp >= warn_pp:
                            sev = DiscrepancySeverity.AVISO
                        else:
                            continue
                        msg = (
                            f"Inconsistencia interna: {mtype} varia de {min_val} a {max_val} "
                            f"({diff_pp:.1f} pp de diferenca)"
                        )
                    else:
                        warn_thr = self.thresholds.get("revenue_eps_fcf_warning", 0.15)
                        block_thr = self.thresholds.get("revenue_eps_fcf_block", 0.30)
                        if deviation >= block_thr:
                            sev = DiscrepancySeverity.BLOQUEIO
                        elif deviation >= warn_thr:
                            sev = DiscrepancySeverity.AVISO
                        else:
                            continue
                        msg = (
                            f"Inconsistencia interna: {mtype} varia de {min_val} a {max_val} "
                            f"({deviation:.1%} de desvio)"
                        )

                    discrepancies.append(Discrepancy(
                        metric_type=mtype,
                        severity=sev,
                        message=msg,
                        actual_value=max_val,
                    ))

        logger.info(f"[DataValidation] {len(discrepancies)} discrepancias de referencia")
        return discrepancies

    def check_gaap_non_gaap(self, metrics: List[MetricEntry]) -> List[str]:
        """
        Verifica se EPS possui distincao GAAP vs non-GAAP.

        Returns:
            Lista de notas sobre GAAP/non-GAAP.
        """
        notes: List[str] = []
        eps_metrics = [m for m in metrics if m.metric_type == "eps"]

        if not eps_metrics:
            return notes

        gaap_eps = [m for m in eps_metrics if m.is_gaap is True]
        non_gaap_eps = [m for m in eps_metrics if m.is_gaap is False]
        unspecified_eps = [m for m in eps_metrics if m.is_gaap is None]

        if gaap_eps and non_gaap_eps:
            notes.append(
                f"GAAP e non-GAAP EPS ambos presentes. "
                f"GAAP: {gaap_eps[0].value}; non-GAAP: {non_gaap_eps[0].value}"
            )
        elif gaap_eps and not non_gaap_eps:
            notes.append(
                "Apenas EPS GAAP identificado. Se houver versao non-GAAP (ajustado), "
                "deve ser explicitamente mencionada e distinguida no relatorio."
            )
        elif non_gaap_eps and not gaap_eps:
            notes.append(
                "Apenas EPS non-GAAP (ajustado) identificado. O relatorio deve "
                "explicitar que o valor e ajustado e, quando possivel, apresentar "
                "o equivalente GAAP para comparacao."
            )
        elif unspecified_eps:
            notes.append(
                "EPS identificado sem especificacao GAAP/non-GAAP. "
                "O relatorio deve esclarecer qual versao esta sendo usada."
            )

        return notes

    def validate(
        self,
        simulation_requirement: str,
        context: Dict[str, Any],
        thresholds: Optional[Dict[str, float]] = None,
    ) -> ValidationReport:
        """
        Executa o pipeline completo de validacao.

        Args:
            simulation_requirement: Texto do requisito da simulacao.
            context: Contexto do grafo / simulacao.
            thresholds: Thresholds customizados (opcional).

        Returns:
            ValidationReport com todas as metricas e discrepancias.
        """
        if thresholds:
            self.thresholds.update(thresholds)

        # 1. Extracao
        metrics = self.extract_metrics(simulation_requirement, context)

        # 2. Validacao estrutural (Tier 1)
        structural_disc = self.validate_structural(metrics)

        # 3. Validacao contra referencia (Tier 2)
        related_facts = context.get("related_facts", [])
        if not isinstance(related_facts, list):
            related_facts = []
        reference_disc = self.validate_against_reference(metrics, related_facts)

        # 4. GAAP vs non-GAAP
        gaap_notes = self.check_gaap_non_gaap(metrics)

        # 5. Consolidacao
        all_disc = structural_disc + reference_disc
        has_block = any(d.severity == DiscrepancySeverity.BLOQUEIO for d in all_disc)
        has_warning = any(d.severity == DiscrepancySeverity.AVISO for d in all_disc)

        if has_block:
            confidence = ConfidenceLevel.BAIXA
        elif has_warning:
            confidence = ConfidenceLevel.MEDIA
        else:
            confidence = ConfidenceLevel.ALTA

        report = ValidationReport(
            metrics=metrics,
            discrepancies=all_disc,
            confidence_level=confidence,
            gaap_non_gaap_notes=gaap_notes,
            is_valid=not has_block,
            requires_override=has_block,
        )

        logger.info(
            f"[DataValidation] Relatorio: {len(metrics)} metricas, "
            f"{len(all_disc)} discrepancias, confianca={confidence.value}"
        )
        return report

    @staticmethod
    def _best_metric(entries: List[MetricEntry]) -> Optional[MetricEntry]:
        """Retorna a metrica mais recente ou a primeira disponivel."""
        if not entries:
            return None
        # Se houver periodo, tenta pegar o mais recente
        with_period = [e for e in entries if e.period]
        if with_period:
            return sorted(with_period, key=lambda x: x.period, reverse=True)[0]
        return entries[0]


# Re-exportar classes principais para facilitar importacao
__all__ = [
    "DataValidationService",
    "ValidationReport",
    "MetricEntry",
    "Discrepancy",
    "ConfidenceLevel",
    "DiscrepancySeverity",
    "DEFAULT_VALIDATION_THRESHOLDS",
]
