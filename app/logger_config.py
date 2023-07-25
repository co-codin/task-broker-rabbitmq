import logging

from app.config import settings


def config_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)

    stream_handler = logging.StreamHandler()
    logger.addHandler(stream_handler)

