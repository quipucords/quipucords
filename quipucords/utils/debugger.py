"""Start remote debugger for quipucords (if required)."""

from logging import getLogger

import environ

logger = getLogger(__name__)

env = environ.Env()

DEBUGPY = env.bool("QUIPUCORDS_DEBUGPY", False)
DEBUGPY_PORT = env.int("QUIPUCORDS_DEBUGPY_PORT", 5678)


def start_debugger_if_required():
    """Start a debugger session if QUIPUCORDS_DEBUGPY envvar is set."""
    if DEBUGPY:
        try:
            import debugpy
        except ImportError:
            logger.exception("debugpy is not installed, can't start debugger.")
            raise SystemExit()

        debugpy.listen(("0.0.0.0", DEBUGPY_PORT))  # noqa: S104
        print("⏳ debugpy debugger can now be attached ⏳", flush=True)
