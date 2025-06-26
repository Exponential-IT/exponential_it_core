import json
import pytest
from datetime import timedelta
from unittest.mock import patch, AsyncMock, MagicMock

from exponential_core.secrets.manager import SecretManager


@pytest.fixture
def fake_secret_dict():
    return {"SecretString": '{"api_key": "1234", "token": "abcd"}'}


def mock_aioboto3_client(get_secret_response):
    """Devuelve un cliente simulado con los métodos esperados configurados"""
    mock_context_client = AsyncMock()
    mock_context_client.get_secret_value.return_value = get_secret_response
    mock_context_client.update_secret.return_value = {}
    mock_context_client.create_secret.return_value = {}
    mock_context_client.delete_secret.return_value = {}

    mock_client_instance = MagicMock()
    mock_client_instance.__aenter__.return_value = mock_context_client
    return mock_client_instance, mock_context_client


@pytest.mark.asyncio
async def test_get_secret_caches_result(fake_secret_dict):
    mock_client_instance, context_client = mock_aioboto3_client(fake_secret_dict)

    with patch("aioboto3.Session.client", return_value=mock_client_instance):
        manager = SecretManager("exponentialit/core", default_ttl_seconds=300)
        result_1 = await manager.get_secret()
        result_2 = await manager.get_secret()

        assert result_1 == {"api_key": "1234", "token": "abcd"}
        assert result_2 is result_1
        assert context_client.get_secret_value.call_count == 1


@pytest.mark.asyncio
async def test_get_secret_respects_ttl(fake_secret_dict):
    mock_client_instance, context_client = mock_aioboto3_client(fake_secret_dict)

    with patch("aioboto3.Session.client", return_value=mock_client_instance):
        manager = SecretManager("exponentialit/core", default_ttl_seconds=1)
        await manager.get_secret()
        manager._cache["exponentialit/core"]["timestamp"] -= timedelta(seconds=2)
        await manager.get_secret()

        assert context_client.get_secret_value.call_count == 2


@pytest.mark.asyncio
async def test_invalidate_removes_secret(fake_secret_dict):
    mock_client_instance, context_client = mock_aioboto3_client(fake_secret_dict)

    with patch("aioboto3.Session.client", return_value=mock_client_instance):
        manager = SecretManager("exponentialit/core")
        await manager.get_secret()
        assert "exponentialit/core" in manager._cache
        manager.invalidate()
        assert "exponentialit/core" not in manager._cache


@pytest.mark.asyncio
async def test_get_secret_by_key(fake_secret_dict):
    mock_client_instance, context_client = mock_aioboto3_client(fake_secret_dict)

    with patch("aioboto3.Session.client", return_value=mock_client_instance):
        manager = SecretManager("exponentialit/core")
        value = await manager.get_secret("api_key")
        assert value == "1234"


@pytest.mark.asyncio
async def test_set_secret_adds_new_key(fake_secret_dict):
    mock_client_instance, context_client = mock_aioboto3_client(fake_secret_dict)

    with patch("aioboto3.Session.client", return_value=mock_client_instance):
        manager = SecretManager("exponentialit/core")
        await manager.set_secret("new_key", "XYZ")

        update_args = context_client.update_secret.call_args[1]
        updated_data = json.loads(update_args["SecretString"])
        assert updated_data["new_key"] == "XYZ"
        assert updated_data["api_key"] == "1234"


@pytest.mark.asyncio
async def test_delete_key_removes_field(fake_secret_dict):
    mock_client_instance, context_client = mock_aioboto3_client(fake_secret_dict)

    with patch("aioboto3.Session.client", return_value=mock_client_instance):
        manager = SecretManager("exponentialit/core")
        await manager.delete_key("token")

        update_args = context_client.update_secret.call_args[1]
        updated_data = json.loads(update_args["SecretString"])
        assert "token" not in updated_data
        assert "api_key" in updated_data


@pytest.mark.asyncio
async def test_cache_expiration(fake_secret_dict):
    mock_client_instance, context_client = mock_aioboto3_client(fake_secret_dict)

    with patch("aioboto3.Session.client", return_value=mock_client_instance):
        manager = SecretManager("exponentialit/core", default_ttl_seconds=1)
        await manager.get_secret()
        manager._cache["exponentialit/core"]["timestamp"] -= timedelta(seconds=2)
        await manager.get_secret()

        assert context_client.get_secret_value.call_count == 2


@pytest.mark.asyncio
async def test_create_secret_calls_boto3_create():
    mock_client_instance, context_client = mock_aioboto3_client({})

    with patch("aioboto3.Session.client", return_value=mock_client_instance):
        manager = SecretManager("exponentialit/core")
        await manager.create_secret({"new_key": "value"})

        context_client.create_secret.assert_called_once()
        args = context_client.create_secret.call_args[1]
        assert args["Name"] == "exponentialit/core"
        assert json.loads(args["SecretString"]) == {"new_key": "value"}


@pytest.mark.asyncio
async def test_delete_secret_force(fake_secret_dict):
    mock_client_instance, context_client = mock_aioboto3_client(fake_secret_dict)

    with patch("aioboto3.Session.client", return_value=mock_client_instance):
        manager = SecretManager("exponentialit/core")
        await manager.get_secret()
        await manager.delete_secret(force_delete=True)

        context_client.delete_secret.assert_called_once_with(
            SecretId="exponentialit/core", ForceDeleteWithoutRecovery=True
        )
        assert "exponentialit/core" not in manager._cache
