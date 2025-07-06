import functools
from botocore.exceptions import ClientError
from exponential_core.exceptions import (
    AWSConnectionError,
    SecretNotFoundError,
    SecretAlreadyExistsError,
)


def handle_boto3_errors_async(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            self_instance = args[0]
            secret_name = getattr(self_instance, "base_secret_name", "desconocido")

            if error_code == "ResourceNotFoundException":
                raise SecretNotFoundError(secret_name=secret_name) from e

            elif error_code == "ResourceExistsException":
                raise SecretAlreadyExistsError(secret_name=secret_name) from e

            raise AWSConnectionError(str(e)) from e

    return wrapper
