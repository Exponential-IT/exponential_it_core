# exponential_core\exceptions\setup.py
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError
import httpx

from exponential_core.exceptions.handler import (
    http_exception_handler,
    validation_exception_handler,
    pydantic_validation_handler,
    httpx_error_handler,
    custom_app_exception_handler,
    general_exception_handler,
)
from exponential_core.exceptions.base import CustomAppException


def setup_exception_handlers(app: FastAPI):
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_handler)
    app.add_exception_handler(httpx.RequestError, httpx_error_handler)
    app.add_exception_handler(CustomAppException, custom_app_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)    
