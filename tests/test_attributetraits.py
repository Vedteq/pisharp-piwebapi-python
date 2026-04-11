"""Tests for AttributeTraits resource — sync and async."""

from __future__ import annotations

import httpx
import pytest
import respx

from pisharp_piwebapi.attributetraits import (
    AsyncAttributeTraitsMixin,
    AttributeTraitsMixin,
)
from pisharp_piwebapi.exceptions import NotFoundError
from pisharp_piwebapi.models import PIAttributeTrait

BASE = "https://piserver/piwebapi"

LIMIT_HI_HI = {
    "Name": "LimitHiHi",
    "Abbreviation": "HH",
    "Description": "High-high alarm limit",
    "AllowChildAttributes": False,
    "AllowDuplicates": False,
    "IsDataReferenceInherited": True,
    "Links": {"Self": f"{BASE}/attributetraits/LimitHiHi"},
}

LIMIT_LO_LO = {
    "Name": "LimitLoLo",
    "Abbreviation": "LL",
    "Description": "Low-low alarm limit",
    "AllowChildAttributes": False,
    "AllowDuplicates": False,
    "IsDataReferenceInherited": True,
    "Links": {},
}


class _SyncAT(AttributeTraitsMixin):
    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AsyncAT(AsyncAttributeTraitsMixin):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


# ========================== SYNC TESTS ==========================


class TestAttributeTraitsSync:
    """Sync happy-path tests."""

    @respx.mock
    def test_get_by_name_happy_path(self) -> None:
        respx.get(f"{BASE}/attributetraits/LimitHiHi").mock(
            return_value=httpx.Response(200, json=LIMIT_HI_HI)
        )
        client = httpx.Client(base_url=BASE)
        result = _SyncAT(client).get_by_name("LimitHiHi")
        assert isinstance(result, PIAttributeTrait)
        assert result.name == "LimitHiHi"
        assert result.abbreviation == "HH"
        assert result.is_data_reference_inherited is True
        client.close()

    @respx.mock
    def test_get_by_name_selected_fields(self) -> None:
        route = respx.get(
            f"{BASE}/attributetraits/LimitHiHi",
            params={"selectedFields": "Name;Abbreviation"},
        ).mock(return_value=httpx.Response(200, json=LIMIT_HI_HI))
        client = httpx.Client(base_url=BASE)
        _SyncAT(client).get_by_name(
            "LimitHiHi", selected_fields="Name;Abbreviation"
        )
        assert route.called
        client.close()

    @respx.mock
    def test_get_multiple_happy_path(self) -> None:
        respx.get(
            f"{BASE}/attributetraits/multiple",
            params=[("name", "LimitHiHi"), ("name", "LimitLoLo")],
        ).mock(
            return_value=httpx.Response(
                200, json={"Items": [LIMIT_HI_HI, LIMIT_LO_LO]}
            )
        )
        client = httpx.Client(base_url=BASE)
        result = _SyncAT(client).get_multiple(["LimitHiHi", "LimitLoLo"])
        assert len(result) == 2
        assert {t.name for t in result} == {"LimitHiHi", "LimitLoLo"}
        client.close()

    @respx.mock
    def test_get_multiple_flat_list_response(self) -> None:
        respx.get(
            f"{BASE}/attributetraits/multiple",
            params=[("name", "LimitHiHi")],
        ).mock(return_value=httpx.Response(200, json=[LIMIT_HI_HI]))
        client = httpx.Client(base_url=BASE)
        result = _SyncAT(client).get_multiple(["LimitHiHi"])
        assert len(result) == 1
        client.close()

    @respx.mock
    def test_get_categories_happy_path(self) -> None:
        respx.get(f"{BASE}/attributetraits/categories").mock(
            return_value=httpx.Response(
                200, json={"Items": ["Limit", "Forecast", "Target"]}
            )
        )
        client = httpx.Client(base_url=BASE)
        result = _SyncAT(client).get_categories()
        assert result == ["Limit", "Forecast", "Target"]
        client.close()


class TestAttributeTraitsSyncErrors:
    """Sync error-path and validation tests."""

    @respx.mock
    def test_get_by_name_not_found(self) -> None:
        respx.get(f"{BASE}/attributetraits/Bogus").mock(
            return_value=httpx.Response(
                404, json={"Errors": ["Trait not found"]}
            )
        )
        client = httpx.Client(base_url=BASE)
        with pytest.raises(NotFoundError):
            _SyncAT(client).get_by_name("Bogus")
        client.close()

    def test_get_by_name_empty_raises(self) -> None:
        client = httpx.Client(base_url=BASE)
        with pytest.raises(ValueError):
            _SyncAT(client).get_by_name("")
        client.close()

    def test_get_multiple_empty_raises(self) -> None:
        client = httpx.Client(base_url=BASE)
        with pytest.raises(ValueError):
            _SyncAT(client).get_multiple([])
        client.close()


# ========================== ASYNC TESTS ==========================


class TestAttributeTraitsAsync:
    """Async happy-path tests."""

    @respx.mock
    async def test_get_by_name_happy_path(self) -> None:
        respx.get(f"{BASE}/attributetraits/LimitHiHi").mock(
            return_value=httpx.Response(200, json=LIMIT_HI_HI)
        )
        client = httpx.AsyncClient(base_url=BASE)
        result = await _AsyncAT(client).get_by_name("LimitHiHi")
        assert result.name == "LimitHiHi"
        await client.aclose()

    @respx.mock
    async def test_get_multiple_happy_path(self) -> None:
        respx.get(
            f"{BASE}/attributetraits/multiple",
            params=[("name", "LimitHiHi"), ("name", "LimitLoLo")],
        ).mock(
            return_value=httpx.Response(
                200, json={"Items": [LIMIT_HI_HI, LIMIT_LO_LO]}
            )
        )
        client = httpx.AsyncClient(base_url=BASE)
        result = await _AsyncAT(client).get_multiple(
            ["LimitHiHi", "LimitLoLo"]
        )
        assert len(result) == 2
        await client.aclose()

    @respx.mock
    async def test_get_categories_happy_path(self) -> None:
        respx.get(f"{BASE}/attributetraits/categories").mock(
            return_value=httpx.Response(
                200, json={"Items": ["Limit", "Forecast"]}
            )
        )
        client = httpx.AsyncClient(base_url=BASE)
        result = await _AsyncAT(client).get_categories()
        assert result == ["Limit", "Forecast"]
        await client.aclose()


class TestAttributeTraitsAsyncErrors:
    """Async error-path and validation tests."""

    @respx.mock
    async def test_get_by_name_not_found(self) -> None:
        respx.get(f"{BASE}/attributetraits/Bogus").mock(
            return_value=httpx.Response(
                404, json={"Errors": ["Trait not found"]}
            )
        )
        client = httpx.AsyncClient(base_url=BASE)
        with pytest.raises(NotFoundError):
            await _AsyncAT(client).get_by_name("Bogus")
        await client.aclose()

    async def test_get_by_name_empty_raises(self) -> None:
        client = httpx.AsyncClient(base_url=BASE)
        with pytest.raises(ValueError):
            await _AsyncAT(client).get_by_name("")
        await client.aclose()

    async def test_get_multiple_empty_raises(self) -> None:
        client = httpx.AsyncClient(base_url=BASE)
        with pytest.raises(ValueError):
            await _AsyncAT(client).get_multiple([])
        await client.aclose()
