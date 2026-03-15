"""Pydantic v2 response models for PI Web API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

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

    def __iter__(self):  # type: ignore[override]
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


class BatchResponse(BaseModel):
    """Response from a batch request. Keys are request IDs."""

    responses: dict[str, BatchResponseItem] = Field(default_factory=dict)


class BatchResponseItem(BaseModel):
    """A single response within a batch."""

    status: int = Field(alias="Status")
    headers: dict[str, str] = Field(alias="Headers", default_factory=dict)
    content: Any = Field(alias="Content", default=None)

    model_config = {"populate_by_name": True}


# Rebuild models that have forward references
BatchResponse.model_rebuild()
