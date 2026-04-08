"""Pydantic v2 response models for PI Web API."""

from __future__ import annotations

from datetime import datetime  # noqa: TCH003
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    import pandas as pd


class PISystemInfo(BaseModel):
    """System information from the PI Web API landing page (``GET /``)."""

    product_title: str = Field(alias="ProductTitle", default="")
    product_version: str = Field(alias="ProductVersion", default="")
    links: dict[str, str] = Field(alias="Links", default_factory=dict)

    model_config = {"populate_by_name": True}


class PISystemStatus(BaseModel):
    """System status from ``GET /system/status``."""

    up_time_in_seconds: float = Field(alias="UpTimeInSeconds", default=0.0)
    state: str = Field(alias="State", default="")
    cache_instances: int = Field(alias="CacheInstances", default=0)

    model_config = {"populate_by_name": True}


class PIUserInfo(BaseModel):
    """Authenticated user information from ``GET /system/userinfo``."""

    identity_type: str = Field(alias="IdentityType", default="")
    name: str = Field(alias="Name", default="")
    is_authenticated: bool = Field(alias="IsAuthenticated", default=False)
    impersonation_level: str = Field(alias="ImpersonationLevel", default="")

    model_config = {"populate_by_name": True}


class PIVersions(BaseModel):
    """Version information from ``GET /system/versions``.

    The response is a flat JSON object mapping component names (e.g.
    ``"PIWebAPI"``, ``"PIDataArchive"``) to version strings.  Since the
    set of keys varies by server configuration, extra fields are
    allowed and collected into ``versions``.
    """

    versions: dict[str, str] = Field(default_factory=dict)

    model_config = {"populate_by_name": True, "extra": "allow"}

    @classmethod
    def model_validate(
        cls,
        obj: Any,
        **kwargs: Any,
    ) -> PIVersions:
        """Build from the flat dict returned by PI Web API."""
        if isinstance(obj, dict) and "versions" not in obj:
            return cls(versions=obj)
        return super().model_validate(obj, **kwargs)


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
    type_qualifier: str = Field(alias="TypeQualifier", default="")
    value: Any = Field(alias="Value", default=None)
    config_string: str = Field(alias="ConfigString", default="")
    data_reference_plugin: str = Field(alias="DataReferencePlugIn", default="")
    has_children: bool = Field(alias="HasChildren", default=False)
    is_configuration_item: bool = Field(alias="IsConfigurationItem", default=False)
    links: dict[str, str] = Field(alias="Links", default_factory=dict)

    model_config = {"populate_by_name": True}


class StreamValue(BaseModel):
    """A single timestamped value from a PI stream.

    The ``timestamp`` field is optional because PI Web API returns
    ``null`` for certain summary types (e.g. ``Count``,
    ``PercentGood``, ``Total``) where a timestamp is not meaningful.

    The ``action`` field is populated only in stream update responses
    (``"Add"``, ``"Edit"``, ``"Delete"``); it is empty for normal
    stream reads.
    """

    timestamp: datetime | None = Field(alias="Timestamp", default=None)
    value: Any = Field(alias="Value")
    units_abbreviation: str = Field(alias="UnitsAbbreviation", default="")
    good: bool = Field(alias="Good", default=True)
    questionable: bool = Field(alias="Questionable", default=False)
    substituted: bool = Field(alias="Substituted", default=False)
    annotated: bool = Field(alias="Annotated", default=False)
    action: str = Field(alias="Action", default="")
    web_id: str = Field(alias="WebId", default="")
    name: str = Field(alias="Name", default="")
    path: str = Field(alias="Path", default="")

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

    def to_dataframe(self) -> pd.DataFrame:
        """Convert stream values to a pandas DataFrame.

        Returns a DataFrame with columns: timestamp, value, good, questionable,
        substituted, annotated, and units_abbreviation. The timestamp column is
        set as the index.

        Requires the ``pandas`` optional dependency::

            pip install pisharp-piwebapi[pandas]
        """
        try:
            import pandas as pd
        except ImportError as exc:
            raise ImportError(
                "pandas is required for to_dataframe(). "
                "Install it with: pip install pisharp-piwebapi[pandas]"
            ) from exc

        rows = [
            {
                "timestamp": item.timestamp,
                "value": item.value,
                "good": item.good,
                "questionable": item.questionable,
                "substituted": item.substituted,
                "annotated": item.annotated,
                "units_abbreviation": item.units_abbreviation,
            }
            for item in self.items
        ]
        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.set_index("timestamp")
        return df


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
    id: str = Field(alias="Id", default="")
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
    id: str = Field(alias="Id", default="")
    name: str = Field(alias="Name")
    description: str = Field(alias="Description", default="")
    path: str = Field(alias="Path", default="")
    is_connected: bool = Field(alias="IsConnected", default=False)
    server_version: str = Field(alias="ServerVersion", default="")
    links: dict[str, str] = Field(alias="Links", default_factory=dict)

    model_config = {"populate_by_name": True}


