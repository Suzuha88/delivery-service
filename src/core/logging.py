from loguru import logger

from .config import logging_settings

logger.level(logging_settings.LOG_LEVEL)
