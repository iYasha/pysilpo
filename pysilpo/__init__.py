import logging
import os

__version__ = "0.2.0"

DEBUG = int(os.getenv("DEBUG", "0"))

logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-17s | [%(name)s] | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
