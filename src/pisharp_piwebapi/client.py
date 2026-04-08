"""Main PI Web API client classes — sync and async."""

from __future__ import annotations

import ssl
import warnings
from typing import Any
from urllib.parse import urlparse

import httpx

from pisharp_piwebapi.analyses import AnalysesMixin, AsyncAnalysesMixin
from pisharp_piwebapi.analysistemplates import (
    AnalysisTemplatesMixin,
    AsyncAnalysisTemplatesMixin,
)
from pisharp_piwebapi.attributes import AsyncAttributesMixin, AttributesMixin
from pisharp_piwebapi.attributetemplates import (
    AsyncAttributeTemplatesMixin,
    AttributeTemplatesMixin,
)
from pisharp_piwebapi.auth import basic_auth, kerberos_auth, ntlm_auth
from pisharp_piwebapi.batch import AsyncBatchMixin, BatchMixin
from pisharp_piwebapi.calculation import AsyncCalculationMixin, CalculationMixin
from pisharp_piwebapi.categories import (
    AnalysisCategoriesMixin,
    AsyncAnalysisCategoriesMixin,
    AsyncAttributeCategoriesMixin,
    AsyncElementCategoriesMixin,
    AsyncTableCategoriesMixin,
    AttributeCategoriesMixin,
    ElementCategoriesMixin,
    TableCategoriesMixin,
)
from pisharp_piwebapi.elements import AsyncElementsMixin, ElementsMixin
from pisharp_piwebapi.elementtemplates import (
    AsyncElementTemplatesMixin,
    ElementTemplatesMixin,
)
from pisharp_piwebapi.enumerationsets import (
    AsyncEnumerationSetsMixin,
    EnumerationSetsMixin,
)
from pisharp_piwebapi.eventframes import AsyncEventFramesMixin, EventFramesMixin
from pisharp_piwebapi.exceptions import raise_for_response, raise_for_response_async
from pisharp_piwebapi.models import PISystemInfo
from pisharp_piwebapi.notificationrules import (
    AsyncNotificationRulesMixin,
    NotificationRulesMixin,
)
from pisharp_piwebapi.pagination import AsyncPaginationMixin, PaginationMixin
from pisharp_piwebapi.points import AsyncPointsMixin, PointsMixin
from pisharp_piwebapi.search import AsyncSearchMixin, SearchMixin
from pisharp_piwebapi.securityidentities import (
    AsyncSecurityIdentitiesMixin,
    SecurityIdentitiesMixin,
)
from pisharp_piwebapi.securitymappings import (
    AsyncSecurityMappingsMixin,
    SecurityMappingsMixin,
)
from pisharp_piwebapi.servers import (
    AssetServersMixin,
    AsyncAssetServersMixin,
    AsyncDatabasesMixin,
    AsyncDataServersMixin,
    DatabasesMixin,
    DataServersMixin,
)
from pisharp_piwebapi.streamsets import AsyncStreamSetsMixin, StreamSetsMixin
from pisharp_piwebapi.system import AsyncSystemMixin, SystemMixin
from pisharp_piwebapi.tables import AsyncTablesMixin, TablesMixin
from pisharp_piwebapi.unitclasses import AsyncUnitClassesMixin, UnitClassesMixin
from pisharp_piwebapi.values import AsyncStreamsMixin, StreamsMixin

_VALID_AUTH_METHODS = {"basic", "kerberos", "ntlm"}


def _build_event_hooks() -> dict[str, list[Any]]:
    """Build httpx sync event hooks for error handling."""

    def _raise_on_error(response: httpx.Response) -> None:
        response.read()  # Ensure body is loaded before inspecting it in the hook
        raise_for_response(response)

    return {"response": [_raise_on_error]}


def _build_async_event_hooks() -> dict[str, list[Any]]:
    """Build httpx async event hooks for error handling."""

    async def _raise_on_error_async(response: httpx.Response) -> None:
        await raise_for_response_async(response)

    return {"response": [_raise_on_error_async]}


