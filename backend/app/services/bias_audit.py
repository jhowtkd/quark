"""
Bias Audit Service

Post-generation neutrality and bias detection for economy reports.
Analyzes generated sections for confirmation bias, claim strength calibration,
and competitive analysis quantification.

Requirements: NEUT-01, NEUT-02, NEUT-03, NEUT-04
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Any, List
from enum import Enum

from ..utils.logger import get_logger

logger = get_logger('futuria.bias_audit')


class BiasDimension(str, Enum):
    """Dimensoes de auditoria de vies."""
    SENTIMENT_BALANCE = "sentiment_balance"
    CLAIM_CALIBRATION = "claim_calibration"
    COMPETITIVE_QUANTIFICATION = "competitive_quantification"


# =============================================================================
# DICIONARIOS DE PALAVRAS-CHAVE
# =============================================================================

# Palavras com conotacao bullish (otimista)
BULLISH_KEYWORDS = frozenset({
    "crescimento", "recuperacao", "recuperação", "oportunidade", "expansao", "expansão",
    "alta", "superar", "forte", "robusto", "otimista", "otimismo", "upside", "rally",
    "boom", "melhora", "melhoria", "avanco", "avanço", "ganho", "lucro", "positivo",
    "aumento", "crescer", "expandir", "valorizacao", "valorização", "potencial",
    "promissor", "vencedor", "liderança", "lideranca", "dominante", "excelente",
    "surpreendente", "extraordinario", "extraordinário", "recorde", "maximo", "máximo",
})

# Palavras com conotacao bearish (pessimista)
BEARISH_KEYWORDS = frozenset({
    "queda", "risco", "preocupacao", "preocupação", "contracao", "contração", "baixa",
    "fracasso", "fragil", "frágil", "vulneravel", "vulnerável", "pessimista", "pessimismo",
    "downside", "crash", "piora", "recuo", "perda", "estresse", "stress", "negativo",
    "reducao", "redução", "diminuicao", "diminuição", "cair", "contrair", "desvalorizacao",
    "desvalorização", "ameaca", "ameaça", "crise", "colapso", "derrota", "fraco",
    "submissao", "submissão", "minimo", "mínimo", "pior", "desastre",
})

# Marcadores de afirmacao forte (requerem evidencia solida)
STRONG_CLAIM_MARKERS = frozenset({
    "certamente", "inevitavelmente", "inevitavelmente", "sem duvida", "sem dúvida",
    "com certeza", "absolutamente", "inquestionavelmente", "inquestionavelmente",
    "definitivamente", "inegavelmente", "inegavelmente", "indiscutivelmente",
    "indiscutivelmente", "obrigatoriamente", "obrigatoriamente", "necessariamente",
    "sempre", "nunca", "impossivel", "impossível", "garantido", "assegurado",
})

# Marcadores de linguagem condicional (apropriados para hipoteses)
CONDITIONAL_MARKERS = frozenset({
    "pode", "talvez", "caso", "se", "provavelmente", "provavelmente",
    "possivelmente", "possivelmente", "em torno de", "aproximadamente",
    "estimado", "estimada", "projetado", "projetada", "esperado", "esperada",
    "previsto", "prevista", "potencialmente", "eventualmente", "hipoteticamente",
})

# Palavras-chave que indicam analise competitiva
COMPETITIVE_CONTEXT_KEYWORDS = frozenset({
    "concorrente", "concorrencia", "concorrência", "mercado", "market share",
    "participacao de mercado", "participação de mercado", "competitivo",
    "competicao", "competição", "rival", "concorrentes", "rivais",
    "elasticidade", "elasticity", "preco", "preço", "regional", "mix",
    "posicionamento", "vantagem competitiva", "diferenciacao", "diferenciação",
})

# Padrao para detectar presenca de numeros em um paragrafo
NUMERIC_PATTERN = re.compile(
    r"(?:US\$\s*|[\d.,]+\s*(?:%|bilh[oõ]es|milh[oõ]es|mil|billion|million|mn|bn))|\b\d+[.,]?\d*\s*%|\b20\d{2}\b",
    re.IGNORECASE,
)


# =============================================================================
# DATACLASSES
# =============================================================================

@dataclass
class DimensionResult:
    """Resultado de uma dimensao de auditoria."""
    score: float  # 0.0 a 1.0
    findings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": round(self.score, 3),
            "findings": self.findings,
            "metadata": self.metadata,
        }


@dataclass
class BiasReport:
    """Relatorio completo de auditoria de vies."""
    bias_score: float = 1.0
    dimensions: Dict[str, DimensionResult] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    is_balanced: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bias_score": round(self.bias_score, 3),
            "dimensions": {k: v.to_dict() for k, v in self.dimensions.items()},
            "warnings": self.warnings,
            "is_balanced": self.is_balanced,
        }


# =============================================================================
# BIAS AUDIT SERVICE
# =============================================================================

class BiasAuditService:
    """
    Servico de auditoria de neutralidade e vies para relatorios de economia.

    Analisa o conteudo gerado em tres dimensoes:
    1. Equilibrio de sentimento (bullish vs bearish)
    2. Calibracao da forca das afirmacoes
    3. Quantificacao da analise competitiva
    """

    # Pesos para o score composto
    WEIGHTS = {
        BiasDimension.SENTIMENT_BALANCE: 0.40,
        BiasDimension.CLAIM_CALIBRATION: 0.35,
        BiasDimension.COMPETITIVE_QUANTIFICATION: 0.25,
    }

    # Thresholds
    WARNING_THRESHOLD = 0.80
    CRITICAL_THRESHOLD = 0.60

    def __init__(self):
        self.bullish_pattern = self._build_keyword_pattern(BULLISH_KEYWORDS)
        self.bearish_pattern = self._build_keyword_pattern(BEARISH_KEYWORDS)
        self.strong_claim_pattern = self._build_keyword_pattern(STRONG_CLAIM_MARKERS)
        self.conditional_pattern = self._build_keyword_pattern(CONDITIONAL_MARKERS)
        self.competitive_pattern = self._build_keyword_pattern(COMPETITIVE_CONTEXT_KEYWORDS)

    @staticmethod
    def _build_keyword_pattern(keywords: frozenset) -> re.Pattern:
        """Constroi regex case-insensitive a partir de um conjunto de palavras."""
        # Ordena por comprimento decrescente para evitar matching parcial
        sorted_kw = sorted(keywords, key=len, reverse=True)
        escaped = [re.escape(kw) for kw in sorted_kw]
        return re.compile(r"\b(?:" + "|".join(escaped) + r")\b", re.IGNORECASE)

    def audit_sections(self, section_contents: List[str]) -> BiasReport:
        """
        Executa auditoria completa sobre o conteudo das secoes geradas.

        Args:
            section_contents: Lista de strings com o conteudo de cada secao.

        Returns:
            BiasReport com score composto e findings por dimensao.
        """
        all_text = "\n\n".join(section_contents)

        # Dimensoes
        sentiment_result = self._analyze_sentiment_balance(section_contents)
        claim_result = self._analyze_claim_calibration(all_text)
        competitive_result = self._analyze_competitive_quantification(all_text)

        dimensions = {
            BiasDimension.SENTIMENT_BALANCE.value: sentiment_result,
            BiasDimension.CLAIM_CALIBRATION.value: claim_result,
            BiasDimension.COMPETITIVE_QUANTIFICATION.value: competitive_result,
        }

        # Score composto
        composite = self._compute_composite_score(dimensions)

        # Warnings consolidados
        warnings: List[str] = []
        if sentiment_result.score < self.WARNING_THRESHOLD:
            warnings.extend(sentiment_result.findings)
        if claim_result.score < self.WARNING_THRESHOLD:
            warnings.extend(claim_result.findings)
        if competitive_result.score < self.WARNING_THRESHOLD:
            warnings.extend(competitive_result.findings)

        is_balanced = composite >= self.WARNING_THRESHOLD

        report = BiasReport(
            bias_score=composite,
            dimensions=dimensions,
            warnings=warnings,
            is_balanced=is_balanced,
        )

        logger.info(
            f"[BiasAudit] Score={report.bias_score:.2f}, "
            f"balanced={report.is_balanced}, warnings={len(report.warnings)}"
        )
        return report

    def _analyze_sentiment_balance(self, section_contents: List[str]) -> DimensionResult:
        """
        Analisa o equilibrio entre palavras bullish e bearish.

        Score = 1.0 quando a razao bullish:bearish esta proxima de 1:1.
        Score cai quando a razao excede 2:1 em qualquer direcao.
        """
        bullish_count = 0
        bearish_count = 0
        bullish_snippets: List[str] = []
        bearish_snippets: List[str] = []

        for text in section_contents:
            for match in self.bullish_pattern.finditer(text):
                bullish_count += 1
                snippet = text[max(0, match.start()-30):match.end()+30]
                bullish_snippets.append(snippet.strip().replace("\n", " "))
            for match in self.bearish_pattern.finditer(text):
                bearish_count += 1
                snippet = text[max(0, match.start()-30):match.end()+30]
                bearish_snippets.append(snippet.strip().replace("\n", " "))

        total = bullish_count + bearish_count
        if total == 0:
            return DimensionResult(
                score=1.0,
                findings=["Nenhuma palavra de sentimento detectada — audit inconclusivo."],
                metadata={"bullish": 0, "bearish": 0, "ratio": 1.0},
            )

        # Calcula razao (maior / menor)
        if bearish_count == 0:
            ratio = float(bullish_count)
        elif bullish_count == 0:
            ratio = float(bearish_count)
        else:
            ratio = max(bullish_count, bearish_count) / min(bullish_count, bearish_count)

        # Score: 1.0 em 1:1, cai ate 0.0 em 5:1
        score = max(0.0, 1.0 - (ratio - 1.0) / 4.0)

        findings: List[str] = []
        if ratio > 2.0:
            dominant = "bullish" if bullish_count > bearish_count else "bearish"
            findings.append(
                f"Desequilibrio de sentimento detectado: {bullish_count} bullish vs "
                f"{bearish_count} bearish (razao {ratio:.1f}:1). "
                f"O relatorio parece consistentemente {dominant}."
            )

        return DimensionResult(
            score=score,
            findings=findings,
            metadata={
                "bullish": bullish_count,
                "bearish": bearish_count,
                "ratio": round(ratio, 2),
            },
        )

    def _analyze_claim_calibration(self, text: str) -> DimensionResult:
        """
        Verifica se afirmacoes fortes possuem evidencia solida (📊)
        e se afirmacoes especulativas usam linguagem condicional.

        Score = 1.0 - proporcao de strong claims sem 📊 entre todas as strong claims.
        """
        findings: List[str] = []
        strong_without_evidence = 0
        strong_total = 0
        speculative_without_conditional = 0
        speculative_total = 0

        # Analisa por frase
        sentences = re.split(r'[.!?\n]+', text)
        for sentence in sentences:
            sentence_stripped = sentence.strip()
            if len(sentence_stripped) < 10:
                continue

            has_strong = bool(self.strong_claim_pattern.search(sentence_stripped))
            has_conditional = bool(self.conditional_pattern.search(sentence_stripped))
            has_fact_tag = "📊" in sentence_stripped
            has_hypothesis_tag = "🔮" in sentence_stripped

            if has_strong:
                strong_total += 1
                if not has_fact_tag:
                    strong_without_evidence += 1
                    snippet = sentence_stripped[:80]
                    findings.append(
                        f"Afirmacao forte sem evidencia solida: '{snippet}...'"
                    )

            # Afirmacoes especulativas (com 🔮) devem ter linguagem condicional
            if has_hypothesis_tag:
                speculative_total += 1
                if not has_conditional and not has_strong:
                    speculative_without_conditional += 1
                    snippet = sentence_stripped[:80]
                    findings.append(
                        f"Projecao sem linguagem condicional: '{snippet}...'"
                    )

        # Score composto para calibracao
        strong_score = 1.0 if strong_total == 0 else (1.0 - strong_without_evidence / strong_total)
        speculative_score = 1.0 if speculative_total == 0 else (1.0 - speculative_without_conditional / speculative_total)
        score = (strong_score * 0.6) + (speculative_score * 0.4)

        return DimensionResult(
            score=score,
            findings=findings[:10],  # Limita findings para nao poluir
            metadata={
                "strong_total": strong_total,
                "strong_without_evidence": strong_without_evidence,
                "speculative_total": speculative_total,
                "speculative_without_conditional": speculative_without_conditional,
            },
        )

    def _analyze_competitive_quantification(self, text: str) -> DimensionResult:
        """
        Detecta paragrafos de analise competitiva que carecem de numeros.

        Score = proporcao de paragrafos competitivos que contem numeros.
        """
        findings: List[str] = []
        competitive_paragraphs = 0
        quantified_paragraphs = 0

        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 20]

        for para in paragraphs:
            if self.competitive_pattern.search(para):
                competitive_paragraphs += 1
                if NUMERIC_PATTERN.search(para):
                    quantified_paragraphs += 1
                else:
                    snippet = para[:100].replace("\n", " ")
                    findings.append(
                        f"Analise competitiva sem quantificacao: '{snippet}...'"
                    )

        if competitive_paragraphs == 0:
            return DimensionResult(
                score=1.0,
                findings=["Nenhuma analise competitiva detectada — audit inconclusivo."],
                metadata={"competitive_paragraphs": 0, "quantified": 0},
            )

        score = quantified_paragraphs / competitive_paragraphs

        return DimensionResult(
            score=score,
            findings=findings[:10],
            metadata={
                "competitive_paragraphs": competitive_paragraphs,
                "quantified": quantified_paragraphs,
            },
        )

    def _compute_composite_score(self, dimensions: Dict[str, DimensionResult]) -> float:
        """Calcula score composto ponderado pelos tres criterios."""
        total_weight = 0.0
        weighted_sum = 0.0

        for dim_key, dim_result in dimensions.items():
            # Mapeia string de volta para enum
            dim_enum = BiasDimension(dim_key)
            weight = self.WEIGHTS.get(dim_enum, 0.0)
            weighted_sum += dim_result.score * weight
            total_weight += weight

        if total_weight == 0:
            return 1.0

        return round(weighted_sum / total_weight, 3)


# Re-exportar
__all__ = [
    "BiasAuditService",
    "BiasReport",
    "DimensionResult",
    "BiasDimension",
]
