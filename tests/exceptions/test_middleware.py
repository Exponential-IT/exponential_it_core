from fastapi import FastAPI
from starlette.testclient import TestClient
from exponential_core.exceptions.middleware import GlobalExceptionMiddleware
from exponential_core.exceptions.types import OdooException

app = FastAPI()
app.add_middleware(GlobalExceptionMiddleware)


@app.get("/odoo")
def raise_odoo():
    raise OdooException("Error de Odoo", {"env": "dev"})


client = TestClient(app)


def test_odoo_exception_middleware():
    """Verifica que OdooException sea capturada por el middleware global y devuelva status 502."""
    res = client.get("/odoo")
    assert res.status_code == 502
    body = res.json()
    assert body["error_type"] == "OdooException"
    assert body["data"]["env"] == "dev"
