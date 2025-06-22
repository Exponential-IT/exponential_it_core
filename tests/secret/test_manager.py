import json
import pytest
from datetime import timedelta
from unittest.mock import patch, MagicMock

from exponential_core.secrets.manager import SecretManager


# 🔁 Único fixture compartido
@pytest.fixture
def fake_secret_dict():
    """Secreto simulado tipo exponentialit/core con claves JSON."""
    return {"SecretString": '{"api_key": "1234", "token": "abcd"}'}


def test_get_secret_caches_result(fake_secret_dict):
    with patch("boto3.session.Session.client") as mock_client:
        mock_instance = MagicMock()
        mock_instance.get_secret_value.return_value = fake_secret_dict
        mock_client.return_value = mock_instance

        manager = SecretManager(
            base_secret_name="exponentialit/core", default_ttl_seconds=300
        )

        result_1 = manager.get_secret()
        result_2 = manager.get_secret()

        assert result_1 == {"api_key": "1234", "token": "abcd"}
        assert result_2 is result_1
        assert mock_instance.get_secret_value.call_count == 1


def test_get_secret_respects_ttl(fake_secret_dict):
    with patch("boto3.session.Session.client") as mock_client:
        mock_instance = MagicMock()
        mock_instance.get_secret_value.return_value = fake_secret_dict
        mock_client.return_value = mock_instance

        manager = SecretManager(
            base_secret_name="exponentialit/core", default_ttl_seconds=1
        )
        manager.get_secret()

        manager._cache["exponentialit/core"]["timestamp"] -= timedelta(seconds=2)
        manager.get_secret()

        assert mock_instance.get_secret_value.call_count == 2


def test_invalidate_removes_secret(fake_secret_dict):
    with patch("boto3.session.Session.client") as mock_client:
        mock_instance = MagicMock()
        mock_instance.get_secret_value.return_value = fake_secret_dict
        mock_client.return_value = mock_instance

        manager = SecretManager(base_secret_name="exponentialit/core")
        manager.get_secret()

        assert "exponentialit/core" in manager._cache
        manager.invalidate()
        assert "exponentialit/core" not in manager._cache


def test_get_secret_by_key(fake_secret_dict):
    with patch("boto3.session.Session.client") as mock_client:
        client = MagicMock()
        client.get_secret_value.return_value = fake_secret_dict
        mock_client.return_value = client

        manager = SecretManager(base_secret_name="exponentialit/core")
        value = manager.get_secret("api_key")

        assert value == "1234"


def test_set_secret_adds_new_key(fake_secret_dict):
    with patch("boto3.session.Session.client") as mock_client:
        client = MagicMock()
        client.get_secret_value.return_value = fake_secret_dict
        mock_client.return_value = client

        manager = SecretManager(base_secret_name="exponentialit/core")
        manager.set_secret("new_key", "XYZ")

        updated_data = json.loads(client.update_secret.call_args[1]["SecretString"])
        assert updated_data["new_key"] == "XYZ"
        assert updated_data["api_key"] == "1234"


def test_delete_key_removes_field(fake_secret_dict):
    with patch("boto3.session.Session.client") as mock_client:
        client = MagicMock()
        client.get_secret_value.return_value = fake_secret_dict
        mock_client.return_value = client

        manager = SecretManager(base_secret_name="exponentialit/core")
        manager.delete_key("token")

        updated_data = json.loads(client.update_secret.call_args[1]["SecretString"])
        assert "token" not in updated_data
        assert "api_key" in updated_data


def test_cache_expiration(fake_secret_dict):
    with patch("boto3.session.Session.client") as mock_client:
        client = MagicMock()
        client.get_secret_value.return_value = fake_secret_dict
        mock_client.return_value = client

        manager = SecretManager(
            base_secret_name="exponentialit/core", default_ttl_seconds=1
        )
        manager.get_secret()
        manager._cache["exponentialit/core"]["timestamp"] -= timedelta(seconds=2)
        manager.get_secret()

        assert client.get_secret_value.call_count == 2


def test_create_secret_calls_boto3_create():
    with patch("boto3.session.Session.client") as mock_client:
        client = MagicMock()
        mock_client.return_value = client

        manager = SecretManager(base_secret_name="exponentialit/core")
        manager.create_secret({"new_key": "value"})

        client.create_secret.assert_called_once()
        args = client.create_secret.call_args[1]
        assert args["Name"] == "exponentialit/core"
        assert json.loads(args["SecretString"]) == {"new_key": "value"}


def test_delete_secret_force(fake_secret_dict):
    with patch("boto3.session.Session.client") as mock_client:
        client = MagicMock()
        client.get_secret_value.return_value = fake_secret_dict  # ✅ mock real
        mock_client.return_value = client

        manager = SecretManager(base_secret_name="exponentialit/core")
        manager.get_secret()
        manager.delete_secret(force_delete=True)

        client.delete_secret.assert_called_once_with(
            SecretId="exponentialit/core", ForceDeleteWithoutRecovery=True
        )
        assert "exponentialit/core" not in manager._cache
