import logging
import os
import sys


_done = False


def _configure_logging() -> None:
    global _done
    if _done and not os.getenv("FORCE_RECONFIGURE_LOGGING"):
        return
    _done = True

    level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
    if sys.stderr.isatty():
        from rich.logging import RichHandler

        handler: logging.Handler = RichHandler(rich_tracebacks=True, markup=True)
        fmt = "%(message)s"
        datefmt = "[%X]"
    else:
        # Cloud Run / Docker: no TTY; avoid Rich edge cases and keep structured logs.
        handler = logging.StreamHandler(sys.stderr)
        fmt = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
        datefmt = None
    logging.basicConfig(level=level, format=fmt, datefmt=datefmt, handlers=[handler], force=True)


_configure_logging()

logger = logging.getLogger("adk_agents")
