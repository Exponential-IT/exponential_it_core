from exponential_core.exceptions.types import (
    InvoiceParsingError,
    OdooException,
    TaxIdNotFoundError,
    ValidTaxIdNotFoundError,
    SecretNotFoundError,
    SecretAlreadyExistsError,
    SecretsNotFound,
    MissingSecretKey,
)


def test_invoice_parsing_error():
    """Verifica que la excepción InvoiceParsingError tenga el mensaje y status correctos."""
    exc = InvoiceParsingError("Faltan datos")
    assert exc.message.startswith("Error al parsear factura")
    assert exc.status_code == 422


def test_odoo_exception():
    """Verifica que la excepción OdooException incluya datos y código 502."""
    exc = OdooException("Error Odoo", {"foo": "bar"})
    assert exc.status_code == 502
    assert "foo" in exc.data


def test_tax_id_not_found_error():
    """Verifica que TaxIdNotFoundError incluya invoice_number y candidatos."""
    exc = TaxIdNotFoundError("FAC123", [0.19, 0.05])
    assert exc.data["invoice_number"] == "FAC123"
    assert exc.data["candidates"] == [0.19, 0.05]


def test_valid_tax_id_not_found_error():
    """Verifica que ValidTaxIdNotFoundError almacene los candidatos."""
    exc = ValidTaxIdNotFoundError(["12345678X", "A12345678"])
    assert exc.message.startswith("No se encontraron identificadores fiscales")
    assert exc.data["candidates"] == ["12345678X", "A12345678"]
    assert exc.status_code == 422


def test_secret_not_found_error():
    """Verifica que SecretNotFoundError use el status 404 y detalle el nombre del secreto."""
    exc = SecretNotFoundError("exponentialit/core")
    assert "exponentialit/core" in exc.message
    assert exc.status_code == 404
    assert exc.data["secret_name"] == "exponentialit/core"


def test_secret_already_exists_error():
    """Verifica que SecretAlreadyExistsError use el status 409 y detalle el nombre del secreto."""
    exc = SecretAlreadyExistsError("exponentialit/core")
    assert "ya existe" in exc.message
    assert exc.status_code == 409
    assert exc.data["secret_name"] == "exponentialit/core"


def test_secrets_not_found():
    """Verifica que SecretsNotFound maneje correctamente el client_vat."""
    exc = SecretsNotFound("B12345678")
    assert "B12345678" in exc.message
    assert exc.status_code == 500
    assert exc.data["client_vat"] == "B12345678"


def test_missing_secret_key():
    """Verifica que MissingSecretKey detalle client_vat y la clave faltante."""
    exc = MissingSecretKey("B12345678", "processor")
    assert "processor" in exc.message
    assert exc.status_code == 500
    assert exc.data == {
        "client_vat": "B12345678",
        "missing_key": "processor",
    }