class _AnalysisTemplatesAccessor(AnalysisTemplatesMixin):
    """Namespace for analysis template operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AnalysesAccessor(AnalysesMixin):
    """Namespace for AF analysis operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AttributeTemplatesAccessor(AttributeTemplatesMixin):
    """Namespace for attribute template operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AttributesAccessor(AttributesMixin):
    """Namespace for attribute operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _PointsAccessor(PointsMixin):
    """Namespace for point operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _StreamsAccessor(StreamsMixin):
    """Namespace for stream operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _StreamSetsAccessor(StreamSetsMixin):
    """Namespace for streamset (multi-stream) operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _CalculationAccessor(CalculationMixin):
    """Namespace for calculation operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _SearchAccessor(SearchMixin):
    """Namespace for indexed AF search on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _ElementsAccessor(ElementsMixin):
    """Namespace for AF element operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _EventFramesAccessor(EventFramesMixin):
    """Namespace for event frame operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _ElementTemplatesAccessor(ElementTemplatesMixin):
    """Namespace for element template operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _NotificationRulesAccessor(NotificationRulesMixin):
    """Namespace for notification rule operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _EnumerationSetsAccessor(EnumerationSetsMixin):
    """Namespace for enumeration set operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AssetServersAccessor(AssetServersMixin):
    """Namespace for asset server operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _DataServersAccessor(DataServersMixin):
    """Namespace for data server operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _DatabasesAccessor(DatabasesMixin):
    """Namespace for database operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _SystemAccessor(SystemMixin):
    """Namespace for system operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _TablesAccessor(TablesMixin):
    """Namespace for AF table operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _UnitClassesAccessor(UnitClassesMixin):
    """Namespace for unit class operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _ElementCategoriesAccessor(ElementCategoriesMixin):
    """Namespace for element category operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AnalysisCategoriesAccessor(AnalysisCategoriesMixin):
    """Namespace for analysis category operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AttributeCategoriesAccessor(AttributeCategoriesMixin):
    """Namespace for attribute category operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _TableCategoriesAccessor(TableCategoriesMixin):
    """Namespace for table category operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _SecurityIdentitiesAccessor(SecurityIdentitiesMixin):
    """Namespace for security identity operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _SecurityMappingsAccessor(SecurityMappingsMixin):
    """Namespace for security mapping operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AsyncAnalysisTemplatesAccessor(AsyncAnalysisTemplatesMixin):
    """Namespace for analysis template operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


class _AsyncAnalysesAccessor(AsyncAnalysesMixin):
    """Namespace for AF analysis operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


class _AsyncAttributeTemplatesAccessor(AsyncAttributeTemplatesMixin):
    """Namespace for attribute template operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


class _AsyncAttributesAccessor(AsyncAttributesMixin):
    """Namespace for attribute operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


class _AsyncPointsAccessor(AsyncPointsMixin):
    """Namespace for point operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


class _AsyncStreamsAccessor(AsyncStreamsMixin):
    """Namespace for stream operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


class _AsyncStreamSetsAccessor(AsyncStreamSetsMixin):
    """Namespace for streamset (multi-stream) operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


class _AsyncCalculationAccessor(AsyncCalculationMixin):
    """Namespace for calculation operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


class _AsyncSearchAccessor(AsyncSearchMixin):
    """Namespace for indexed AF search on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


class _AsyncElementsAccessor(AsyncElementsMixin):
    """Namespace for AF element operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


class _AsyncEventFramesAccessor(AsyncEventFramesMixin):
    """Namespace for event frame operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


class _AsyncElementTemplatesAccessor(AsyncElementTemplatesMixin):
    """Namespace for element template operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


class _AsyncNotificationRulesAccessor(AsyncNotificationRulesMixin):
    """Namespace for notification rule operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


class _AsyncEnumerationSetsAccessor(AsyncEnumerationSetsMixin):
    """Namespace for enumeration set operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


