"""Tests to cover gaps: GeneratedClient PUT/PATCH/DELETE, datetime timestamps, etc."""

from __future__ import annotations

from datetime import datetime, timezone

import httpx
import respx

from pisharp_piwebapi._generated.runtime import GeneratedClient

BASE_URL = "https://piserver.example.com/piwebapi"


class TestGeneratedClientPut:
    def test_put_with_json(self):
        with respx.mock:
            route = respx.put(f"{BASE_URL}/test/123").mock(
                return_value=httpx.Response(
                    200,
                    json={"updated": True},
                    headers={"content-type": "application/json"},
                )
            )
            client = GeneratedClient(
                httpx.Client(base_url=BASE_URL, headers={"Accept": "application/json"})
            )
            result = client.put("/test/123", json={"Name": "new"})
            assert result == {"updated": True}
            assert route.called
            client._client.close()

    def test_put_no_content(self):
        with respx.mock:
            respx.put(f"{BASE_URL}/test/123").mock(return_value=httpx.Response(204))
            client = GeneratedClient(
                httpx.Client(base_url=BASE_URL, headers={"Accept": "application/json"})
            )
            result = client.put("/test/123", json={"Name": "new"})
            assert result is None
            client._client.close()


class TestGeneratedClientPatch:
    def test_patch_with_json(self):
        with respx.mock:
            route = respx.patch(f"{BASE_URL}/test/123").mock(
                return_value=httpx.Response(
                    200,
                    json={"patched": True},
                    headers={"content-type": "application/json"},
                )
            )
            client = GeneratedClient(
                httpx.Client(base_url=BASE_URL, headers={"Accept": "application/json"})
            )
            result = client.patch("/test/123", json={"Description": "updated"})
            assert result == {"patched": True}
            assert route.called
            client._client.close()

    def test_patch_no_content(self):
        with respx.mock:
            respx.patch(f"{BASE_URL}/test/123").mock(return_value=httpx.Response(204))
            client = GeneratedClient(
                httpx.Client(base_url=BASE_URL, headers={"Accept": "application/json"})
            )
            result = client.patch("/test/123", json={"Description": "updated"})
            assert result is None
            client._client.close()


class TestGeneratedClientDeleteWithContent:
    def test_delete_with_json_response(self):
        with respx.mock:
            respx.delete(f"{BASE_URL}/test/123").mock(
                return_value=httpx.Response(
                    200,
                    json={"deleted": True},
                    headers={"content-type": "application/json"},
                )
            )
            client = GeneratedClient(
                httpx.Client(base_url=BASE_URL, headers={"Accept": "application/json"})
            )
            result = client.delete("/test/123")
            assert result == {"deleted": True}
            client._client.close()


class TestGeneratedClientWithParams:
    def test_get_with_params(self):
        with respx.mock:
            respx.get(f"{BASE_URL}/test", params={"q": "hello"}).mock(
                return_value=httpx.Response(200, json={"Items": []})
            )
            client = GeneratedClient(
                httpx.Client(base_url=BASE_URL, headers={"Accept": "application/json"})
            )
            result = client.get("/test", params={"q": "hello"})
            assert result == {"Items": []}
            client._client.close()

    def test_post_with_params(self):
        with respx.mock:
            route = respx.post(f"{BASE_URL}/test").mock(return_value=httpx.Response(202))
            client = GeneratedClient(
                httpx.Client(base_url=BASE_URL, headers={"Accept": "application/json"})
            )
            result = client.post("/test", json={"data": 1}, params={"mode": "async"})
            assert result is None
            assert route.called
            client._client.close()


class TestStreamUpdateWithDatetime:
    """Test that update_value works with a datetime object."""

    def test_update_value_with_datetime_object(self, sync_client):
        from conftest import SINUSOID_POINT

        client, mock = sync_client
        web_id = SINUSOID_POINT["WebId"]
        route = mock.post(f"/streams/{web_id}/value").mock(return_value=httpx.Response(202))
        ts = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        client.streams.update_value(web_id, 99.9, timestamp=ts)
        assert route.called


class TestAssetServerGetByName:
    """Test the get_by_name methods on servers."""

    def test_asset_server_get_by_name(self, sync_client):
        from conftest import ASSET_SERVER

        client, mock = sync_client
        mock.get("/assetservers", params={"name": "MyAFServer"}).mock(
            return_value=httpx.Response(200, json=ASSET_SERVER)
        )
        svr = client.assetservers.get_by_name("MyAFServer")
        assert svr.name == "MyAFServer"

    def test_data_server_get_by_name(self, sync_client):
        from conftest import DATA_SERVER

        client, mock = sync_client
        mock.get("/dataservers", params={"name": "MyPIServer"}).mock(
            return_value=httpx.Response(200, json=DATA_SERVER)
        )
        svr = client.dataservers.get_by_name("MyPIServer")
        assert svr.name == "MyPIServer"


class TestItemsFallbackEmptyResponse:
    """Regression: list-returning methods must return [] when response has no Items key.

    Previously the fallback was ``data.get("Items", data)``, which caused the dict
    itself to be iterated as a list, producing a ValidationError on each string key.
    """

    def test_points_search_empty_dict_response(self, sync_client):
        from conftest import DATA_SERVER

        client, mock = sync_client
        ds_wid = DATA_SERVER["WebId"]
        # Server returned neither an Items list nor a flat list — just {}.
        mock.get(
            f"/dataservers/{ds_wid}/points",
            params={"nameFilter": "*", "maxCount": 100},
        ).mock(return_value=httpx.Response(200, json={}))
        result = client.points.search(ds_wid)
        assert result == []

    def test_element_children_empty_dict_response(self, sync_client):
        from conftest import ELEMENT_PUMP

        client, mock = sync_client
        el_wid = ELEMENT_PUMP["WebId"]
        mock.get(
            f"/elements/{el_wid}/elements",
            params={"nameFilter": "*", "maxCount": 100},
        ).mock(return_value=httpx.Response(200, json={}))
        result = client.elements.get_child_elements(el_wid)
        assert result == []
