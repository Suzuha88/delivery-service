from loguru import logger

from .config import settings

logger.level(settings.LOG_LEVEL)
