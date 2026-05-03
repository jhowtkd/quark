# FUTUR.IA Backend - Flask Application Factory
# -*- coding: utf-8 -*-
"""
Flask Application Factory
"""

import atexit
import os
import signal
import warnings

# Suppress multiprocessing resource_tracker warnings
warnings.filterwarnings("ignore", message=".*resource_tracker.*")

from flask import Flask, request
from flask_cors import CORS

from .config import Config
from .utils.logger import setup_logger, get_logger


def create_app(config_class=Config):
    """Flask application factory function"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # JSON encoding configuration
    if hasattr(app, 'json') and hasattr(app.json, 'ensure_ascii'):
        app.json.ensure_ascii = False

    # Setup logging
    logger = setup_logger('futuria')

    # Only log startup info in main process (avoid double logging in debug mode)
    is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    debug_mode = app.config.get('DEBUG', False)
    should_log_startup = not debug_mode or is_reloader_process

    if should_log_startup:
        logger.info("=" * 50)
        logger.info("FUTUR.IA Backend starting...")
        logger.info("=" * 50)

    # Wire observability client once at startup
    from .observability import build_observability_client
    obs_client = build_observability_client(config_class)
    app.config["OBSERVABILITY_CLIENT"] = obs_client

    if should_log_startup:
        if obs_client.is_enabled:
            logger.info(
                "Observability enabled: host=%s, env=%s, release=%s",
                config_class.LANGFUSE_HOST or "not set",
                config_class.LANGFUSE_ENV,
                config_class.LANGFUSE_RELEASE,
            )
        else:
            logger.info("Observability disabled (LANGFUSE_ENABLED=false)")

    # Register observability shutdown: flush traces then shutdown the client.
    # This runs after atexit handlers from other subsystems so traces are sent first.
    def _observability_shutdown():
        if app.config.get("OBSERVABILITY_CLIENT") is not None:
            client = app.config["OBSERVABILITY_CLIENT"]
            try:
                client.flush()
            except Exception:
                pass
            try:
                client.shutdown()
            except Exception:
                pass

    atexit.register(_observability_shutdown)

    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register simulation cleanup function
    from .services.simulation_runner import SimulationRunner
    SimulationRunner.register_cleanup()
    if should_log_startup:
        logger.info("Simulation cleanup registered")

    # Request logging middleware
    @app.before_request
    def log_request():
        req_logger = get_logger('futuria.request')
        req_logger.debug(f"Request: {request.method} {request.path}")
        if request.content_type and 'json' in request.content_type:
            req_logger.debug(f"Request body: {request.get_json(silent=True)}")

    @app.after_request
    def log_response(response):
        req_logger = get_logger('futuria.request')
        req_logger.debug(f"Response: {response.status_code}")
        return response

    # Register blueprints
    from .api import graph_bp, simulation_bp, report_bp, research_bp, feedback_bp
    from .api.health import health_bp
    from .api.observability import observability_bp
    app.register_blueprint(graph_bp, url_prefix='/api/graph')
    app.register_blueprint(simulation_bp, url_prefix='/api/simulation')
    app.register_blueprint(report_bp, url_prefix='/api/report')
    app.register_blueprint(research_bp, url_prefix='/api/research')
    app.register_blueprint(feedback_bp, url_prefix='/api/feedback')
    app.register_blueprint(health_bp, url_prefix='/api/health')
    app.register_blueprint(observability_bp, url_prefix='/api/observability')

    # Health check (backward compat)
    @app.route('/health')
    def health():
        return {'status': 'ok', 'service': 'FUTUR.IA Backend'}

    if should_log_startup:
        logger.info("FUTUR.IA Backend started successfully")

    return app
