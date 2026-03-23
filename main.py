"""Main entry point для запуска API сервера"""

import sys
from pathlib import Path

import uvicorn

from src.infrastructure.config.settings import get_settings


def main():
    settings = get_settings()

    # Setup loguru
    from loguru import logger
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
        level="DEBUG",
        colorize=True,
    )
    logger.add(
        "logs/app.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function} | {message}",
        level="DEBUG",
        rotation="10 MB",
    )
    logger.info(f"Logging initialized: level=DEBUG")

    # Run server
    uvicorn.run(
        "src.interfaces.api.app:app",
        host="0.0.0.0",
        port=settings.api_port,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    main()
