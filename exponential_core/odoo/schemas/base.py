# exponential_core/schemas/base.py

from pydantic import BaseModel
from abc import ABC, abstractmethod
from exponential_core.odoo.schemas.mixins import StrNormalizerMixin


class OdooPayloadMixin(ABC):
    def as_odoo_payload(self) -> dict:
        data = self.model_dump(exclude_none=True)
        return self.transform_payload(data)

    @abstractmethod
    def transform_payload(self, data: dict) -> dict:
        """Personaliza cómo se transforma el payload final de Odoo"""
        return data


class BaseSchema(BaseModel, StrNormalizerMixin, OdooPayloadMixin):
    """Base para todos los schemas con normalización de strings y soporte Odoo."""

    pass