class EventFrame(BaseModel):
    """Represents a PI AF Event Frame."""

    web_id: str = Field(alias="WebId")
    id: str = Field(alias="Id", default="")
    name: str = Field(alias="Name")
    description: str = Field(alias="Description", default="")
    start_time: datetime = Field(alias="StartTime")
    end_time: datetime | None = Field(alias="EndTime", default=None)
    template_name: str = Field(alias="TemplateName", default="")
    severity: str = Field(alias="Severity", default="None")
    acknowledged_by: str = Field(alias="AcknowledgedBy", default="")
    acknowledged_date: datetime | None = Field(alias="AcknowledgedDate", default=None)
    can_be_acknowledged: bool = Field(alias="CanBeAcknowledged", default=False)
    is_acknowledged: bool = Field(alias="IsAcknowledged", default=False)
    is_locked: bool = Field(alias="IsLocked", default=False)
    are_values_captured: bool = Field(alias="AreValuesCaptured", default=False)
    ref_element_web_ids: list[str] = Field(alias="RefElementWebIds", default_factory=list)
    links: dict[str, str] = Field(alias="Links", default_factory=dict)

    model_config = {"populate_by_name": True}


class Analysis(BaseModel):
    """Represents a PI AF Analysis."""

    web_id: str = Field(alias="WebId")
    id: str = Field(alias="Id", default="")
    name: str = Field(alias="Name")
    description: str = Field(alias="Description", default="")
    path: str = Field(alias="Path", default="")
    analysis_rule_plugin_name: str = Field(alias="AnalysisRulePlugInName", default="")
    auto_created: bool = Field(alias="AutoCreated", default=False)
    category_names: list[str] = Field(alias="CategoryNames", default_factory=list)
    group_id: int = Field(alias="GroupId", default=0)
    has_notification: bool = Field(alias="HasNotification", default=False)
    has_target: bool = Field(alias="HasTarget", default=False)
    has_template: bool = Field(alias="HasTemplate", default=False)
    is_configured: bool = Field(alias="IsConfigured", default=False)
    is_time_rule_defined_by_template: bool = Field(
        alias="IsTimeRuleDefinedByTemplate", default=False
    )
    maximum_queue_size: int = Field(alias="MaximumQueueSize", default=0)
    output_time: str = Field(alias="OutputTime", default="")
    priority: str = Field(alias="Priority", default="None")
    publish_results: bool = Field(alias="PublishResults", default=False)
    status: str = Field(alias="Status", default="")
    target_web_id: str = Field(alias="TargetWebId", default="")
    template_name: str = Field(alias="TemplateName", default="")
    links: dict[str, str] = Field(alias="Links", default_factory=dict)

    model_config = {"populate_by_name": True}


class TimeRule(BaseModel):
    """Represents a PI AF Time Rule (used by Analyses)."""

    web_id: str = Field(alias="WebId")
    id: str = Field(alias="Id", default="")
    name: str = Field(alias="Name")
    description: str = Field(alias="Description", default="")
    path: str = Field(alias="Path", default="")
    config_string: str = Field(alias="ConfigString", default="")
    config_string_stored: str = Field(alias="ConfigStringStored", default="")
    display_string: str = Field(alias="DisplayString", default="")
    editor_type: str = Field(alias="EditorType", default="")
    is_configured: bool = Field(alias="IsConfigured", default=False)
    is_initializing: bool = Field(alias="IsInitializing", default=False)
    merge_duplicated_items: bool = Field(alias="MergeDuplicatedItems", default=False)
    plug_in_name: str = Field(alias="PlugInName", default="")
    links: dict[str, str] = Field(alias="Links", default_factory=dict)

    model_config = {"populate_by_name": True}


