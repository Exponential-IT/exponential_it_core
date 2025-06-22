# exponential_core/exceptions/__init__.py
from exponential_core.exceptions.setup import setup_exception_handlers
from exponential_core.exceptions.middleware import GlobalExceptionMiddleware
from exponential_core.exceptions.base import CustomAppException

# 👇 Importación explícita solo para autocompletado (VSCode, PyCharm, etc.)
from exponential_core.exceptions.types import (
    InvoiceParsingError,
    TaxIdNotFoundError,
    ValidTaxIdNotFoundError,
    OdooException,
    SecretNotFoundError,
    SecretAlreadyExistsError,
    SecretsNotFound,
    MissingSecretKey,
)

from . import types

__all__ = [
    "setup_exception_handlers",
    "GlobalExceptionMiddleware",
    "CustomAppException",
    # explícitos
    "InvoiceParsingError",
    "TaxIdNotFoundError",
    "ValidTaxIdNotFoundError",
    "OdooException",
    "SecretNotFoundError",
    "SecretAlreadyExistsError",
    "SecretsNotFound",
    "MissingSecretKey",
]

# 👇 Dinámico para futuros tipos sin romper compatibilidad
for name in dir(types):
    obj = getattr(types, name)
    if not name.startswith("_") and isinstance(obj, type) and issubclass(obj, CustomAppException):
        globals()[name] = obj
        if name not in __all__:
            __all__.append(name)
