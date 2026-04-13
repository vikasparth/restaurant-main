import logging
import sys

from pythonjsonlogger.json import JsonFormatter

from core.config import settings


def setup_logging() -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove any existing handlers
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if settings.is_production:
        # JSON format — parsed by Render log viewer
        formatter = JsonFormatter(fmt="%(asctime)s %(levelname)s %(name)s %(message)s")
    else:
        # Human-readable format for local development
        formatter = logging.Formatter(
            fmt="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
            datefmt="%H:%M:%S",
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


# Module-level logger — import this in other modules
logger = logging.getLogger("aap_ki_rasoi")
