"""Point lookup and management operations for PI Web API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from pisharp_piwebapi.exceptions import raise_for_response, raise_for_response_async
from pisharp_piwebapi.models import PIDataServer, PIPoint

if TYPE_CHECKING:
    import httpx


class PointsMixin:
    """Methods for PI Point lookup. Mixed into the sync client class."""

    _client: httpx.Client

    def get_by_path(self, path: str) -> PIPoint:
        """Look up a PI Point by its full path.

        Args:
            path: Full PI point path, e.g. ``r"\\\\SERVER\\sinusoid"``.

        Returns:
            A :class:`PIPoint` populated from the API response.

        Raises:
            NotFoundError: If the point does not exist on the server.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get("/points", params={"path": path})
        raise_for_response(resp)
        return PIPoint.model_validate(resp.json())

    def get_by_web_id(self, web_id: str) -> PIPoint:
        """Look up a PI Point by its WebID.

        Args:
            web_id: The WebID of the point (e.g. ``"P0AbEDFoo123"``).

        Returns:
            A :class:`PIPoint` populated from the API response.

        Raises:
            NotFoundError: If no point with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get(f"/points/{quote(web_id, safe='')}")
        raise_for_response(resp)
        return PIPoint.model_validate(resp.json())

    def search(
        self,
        data_server_web_id: str,
        name_filter: str = "*",
        max_count: int = 100,
    ) -> list[PIPoint]:
        """Search for PI Points by name pattern on a specific Data Server.

        PI Web API does not expose a global ``/points/search`` endpoint.
        Points must be searched within a Data Server using
        ``GET /dataservers/{webId}/points?nameFilter=...``.

        Args:
            data_server_web_id: WebID of the PI Data Server (PI Server) to search.
                Obtain this via the ``/dataservers`` endpoint or
                ``client.points.get_data_server()``.
            name_filter: Name pattern supporting wildcards, e.g. ``"sinu*"``.
                Defaults to ``"*"`` (all points).
            max_count: Maximum number of results to return. Defaults to ``100``.

        Returns:
            List of :class:`PIPoint` objects matching the name filter.

        Raises:
            NotFoundError: If the Data Server WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get(
            f"/dataservers/{quote(data_server_web_id, safe='')}/points",
            params={"nameFilter": name_filter, "maxCount": max_count},
        )
        raise_for_response(resp)
        data = resp.json()
        items = data.get("Items", data) if isinstance(data, dict) else data
        return [PIPoint.model_validate(item) for item in items]

    def get_data_servers(self) -> list[PIDataServer]:
        """Return all PI Data Servers (PI Servers) registered with PI Web API.

        Returns:
            List of :class:`PIDataServer` objects.

        Raises:
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get("/dataservers")
        raise_for_response(resp)
        data = resp.json()
        items = data.get("Items", data) if isinstance(data, dict) else data
        return [PIDataServer.model_validate(item) for item in items]

    def get_data_server(self, web_id: str) -> PIDataServer:
        """Return a single PI Data Server by its WebID.

        Args:
            web_id: WebID of the PI Data Server.

        Returns:
            A :class:`PIDataServer` populated from the API response.

        Raises:
            NotFoundError: If no data server with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get(f"/dataservers/{quote(web_id, safe='')}")
        raise_for_response(resp)
        return PIDataServer.model_validate(resp.json())

    def create_point(
        self,
        data_server_web_id: str,
        name: str,
        *,
        point_type: str = "Float32",
        point_class: str = "classic",
        descriptor: str = "",
        engineering_units: str = "",
        future: bool = False,
        extra_fields: dict[str, Any] | None = None,
    ) -> None:
        """Create a new PI Point on a PI Data Server.

        Calls ``POST /dataservers/{webId}/points``.  PI Web API returns
        HTTP 201 with an empty body on success.

        Args:
            data_server_web_id: WebID of the PI Data Server that will own the
                new point.
            name: Tag name for the new PI Point (e.g. ``"MyTag"``).
            point_type: PI Point type string — one of ``"Float32"``
                (default), ``"Float64"``, ``"Int32"``, ``"Int64"``,
                ``"String"``, ``"Digital"``, ``"Timestamp"``, ``"Blob"``.
            point_class: PI Point class. Defaults to ``"classic"``.
            descriptor: Optional free-text description shown in PI clients.
            engineering_units: EU label (e.g. ``"degC"``).
            future: Whether the point accepts future-dated values.
                Defaults to ``False``.
            extra_fields: Additional key-value pairs merged into the request
                body as-is, for any server-specific attributes not covered by
                the standard parameters.

        Raises:
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: If the server returns any other non-2xx status
                (e.g. 409 if a point with that name already exists).
        """
        body: dict[str, Any] = {
            "Name": name,
            "PointType": point_type,
            "PointClass": point_class,
            "Descriptor": descriptor,
            "EngineeringUnits": engineering_units,
            "Future": future,
        }
        if extra_fields:
            body.update(extra_fields)

        resp = self._client.post(
            f"/dataservers/{quote(data_server_web_id, safe='')}/points",
            json=body,
        )
        raise_for_response(resp)

    def delete_point(self, web_id: str) -> None:
        """Delete a PI Point from the PI Data Server.

        Calls ``DELETE /points/{webId}``.  The operation is permanent; there
        is no soft-delete or recycle bin in PI Web API.

        Args:
            web_id: WebID of the PI Point to delete.

        Raises:
            NotFoundError: If no point with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.delete(f"/points/{quote(web_id, safe='')}")
        raise_for_response(resp)


class AsyncPointsMixin:
    """Async methods for PI Point lookup. Mixed into the async client class."""

    _client: httpx.AsyncClient

    async def get_by_path(self, path: str) -> PIPoint:
        """Look up a PI Point by its full path.

        Args:
            path: Full PI point path, e.g. ``r"\\\\SERVER\\sinusoid"``.

        Returns:
            A :class:`PIPoint` populated from the API response.

        Raises:
            NotFoundError: If the point does not exist on the server.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get("/points", params={"path": path})
        await raise_for_response_async(resp)
        return PIPoint.model_validate(resp.json())

    async def get_by_web_id(self, web_id: str) -> PIPoint:
        """Look up a PI Point by its WebID.

        Args:
            web_id: The WebID of the point (e.g. ``"P0AbEDFoo123"``).

        Returns:
            A :class:`PIPoint` populated from the API response.

        Raises:
            NotFoundError: If no point with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get(f"/points/{quote(web_id, safe='')}")
        await raise_for_response_async(resp)
        return PIPoint.model_validate(resp.json())

    async def search(
        self,
        data_server_web_id: str,
        name_filter: str = "*",
        max_count: int = 100,
    ) -> list[PIPoint]:
        """Search for PI Points by name pattern on a specific Data Server.

        PI Web API does not expose a global ``/points/search`` endpoint.
        Points must be searched within a Data Server using
        ``GET /dataservers/{webId}/points?nameFilter=...``.

        Args:
            data_server_web_id: WebID of the PI Data Server (PI Server) to search.
            name_filter: Name pattern supporting wildcards, e.g. ``"sinu*"``.
                Defaults to ``"*"`` (all points).
            max_count: Maximum number of results to return. Defaults to ``100``.

        Returns:
            List of :class:`PIPoint` objects matching the name filter.

        Raises:
            NotFoundError: If the Data Server WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get(
            f"/dataservers/{quote(data_server_web_id, safe='')}/points",
            params={"nameFilter": name_filter, "maxCount": max_count},
        )
        await raise_for_response_async(resp)
        data = resp.json()
        items = data.get("Items", data) if isinstance(data, dict) else data
        return [PIPoint.model_validate(item) for item in items]

    async def get_data_servers(self) -> list[PIDataServer]:
        """Return all PI Data Servers (PI Servers) registered with PI Web API.

        Returns:
            List of :class:`PIDataServer` objects.

        Raises:
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get("/dataservers")
        await raise_for_response_async(resp)
        data = resp.json()
        items = data.get("Items", data) if isinstance(data, dict) else data
        return [PIDataServer.model_validate(item) for item in items]

    async def get_data_server(self, web_id: str) -> PIDataServer:
        """Return a single PI Data Server by its WebID.

        Args:
            web_id: WebID of the PI Data Server.

        Returns:
            A :class:`PIDataServer` populated from the API response.

        Raises:
            NotFoundError: If no data server with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get(f"/dataservers/{quote(web_id, safe='')}")
        await raise_for_response_async(resp)
        return PIDataServer.model_validate(resp.json())

    async def create_point(
        self,
        data_server_web_id: str,
        name: str,
        *,
        point_type: str = "Float32",
        point_class: str = "classic",
        descriptor: str = "",
        engineering_units: str = "",
        future: bool = False,
        extra_fields: dict[str, Any] | None = None,
    ) -> None:
        """Create a new PI Point on a PI Data Server.

        Calls ``POST /dataservers/{webId}/points``.  PI Web API returns
        HTTP 201 with an empty body on success.

        Args:
            data_server_web_id: WebID of the PI Data Server that will own the
                new point.
            name: Tag name for the new PI Point (e.g. ``"MyTag"``).
            point_type: PI Point type string — one of ``"Float32"``
                (default), ``"Float64"``, ``"Int32"``, ``"Int64"``,
                ``"String"``, ``"Digital"``, ``"Timestamp"``, ``"Blob"``.
            point_class: PI Point class. Defaults to ``"classic"``.
            descriptor: Optional free-text description.
            engineering_units: EU label (e.g. ``"degC"``).
            future: Whether the point accepts future-dated values.
                Defaults to ``False``.
            extra_fields: Additional key-value pairs merged into the request
                body for server-specific attributes not covered by the
                standard parameters.

        Raises:
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: If the server returns any other non-2xx status.
        """
        body: dict[str, Any] = {
            "Name": name,
            "PointType": point_type,
            "PointClass": point_class,
            "Descriptor": descriptor,
            "EngineeringUnits": engineering_units,
            "Future": future,
        }
        if extra_fields:
            body.update(extra_fields)

        resp = await self._client.post(
            f"/dataservers/{quote(data_server_web_id, safe='')}/points",
            json=body,
        )
        await raise_for_response_async(resp)

    async def delete_point(self, web_id: str) -> None:
        """Delete a PI Point from the PI Data Server.

        Calls ``DELETE /points/{webId}``.  The operation is permanent.

        Args:
            web_id: WebID of the PI Point to delete.

        Raises:
            NotFoundError: If no point with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.delete(f"/points/{quote(web_id, safe='')}")
        await raise_for_response_async(resp)
