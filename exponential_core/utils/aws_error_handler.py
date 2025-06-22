# exponential_core\utils\aws_error_handler.py
from functools import wraps
from botocore.exceptions import ClientError

from exponential_core.exceptions.types import (
    SecretNotFoundError,
    SecretAlreadyExistsError,
    CustomAppException,
)


def handle_boto3_errors(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except ClientError as e:
            code = e.response["Error"]["Code"]
            name = getattr(self, "base_secret_name", "desconocido")

            if code == "ResourceNotFoundException":
                raise SecretNotFoundError(secret_name=name) from e
            elif code == "ResourceExistsException":
                raise SecretAlreadyExistsError(secret_name=name) from e

            # Cualquier otro error de boto3
            raise CustomAppException(
                message=f"Error inesperado de AWS Secrets Manager ({code})",
                status_code=500,
                data={"secret_name": name, "raw_error": str(e)},
            ) from e

    return wrapper
