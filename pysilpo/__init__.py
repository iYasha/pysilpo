import logging
import os

from pysilpo.client import Silpo

__version__ = "1.0.2"

DEBUG = int(os.getenv("DEBUG", "0"))

logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-17s | [%(name)s] | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

__all__ = ("__version__", "Silpo")
