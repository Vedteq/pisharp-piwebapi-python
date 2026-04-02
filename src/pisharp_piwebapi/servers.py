"""Asset Server, Data Server, and Database operations for PI Web API."""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote

from pisharp_piwebapi.exceptions import (
    raise_for_response,
    raise_for_response_async,
    validate_web_id,
)
from pisharp_piwebapi.models import PIAssetServer, PIDatabase, PIDataServer, PIElement

if TYPE_CHECKING:
    import httpx


class AssetServersMixin:
    """Methods for PI AF Asset Server operations. Mixed into client classes."""

    _client: httpx.Client

    def list_all(self) -> list[PIAssetServer]:
        """Return all AF Servers known to PI Web API."""
        resp = self._client.get("/assetservers")
        raise_for_response(resp)
        data = resp.json()
        items = data.get("Items", []) if isinstance(data, dict) else data
        return [PIAssetServer.model_validate(item) for item in items]

    def get_by_name(self, name: str) -> PIAssetServer:
        """Look up an AF Server by name."""
        resp = self._client.get("/assetservers", params={"name": name})
        raise_for_response(resp)
        return PIAssetServer.model_validate(resp.json())

    def get_by_web_id(self, web_id: str) -> PIAssetServer:
        """Look up an AF Server by WebID."""
        validate_web_id(web_id)
        resp = self._client.get(f"/assetservers/{quote(web_id, safe='')}")
        raise_for_response(resp)
        return PIAssetServer.model_validate(resp.json())

    def get_databases(self, web_id: str) -> list[PIDatabase]:
        """List AF Databases on an AF Server."""
        validate_web_id(web_id)
        resp = self._client.get(f"/assetservers/{quote(web_id, safe='')}/assetdatabases")
        raise_for_response(resp)
        data = resp.json()
        items = data.get("Items", []) if isinstance(data, dict) else data
        return [PIDatabase.model_validate(item) for item in items]


class DataServersMixin:
    """Methods for PI Data Archive Server operations. Mixed into client classes."""

    _client: httpx.Client

    def list_all(self) -> list[PIDataServer]:
        """Return all PI Data Archive servers known to PI Web API."""
        resp = self._client.get("/dataservers")
        raise_for_response(resp)
        data = resp.json()
        items = data.get("Items", []) if isinstance(data, dict) else data
        return [PIDataServer.model_validate(item) for item in items]

    def get_by_name(self, name: str) -> PIDataServer:
        """Look up a Data Server by name."""
        resp = self._client.get("/dataservers", params={"name": name})
        raise_for_response(resp)
        return PIDataServer.model_validate(resp.json())

    def get_by_web_id(self, web_id: str) -> PIDataServer:
        """Look up a Data Server by WebID."""
        validate_web_id(web_id)
        resp = self._client.get(f"/dataservers/{quote(web_id, safe='')}")
        raise_for_response(resp)
        return PIDataServer.model_validate(resp.json())


class DatabasesMixin:
    """Methods for PI AF Database operations. Mixed into client classes."""

    _client: httpx.Client

    def get_by_path(self, path: str) -> PIDatabase:
        """Look up an AF Database by its full path."""
        resp = self._client.get("/assetdatabases", params={"path": path})
        raise_for_response(resp)
        return PIDatabase.model_validate(resp.json())

    def get_by_web_id(self, web_id: str) -> PIDatabase:
        """Look up an AF Database by WebID."""
        validate_web_id(web_id)
        resp = self._client.get(f"/assetdatabases/{quote(web_id, safe='')}")
        raise_for_response(resp)
        return PIDatabase.model_validate(resp.json())

    def get_elements(self, web_id: str, max_count: int = 1000) -> list[PIElement]:
        """Get top-level elements in an AF Database."""
        validate_web_id(web_id)
        resp = self._client.get(
            f"/assetdatabases/{quote(web_id, safe='')}/elements",
            params={"maxCount": max_count},
        )
        raise_for_response(resp)
        data = resp.json()
        items = data.get("Items", []) if isinstance(data, dict) else data
        return [PIElement.model_validate(item) for item in items]


