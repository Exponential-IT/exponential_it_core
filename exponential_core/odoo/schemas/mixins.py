# exponential_core/schemas/mixins.py

from pydantic import field_validator
from typing import Any, Optional


class StrNormalizerMixin:
    @field_validator("*", mode="before")
    @classmethod
    def normalize_optional_strings(cls, v: Any, info):
        if info.field_annotation in [str, Optional[str]]:
            if isinstance(v, str) and not v.strip():
                return None
        return v
