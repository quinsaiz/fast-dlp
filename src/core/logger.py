import logging
import sys


def setup_logger(name: str):
    root_logger = logging.getLogger()

    if not root_logger.handlers:
        root_logger.setLevel(logging.INFO)

        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

    return logging.getLogger(name)
