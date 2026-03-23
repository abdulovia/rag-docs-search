"""Настройка логирования через loguru"""

import sys
from pathlib import Path
from loguru import logger


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "text",
    log_dir: Path = Path("logs"),
) -> None:
    """Настройка логирования"""
    
    # Удаляем стандартные handlers
    logger.remove()
    
    # Формат для консоли
    console_format = (
        "<green>{time:HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Формат для файла (без цветов)
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
    )
    
    # Console handler
    logger.add(
        sys.stderr,
        format=console_format,
        level=log_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    
    # File handlers
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Основной лог
    logger.add(
        log_dir / "app.log",
        format=file_format,
        level=log_level,
        rotation="10 MB",
        retention="7 days",
        encoding="utf-8",
        backtrace=True,
        diagnose=True,
    )
    
    # Debug лог (всё)
    logger.add(
        log_dir / "debug.log",
        format=file_format,
        level="DEBUG",
        rotation="50 MB",
        retention="3 days",
        encoding="utf-8",
        backtrace=True,
        diagnose=True,
        filter=lambda record: record["level"].name in ("DEBUG", "TRACE"),
    )
    
    # Error лог
    logger.add(
        log_dir / "error.log",
        format=file_format,
        level="ERROR",
        rotation="10 MB",
        retention="14 days",
        encoding="utf-8",
        backtrace=True,
        diagnose=True,
    )
    
    # RAG pipeline лог
    logger.add(
        log_dir / "rag.log",
        format=file_format,
        level="DEBUG",
        rotation="20 MB",
        retention="7 days",
        encoding="utf-8",
        filter=lambda record: "rag" in record["name"].lower() 
            or "retriev" in record["name"].lower()
            or "llm" in record["name"].lower()
            or "embed" in record["name"].lower()
            or "vector" in record["name"].lower(),
    )
    
    logger.info(f"Logging initialized: level={log_level}, dir={log_dir}")
