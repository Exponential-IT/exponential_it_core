# exponential_core\logger\configure.py
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from colorlog import ColoredFormatter

_logger_initialized = False  # Protección global


def configure_logging(
    log_level: str = "INFO",
    log_file: str = "logs/errors.log",
    force: bool = False,
    log_to_console: bool = True,
    log_to_file: bool = True,
):
    """
    Configura el sistema de logging con consola y/o archivo rotativo.

    Args:
        log_level (str): Nivel de log (ej: "DEBUG", "INFO").
        log_file (str): Ruta del archivo de log.
        force (bool): Forzar reconfiguración si ya está inicializado.
        log_to_console (bool): Habilita logs en la consola.
        log_to_file (bool): Habilita logs en archivo rotativo.
    """
    global _logger_initialized

    if _logger_initialized and not force:
        return logging.getLogger("app")

    logger = logging.getLogger("app")
    logger.setLevel(log_level)
    logger.handlers.clear()

    if log_to_file:
        log_file_path = Path(log_file).resolve()
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            filename=log_file_path,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding="utf-8",
        )
        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(pathname)s:%(lineno)d | %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    if log_to_console:
        console_handler = logging.StreamHandler()
        color_formatter = ColoredFormatter(
            "%(log_color)s%(asctime)s | %(levelname)s | %(name)s | %(pathname)s:%(lineno)d | %(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
            style="%",
        )
        console_handler.setFormatter(color_formatter)
        logger.addHandler(console_handler)

    _logger_initialized = True
    return logger
