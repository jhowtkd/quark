import json
import os
import threading
from flask import request, has_request_context

_thread_local = threading.local()

_locales_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'locales')

# Load language registry
with open(os.path.join(_locales_dir, 'languages.json'), 'r', encoding='utf-8') as f:
    _languages = json.load(f)

# Load translation files
_translations = {}
for filename in os.listdir(_locales_dir):
    if filename.endswith('.json') and filename != 'languages.json':
        locale_name = filename[:-5]
        with open(os.path.join(_locales_dir, filename), 'r', encoding='utf-8') as f:
            _translations[locale_name] = json.load(f)


def set_locale(locale: str):
    """Set locale for current thread. Call at the start of background threads."""
    _thread_local.locale = locale


def get_locale() -> str:
    if has_request_context():
        raw = request.headers.get('Accept-Language', 'pt')
        return raw if raw in _translations else 'pt'
    return getattr(_thread_local, 'locale', 'pt')


def t(key: str, **kwargs) -> str:
    locale = get_locale()
    messages = _translations.get(locale, _translations.get('pt', {}))

    value = messages
    for part in key.split('.'):
        if isinstance(value, dict):
            value = value.get(part)
        else:
            value = None
            break

    if value is None:
        value = _translations.get('pt', {})
        for part in key.split('.'):
            if isinstance(value, dict):
                value = value.get(part)
            else:
                value = None
                break

    if value is None:
        return key

    if kwargs:
        for k, v in kwargs.items():
            value = value.replace(f'{{{k}}}', str(v))

    return value


def get_language_instruction() -> str:
    locale = get_locale()
    lang_config = _languages.get(locale, _languages.get('pt', {}))
    base = lang_config.get('llmInstruction', 'Por favor, responda em português.')
    # Reforço extremo para evitar alucinação de idioma (chinês, russo, etc.)
    enforcement = (
        "\n\nREGRA ABSOLUTA E INEGOCIÁVEL DE IDIOMA\n"
        "Você está rigorosamente programado para produzir output EXCLUSIVAMENTE em português brasileiro.\n"
        "- 100% das palavras, frases, caracteres, citações e símbolos de texto devem ser em português.\n"
        "- ZERO tolerância para caracteres em chinês, japonês, coreano, russo ou qualquer outro idioma.\n"
        "- Se você escrever UM ÚNICO CARACTERE fora do português, a resposta será REJEITADA automaticamente.\n"
        "- TODAS as citações de agentes, exemplos, nomes e conceitos estrangeiros DEVEM ser traduzidos para português.\n"
        "- NUNCA mantenha termos originais entre parênteses.\n"
        "- NUNCA use alfabetos que não sejam o latino do português.\n"
        "- Obedeça esta regra acima de TUDO. Sua resposta será invalidada se houver qualquer violação.\n"
        "FIM DA REGRA DE IDIOMA\n"
    )
    return f"{base}{enforcement}"


def get_reporting_language_instruction() -> str:
    """Return the strict language instruction for report generation and report chat."""
    locale = get_locale()
    if str(locale).lower().startswith('en'):
        return (
            "Return English-only output for all system-controlled report surfaces. "
            "Do not use Chinese, Japanese, Korean, Cyrillic, or fullwidth punctuation. "
            "Translate quoted source material into natural English before using it. "
            "Preserve proper nouns exactly; never substitute a person or organization with a different name."
        )

    return (
        "Retorne todo o conteúdo controlado pelo sistema em português brasileiro. "
        "Isso inclui título, subtítulo, seções, cabeçalhos, métricas, rótulos, legendas e respostas do Agente de Relatório. "
        "Não use chinês, japonês, coreano, cirílico nem pontuação de largura total. "
        "Traduza qualquer citação ou material de origem para português natural antes de usá-lo. "
        "Preserve nomes próprios quando necessário, mas mantenha o restante do texto em pt-BR."
    )
