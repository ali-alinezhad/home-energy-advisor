import logging
from datetime import datetime
from pathlib import Path

from app.core.settings import settings

LOG_DIR = Path("var/log")

logger = logging.getLogger("home-energy-advisor")
logger.setLevel(logging.INFO)


def configure_logging() -> None:
    if logger.handlers:
        return

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if settings.log_to_file:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_file_name = datetime.now().strftime("%Y-%m-%d") + ".log"
        file_handler = logging.FileHandler(LOG_DIR / log_file_name)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
