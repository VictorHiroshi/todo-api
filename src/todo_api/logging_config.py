import logging

import structlog


def configure_logging(debug: bool = False) -> None:
    """Configura structlog para JSON em produção e console legível em dev."""
    # Processadores compartilhados
    shared_processors = [
        structlog.contextvars.merge_contextvars,  # injeta request_id, etc.
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if debug:
        # Desenvolvimento: console colorido e legível
        renderer = structlog.dev.ConsoleRenderer()
    else:
        # Produção: JSON para agregadores
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
