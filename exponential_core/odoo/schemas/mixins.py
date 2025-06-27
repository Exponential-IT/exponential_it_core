# exponential_core/schemas/mixins.py

from pydantic import field_validator
from typing import Any, Optional, Union, get_origin, get_args


class StrNormalizerMixin:
    @field_validator("*", mode="before")
    @classmethod
    def normalize_optional_strings(cls, v: Any, info):
        annotation = info.annotation
        origin = get_origin(annotation)
        args = get_args(annotation)

        is_optional_str = annotation is str or (
            origin is Union and str in args and type(None) in args
        )

        if is_optional_str and isinstance(v, str) and not v.strip():
            return None

        return v
