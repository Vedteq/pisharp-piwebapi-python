"""Stream read/write operations for PI Web API."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from pisharp_piwebapi.models import StreamValue, StreamValues

if TYPE_CHECKING:
    import httpx


class StreamsMixin:
    """Methods for reading and writing PI stream values. Mixed into client classes."""

    _client: httpx.Client

    def get_value(self, web_id: str) -> StreamValue:
        """Read the current value of a stream.

        Args:
            web_id: WebID of the PI Point or attribute.

        Returns:
            The current StreamValue.
        """
        resp = self._client.get(f"/streams/{quote(web_id, safe='')}/value")
        resp.raise_for_status()
        return StreamValue.model_validate(resp.json())

    def get_recorded(
        self,
        web_id: str,
        start_time: str = "-1h",
        end_time: str = "*",
        max_count: int = 1000,
    ) -> StreamValues:
        """Read recorded values from a stream.

        Args:
            web_id: WebID of the PI Point or attribute.
            start_time: Start time (PI time string, e.g. "-1h", "2024-01-01T00:00:00Z").
            end_time: End time (PI time string, e.g. "*" for now).
            max_count: Maximum number of values to return.

        Returns:
            StreamValues containing the recorded values.
        """
        resp = self._client.get(
            f"/streams/{quote(web_id, safe='')}/recorded",
            params={
                "startTime": start_time,
                "endTime": end_time,
                "maxCount": max_count,
            },
        )
        resp.raise_for_status()
        return StreamValues.model_validate(resp.json())

    def get_interpolated(
        self,
        web_id: str,
        start_time: str = "-1h",
        end_time: str = "*",
        interval: str = "10m",
    ) -> StreamValues:
        """Read interpolated values from a stream.

        Args:
            web_id: WebID of the PI Point or attribute.
            start_time: Start time.
            end_time: End time.
            interval: Interpolation interval (e.g. "10m", "1h").

        Returns:
            StreamValues containing the interpolated values.
        """
        resp = self._client.get(
            f"/streams/{quote(web_id, safe='')}/interpolated",
            params={
                "startTime": start_time,
                "endTime": end_time,
                "interval": interval,
            },
        )
        resp.raise_for_status()
        return StreamValues.model_validate(resp.json())

    def update_value(
        self,
        web_id: str,
        value: Any,
        timestamp: str | datetime | None = None,
    ) -> None:
        """Write a single value to a stream.

        Args:
            web_id: WebID of the PI Point or attribute.
            value: The value to write.
            timestamp: Optional timestamp (defaults to server time if omitted).
        """
        body: dict[str, Any] = {"Value": value}
        if timestamp is not None:
            body["Timestamp"] = (
                timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp
            )
        resp = self._client.post(
            f"/streams/{quote(web_id, safe='')}/value",
            json=body,
        )
        resp.raise_for_status()

    def update_values(
        self,
        web_id: str,
        values: list[dict[str, Any]],
    ) -> None:
        """Write multiple values to a stream.

        Args:
            web_id: WebID of the PI Point or attribute.
            values: List of dicts with "Value" and optionally "Timestamp" keys.
        """
        resp = self._client.post(
            f"/streams/{quote(web_id, safe='')}/recorded",
            json=values,
        )
        resp.raise_for_status()


class AsyncStreamsMixin:
    """Async methods for reading and writing PI stream values."""

    _client: httpx.AsyncClient

    async def get_value(self, web_id: str) -> StreamValue:
        """Read the current value of a stream (async)."""
        resp = await self._client.get(f"/streams/{quote(web_id, safe='')}/value")
        resp.raise_for_status()
        return StreamValue.model_validate(resp.json())

    async def get_recorded(
        self,
        web_id: str,
        start_time: str = "-1h",
        end_time: str = "*",
        max_count: int = 1000,
    ) -> StreamValues:
        """Read recorded values from a stream (async)."""
        resp = await self._client.get(
            f"/streams/{quote(web_id, safe='')}/recorded",
            params={
                "startTime": start_time,
                "endTime": end_time,
                "maxCount": max_count,
            },
        )
        resp.raise_for_status()
        return StreamValues.model_validate(resp.json())

    async def get_interpolated(
        self,
        web_id: str,
        start_time: str = "-1h",
        end_time: str = "*",
        interval: str = "10m",
    ) -> StreamValues:
        """Read interpolated values from a stream (async)."""
        resp = await self._client.get(
            f"/streams/{quote(web_id, safe='')}/interpolated",
            params={
                "startTime": start_time,
                "endTime": end_time,
                "interval": interval,
            },
        )
        resp.raise_for_status()
        return StreamValues.model_validate(resp.json())

    async def update_value(
        self,
        web_id: str,
        value: Any,
        timestamp: str | datetime | None = None,
    ) -> None:
        """Write a single value to a stream (async)."""
        body: dict[str, Any] = {"Value": value}
        if timestamp is not None:
            body["Timestamp"] = (
                timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp
            )
        resp = await self._client.post(
            f"/streams/{quote(web_id, safe='')}/value",
            json=body,
        )
        resp.raise_for_status()

    async def update_values(
        self,
        web_id: str,
        values: list[dict[str, Any]],
    ) -> None:
        """Write multiple values to a stream (async)."""
        resp = await self._client.post(
            f"/streams/{quote(web_id, safe='')}/recorded",
            json=values,
        )
        resp.raise_for_status()
