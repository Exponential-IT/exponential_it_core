# exponential_core\exceptions\types.py
from typing import List
from exponential_core.exceptions.base import CustomAppException


class InvoiceParsingError(CustomAppException):
    def __init__(self, detail: str):
        super().__init__(f"Error al parsear factura: {detail}", status_code=422)


class TaxIdNotFoundError(CustomAppException):
    def __init__(self, invoice_number: str, candidates: list[float]):
        super().__init__(
            message=(
                f"No se encontró un tax_id válido para la factura '{invoice_number}'. "
                f"Porcentajes candidatos: {candidates}"
            ),
            status_code=422,
            data={
                "invoice_number": invoice_number,
                "candidates": candidates,
            },
        )


class ValidTaxIdNotFoundError(CustomAppException):
    def __init__(self, raw_ids: List[str]):
        super().__init__(
            message="No se encontraron identificadores fiscales válidos.",
            status_code=422,
            data={"candidates": raw_ids},
        )


class OdooException(CustomAppException):
    def __init__(self, detail: str, data: dict = None, status_code: int = 502):
        super().__init__(message=detail, status_code=status_code, data=data or {})


class SecretNotFoundError(CustomAppException):
    def __init__(self, secret_name: str):
        super().__init__(
            message=f"El secreto '{secret_name}' no fue encontrado en AWS Secrets Manager.",
            status_code=404,
            data={"secret_name": secret_name},
        )


class SecretAlreadyExistsError(CustomAppException):
    def __init__(self, secret_name: str):
        super().__init__(
            message=f"El secreto '{secret_name}' ya existe en AWS Secrets Manager.",
            status_code=409,  # Conflicto
            data={"secret_name": secret_name},
        )


class SecretsNotFound(CustomAppException):
    def __init__(self, client_vat: str):
        super().__init__(
            message=f"No se encontraron secretos para el cliente '{client_vat}' en AWS Secrets Manager.",
            status_code=500,
            data={"client_vat": client_vat},
        )


class MissingSecretKey(CustomAppException):
    def __init__(self, client_vat: str, key: str):
        super().__init__(
            message=f"Falta la clave secreta '{key}' para el cliente '{client_vat}'.",
            status_code=500,
            data={"client_vat": client_vat, "missing_key": key},
        )


class AWSConnectionError(CustomAppException):
    def __init__(self, detail: str = "Error al conectar con AWS Secrets Manager"):
        super().__init__(message=detail, status_code=500)


class SecretsServiceNotLoaded(CustomAppException):
    def __init__(self):
        super().__init__(
            message="SecretsService.load() no fue invocado antes de acceder a los secretos.",
            status_code=422,
        )
