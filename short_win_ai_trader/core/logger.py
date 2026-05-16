"""日志系统 — 使用structlog实现结构化日志"""

import logging
import os
import sys
from pathlib import Path

import structlog


def setup_logging(
    level: str = "INFO",
    log_file: str = "logs/swat.log",
    max_size: int = 10485760,
    backup_count: int = 5,
):
    """配置结构化日志系统
    
    Args:
        level: 日志级别
        log_file: 日志文件路径
        max_size: 单个日志文件最大字节
        backup_count: 保留日志文件数
    """
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # 标准库logging配置
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper(), logging.INFO),
    )

    # 文件handler
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        log_file, maxBytes=max_size, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setLevel(getattr(logging, level.upper(), logging.INFO))

    # structlog配置
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer(colors=True) if sys.stdout.isatty() 
            else structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logger = structlog.get_logger("swat")
    return logger


def get_logger(name: str = "swat"):
    """获取命名日志器"""
    return structlog.get_logger(name)
