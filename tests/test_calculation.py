"""Tests for the Calculation resource (server-side expression evaluation)."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from pisharp_piwebapi.calculation import AsyncCalculationMixin, CalculationMixin
from pisharp_piwebapi.exceptions import PIWebAPIError
from pisharp_piwebapi.models import StreamSummary, StreamValues

BASE = "https://pi.example.com/piwebapi"
EXPR = "'sinusoid' * 2 + 10"
WEB_ID = "P0AbEDFsinusoid"


class _SyncCalc(CalculationMixin):
    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AsyncCalc(AsyncCalculationMixin):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


# --- Recorded ---

RECORDED_RESPONSE = {
    "Items": [
        {
            "Timestamp": "2024-06-01T12:00:00Z",
            "Value": 42.0,
            "Good": True,
            "Questionable": False,
            "Substituted": False,
            "Annotated": False,
            "UnitsAbbreviation": "",
        },
        {
            "Timestamp": "2024-06-01T12:05:00Z",
            "Value": 44.0,
            "Good": True,
            "Questionable": False,
            "Substituted": False,
            "Annotated": False,
            "UnitsAbbreviation": "",
        },
    ],
}


@respx.mock
def test_get_recorded_happy_path() -> None:
    """get_recorded returns StreamValues from /calculation/recorded."""
    route = respx.get(f"{BASE}/calculation/recorded").mock(
        return_value=httpx.Response(200, json=RECORDED_RESPONSE)
    )
    with httpx.Client(base_url=BASE) as client:
        calc = _SyncCalc(client)
        result = calc.get_recorded(EXPR)

    assert isinstance(result, StreamValues)
    assert len(result.items) == 2
    assert result.items[0].value == 42.0
    req = route.calls.last.request
    assert "expression" in str(req.url)


@respx.mock
def test_get_recorded_forwards_params() -> None:
    """get_recorded forwards start_time, end_time, and web_id."""
    route = respx.get(f"{BASE}/calculation/recorded").mock(
        return_value=httpx.Response(200, json=RECORDED_RESPONSE)
    )
    with httpx.Client(base_url=BASE) as client:
        calc = _SyncCalc(client)
        calc.get_recorded(
            EXPR,
            start_time="-8h",
            end_time="*-1h",
            web_id=WEB_ID,
        )

    url = str(route.calls.last.request.url)
    assert "startTime=-8h" in url
    assert "endTime=*-1h" in url or "endTime=%2A-1h" in url
    assert f"webId={WEB_ID}" in url


@respx.mock
def test_get_recorded_omits_web_id_when_none() -> None:
    """web_id is not included in query when None."""
    route = respx.get(f"{BASE}/calculation/recorded").mock(
        return_value=httpx.Response(200, json=RECORDED_RESPONSE)
    )
    with httpx.Client(base_url=BASE) as client:
        calc = _SyncCalc(client)
        calc.get_recorded(EXPR)

    url = str(route.calls.last.request.url)
    assert "webId" not in url


@respx.mock
def test_get_recorded_error_raises() -> None:
    """get_recorded raises PIWebAPIError on bad expression."""
    respx.get(f"{BASE}/calculation/recorded").mock(
        return_value=httpx.Response(
            400, json={"Message": "Invalid expression"}
        )
    )
    with httpx.Client(base_url=BASE) as client:
        calc = _SyncCalc(client)
        with pytest.raises(PIWebAPIError, match="Invalid expression"):
            calc.get_recorded("bad expression!!!")


# --- Summary ---

SUMMARY_RESPONSE = {
    "Items": [
        {
            "Type": "Average",
            "Value": {
                "Timestamp": "2024-06-01T12:00:00Z",
                "Value": 43.5,
                "Good": True,
                "Questionable": False,
                "Substituted": False,
                "Annotated": False,
                "UnitsAbbreviation": "",
            },
        },
    ],
}


@respx.mock
def test_get_summary_happy_path() -> None:
    """get_summary returns StreamSummary from /calculation/summary."""
    route = respx.get(f"{BASE}/calculation/summary").mock(
        return_value=httpx.Response(200, json=SUMMARY_RESPONSE)
    )
    with httpx.Client(base_url=BASE) as client:
        calc = _SyncCalc(client)
        result = calc.get_summary(EXPR)

    assert isinstance(result, StreamSummary)
    assert len(result.items) == 1
    assert result.items[0].type == "Average"


@respx.mock
def test_get_summary_forwards_params() -> None:
    """get_summary forwards all query parameters."""
    route = respx.get(f"{BASE}/calculation/summary").mock(
        return_value=httpx.Response(200, json=SUMMARY_RESPONSE)
    )
    with httpx.Client(base_url=BASE) as client:
        calc = _SyncCalc(client)
        calc.get_summary(
            EXPR,
            start_time="-4h",
            end_time="*",
            summary_type="Average",
            calculation_basis="EventWeighted",
            web_id=WEB_ID,
        )

    url = str(route.calls.last.request.url)
    assert "summaryType=Average" in url
    assert "calculationBasis=EventWeighted" in url
    assert f"webId={WEB_ID}" in url


# --- Intervals ---


@respx.mock
def test_get_at_intervals_happy_path() -> None:
    """get_at_intervals returns StreamValues from /calculation/intervals."""
    route = respx.get(f"{BASE}/calculation/intervals").mock(
        return_value=httpx.Response(200, json=RECORDED_RESPONSE)
    )
    with httpx.Client(base_url=BASE) as client:
        calc = _SyncCalc(client)
        result = calc.get_at_intervals(EXPR, sample_interval="5m")

    assert isinstance(result, StreamValues)
    assert len(result.items) == 2
    url = str(route.calls.last.request.url)
    assert "sampleInterval=5m" in url


@respx.mock
def test_get_at_intervals_with_web_id() -> None:
    """get_at_intervals forwards web_id."""
    respx.get(f"{BASE}/calculation/intervals").mock(
        return_value=httpx.Response(200, json=RECORDED_RESPONSE)
    )
    with httpx.Client(base_url=BASE) as client:
        calc = _SyncCalc(client)
        calc.get_at_intervals(EXPR, web_id=WEB_ID)


# --- Times ---


@respx.mock
def test_get_at_times_happy_path() -> None:
    """get_at_times returns values at specified timestamps."""
    respx.get(f"{BASE}/calculation/times").mock(
        return_value=httpx.Response(200, json=RECORDED_RESPONSE)
    )
    with httpx.Client(base_url=BASE) as client:
        calc = _SyncCalc(client)
        result = calc.get_at_times(EXPR, times=["*-1h", "*-30m", "*"])

    assert isinstance(result, StreamValues)


@respx.mock
def test_get_at_times_forwards_multiple_time_params() -> None:
    """get_at_times sends repeated time= query parameters."""
    route = respx.get(f"{BASE}/calculation/times").mock(
        return_value=httpx.Response(200, json=RECORDED_RESPONSE)
    )
    with httpx.Client(base_url=BASE) as client:
        calc = _SyncCalc(client)
        calc.get_at_times(EXPR, times=["*-1h", "*-30m"])

    url = str(route.calls.last.request.url)
    # Should have two time= params
    assert url.count("time=") >= 2


@respx.mock
def test_get_at_times_with_web_id() -> None:
    """get_at_times forwards web_id."""
    route = respx.get(f"{BASE}/calculation/times").mock(
        return_value=httpx.Response(200, json=RECORDED_RESPONSE)
    )
    with httpx.Client(base_url=BASE) as client:
        calc = _SyncCalc(client)
        calc.get_at_times(EXPR, times=["*"], web_id=WEB_ID)

    url = str(route.calls.last.request.url)
    assert f"webId={WEB_ID}" in url


# ===== Async tests =====


@respx.mock
async def test_async_get_recorded_happy_path() -> None:
    """Async get_recorded returns StreamValues."""
    respx.get(f"{BASE}/calculation/recorded").mock(
        return_value=httpx.Response(200, json=RECORDED_RESPONSE)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        calc = _AsyncCalc(client)
        result = await calc.get_recorded(EXPR)

    assert isinstance(result, StreamValues)
    assert len(result.items) == 2


@respx.mock
async def test_async_get_summary_happy_path() -> None:
    """Async get_summary returns StreamSummary."""
    respx.get(f"{BASE}/calculation/summary").mock(
        return_value=httpx.Response(200, json=SUMMARY_RESPONSE)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        calc = _AsyncCalc(client)
        result = await calc.get_summary(EXPR)

    assert isinstance(result, StreamSummary)
    assert len(result.items) == 1


@respx.mock
async def test_async_get_at_intervals_happy_path() -> None:
    """Async get_at_intervals returns StreamValues."""
    respx.get(f"{BASE}/calculation/intervals").mock(
        return_value=httpx.Response(200, json=RECORDED_RESPONSE)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        calc = _AsyncCalc(client)
        result = await calc.get_at_intervals(EXPR)

    assert isinstance(result, StreamValues)


@respx.mock
async def test_async_get_at_times_happy_path() -> None:
    """Async get_at_times returns StreamValues."""
    respx.get(f"{BASE}/calculation/times").mock(
        return_value=httpx.Response(200, json=RECORDED_RESPONSE)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        calc = _AsyncCalc(client)
        result = await calc.get_at_times(EXPR, times=["*-1h", "*"])

    assert isinstance(result, StreamValues)


@respx.mock
async def test_async_get_recorded_error_raises() -> None:
    """Async get_recorded raises on error."""
    respx.get(f"{BASE}/calculation/recorded").mock(
        return_value=httpx.Response(
            400, json={"Message": "Bad expression"}
        )
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        calc = _AsyncCalc(client)
        with pytest.raises(PIWebAPIError, match="Bad expression"):
            await calc.get_recorded("bad!!!")


@respx.mock
async def test_async_get_summary_forwards_params() -> None:
    """Async get_summary forwards all parameters."""
    route = respx.get(f"{BASE}/calculation/summary").mock(
        return_value=httpx.Response(200, json=SUMMARY_RESPONSE)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        calc = _AsyncCalc(client)
        await calc.get_summary(
            EXPR,
            summary_type="Minimum",
            web_id=WEB_ID,
        )

    url = str(route.calls.last.request.url)
    assert "summaryType=Minimum" in url
    assert f"webId={WEB_ID}" in url