class _AsyncAssetServersAccessor(AsyncAssetServersMixin):
    """Namespace for asset server operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


class _AsyncDataServersAccessor(AsyncDataServersMixin):
    """Namespace for data server operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


class _AsyncDatabasesAccessor(AsyncDatabasesMixin):
    """Namespace for database operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


class _AsyncSystemAccessor(AsyncSystemMixin):
    """Namespace for system operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


class _AsyncTablesAccessor(AsyncTablesMixin):
    """Namespace for AF table operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


class _AsyncUnitClassesAccessor(AsyncUnitClassesMixin):
    """Namespace for unit class operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


class _AsyncElementCategoriesAccessor(AsyncElementCategoriesMixin):
    """Namespace for element category operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


class _AsyncAnalysisCategoriesAccessor(AsyncAnalysisCategoriesMixin):
    """Namespace for analysis category operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


class _AsyncAttributeCategoriesAccessor(AsyncAttributeCategoriesMixin):
    """Namespace for attribute category operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


class _AsyncTableCategoriesAccessor(AsyncTableCategoriesMixin):
    """Namespace for table category operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


class _AsyncSecurityIdentitiesAccessor(AsyncSecurityIdentitiesMixin):
    """Namespace for security identity operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


class _AsyncSecurityMappingsAccessor(AsyncSecurityMappingsMixin):
    """Namespace for security mapping operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


