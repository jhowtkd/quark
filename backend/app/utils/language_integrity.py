"""Shared language integrity checks for reporting outputs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Dict, Any, List

FORBIDDEN_PATTERNS: dict[str, re.Pattern[str]] = {
    "cjk": re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]"),
    "kana": re.compile(r"[\u3040-\u30ff]"),
    "hangul": re.compile(r"[\uac00-\ud7af]"),
    "cyrillic": re.compile(r"[\u0400-\u04ff\u0500-\u052f]"),
    "fullwidth": re.compile(r"[\u3000-\u303f\uff00-\uffef]"),
}

ENTITY_PATTERN = re.compile(
    r"\b(?:[A-ZÀ-ÖØ-Þ][a-zà-öø-ÿ]+(?:[ \t]+(?:da|de|do|dos|das|e))?[ \t]+)+[A-ZÀ-ÖØ-Þ][a-zà-öø-ÿ]+\b"
)
DEFAULT_SUSPECT_TERMS = (
    "Flamengo",
    "Flamengo Bolsonaro",
)

# Stopwords that appear in generic section-heading phrases.
# These are filtered from entity_drift detection so that "Medical Monitoring"
# or "Professional Response" headings don't trigger false positives.
_GENERIC_PHRASE_STOPWORDS = frozenset({
    # Analysis/action nouns
    "analysis", "trend", "trends", "pattern", "patterns",
    "assessment", "evaluation", "overview", "summary", "conclusion",
    "introduction", "discussion", "findings", "results", "methods",
    "background", "objectives", "references", "appendix", "annex", "addendum", "supplement",
    "approach", "approachs", "approaches", "considerations",
    # Risk/opportunity nouns
    "risk", "risks", "opportunity", "opportunities", "gaps",
    # Response/action nouns
    "response", "responses", "reaction", "reactions",
    # Professional/institutional nouns
    "professional", "professionals", "institutional", "community", "communities",
    "regulatory", "regulations", "governance", "framework", "frameworks",
    "landscape", "dynamics", "tensions",
    # Monitoring/measurement nouns
    "monitoring", "measurement", "measurements", "assessments",
    # General modifiers
    "context", "perspective", "perspectives",
    "consequences", "implications", "factors",
    "safety", "security", "protocol", "protocols", "projections",
    # Medical/health nouns (generic, not entity names)
    "medical", "clinical", "patient", "patients", "treatment", "treatments",
    "health", "healthcare", "diagnosis", "therapeutic", "intervention", "interventions",
    "safety", "concern", "concerns", "disruption", "disruptions",
    # Organizational nouns
    "society", "societies", "association", "associations",
    "organization", "organisations", "institution", "institutions",
    "committee", "council", "board",
    # General adjectives/adverbs that appear in headings
    "harm", "reduction", "increased", "decreased", "enhanced", "natural",
    "emerging", "emergent", "current", "new", "identified",
    "axis", "protocol", "protocols", "projections",
})


@dataclass(frozen=True)
class LanguageIntegrityResult:
    forbidden_categories: tuple[str, ...]
    missing_entities: tuple[str, ...]
    suspect_terms: tuple[str, ...]
    entity_drift: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return (
            not self.forbidden_categories
            and not self.missing_entities
            and not self.suspect_terms
            and not self.entity_drift
        )


def _normalize(items: Iterable[str] | None) -> tuple[str, ...]:
    if not items:
        return ()
    return tuple(item for item in items if item)


def _canonicalize_entity(value: str) -> str:
    cleaned = " ".join((value or "").split()).strip()
    return re.sub(r"^(?:the|a|an|o|os|as|um|uma)\s+", "", cleaned, flags=re.IGNORECASE)


def _entity_tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ']+", _canonicalize_entity(value).casefold())
        if len(token) > 2
    }


def extract_entity_candidates(text: str | None) -> tuple[str, ...]:
    content = text or ""
    candidates: list[str] = []
    seen: set[str] = set()
    for match in ENTITY_PATTERN.findall(content):
        candidate = " ".join(match.split())
        key = candidate.casefold()
        if key in seen:
            continue
        seen.add(key)
        candidates.append(candidate)
    return tuple(candidates)


def assess_text_integrity(
    text: str | None,
    *,
    expected_entities: Iterable[str] | None = None,
    allowed_entities: Iterable[str] | None = None,
    suspect_terms: Iterable[str] | None = None,
) -> LanguageIntegrityResult:
    content = text or ""
    lowered = content.casefold()

    forbidden_categories = tuple(
        name for name, pattern in FORBIDDEN_PATTERNS.items() if pattern.search(content)
    )

    expected = _normalize(expected_entities)
    missing_entities = tuple(entity for entity in expected if entity.casefold() not in lowered)

    suspects = _normalize(suspect_terms) or DEFAULT_SUSPECT_TERMS
    present_suspects = tuple(term for term in suspects if term.casefold() in lowered)

    allowed = _normalize(allowed_entities)
    allowed_casefold = {_canonicalize_entity(allowed_entity).casefold() for allowed_entity in allowed}
    allowed_tokens = set().union(*(_entity_tokens(entity) for entity in allowed)) if allowed else set()
    candidate_entities = extract_entity_candidates(content)
    entity_drift = tuple(
        entity
        for entity in candidate_entities
        if allowed
        and _canonicalize_entity(entity).casefold() not in allowed_casefold
        and bool(_entity_tokens(entity) & allowed_tokens)
    )
    # Generic-heading filter:
    # Filter out headings that reuse domain terminology from allowed content:
    #   - all-stopword headings (non_stop is empty)
    #   - headings where ALL non-stop tokens are already present in the full allowed token set
    #     (this catches headings like "Informal Hormonal Transformation Protocols" that reuse
    #     all their content words from prior sections, even when spread across multiple entities)
    #   - headings where non-stop tokens are a proper subset of a SINGLE allowed entity's tokens
    #     (e.g., "Medical Monitoring" ⊆ "Medical Response")
    _allowed_entity_tokens = {
        frozenset(_entity_tokens(entity)): entity
        for entity in (allowed or [])
    }
    _all_allowed_tokens = set().union(*(_entity_tokens(e) for e in (allowed or [])))
    _filtered: list[str] = []
    for entity in entity_drift:
        non_stop = {tok for tok in _entity_tokens(entity) if tok not in _GENERIC_PHRASE_STOPWORDS}
        if not non_stop:
            continue  # all-stopword heading → filter out
        # Filter if ALL non-stop tokens are already in the global allowed token set
        if non_stop <= _all_allowed_tokens:
            continue  # heading reusing existing terminology → filter out
        # Filter if non_stop tokens are a proper subset of a SINGLE allowed entity's tokens
        for allowed_toks in _allowed_entity_tokens:
            if non_stop <= allowed_toks:
                break
        else:
            _filtered.append(entity)
    entity_drift = _filtered

    return LanguageIntegrityResult(
        forbidden_categories=forbidden_categories,
        missing_entities=missing_entities,
        suspect_terms=present_suspects,
        entity_drift=tuple(entity_drift),
    )


def enforce_controlled_output(
    text: str | None,
    *,
    fallback_text: str,
    expected_entities: Iterable[str] | None = None,
    allowed_entity_source: str | None = None,
    suspect_terms: Iterable[str] | None = None,
) -> tuple[str, LanguageIntegrityResult]:
    allowed_entities = extract_entity_candidates(allowed_entity_source)
    result = assess_text_integrity(
        text,
        expected_entities=expected_entities,
        allowed_entities=allowed_entities,
        suspect_terms=suspect_terms,
    )
    if result.ok:
        return (text or ""), result
    return fallback_text, result


# =============================================================================
# Language Switching Detection (QUAL-01)
# =============================================================================

PORTUGUESE_STOPWORDS = frozenset({
    "o", "a", "os", "as", "um", "uma", "uns", "umas", "de", "do", "da", "dos", "das",
    "em", "no", "na", "nos", "nas", "por", "para", "pelo", "pela", "pelos", "pelas",
    "com", "sem", "sob", "sobre", "entre", "ante", "apos", "atras", "ate", "desde",
    "que", "se", "porque", "pois", "mas", "entao", "quando", "enquanto", "embora",
    "e", "ou", "nem", "tambem", "ja", "ainda", "so", "apenas", "muito", "mais",
    "menos", "bem", "mal", "assim", "aqui", "ai", "la", "onde", "como", "qual",
    "quem", "cujo", "cuja", "cujos", "cujas", "este", "esta", "estes", "estas",
    "esse", "essa", "esses", "essas", "aquele", "aquela", "aqueles", "aquelas",
    "meu", "minha", "meus", "minhas", "teu", "tua", "teus", "tuas", "seu", "sua",
    "seus", "suas", "nosso", "nossa", "nossos", "nossas", "dela", "dele", "delas",
    "deles", "esta", "está", "estão", "foi", "foram", "ser", "será", "são", "sao",
    "tem", "têm", "há", "houve", "pode", "podem", "deve", "devem", "pela", "pelo",
    "pelos", "pelas", "nos", "nas", "num", "numa", "nuns", "numas", "ao", "à", "aos",
    "às", "diz", "dizem", "afirma", "afirmam", "segundo", "conforme", "durante",
    "após", "através", "devido", "contra", "perante", "exceto", "salvo", "mediante",
})

ENGLISH_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "by", "from", "as", "is", "was", "are", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could", "should",
    "may", "might", "must", "shall", "can", "need", "dare", "ought", "used", "to",
    "this", "that", "these", "those", "i", "you", "he", "she", "it", "we", "they",
    "me", "him", "her", "us", "them", "my", "your", "his", "its", "our", "their",
    "mine", "yours", "hers", "ours", "theirs", "what", "which", "who", "whom",
    "whose", "where", "when", "why", "how", "all", "each", "every", "both", "few",
    "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very", "just", "now", "then", "here", "there",
    "up", "down", "out", "off", "over", "under", "again", "further", "once",
    "said", "says", "according", "during", "through", "between", "among", "within",
    "without", "against", "toward", "towards", "about", "above", "below", "before",
    "after", "since", "until", "while", "because", "if", "unless", "although",
    "though", "however", "therefore", "thus", "hence", "moreover", "furthermore",
})


def detect_language_switches(
    text: str | None,
    expected_lang: str = "pt",
    threshold_ratio: float = 0.08,
) -> List[Dict[str, Any]]:
    """
    Detecta troca de idioma no meio de um texto.

    Analisa por paragrafo usando densidade de stopwords.
    Retorna lista de switches detectados.

    Args:
        text: Texto a analisar.
        expected_lang: Idioma esperado ('pt' ou 'en').
        threshold_ratio: Razao minima de stopwords para considerar um idioma.

    Returns:
        Lista de dicts com 'paragraph_index', 'expected', 'detected', 'snippet'.
    """
    content = text or ""
    expected_pt = expected_lang.lower().startswith("pt")
    switches: List[Dict[str, Any]] = []

    paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 30]
    if not paragraphs:
        return []

    for idx, para in enumerate(paragraphs):
        words = re.findall(r"[a-zA-ZÀ-ÖØ-öø-ÿ]+", para.lower())
        if not words:
            continue

        pt_count = sum(1 for w in words if w in PORTUGUESE_STOPWORDS)
        en_count = sum(1 for w in words if w in ENGLISH_STOPWORDS)

        pt_ratio = pt_count / len(words)
        en_ratio = en_count / len(words)

        detected = "unknown"
        if pt_ratio > en_ratio and pt_ratio > threshold_ratio:
            detected = "pt"
        elif en_ratio > pt_ratio and en_ratio > threshold_ratio:
            detected = "en"

        if expected_pt and detected == "en":
            switches.append({
                "paragraph_index": idx,
                "expected": "pt",
                "detected": "en",
                "snippet": para[:120].replace("\n", " "),
            })
        elif not expected_pt and detected == "pt":
            switches.append({
                "paragraph_index": idx,
                "expected": "en",
                "detected": "pt",
                "snippet": para[:120].replace("\n", " "),
            })

    return switches
