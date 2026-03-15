"""Pydantic v2 response models for PI Web API."""

from __future__ import annotations

from datetime import datetime  # noqa: TCH003
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator

from pydantic import BaseModel, Field


class PIPoint(BaseModel):
    """Represents a PI Point (tag)."""

    web_id: str = Field(alias="WebId")
    id: int = Field(alias="Id", default=0)
    name: str = Field(alias="Name")
    path: str = Field(alias="Path", default="")
    descriptor: str = Field(alias="Descriptor", default="")
    point_class: str = Field(alias="PointClass", default="classic")
    point_type: str = Field(alias="PointType", default="Float32")
    engineering_units: str = Field(alias="EngineeringUnits", default="")
    future: bool = Field(alias="Future", default=False)
    links: dict[str, str] = Field(alias="Links", default_factory=dict)

    model_config = {"populate_by_name": True}


class PIAttribute(BaseModel):
    """Represents a PI AF Attribute."""

    web_id: str = Field(alias="WebId")
    name: str = Field(alias="Name")
    path: str = Field(alias="Path", default="")
    description: str = Field(alias="Description", default="")
    type: str = Field(alias="Type", default="")
    value: Any = Field(alias="Value", default=None)
    links: dict[str, str] = Field(alias="Links", default_factory=dict)

    model_config = {"populate_by_name": True}


class StreamValue(BaseModel):
    """A single timestamped value from a PI stream."""

    timestamp: datetime = Field(alias="Timestamp")
    value: Any = Field(alias="Value")
    units_abbreviation: str = Field(alias="UnitsAbbreviation", default="")
    good: bool = Field(alias="Good", default=True)
    questionable: bool = Field(alias="Questionable", default=False)
    substituted: bool = Field(alias="Substituted", default=False)
    annotated: bool = Field(alias="Annotated", default=False)

    model_config = {"populate_by_name": True}


class StreamValues(BaseModel):
    """A collection of timestamped values from a PI stream."""

    web_id: str = Field(alias="WebId", default="")
    name: str = Field(alias="Name", default="")
    path: str = Field(alias="Path", default="")
    items: list[StreamValue] = Field(alias="Items", default_factory=list)
    units_abbreviation: str = Field(alias="UnitsAbbreviation", default="")
    links: dict[str, str] = Field(alias="Links", default_factory=dict)

    model_config = {"populate_by_name": True}

    def __iter__(self) -> Iterator[StreamValue]:  # type: ignore[override]
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)


class PIElement(BaseModel):
    """Represents a PI AF Element."""

    web_id: str = Field(alias="WebId")
    name: str = Field(alias="Name")
    path: str = Field(alias="Path", default="")
    description: str = Field(alias="Description", default="")
    template_name: str = Field(alias="TemplateName", default="")
    has_children: bool = Field(alias="HasChildren", default=False)
    links: dict[str, str] = Field(alias="Links", default_factory=dict)

    model_config = {"populate_by_name": True}


class PIDatabase(BaseModel):
    """Represents a PI AF Database."""

    web_id: str = Field(alias="WebId")
    name: str = Field(alias="Name")
    path: str = Field(alias="Path", default="")
    description: str = Field(alias="Description", default="")
    links: dict[str, str] = Field(alias="Links", default_factory=dict)

    model_config = {"populate_by_name": True}


class PIDataServer(BaseModel):
    """Represents a PI Data Server (PI Server)."""

    web_id: str = Field(alias="WebId")
    name: str = Field(alias="Name")
    path: str = Field(alias="Path", default="")
    is_connected: bool = Field(alias="IsConnected", default=False)
    server_version: str = Field(alias="ServerVersion", default="")
    links: dict[str, str] = Field(alias="Links", default_factory=dict)

    model_config = {"populate_by_name": True}


class PIAssetServer(BaseModel):
    """Represents a PI Asset Server (AF Server).

    Asset servers host AF databases.  Use :meth:`ElementsMixin.get_asset_servers`
    to enumerate them, then pass :attr:`web_id` to
    :meth:`ElementsMixin.get_databases` to list the AF databases on that server.
    """

    web_id: str = Field(alias="WebId")
    name: str = Field(alias="Name")
    path: str = Field(alias="Path", default="")
    is_connected: bool = Field(alias="IsConnected", default=False)
    server_version: str = Field(alias="ServerVersion", default="")
    links: dict[str, str] = Field(alias="Links", default_factory=dict)

    model_config = {"populate_by_name": True}


class StreamSummaryValue(BaseModel):
    """A single summary statistic within a stream summary response.

    PI Web API wraps each summary value in an object containing the
    calculated value and the time range over which it was computed.
    """

    type: str = Field(alias="Type", default="")
    value: StreamValue | None = Field(alias="Value", default=None)

    model_config = {"populate_by_name": True}


class StreamSummary(BaseModel):
    """Summary statistics for a single PI stream over a time range.

    Returned by ``GET /streams/{webId}/summary``.  The ``items`` list
    contains one :class:`StreamSummaryValue` per requested statistic type
    (e.g. ``"Minimum"``, ``"Maximum"``, ``"Mean"``, ``"StdDev"``,
    ``"Count"``, ``"PercentGood"``).
    """

    web_id: str = Field(alias="WebId", default="")
    name: str = Field(alias="Name", default="")
    path: str = Field(alias="Path", default="")
    items: list[StreamSummaryValue] = Field(alias="Items", default_factory=list)
    links: dict[str, str] = Field(alias="Links", default_factory=dict)

    model_config = {"populate_by_name": True}

    def as_dict(self) -> dict[str, Any]:
        """Return summary statistics as a plain ``{type: value}`` mapping.

        Returns:
            Dict mapping summary type name (e.g. ``"Minimum"``) to the raw
            value from the nested :class:`StreamValue`, or ``None`` if the
            statistic value was not returned by the server.
        """
        return {
            item.type: (item.value.value if item.value is not None else None)
            for item in self.items
        }


class StreamSetItem(BaseModel):
    """A single stream's data within a streamset response."""

    web_id: str = Field(alias="WebId", default="")
    name: str = Field(alias="Name", default="")
    path: str = Field(alias="Path", default="")
    items: list[StreamValue] = Field(alias="Items", default_factory=list)
    units_abbreviation: str = Field(alias="UnitsAbbreviation", default="")
    links: dict[str, str] = Field(alias="Links", default_factory=dict)

    model_config = {"populate_by_name": True}


class BatchResponseItem(BaseModel):
    """A single response within a PI Web API batch result."""

    status: int = Field(alias="Status")
    headers: dict[str, str] = Field(alias="Headers", default_factory=dict)
    content: Any = Field(alias="Content", default=None)

    model_config = {"populate_by_name": True}


class BatchResponse(BaseModel):
    """Response from a batch request.

    The ``responses`` dict maps each caller-assigned request ID to a
    :class:`BatchResponseItem` containing its individual status and body.
    """

    responses: dict[str, BatchResponseItem] = Field(default_factory=dict)
