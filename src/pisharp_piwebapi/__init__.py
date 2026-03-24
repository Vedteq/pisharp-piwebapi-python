"""pisharp-piwebapi — A modern Python SDK for PI Web API."""

from pisharp_piwebapi._pandas import stream_values_to_dataframe
from pisharp_piwebapi.auth import basic_auth, kerberos_auth, ntlm_auth
from pisharp_piwebapi.client import AsyncPIWebAPIClient, PIWebAPIClient
from pisharp_piwebapi.exceptions import (
    AuthenticationError,
    BatchError,
    NotFoundError,
    PIWebAPIError,
    RateLimitError,
    ServerError,
)
from pisharp_piwebapi.models import (
    Analysis,
    EnumerationSet,
    EnumerationValue,
    EventFrame,
    PIAssetServer,
    PIAttribute,
    PIDatabase,
    PIDataServer,
    PIElement,
    PIElementTemplate,
    PINotificationRule,
    PIPoint,
    StreamSetItem,
    StreamSummary,
    StreamSummaryValue,
    StreamValue,
    StreamValues,
    TimeRule,
)

__all__ = [
    "PIWebAPIClient",
    "AsyncPIWebAPIClient",
    "PIWebAPIError",
    "AuthenticationError",
    "NotFoundError",
    "BatchError",
    "RateLimitError",
    "ServerError",
    "Analysis",
    "EnumerationSet",
    "EnumerationValue",
    "EventFrame",
    "PIAssetServer",
    "PIAttribute",
    "PIDatabase",
    "PIDataServer",
    "PIElement",
    "PIElementTemplate",
    "PINotificationRule",
    "PIPoint",
    "StreamSetItem",
    "StreamSummary",
    "StreamSummaryValue",
    "StreamValue",
    "StreamValues",
    "TimeRule",
    "stream_values_to_dataframe",
    "basic_auth",
    "kerberos_auth",
    "ntlm_auth",
]

__version__ = "0.1.0"