class PIWebAPIClient(BatchMixin, PaginationMixin):
    """Synchronous PI Web API client.

    Usage::

        client = PIWebAPIClient(
            base_url="https://your-server/piwebapi",
            username="user",
            password="pass",
        )
        point = client.points.get_by_path(r"\\\\SERVER\\sinusoid")
        value = client.streams.get_value(point.web_id)
    """

    def __init__(
        self,
        base_url: str,
        *,
        username: str | None = None,
        password: str | None = None,
        auth_method: str = "basic",
        verify_ssl: bool = True,
        cert: str | tuple[str, str] | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the PI Web API client.

        Args:
            base_url: PI Web API base URL (e.g. "https://server/piwebapi").
            username: Username for Basic or NTLM auth.
            password: Password for Basic or NTLM auth.
            auth_method: Authentication method — one of ``"basic"``,
                ``"kerberos"``, or ``"ntlm"``. Defaults to ``"basic"``.
            verify_ssl: Whether to verify SSL certificates.
            cert: Client certificate path or (cert, key) tuple.
            timeout: Request timeout in seconds.
        """
        if auth_method not in _VALID_AUTH_METHODS:
            raise ValueError(
                f"Unknown auth_method {auth_method!r}. "
                f"Choose from {sorted(_VALID_AUTH_METHODS)}."
            )
        if auth_method in ("basic", "ntlm") and not (username and password):
            raise ValueError(
                f"auth_method={auth_method!r} requires both "
                "username and password."
            )

        parsed_url = urlparse(base_url)
        if parsed_url.scheme not in ("http", "https"):
            raise ValueError(
                f"base_url must use http:// or https://. "
                f"Got scheme: {parsed_url.scheme!r}"
            )
        if parsed_url.scheme == "http":
            warnings.warn(
                "base_url uses http:// — credentials will be sent in "
                "cleartext. Use https:// for production.",
                UserWarning,
                stacklevel=2,
            )

        auth: httpx.Auth | None = None
        if auth_method == "kerberos":
            auth = kerberos_auth()
        elif auth_method == "ntlm":
            # username/password guaranteed non-None by validation above
            auth = ntlm_auth(username, password)  # type: ignore[arg-type]
        else:
            auth = basic_auth(username, password)  # type: ignore[arg-type]

        if not verify_ssl:
            warnings.warn(
                "verify_ssl=False disables TLS certificate validation. "
                "Consider passing a CA bundle path or ssl.SSLContext "
                "instead for production use.",
                UserWarning,
                stacklevel=2,
            )

        ssl_context: ssl.SSLContext | bool = verify_ssl
        if cert:
            ssl_context = ssl.create_default_context()
            if not verify_ssl:
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
            if isinstance(cert, tuple):
                ssl_context.load_cert_chain(cert[0], cert[1])
            else:
                ssl_context.load_cert_chain(cert)

        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            auth=auth,
            verify=ssl_context,
            timeout=timeout,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            event_hooks=_build_event_hooks(),
        )
        self.analyses = _AnalysesAccessor(self._client)
        self.analysistemplates = _AnalysisTemplatesAccessor(self._client)
        self.attributetemplates = _AttributeTemplatesAccessor(self._client)
        self.attributes = _AttributesAccessor(self._client)
        self.points = _PointsAccessor(self._client)
        self.streams = _StreamsAccessor(self._client)
        self.streamsets = _StreamSetsAccessor(self._client)
        self.calculation = _CalculationAccessor(self._client)
        self.search = _SearchAccessor(self._client)
        self.elements = _ElementsAccessor(self._client)
        self.eventframes = _EventFramesAccessor(self._client)
        self.elementtemplates = _ElementTemplatesAccessor(self._client)
        self.enumerationsets = _EnumerationSetsAccessor(self._client)
        self.notificationrules = _NotificationRulesAccessor(self._client)
        self.assetservers = _AssetServersAccessor(self._client)
        self.dataservers = _DataServersAccessor(self._client)
        self.databases = _DatabasesAccessor(self._client)
        self.system = _SystemAccessor(self._client)
        self.tables = _TablesAccessor(self._client)
        self.unitclasses = _UnitClassesAccessor(self._client)
        self.elementcategories = _ElementCategoriesAccessor(self._client)
        self.analysiscategories = _AnalysisCategoriesAccessor(self._client)
        self.attributecategories = _AttributeCategoriesAccessor(self._client)
        self.tablecategories = _TableCategoriesAccessor(self._client)
        self.securityidentities = _SecurityIdentitiesAccessor(self._client)
        self.securitymappings = _SecurityMappingsAccessor(self._client)

    def home(self) -> PISystemInfo:
        """Return system information from the PI Web API landing page.

        Calls ``GET /`` and returns product title, version, and links to
        all available controllers.  Useful as a connectivity check.

        Returns:
            A :class:`PISystemInfo` with product version and controller links.

        Raises:
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get("/")
        raise_for_response(resp)
        return PISystemInfo.model_validate(resp.json())

    def close(self) -> None:
        """Close the underlying HTTP connection."""
        self._client.close()

    def __enter__(self) -> PIWebAPIClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class AsyncPIWebAPIClient(AsyncBatchMixin, AsyncPaginationMixin):
    """Asynchronous PI Web API client.

    Usage::

        async with AsyncPIWebAPIClient(
            base_url="https://your-server/piwebapi",
            username="user",
            password="pass",
        ) as client:
            point = await client.points.get_by_path(r"\\\\SERVER\\sinusoid")
            value = await client.streams.get_value(point.web_id)
    """

    def __init__(
        self,
        base_url: str,
        *,
        username: str | None = None,
        password: str | None = None,
        auth_method: str = "basic",
        verify_ssl: bool = True,
        cert: str | tuple[str, str] | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the async PI Web API client.

        Args:
            base_url: PI Web API base URL (e.g. "https://server/piwebapi").
            username: Username for Basic or NTLM auth.
            password: Password for Basic or NTLM auth.
            auth_method: Authentication method — one of ``"basic"``,
                ``"kerberos"``, or ``"ntlm"``. Defaults to ``"basic"``.
            verify_ssl: Whether to verify SSL certificates.
            cert: Client certificate path or (cert, key) tuple.
            timeout: Request timeout in seconds.
        """
        if auth_method not in _VALID_AUTH_METHODS:
            raise ValueError(
                f"Unknown auth_method {auth_method!r}. "
                f"Choose from {sorted(_VALID_AUTH_METHODS)}."
            )
        if auth_method in ("basic", "ntlm") and not (username and password):
            raise ValueError(
                f"auth_method={auth_method!r} requires both "
                "username and password."
            )

        parsed_url = urlparse(base_url)
        if parsed_url.scheme not in ("http", "https"):
            raise ValueError(
                f"base_url must use http:// or https://. "
                f"Got scheme: {parsed_url.scheme!r}"
            )
        if parsed_url.scheme == "http":
            warnings.warn(
                "base_url uses http:// — credentials will be sent in "
                "cleartext. Use https:// for production.",
                UserWarning,
                stacklevel=2,
            )

        auth: httpx.Auth | None = None
        if auth_method == "kerberos":
            auth = kerberos_auth()
        elif auth_method == "ntlm":
            auth = ntlm_auth(username, password)  # type: ignore[arg-type]
        else:
            auth = basic_auth(username, password)  # type: ignore[arg-type]

        if not verify_ssl:
            warnings.warn(
                "verify_ssl=False disables TLS certificate validation. "
                "Consider passing a CA bundle path or ssl.SSLContext "
                "instead for production use.",
                UserWarning,
                stacklevel=2,
            )

        ssl_context: ssl.SSLContext | bool = verify_ssl
        if cert:
            ssl_context = ssl.create_default_context()
            if not verify_ssl:
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
            if isinstance(cert, tuple):
                ssl_context.load_cert_chain(cert[0], cert[1])
            else:
                ssl_context.load_cert_chain(cert)

        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            auth=auth,
            verify=ssl_context,
            timeout=timeout,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            event_hooks=_build_async_event_hooks(),
        )
        self.analyses = _AsyncAnalysesAccessor(self._client)
        self.analysistemplates = _AsyncAnalysisTemplatesAccessor(self._client)
        self.attributetemplates = _AsyncAttributeTemplatesAccessor(
            self._client
        )
        self.attributes = _AsyncAttributesAccessor(self._client)
        self.points = _AsyncPointsAccessor(self._client)
        self.streams = _AsyncStreamsAccessor(self._client)
        self.streamsets = _AsyncStreamSetsAccessor(self._client)
        self.calculation = _AsyncCalculationAccessor(self._client)
        self.search = _AsyncSearchAccessor(self._client)
        self.elements = _AsyncElementsAccessor(self._client)
        self.eventframes = _AsyncEventFramesAccessor(self._client)
        self.elementtemplates = _AsyncElementTemplatesAccessor(self._client)
        self.enumerationsets = _AsyncEnumerationSetsAccessor(self._client)
        self.notificationrules = _AsyncNotificationRulesAccessor(self._client)
        self.assetservers = _AsyncAssetServersAccessor(self._client)
        self.dataservers = _AsyncDataServersAccessor(self._client)
        self.databases = _AsyncDatabasesAccessor(self._client)
        self.system = _AsyncSystemAccessor(self._client)
        self.tables = _AsyncTablesAccessor(self._client)
        self.unitclasses = _AsyncUnitClassesAccessor(self._client)
        self.elementcategories = _AsyncElementCategoriesAccessor(self._client)
        self.analysiscategories = _AsyncAnalysisCategoriesAccessor(self._client)
        self.attributecategories = _AsyncAttributeCategoriesAccessor(
            self._client
        )
        self.tablecategories = _AsyncTableCategoriesAccessor(self._client)
        self.securityidentities = _AsyncSecurityIdentitiesAccessor(
            self._client
        )
        self.securitymappings = _AsyncSecurityMappingsAccessor(self._client)

    async def home(self) -> PISystemInfo:
        """Return system information from the PI Web API landing page.

        Calls ``GET /`` and returns product title, version, and links to
        all available controllers.  Useful as a connectivity check.

        Returns:
            A :class:`PISystemInfo` with product version and controller links.

        Raises:
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get("/")
        await raise_for_response_async(resp)
        return PISystemInfo.model_validate(resp.json())

    async def aclose(self) -> None:
        """Close the underlying HTTP connection."""
        await self._client.aclose()

    async def __aenter__(self) -> AsyncPIWebAPIClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()