class EnumerationSet(BaseModel):
    """Represents a PI AF Enumeration Set."""

    web_id: str = Field(alias="WebId")
    id: str = Field(alias="Id", default="")
    name: str = Field(alias="Name")
    description: str = Field(alias="Description", default="")
    path: str = Field(alias="Path", default="")
    links: dict[str, str] = Field(alias="Links", default_factory=dict)

    model_config = {"populate_by_name": True}


class EnumerationValue(BaseModel):
    """Represents a single value in a PI AF Enumeration Set."""

    web_id: str = Field(alias="WebId")
    id: str = Field(alias="Id", default="")
    name: str = Field(alias="Name")
    description: str = Field(alias="Description", default="")
    value: int = Field(alias="Value", default=0)
    path: str = Field(alias="Path", default="")
    links: dict[str, str] = Field(alias="Links", default_factory=dict)

    model_config = {"populate_by_name": True}


class PIElementTemplate(BaseModel):
    """Represents a PI AF Element Template."""

    web_id: str = Field(alias="WebId")
    id: str = Field(alias="Id", default="")
    name: str = Field(alias="Name")
    description: str = Field(alias="Description", default="")
    path: str = Field(alias="Path", default="")
    instance_type: str = Field(alias="InstanceType", default="Element")
    naming_pattern: str = Field(alias="NamingPattern", default="")
    category_names: list[str] = Field(alias="CategoryNames", default_factory=list)
    allow_element_to_extend: bool = Field(alias="AllowElementToExtend", default=False)
    base_template: str = Field(alias="BaseTemplate", default="")
    severity: str = Field(alias="Severity", default="None")
    can_be_acknowledged: bool = Field(alias="CanBeAcknowledged", default=False)
    links: dict[str, str] = Field(alias="Links", default_factory=dict)

    model_config = {"populate_by_name": True}


class PIAttributeTemplate(BaseModel):
    """Represents a PI AF Attribute Template.

    Attribute templates define the attributes that are automatically
    created on elements derived from an element template.
    """

    web_id: str = Field(alias="WebId")
    id: str = Field(alias="Id", default="")
    name: str = Field(alias="Name")
    description: str = Field(alias="Description", default="")
    path: str = Field(alias="Path", default="")
    type: str = Field(alias="Type", default="")
    type_qualifier: str = Field(alias="TypeQualifier", default="")
    default_value: Any = Field(alias="DefaultValue", default=None)
    config_string: str = Field(alias="ConfigString", default="")
    data_reference_plugin: str = Field(alias="DataReferencePlugIn", default="")
    has_children: bool = Field(alias="HasChildren", default=False)
    is_configuration_item: bool = Field(alias="IsConfigurationItem", default=False)
    is_excluded: bool = Field(alias="IsExcluded", default=False)
    is_hidden: bool = Field(alias="IsHidden", default=False)
    is_manual_data_entry: bool = Field(alias="IsManualDataEntry", default=False)
    category_names: list[str] = Field(alias="CategoryNames", default_factory=list)
    trait_name: str = Field(alias="TraitName", default="")
    default_units_name: str = Field(alias="DefaultUnitsName", default="")
    links: dict[str, str] = Field(alias="Links", default_factory=dict)

    model_config = {"populate_by_name": True}


class PINotificationRule(BaseModel):
    """Represents a PI AF Notification Rule."""

    web_id: str = Field(alias="WebId")
    id: str = Field(alias="Id", default="")
    name: str = Field(alias="Name")
    description: str = Field(alias="Description", default="")
    path: str = Field(alias="Path", default="")
    auto_created: bool = Field(alias="AutoCreated", default=False)
    category_names: list[str] = Field(alias="CategoryNames", default_factory=list)
    criteria: str = Field(alias="Criteria", default="")
    multi_trigger_event_option: str = Field(alias="MultiTriggerEventOption", default="")
    nonrepetition_interval: str = Field(alias="NonrepetitionInterval", default="")
    resend_interval: str = Field(alias="ResendInterval", default="")
    status: str = Field(alias="Status", default="")
    template_name: str = Field(alias="TemplateName", default="")
    links: dict[str, str] = Field(alias="Links", default_factory=dict)

    model_config = {"populate_by_name": True}


