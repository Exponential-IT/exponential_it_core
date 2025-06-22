# exponential_core\logger\core.py
import logging

def get_logger(name="app") -> logging.Logger:
    """
    Obtiene el logger nombrado. No configura nada si ya tiene handlers.
    Si no tiene handlers (por ejemplo, en tests), devuelve un logger vacío
    que solo funcionará si alguien lo configura manualmente.
    """
    logger = logging.getLogger(name)

    # Si ya tiene handlers, lo devolvemos tal cual (usa la configuración global)
    if logger.hasHandlers():
        return logger

    # ❌ No configuramos nada — el microservicio es responsable de hacerlo
    return logger
