from __future__ import annotations

import re
from datetime import datetime
from enum import StrEnum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class DocumentTypeLetter(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    M = "M"
    NA = "N/A"  # por compatibilidad si quisieras mapearlo; no se usa por defecto


_DOC_LETTER_RE = re.compile(
    r"\b(Factura|Nota\s+de\s+Cr[eé]dito|Nota\s+de\s+D[eé]bito)\s*([ABCM])\b", re.I
)
_DOC_LETTER_TIGHT_RE = re.compile(r"\bFactura\s*([ABCM])\b", re.I)
_DOC_LETTER_PACKED_RE = re.compile(r"\bFactura?([ABCM])\b", re.I)  # ej. "FACTURAA"

_CODE_RE = re.compile(
    r"\b(COD(?:\.|IGO)?|C[óo]d(?:\.|igo)?|Cod\.?\.?Nro\.?)\s*[:.]?\s*(\d{1,3})\b", re.I
)
_CODE_DIGITS_RE = re.compile(r"\b(\d{1,3})\b")

# 0001-00001234  |  0001 00001234  |  00001-00000245
_DOCNUM_RE = re.compile(r"\b(?P<pv>\d{4,5})\s*[-\s]\s*(?P<num>\d{6,8})\b")

# 14 dígitos de CAE/CAEA
_CAE_DIGITS_RE = re.compile(r"\b(CAE|CAEA)\s*[:#]?\s*([0-9\.\s-]{10,})\b", re.I)
_ONLY_DIGITS_RE = re.compile(r"\D+")

# fechas comunes dd/mm/yyyy o yyyy-mm-dd
_DATE_SLASH_RE = re.compile(r"\b(\d{2})[/-](\d{2})[/-](\d{4})\b")
_DATE_ISO_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")


def _only_digits(s: str) -> str:
    return _ONLY_DIGITS_RE.sub("", s)


def _normalize_doc_number(s: str) -> Optional[str]:
    """
    Devuelve ####-######## si detecta dos bloques numéricos (pv y num).
    Acepta separador espacio o guion. Rellena con ceros a la izquierda (pv: 4/5, num: 8).
    """
    if not s:
        return None
    m = _DOCNUM_RE.search(s)
    if not m:
        # intento “libre”: si hay dos grupos de dígitos pegados
        digits = re.findall(r"\d+", s)
        if len(digits) >= 2:
            pv, num = digits[0], digits[1]
            pv = pv.zfill(4 if len(pv) <= 4 else 5)
            num = num.zfill(8)
            return f"{pv}-{num}"
        return None
    pv = m.group("pv")
    num = m.group("num")
    pv = pv.zfill(4 if len(pv) <= 4 else 5)
    num = num.zfill(8)
    return f"{pv}-{num}"


def _normalize_cae(s: str) -> Optional[str]:
    if not s:
        return None
    # si viene con rótulo CAE/CAEA en el texto
    m = _CAE_DIGITS_RE.search(s)
    if m:
        digits = _only_digits(m.group(2))
        return digits if len(digits) == 14 else (digits or None)
    # si es solo dígitos (o con puntuación)
    digits = _only_digits(s)
    return digits if len(digits) == 14 else (digits or None)


def _normalize_cae_due_date(s: str) -> Optional[str]:
    if not s:
        return None
    # dd/mm/yyyy o dd-mm-yyyy
    m = _DATE_SLASH_RE.search(s)
    if m:
        d, mth, y = m.groups()
        try:
            return datetime(int(y), int(mth), int(d)).date().isoformat()
        except ValueError:
            pass
    # yyyy-mm-dd ya normal
    m = _DATE_ISO_RE.search(s)
    if m:
        y, mth, d = m.groups()
        try:
            return datetime(int(y), int(mth), int(d)).date().isoformat()
        except ValueError:
            pass
    return s.strip() or None


def _extract_doc_letter(s: str) -> Optional[str]:
    if not s:
        return None
    for rx in (_DOC_LETTER_RE, _DOC_LETTER_TIGHT_RE, _DOC_LETTER_PACKED_RE):
        m = rx.search(s)
        if m:
            # la letra puede estar en el último grupo
            letter = m.groups()[-1]
            letter = letter.strip().upper()
            if letter in {"A", "B", "C", "M"}:
                return letter
    # fallback: si la cadena es solo una letra válida
    s1 = s.strip().upper()
    if s1 in {"A", "B", "C", "M"}:
        return s1
    return None


def _extract_doc_code(s: str) -> Optional[str]:
    if not s:
        return None
    m = _CODE_RE.search(s)
    if m:
        code = m.group(2)
        return code.zfill(2)
    # si solo vienen los dígitos aislados y son razonables (1–3)
    m = _CODE_DIGITS_RE.search(s)
    if m:
        code = m.group(1)
        if 1 <= len(code) <= 3:
            return code.zfill(2)
    return None


class DocumentMetadataSchema(BaseModel):
    """
    Esquema de salida del prompt de metadatos AFIP.
    Todos los campos son opcionales (null si no se encuentran).
    """

    model_config = ConfigDict(extra="ignore", use_enum_values=True)

    document_type: Optional[DocumentTypeLetter] = Field(
        default=None, description="Letra del comprobante: A, B, C, M."
    )
    document_code: Optional[str] = Field(
        default=None, description="Código AFIP (p. ej., 01, 006, 011)."
    )
    document_number: Optional[str] = Field(
        default=None, description="Número normalizado ####-########."
    )
    cae: Optional[str] = Field(
        default=None, description="Código CAE/CAEA de 14 dígitos."
    )
    cae_due_date: Optional[str] = Field(
        default=None,
        description="Fecha de vencimiento del CAE en ISO (YYYY-MM-DD) si fue posible normalizar.",
    )
    inv_id: Optional[int] = Field(default=None)
    purchase_order_number: Optional[str] = Field(default=None)

    # --- Validaciones y normalizaciones ---

    @field_validator("document_type", mode="before")
    @classmethod
    def _v_document_type(cls, v):
        if v is None:
            return None
        # intentar extraer desde textos como "FACTURAA", "Factura A", etc.
        letter = _extract_doc_letter(str(v))
        # si no se pudo extraer, permitir que Pydantic valide si es letra directa
        return letter or v

    @field_validator("document_code", mode="before")
    @classmethod
    def _v_document_code(cls, v):
        if v is None:
            return None
        code = _extract_doc_code(str(v))
        return code or str(v).strip() or None

    @field_validator("document_number", mode="before")
    @classmethod
    def _v_document_number(cls, v):
        if v is None:
            return None
        norm = _normalize_doc_number(str(v))
        return norm or None

    @field_validator("cae", mode="before")
    @classmethod
    def _v_cae(cls, v):
        if v is None:
            return None
        norm = _normalize_cae(str(v))
        return norm or None

    @field_validator("cae_due_date", mode="before")
    @classmethod
    def _v_cae_due_date(cls, v):
        if v is None:
            return None
        return _normalize_cae_due_date(str(v))
