"""
Configuration Management
Loads configuration from .env file in project root without mutating process env.
"""

import os
from typing import Optional
from dotenv import dotenv_values

# Read .env from project root without exporting values into os.environ.
project_root_env = os.path.join(os.path.dirname(__file__), '../../.env')
DOTENV_VALUES = dotenv_values(project_root_env) if os.path.exists(project_root_env) else {}


def _env(key: str, default=None):
    """Resolve config from process env first, then .env file, then default."""
    return os.environ.get(key, DOTENV_VALUES.get(key, default))


class Config:
    """Flask configuration class"""

    # Flask config
    SECRET_KEY = _env('SECRET_KEY', 'futuria-secret-key')
    DEBUG = str(_env('FLASK_DEBUG', 'True')).lower() == 'true'

    # JSON configuration
    JSON_AS_ASCII = False

    # LLM configuration (OpenAI-compatible)
    LLM_API_KEY = _env('LLM_API_KEY')
    LLM_BASE_URL = _env('LLM_BASE_URL', 'https://api.openai.com/v1')
    LLM_MODEL_NAME = _env('LLM_MODEL_NAME', 'gpt-4o-mini')

    # Zep configuration
    ZEP_API_KEY = _env('ZEP_API_KEY')

    # File upload configuration
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'md', 'txt', 'markdown'}

    # Text processing configuration
    DEFAULT_CHUNK_SIZE = 300  # Default chunk size
    DEFAULT_CHUNK_OVERLAP = 30  # Default overlap size

    # OASIS simulation configuration
    OASIS_DEFAULT_MAX_ROUNDS = int(_env('OASIS_DEFAULT_MAX_ROUNDS', '10'))
    OASIS_SIMULATION_DATA_DIR = os.path.join(os.path.dirname(__file__), '../uploads/simulations')

    # OASIS platform available actions
    OASIS_TWITTER_ACTIONS = [
        'CREATE_POST', 'LIKE_POST', 'REPOST', 'FOLLOW', 'DO_NOTHING', 'QUOTE_POST'
    ]
    OASIS_REDDIT_ACTIONS = [
        'LIKE_POST', 'DISLIKE_POST', 'CREATE_POST', 'CREATE_COMMENT',
        'LIKE_COMMENT', 'DISLIKE_COMMENT', 'SEARCH_POSTS', 'SEARCH_USER',
        'TREND', 'REFRESH', 'DO_NOTHING', 'FOLLOW', 'MUTE'
    ]

    # Report Agent configuration
    REPORT_AGENT_MAX_TOOL_CALLS = int(_env('REPORT_AGENT_MAX_TOOL_CALLS', '5'))
    REPORT_AGENT_MAX_REFLECTION_ROUNDS = int(_env('REPORT_AGENT_MAX_REFLECTION_ROUNDS', '2'))
    REPORT_AGENT_TEMPERATURE = float(_env('REPORT_AGENT_TEMPERATURE', '0.5'))

    # Langfuse observability configuration (self-hosted)
    LANGFUSE_ENABLED = str(_env('LANGFUSE_ENABLED', 'false')).lower() == 'true'
    LANGFUSE_HOST = _env('LANGFUSE_HOST')
    LANGFUSE_PUBLIC_KEY = _env('LANGFUSE_PUBLIC_KEY')
    LANGFUSE_SECRET_KEY = _env('LANGFUSE_SECRET_KEY')
    LANGFUSE_ENV = _env('LANGFUSE_ENV', 'development')
    LANGFUSE_RELEASE = _env('LANGFUSE_RELEASE', 'local')
    LANGFUSE_DEBUG = str(_env('LANGFUSE_DEBUG', 'false')).lower() == 'true'
    LANGFUSE_SAMPLE_RATE = float(_env('LANGFUSE_SAMPLE_RATE', '1.0'))

    # Deep research connector API keys
    BRAVE_SEARCH_API_KEY: Optional[str] = _env('BRAVE_SEARCH_API_KEY')
    TAVILY_API_KEY: Optional[str] = _env('TAVILY_API_KEY')
    JINA_API_KEY: Optional[str] = _env('JINA_API_KEY')

    @classmethod
    def validate(cls):
        """Validate required configuration."""
        errors = []
        if not cls.LLM_API_KEY:
            errors.append('LLM_API_KEY not configured')
        if not cls.ZEP_API_KEY:
            errors.append('ZEP_API_KEY not configured')

        explicit_langfuse_enabled = os.environ.get('LANGFUSE_ENABLED')
        if explicit_langfuse_enabled is not None:
            langfuse_enabled = explicit_langfuse_enabled.lower() == 'true'
            lookup = os.environ.get
        else:
            langfuse_enabled = str(_env('LANGFUSE_ENABLED', 'false')).lower() == 'true'
            lookup = lambda key: _env(key)

        if langfuse_enabled:
            if not lookup('LANGFUSE_HOST'):
                errors.append('LANGFUSE_HOST not configured')
            if not lookup('LANGFUSE_PUBLIC_KEY'):
                errors.append('LANGFUSE_PUBLIC_KEY not configured')
            if not lookup('LANGFUSE_SECRET_KEY'):
                errors.append('LANGFUSE_SECRET_KEY not configured')
        return errors
