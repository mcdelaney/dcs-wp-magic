import logging


def get_logger(logger):
    logFormatter = logging.Formatter(
        "%(asctime)s [%(filename)s] [%(levelname)-5.5s]  %(message)s")

    fileHandler = logging.FileHandler(f"log/{logger.name}.log", 'w')
    fileHandler.setFormatter(logFormatter)
    logger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    logger.addHandler(consoleHandler)
    return logger