class PINotificationRuleSubscriber(BaseModel):
    """Represents a PI AF Notification Rule Subscriber.

    Subscribers define the delivery contacts that receive notifications
    when a notification rule triggers.  Each subscriber references a
    notification contact template and an optional delivery channel.
    """

    web_id: str = Field(alias="WebId")
    id: str = Field(alias="Id", default="")
    name: str = Field(alias="Name")
    description: str = Field(alias="Description", default="")
    path: str = Field(alias="Path", default="")
    config_string: str = Field(alias="ConfigString", default="")
    contact_template_name: str = Field(
        alias="ContactTemplateName", default=""
    )
    contact_type: str = Field(alias="ContactType", default="")
    delivery_channel_name: str = Field(
        alias="DeliveryChannelName", default=""
    )
    plug_in_name: str = Field(alias="PlugInName", default="")
    escalation_timeout: str = Field(alias="EscalationTimeout", default="")
    is_enabled: bool = Field(alias="IsEnabled", default=True)
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
    """A single stream's data within a streamset response.

    When a partial failure occurs (e.g. one tag is deleted or
    access-denied), PI Web API populates the ``errors`` list instead
    of ``items``.  Check ``errors`` to detect per-stream failures in
    multi-tag queries.
    """

    web_id: str = Field(alias="WebId", default="")
    name: str = Field(alias="Name", default="")
    path: str = Field(alias="Path", default="")
    items: list[StreamValue] = Field(alias="Items", default_factory=list)
    errors: list[str] = Field(alias="Errors", default_factory=list)
    units_abbreviation: str = Field(alias="UnitsAbbreviation", default="")
    links: dict[str, str] = Field(alias="Links", default_factory=dict)

    model_config = {"populate_by_name": True}


class StreamUpdate(BaseModel):
    """Response from a stream update registration or retrieval.

    Contains events received since the last marker, plus a new marker
    for subsequent retrieval.  Returned by
    ``POST /streams/{webId}/updates`` (register) and
    ``GET /streams/updates/{marker}`` (retrieve).
    """

    source: str = Field(alias="Source", default="")
    source_name: str = Field(alias="SourceName", default="")
    source_path: str = Field(alias="SourcePath", default="")
    latest_marker: str = Field(alias="LatestMarker", default="")
    status: str = Field(alias="Status", default="")
    events: list[StreamValue] = Field(alias="Events", default_factory=list)
    exception: Any = Field(alias="Exception", default=None)

    model_config = {"populate_by_name": True}


class PITable(BaseModel):
    """Represents a PI AF Table.

    AF Tables store tabular lookup or configuration data within an
    AF database.  Use the table controller to retrieve metadata and
    the ``get_data`` / ``update_data`` methods to read or write the
    actual row data.
    """

    web_id: str = Field(alias="WebId")
    id: str = Field(alias="Id", default="")
    name: str = Field(alias="Name")
    description: str = Field(alias="Description", default="")
    path: str = Field(alias="Path", default="")
    category_names: list[str] = Field(alias="CategoryNames", default_factory=list)
    convert_to_local_time: bool = Field(alias="ConvertToLocalTime", default=False)
    time_zone: str = Field(alias="TimeZone", default="")
    links: dict[str, str] = Field(alias="Links", default_factory=dict)

    model_config = {"populate_by_name": True}


class PITableData(BaseModel):
    """Tabular data from a PI AF Table.

    The ``columns`` dict maps column names to their PI type strings.
    The ``rows`` list contains one dict per row, mapping column names
    to cell values.
    """

    columns: dict[str, str] = Field(alias="Columns", default_factory=dict)
    rows: list[dict[str, Any]] = Field(alias="Rows", default_factory=list)

    model_config = {"populate_by_name": True}


class PIUnitClass(BaseModel):
    """Represents a PI AF Unit Class (e.g. Temperature, Pressure).

    Unit classes group related engineering units and define a canonical
    unit for conversions.  Use the unit classes controller to list
    available classes and their member units.
    """

    web_id: str = Field(alias="WebId")
    id: str = Field(alias="Id", default="")
    name: str = Field(alias="Name")
    description: str = Field(alias="Description", default="")
    path: str = Field(alias="Path", default="")
    canonical_unit_name: str = Field(alias="CanonicalUnitName", default="")
    canonical_unit_abbreviation: str = Field(
        alias="CanonicalUnitAbbreviation", default=""
    )
    links: dict[str, str] = Field(alias="Links", default_factory=dict)

    model_config = {"populate_by_name": True}


