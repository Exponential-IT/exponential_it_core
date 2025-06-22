# exponential_core\utils\format_error.py
from datetime import datetime, timezone


def format_error_response(
    message: str,
    error_type: str,
    status_code: int,
):
    """
    Crea una respuesta de error estándar para la API.

    Args:
        message (str): Mensaje de error para el cliente.
        error_type (str): Tipo o categoría del error.
        status_code (int): Código HTTP correspondiente.

    Returns:
        dict: Estructura de respuesta con metadatos del error.
    """
    return {
        "detail": message,
        "error_type": error_type,
        "status_code": status_code,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

