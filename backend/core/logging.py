import logging
import sys
from core.middleware import request_id_var

from pythonjsonlogger.json import JsonFormatter

from core.config import settings


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True


def setup_logging() -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove any existing handlers
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIdFilter())

    if settings.is_production:
        # JSON format — parsed by Render log viewer
        formatter = JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s"
        )
    else:
        # Human-readable format for local development
        formatter = logging.Formatter(
            fmt="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s  %(request_id)s",
            datefmt="%H:%M:%S",
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


# Module-level logger — import this in other modules
logger = logging.getLogger("aap_ki_rasoi")
