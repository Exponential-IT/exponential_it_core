# exponential_core/schemas/base.py

from abc import ABC, abstractmethod
from pydantic import BaseModel


class OdooPayloadMixin(ABC):
    def as_odoo_payload(self) -> dict:
        """
        Punto de entrada estándar:
        - Toma los datos del modelo (sin None)
        - Delega la personalización a transform_payload(data)
        """
        data = self.model_dump(exclude_none=True)
        return self.transform_payload(data)

    @abstractmethod
    def transform_payload(self, data: dict) -> dict:
        """Personaliza cómo se transforma el payload final de Odoo"""
        ...


class BaseSchema(BaseModel, OdooPayloadMixin):
    """Base para todos los schemas con normalización de strings y soporte Odoo."""

    # Puedes configurar Pydantic v2 aquí si quieres:
    # model_config = ConfigDict(extra="ignore", use_enum_values=True, populate_by_name=True)
    pass