class PIUnit(BaseModel):
    """Represents a PI AF Unit of Measure.

    Units belong to a unit class and define conversion factors relative
    to the canonical unit: ``canonical = factor * value + offset``.
    Built-in units are read-only; custom units can be created within
    user-defined unit classes.
    """

    web_id: str = Field(alias="WebId")
    id: str = Field(alias="Id", default="")
    name: str = Field(alias="Name")
    abbreviation: str = Field(alias="Abbreviation", default="")
    description: str = Field(alias="Description", default="")
    path: str = Field(alias="Path", default="")
    factor: float = Field(alias="Factor", default=1.0)
    offset: float = Field(alias="Offset", default=0.0)
    reference_factor: float = Field(alias="ReferenceFactor", default=0.0)
    reference_offset: float = Field(alias="ReferenceOffset", default=0.0)
    reference_unit_abbreviation: str = Field(
        alias="ReferenceUnitAbbreviation", default=""
    )
    links: dict[str, str] = Field(alias="Links", default_factory=dict)

    model_config = {"populate_by_name": True}


class PICategory(BaseModel):
    """Represents a PI AF Category (element, analysis, or attribute).

    Categories are used to classify AF objects within a database.
    The same model is used for element categories, analysis categories,
    and attribute categories since the API response shape is identical.
    """

    web_id: str = Field(alias="WebId")
    id: str = Field(alias="Id", default="")
    name: str = Field(alias="Name")
    description: str = Field(alias="Description", default="")
    path: str = Field(alias="Path", default="")
    links: dict[str, str] = Field(alias="Links", default_factory=dict)

    model_config = {"populate_by_name": True}


class PIAnalysisTemplate(BaseModel):
    """Represents a PI AF Analysis Template.

    Analysis templates define reusable analysis configurations that
    are automatically applied to elements derived from an element
    template.  Creating an analysis template can auto-create concrete
    analyses on all derived elements.
    """

    web_id: str = Field(alias="WebId")
    id: str = Field(alias="Id", default="")
    name: str = Field(alias="Name")
    description: str = Field(alias="Description", default="")
    path: str = Field(alias="Path", default="")
    analysis_rule_plugin_name: str = Field(
        alias="AnalysisRulePlugInName", default=""
    )
    category_names: list[str] = Field(
        alias="CategoryNames", default_factory=list
    )
    create_enabled: bool = Field(alias="CreateEnabled", default=False)
    group_id: int = Field(alias="GroupId", default=0)
    has_notification_template: bool = Field(
        alias="HasNotificationTemplate", default=False
    )
    has_target: bool = Field(alias="HasTarget", default=False)
    output_time: str = Field(alias="OutputTime", default="")
    target_name: str = Field(alias="TargetName", default="")
    time_rule_plugin_name: str = Field(
        alias="TimeRulePlugInName", default=""
    )
    links: dict[str, str] = Field(alias="Links", default_factory=dict)

    model_config = {"populate_by_name": True}


class PISecurityIdentity(BaseModel):
    """Represents a PI Security Identity.

    Security identities are the principal objects used by the PI Data
    Archive to control access to points, servers, and other resources.
    They map to Windows users/groups via security mappings.
    """

    web_id: str = Field(alias="WebId")
    id: str = Field(alias="Id", default="")
    name: str = Field(alias="Name")
    description: str = Field(alias="Description", default="")
    path: str = Field(alias="Path", default="")
    is_enabled: bool = Field(alias="IsEnabled", default=True)
    links: dict[str, str] = Field(alias="Links", default_factory=dict)

    model_config = {"populate_by_name": True}


class PISecurityMapping(BaseModel):
    """Represents a PI Security Mapping.

    Security mappings associate Windows identities (users or groups)
    with PI security identities, controlling which Windows accounts
    receive which PI security identity when connecting.
    """

    web_id: str = Field(alias="WebId")
    id: str = Field(alias="Id", default="")
    name: str = Field(alias="Name")
    description: str = Field(alias="Description", default="")
    path: str = Field(alias="Path", default="")
    account: str = Field(alias="Account", default="")
    security_identity_web_id: str = Field(
        alias="SecurityIdentityWebId", default=""
    )
    security_identity_name: str = Field(
        alias="SecurityIdentityName", default=""
    )
    is_enabled: bool = Field(alias="IsEnabled", default=True)
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
