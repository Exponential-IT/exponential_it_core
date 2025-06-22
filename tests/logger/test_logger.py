import os
import logging
from fastapi import FastAPI
from fastapi.testclient import TestClient
from exponential_core.logger import configure_logging, get_logger

log_path = "test_logs/test.log"
log_dir = "test_logs"

app = FastAPI()
logger = get_logger()


@app.get("/log")
def log_something():
    logger.info("Mensaje de prueba desde /log")
    return {"logged": True}


client = TestClient(app)


def test_log_file_created_and_contains_message():
    """Verifica que el log se escriba correctamente en el archivo."""
    # Cerrar handlers si ya estaban activos
    for handler in logging.getLogger("app").handlers:
        if isinstance(handler, logging.FileHandler):
            handler.close()

    if os.path.exists(log_path):
        os.remove(log_path)

    configure_logging(
        log_file=log_path,
        log_to_console=False,
        force=True,
    )

    try:
        response = client.get("/log")
        assert response.status_code == 200

        assert os.path.exists(log_path)
        with open(log_path, encoding="utf-8") as f:
            content = f.read()
            assert "Mensaje de prueba desde /log" in content
    finally:
        # Limpieza
        for handler in logging.getLogger("app").handlers:
            if isinstance(handler, logging.FileHandler):
                handler.close()
        if os.path.exists(log_path):
            os.remove(log_path)
        if os.path.exists(log_dir) and not os.listdir(log_dir):
            os.rmdir(log_dir)
