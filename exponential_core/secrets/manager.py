import boto3
import json
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any

from exponential_core.utils.aws_error_handler import handle_boto3_errors


class SecretManager:
    def __init__(
        self,
        base_secret_name: str,
        region_name: str = "eu-west-3",
        default_ttl_seconds: int = 300,
    ):
        session = boto3.session.Session()
        self._client = session.client("secretsmanager", region_name=region_name)
        self._cache: Dict[str, Dict] = {}
        self.base_secret_name = base_secret_name
        self.default_ttl_seconds = default_ttl_seconds

    @handle_boto3_errors
    def _get_secret_dict(self, ttl_seconds: Optional[int] = None) -> dict:
        now = datetime.now(timezone.utc)
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds

        if self.base_secret_name in self._cache:
            entry = self._cache[self.base_secret_name]
            if (now - entry["timestamp"]).total_seconds() < ttl:
                return entry["value"]
            else:
                self._cache.pop(self.base_secret_name)

        response = self._client.get_secret_value(SecretId=self.base_secret_name)

        if "SecretString" in response:
            secret_dict = json.loads(response["SecretString"])
        elif "SecretBinary" in response:
            secret_dict = json.loads(response["SecretBinary"].decode("utf-8"))
        else:
            raise ValueError(
                f"[SecretsManager] El secreto '{self.base_secret_name}' no contiene datos válidos."
            )

        self._cache[self.base_secret_name] = {"value": secret_dict, "timestamp": now}
        return secret_dict

    def get_secret(
        self, key: Optional[str] = None, ttl_seconds: Optional[int] = None
    ) -> Any:
        secret_data = self._get_secret_dict(ttl_seconds)
        return secret_data if key is None else secret_data.get(key)

    def invalidate(self):
        self._cache.pop(self.base_secret_name, None)

    @handle_boto3_errors
    def create_secret(self, initial_data: dict):
        if not isinstance(initial_data, dict):
            raise ValueError("El dato inicial debe ser un diccionario.")

        self._client.create_secret(
            Name=self.base_secret_name,
            SecretString=json.dumps(initial_data),
        )

        self._cache[self.base_secret_name] = {
            "value": initial_data,
            "timestamp": datetime.now(timezone.utc),
        }

    @handle_boto3_errors
    def _save_secret_dict(self, data: dict):
        self._client.update_secret(
            SecretId=self.base_secret_name,
            SecretString=json.dumps(data),
        )
        self._cache[self.base_secret_name] = {
            "value": data,
            "timestamp": datetime.now(timezone.utc),
        }

    def set_secret(self, key: str, value: Any):
        data = self._get_secret_dict()
        data[key] = value
        self._save_secret_dict(data)

    def delete_key(self, key: str):
        data = self._get_secret_dict()
        if key in data:
            del data[key]
            self._save_secret_dict(data)

    @handle_boto3_errors
    def delete_secret(self, force_delete: bool = False, recovery_days: int = 7):
        self.invalidate()
        if force_delete:
            self._client.delete_secret(
                SecretId=self.base_secret_name, ForceDeleteWithoutRecovery=True
            )
        else:
            self._client.delete_secret(
                SecretId=self.base_secret_name, RecoveryWindowInDays=recovery_days
            )

    @handle_boto3_errors
    def list_secrets(self) -> List[str]:
        secrets = []
        paginator = self._client.get_paginator("list_secrets")
        for page in paginator.paginate():
            for secret in page.get("SecretList", []):
                secrets.append(secret["Name"])
        return secrets