class AsyncAssetServersMixin:
    """Async methods for PI AF Asset Server operations."""

    _client: httpx.AsyncClient

    async def list_all(self) -> list[PIAssetServer]:
        """Return all AF Servers known to PI Web API (async)."""
        resp = await self._client.get("/assetservers")
        await raise_for_response_async(resp)
        data = resp.json()
        items = data.get("Items", []) if isinstance(data, dict) else data
        return [PIAssetServer.model_validate(item) for item in items]

    async def get_by_name(self, name: str) -> PIAssetServer:
        """Look up an AF Server by name (async)."""
        resp = await self._client.get("/assetservers", params={"name": name})
        await raise_for_response_async(resp)
        return PIAssetServer.model_validate(resp.json())

    async def get_by_web_id(self, web_id: str) -> PIAssetServer:
        """Look up an AF Server by WebID (async)."""
        validate_web_id(web_id)
        resp = await self._client.get(f"/assetservers/{quote(web_id, safe='')}")
        await raise_for_response_async(resp)
        return PIAssetServer.model_validate(resp.json())

    async def get_databases(self, web_id: str) -> list[PIDatabase]:
        """List AF Databases on an AF Server (async)."""
        validate_web_id(web_id)
        resp = await self._client.get(
            f"/assetservers/{quote(web_id, safe='')}/assetdatabases"
        )
        await raise_for_response_async(resp)
        data = resp.json()
        items = data.get("Items", []) if isinstance(data, dict) else data
        return [PIDatabase.model_validate(item) for item in items]


class AsyncDataServersMixin:
    """Async methods for PI Data Archive Server operations."""

    _client: httpx.AsyncClient

    async def list_all(self) -> list[PIDataServer]:
        """Return all PI Data Archive servers (async)."""
        resp = await self._client.get("/dataservers")
        await raise_for_response_async(resp)
        data = resp.json()
        items = data.get("Items", []) if isinstance(data, dict) else data
        return [PIDataServer.model_validate(item) for item in items]

    async def get_by_name(self, name: str) -> PIDataServer:
        """Look up a Data Server by name (async)."""
        resp = await self._client.get("/dataservers", params={"name": name})
        await raise_for_response_async(resp)
        return PIDataServer.model_validate(resp.json())

    async def get_by_web_id(self, web_id: str) -> PIDataServer:
        """Look up a Data Server by WebID (async)."""
        validate_web_id(web_id)
        resp = await self._client.get(f"/dataservers/{quote(web_id, safe='')}")
        await raise_for_response_async(resp)
        return PIDataServer.model_validate(resp.json())


class AsyncDatabasesMixin:
    """Async methods for PI AF Database operations."""

    _client: httpx.AsyncClient

    async def get_by_path(self, path: str) -> PIDatabase:
        """Look up an AF Database by its full path (async)."""
        resp = await self._client.get("/assetdatabases", params={"path": path})
        await raise_for_response_async(resp)
        return PIDatabase.model_validate(resp.json())

    async def get_by_web_id(self, web_id: str) -> PIDatabase:
        """Look up an AF Database by WebID (async)."""
        validate_web_id(web_id)
        resp = await self._client.get(f"/assetdatabases/{quote(web_id, safe='')}")
        await raise_for_response_async(resp)
        return PIDatabase.model_validate(resp.json())

    async def get_elements(self, web_id: str, max_count: int = 1000) -> list[PIElement]:
        """Get top-level elements in an AF Database (async)."""
        validate_web_id(web_id)
        resp = await self._client.get(
            f"/assetdatabases/{quote(web_id, safe='')}/elements",
            params={"maxCount": max_count},
        )
        await raise_for_response_async(resp)
        data = resp.json()
        items = data.get("Items", []) if isinstance(data, dict) else data
        return [PIElement.model_validate(item) for item in items]
