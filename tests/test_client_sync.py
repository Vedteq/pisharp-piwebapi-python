"""Integration tests for the synchronous PIWebAPIClient."""

from __future__ import annotations

import warnings

import httpx
import pytest
import respx
from conftest import (
    BASE_URL,
    BATCH_RESPONSE,
    CDIT158_POINT,
    CURRENT_VALUE,
    INTERPOLATED_VALUES,
    RECORDED_VALUES,
    SINUSOID_POINT,
)

from pisharp_piwebapi.exceptions import (
    AuthenticationError,
    NotFoundError,
    PIWebAPIError,
    RateLimitError,
    ServerError,
)
from pisharp_piwebapi.client import PIWebAPIClient
from pisharp_piwebapi.models import PIPoint, PISystemInfo, StreamValue, StreamValues

WEB_ID = SINUSOID_POINT["WebId"]


# ── Points ──────────────────────────────────────────────────────────


class TestPointsSync:
    def test_get_by_path(self, sync_client):
        client, mock = sync_client
        mock.get("/points", params={"path": "\\\\SERVER\\sinusoid"}).mock(
            return_value=httpx.Response(200, json=SINUSOID_POINT)
        )
        point = client.points.get_by_path(r"\\SERVER\sinusoid")
        assert isinstance(point, PIPoint)
        assert point.web_id == WEB_ID
        assert point.name == "sinusoid"

    def test_get_by_web_id(self, sync_client):
        client, mock = sync_client
        mock.get(f"/points/{WEB_ID}").mock(return_value=httpx.Response(200, json=SINUSOID_POINT))
        point = client.points.get_by_web_id(WEB_ID)
        assert point.name == "sinusoid"

    def test_search(self, sync_client):
        client, mock = sync_client
        ds_web_id = "DS001"
        mock.get(f"/dataservers/{ds_web_id}/points").mock(
            return_value=httpx.Response(200, json={"Items": [SINUSOID_POINT, CDIT158_POINT]})
        )
        results = client.points.search(ds_web_id, name_filter="sinu*")
        assert len(results) == 2
        assert results[0].name == "sinusoid"
        assert results[1].name == "cdit158"

    def test_search_flat_response(self, sync_client):
        """Some PI Web API versions return a flat array instead of {Items: [...]}."""
        client, mock = sync_client
        ds_web_id = "DS001"
        mock.get(f"/dataservers/{ds_web_id}/points").mock(
            return_value=httpx.Response(200, json=[SINUSOID_POINT])
        )
        results = client.points.search(ds_web_id, name_filter="sinu*")
        assert len(results) == 1


# ── Streams ─────────────────────────────────────────────────────────


class TestStreamsSync:
    def test_get_value(self, sync_client):
        client, mock = sync_client
        mock.get(f"/streams/{WEB_ID}/value").mock(
            return_value=httpx.Response(200, json=CURRENT_VALUE)
        )
        val = client.streams.get_value(WEB_ID)
        assert isinstance(val, StreamValue)
        assert val.value == 42.5
        assert val.good is True

    def test_get_recorded(self, sync_client):
        client, mock = sync_client
        mock.get(f"/streams/{WEB_ID}/recorded").mock(
            return_value=httpx.Response(200, json=RECORDED_VALUES)
        )
        vals = client.streams.get_recorded(WEB_ID)
        assert isinstance(vals, StreamValues)
        assert len(vals) == 3
        assert vals.items[0].value == 10.0

    def test_get_interpolated(self, sync_client):
        client, mock = sync_client
        mock.get(f"/streams/{WEB_ID}/interpolated").mock(
            return_value=httpx.Response(200, json=INTERPOLATED_VALUES)
        )
        vals = client.streams.get_interpolated(WEB_ID)
        assert len(vals) == 4

    def test_update_value(self, sync_client):
        client, mock = sync_client
        route = mock.post(f"/streams/{WEB_ID}/value").mock(return_value=httpx.Response(202))
        client.streams.update_value(WEB_ID, 99.9)
        assert route.called

    def test_update_value_with_timestamp(self, sync_client):
        client, mock = sync_client
        route = mock.post(f"/streams/{WEB_ID}/value").mock(return_value=httpx.Response(202))
        client.streams.update_value(WEB_ID, 99.9, timestamp="2024-06-15T12:00:00Z")
        assert route.called

    def test_update_values_bulk(self, sync_client):
        client, mock = sync_client
        route = mock.post(f"/streams/{WEB_ID}/recorded").mock(return_value=httpx.Response(202))
        client.streams.update_values(
            WEB_ID,
            [
                {"Value": 1.0, "Timestamp": "2024-06-15T11:00:00Z"},
                {"Value": 2.0, "Timestamp": "2024-06-15T11:05:00Z"},
            ],
        )
        assert route.called


