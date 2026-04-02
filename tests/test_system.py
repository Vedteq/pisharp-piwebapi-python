"""Tests for the System controller (status, userinfo, versions)."""

from __future__ import annotations

import httpx
import pytest
import respx

from pisharp_piwebapi.models import PISystemStatus, PIUserInfo, PIVersions

BASE = "https://pi.example.com/piwebapi"

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sync_client():
    from pisharp_piwebapi.client import PIWebAPIClient
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        client = PIWebAPIClient(
            BASE, username="user", password="pass", verify_ssl=False,
        )
    yield client
    client.close()


@pytest.fixture()
def async_client():
    from pisharp_piwebapi.client import AsyncPIWebAPIClient
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        client = AsyncPIWebAPIClient(
            BASE, username="user", password="pass", verify_ssl=False,
        )
    return client


# ---------------------------------------------------------------------------
# Sync — get_status
# ---------------------------------------------------------------------------

class TestSystemStatusSync:
    @respx.mock
    def test_get_status(self, sync_client):
        respx.get(f"{BASE}/system/status").mock(
            return_value=httpx.Response(200, json={
                "UpTimeInSeconds": 12345.6,
                "State": "Running",
                "CacheInstances": 2,
            })
        )
        result = sync_client.system.get_status()
        assert isinstance(result, PISystemStatus)
        assert result.up_time_in_seconds == 12345.6
        assert result.state == "Running"
        assert result.cache_instances == 2

    @respx.mock
    def test_get_status_401(self, sync_client):
        from pisharp_piwebapi.exceptions import AuthenticationError
        respx.get(f"{BASE}/system/status").mock(
            return_value=httpx.Response(401, json={"Message": "Unauthorized"})
        )
        with pytest.raises(AuthenticationError):
            sync_client.system.get_status()


# ---------------------------------------------------------------------------
# Sync — get_user_info
# ---------------------------------------------------------------------------

class TestUserInfoSync:
    @respx.mock
    def test_get_user_info(self, sync_client):
        respx.get(f"{BASE}/system/userinfo").mock(
            return_value=httpx.Response(200, json={
                "IdentityType": "WindowsIdentity",
                "Name": "DOMAIN\\user",
                "IsAuthenticated": True,
                "ImpersonationLevel": "Impersonation",
            })
        )
        result = sync_client.system.get_user_info()
        assert isinstance(result, PIUserInfo)
        assert result.name == "DOMAIN\\user"
        assert result.is_authenticated is True
        assert result.impersonation_level == "Impersonation"


# ---------------------------------------------------------------------------
# Sync — get_versions
# ---------------------------------------------------------------------------

class TestVersionsSync:
    @respx.mock
    def test_get_versions(self, sync_client):
        respx.get(f"{BASE}/system/versions").mock(
            return_value=httpx.Response(200, json={
                "PIWebAPI": "2023 SP1",
                "PIDataArchive": "3.4.440",
                "PINotificationsService": "2.5.0",
            })
        )
        result = sync_client.system.get_versions()
        assert isinstance(result, PIVersions)
        assert result.versions["PIWebAPI"] == "2023 SP1"
        assert result.versions["PIDataArchive"] == "3.4.440"
        assert "PINotificationsService" in result.versions


# ---------------------------------------------------------------------------
# Async — get_status
# ---------------------------------------------------------------------------

class TestSystemStatusAsync:
    @respx.mock
    async def test_get_status(self, async_client):
        respx.get(f"{BASE}/system/status").mock(
            return_value=httpx.Response(200, json={
                "UpTimeInSeconds": 99.0,
                "State": "Starting",
                "CacheInstances": 0,
            })
        )
        async with async_client:
            result = await async_client.system.get_status()
        assert isinstance(result, PISystemStatus)
        assert result.state == "Starting"

    @respx.mock
    async def test_get_status_500(self, async_client):
        from pisharp_piwebapi.exceptions import ServerError
        respx.get(f"{BASE}/system/status").mock(
            return_value=httpx.Response(500, json={"Message": "Internal error"})
        )
        async with async_client:
            with pytest.raises(ServerError):
                await async_client.system.get_status()


# ---------------------------------------------------------------------------
# Async — get_user_info
# ---------------------------------------------------------------------------

class TestUserInfoAsync:
    @respx.mock
    async def test_get_user_info(self, async_client):
        respx.get(f"{BASE}/system/userinfo").mock(
            return_value=httpx.Response(200, json={
                "IdentityType": "WindowsIdentity",
                "Name": "DOMAIN\\admin",
                "IsAuthenticated": True,
                "ImpersonationLevel": "Delegation",
            })
        )
        async with async_client:
            result = await async_client.system.get_user_info()
        assert result.name == "DOMAIN\\admin"


# ---------------------------------------------------------------------------
# Async — get_versions
# ---------------------------------------------------------------------------

class TestVersionsAsync:
    @respx.mock
    async def test_get_versions(self, async_client):
        respx.get(f"{BASE}/system/versions").mock(
            return_value=httpx.Response(200, json={
                "PIWebAPI": "2024",
            })
        )
        async with async_client:
            result = await async_client.system.get_versions()
        assert result.versions["PIWebAPI"] == "2024"
