import functools
from botocore.exceptions import ClientError
from exponential_core.exceptions import AWSConnectionError


def handle_boto3_errors_async(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ClientError as e:
            raise AWSConnectionError(str(e)) from e
    return wrapper