# ── Batch ───────────────────────────────────────────────────────────


class TestBatchSync:
    def test_execute_batch(self, sync_client):
        client, mock = sync_client
        mock.post("/batch").mock(return_value=httpx.Response(200, json=BATCH_RESPONSE))
        result = client.execute_batch(
            {
                "1": {"Method": "GET", "Resource": f"/points/{WEB_ID}"},
                "2": {
                    "Method": "GET",
                    "Resource": f"/streams/{WEB_ID}/value",
                },
            }
        )
        assert "1" in result
        assert result["1"]["Status"] == 200


# ── Pagination ──────────────────────────────────────────────────────


class TestPaginationSync:
    def test_get_all_pages_single_page(self, sync_client):
        client, mock = sync_client
        mock.get("/points/search").mock(
            return_value=httpx.Response(
                200,
                json={
                    "Items": [SINUSOID_POINT, CDIT158_POINT],
                    "Links": {},
                },
            )
        )
        items = client.get_all_pages("/points/search", params={"q": "sinu*"})
        assert len(items) == 2

    def test_get_all_pages_multi_page(self):
        page2_url = f"{BASE_URL}/points/search?startIndex=1"

        with respx.mock:
            respx.get(f"{BASE_URL}/points/search", params={"q": "sinu*"}).mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "Items": [SINUSOID_POINT],
                        "Links": {"Next": page2_url},
                    },
                )
            )
            respx.get(page2_url).mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "Items": [CDIT158_POINT],
                        "Links": {},
                    },
                )
            )
            from pisharp_piwebapi.client import PIWebAPIClient

            with PIWebAPIClient(
                base_url=BASE_URL, username="admin", password="secret", verify_ssl=False
            ) as client:
                items = client.get_all_pages("/points/search", params={"q": "sinu*"})
                assert len(items) == 2


# ── Error handling ──────────────────────────────────────────────────


class TestErrorHandlingSync:
    def test_401_raises_auth_error(self, sync_client):
        client, mock = sync_client
        mock.get("/points").mock(return_value=httpx.Response(401, json={"Message": "Unauthorized"}))
        with pytest.raises(AuthenticationError) as exc_info:
            client.points.get_by_path("\\\\SERVER\\sinusoid")
        assert exc_info.value.status_code == 401

    def test_403_raises_auth_error(self, sync_client):
        client, mock = sync_client
        mock.get("/points").mock(return_value=httpx.Response(403, json={"Message": "Forbidden"}))
        with pytest.raises(AuthenticationError):
            client.points.get_by_path("\\\\SERVER\\sinusoid")

    def test_404_raises_not_found(self, sync_client):
        client, mock = sync_client
        mock.get(f"/points/{WEB_ID}").mock(
            return_value=httpx.Response(404, json={"Message": "Point not found"})
        )
        with pytest.raises(NotFoundError):
            client.points.get_by_web_id(WEB_ID)

    def test_429_raises_rate_limit(self, sync_client):
        client, mock = sync_client
        mock.get(f"/streams/{WEB_ID}/value").mock(
            return_value=httpx.Response(429, json={"Message": "Too many requests"})
        )
        with pytest.raises(RateLimitError):
            client.streams.get_value(WEB_ID)

    def test_500_raises_server_error(self, sync_client):
        client, mock = sync_client
        mock.get(f"/streams/{WEB_ID}/value").mock(
            return_value=httpx.Response(500, json={"Message": "Internal error"})
        )
        with pytest.raises(ServerError):
            client.streams.get_value(WEB_ID)

    def test_generic_error(self, sync_client):
        client, mock = sync_client
        mock.get(f"/streams/{WEB_ID}/value").mock(
            return_value=httpx.Response(418, text="I'm a teapot")
        )
        with pytest.raises(PIWebAPIError):
            client.streams.get_value(WEB_ID)


