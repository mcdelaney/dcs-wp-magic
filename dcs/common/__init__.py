"""Logger to be used by various modules."""
import logging
from pathlib import Path


def get_logger(logger, propogate=False):
    logFormatter = logging.Formatter(
        "%(asctime)s [%(name)s] [%(levelname)-5.5s]  %(message)s")
    file_path = Path(f"log/{logger.name}.log")
    if not file_path.parent.exists():
        file_path.parent.mkdir()
    fileHandler = logging.FileHandler(file_path, 'w')
    fileHandler.setFormatter(logFormatter)
    logger.addHandler(fileHandler)
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    logger.addHandler(consoleHandler)
    logger.propogate = propogate
    return logger
