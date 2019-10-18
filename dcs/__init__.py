import logging
from pathlib import Path


def get_logger(logger):
    logFormatter = logging.Formatter(
        "%(asctime)s [%(filename)s] [%(levelname)-5.5s]  %(message)s")

    file_path = Path(f"log/logger.name.log")
    if not file_path.exists():
        file_path.parent.mkdir()
    fileHandler = logging.FileHandler(file_path, 'w')
    fileHandler.setFormatter(logFormatter)
    logger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    logger.addHandler(consoleHandler)
    return logger