# ── Context manager ─────────────────────────────────────────────────


class TestContextManagerSync:
    def test_context_manager(self):
        with respx.mock(base_url=BASE_URL):
            from pisharp_piwebapi.client import PIWebAPIClient

            with PIWebAPIClient(
                base_url=BASE_URL,
                username="admin",
                password="secret",
                verify_ssl=False,
            ) as client:
                assert client is not None


# ── Home / System Info ───────────────────────────────────────────────


class TestHomeSync:
    def test_home(self, sync_client):
        client, mock = sync_client
        home_response = {
            "ProductTitle": "PI Web API",
            "ProductVersion": "2024 SP1",
            "Links": {
                "Self": f"{BASE_URL}/",
                "AssetServers": f"{BASE_URL}/assetservers",
                "DataServers": f"{BASE_URL}/dataservers",
            },
        }
        mock.get("/").mock(return_value=httpx.Response(200, json=home_response))
        info = client.home()
        assert isinstance(info, PISystemInfo)
        assert info.product_title == "PI Web API"
        assert info.product_version == "2024 SP1"
        assert "AssetServers" in info.links

    def test_home_auth_failure(self, sync_client):
        client, mock = sync_client
        mock.get("/").mock(
            return_value=httpx.Response(401, json={"Message": "Unauthorized"})
        )
        with pytest.raises(AuthenticationError):
            client.home()


# ── Security: HTTP scheme warning ────────────────────────────────────


class TestHttpSchemeWarningSync:
    def test_http_base_url_warns(self):
        with pytest.warns(UserWarning, match="http://.*cleartext"):
            with respx.mock(base_url="http://insecure.example.com/piwebapi"):
                PIWebAPIClient(
                    base_url="http://insecure.example.com/piwebapi",
                    username="admin",
                    password="secret",
                )

    def test_https_base_url_no_cleartext_warning(self):
        with respx.mock(base_url=BASE_URL):
            with warnings.catch_warnings():
                warnings.filterwarnings("error", message=".*cleartext.*")
                PIWebAPIClient(
                    base_url=BASE_URL,
                    username="admin",
                    password="secret",
                )


# ── Security: SSL context with cert + verify_ssl=False ──────────────


class TestSslContextSync:
    def test_cert_with_verify_ssl_false_disables_verification(self):
        """When cert is provided and verify_ssl=False, TLS verification is off."""
        import ssl
        from unittest.mock import patch

        # Patch load_cert_chain to avoid needing real cert files
        with patch.object(ssl.SSLContext, "load_cert_chain"):
            with respx.mock(base_url=BASE_URL):
                client = PIWebAPIClient(
                    base_url=BASE_URL,
                    username="admin",
                    password="secret",
                    verify_ssl=False,
                    cert=("/path/to/cert.pem", "/path/to/key.pem"),
                )
                ctx = client._client._transport._pool._ssl_context
                assert isinstance(ctx, ssl.SSLContext)
                assert ctx.check_hostname is False
                assert ctx.verify_mode == ssl.CERT_NONE
                client.close()


class TestBaseUrlValidationSync:
    def test_invalid_scheme_raises_value_error(self):
        """PIWebAPIClient rejects base_url with non-http(s) scheme."""
        with pytest.raises(ValueError, match="must use http:// or https://"):
            PIWebAPIClient(
                base_url="ftp://piserver/piwebapi",
                username="admin",
                password="secret",
            )

    def test_empty_scheme_raises_value_error(self):
        """PIWebAPIClient rejects base_url without a scheme."""
        with pytest.raises(ValueError, match="must use http:// or https://"):
            PIWebAPIClient(
                base_url="piserver/piwebapi",
                username="admin",
                password="secret",
            )
