from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from exponential_core.exceptions import setup
from exponential_core.exceptions.types import InvoiceParsingError
from exponential_core.exceptions.middleware import GlobalExceptionMiddleware

app = FastAPI()
setup.setup_exception_handlers(app)
app.add_middleware(
    GlobalExceptionMiddleware
)  # 🔧 Importante para capturar Exception genérico


@app.get("/http-error")
def raise_http_error():
    raise HTTPException(status_code=502, detail="No se pudo conectar con el servicio")


@app.get("/custom-error")
def raise_custom_error():
    raise InvoiceParsingError("No se pudo extraer el NIT")


@app.get("/unhandled")
def raise_unhandled():
    raise ValueError("Algo inesperado")


client = TestClient(app)


def test_http_exception_handler():
    """
    Verifica que una HTTPException se maneje y devuelva el mismo status_code con formato uniforme.
    """
    response = client.get("/http-error")
    assert response.status_code == 502
    body = response.json()
    assert body["error_type"] == "HttpException"
    assert body["detail"] == "No se pudo conectar con el servicio"
    assert body["status_code"] == 502
    assert "timestamp" in body


def test_custom_app_exception_handler():
    """
    Verifica que una excepción personalizada como InvoiceParsingError
    """
    response = client.get("/custom-error")
    assert response.status_code == 422
    body = response.json()
    assert body["error_type"] == "InvoiceParsingError"
    assert "NIT" in body["detail"]
    assert body["status_code"] == 422
    assert "timestamp" in body


def test_unhandled_exception_handler():
    """
    Verifica que excepciones no previstas (como ValueError) se manejen con mensaje genérico.
    """
    response = client.get("/unhandled")
    assert response.status_code == 500
    body = response.json()
    assert body["error_type"] == "UnhandledException"
    assert body["detail"] == "Internal server error"
    assert body["status_code"] == 500
    assert "timestamp" in body
