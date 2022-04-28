import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

__all__ = ["__version__"]


def _fetchVersion():
    HERE = Path(__file__).parent.resolve()

    for settings in HERE.rglob("package.json"):
        try:
            with settings.open() as f:
                return json.load(f)["version"]
        except FileNotFoundError:
            log.critical(f"Could not resolve package.json under dir {HERE!s}")


__version__ = _fetchVersion()
