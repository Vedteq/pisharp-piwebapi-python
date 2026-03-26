"""Tests for the extended PI Web API models."""

from __future__ import annotations

from pisharp_piwebapi.models import (
    Analysis,
    EnumerationSet,
    EnumerationValue,
    EventFrame,
    PIAssetServer,
    PIDataServer,
    PIElementTemplate,
    PINotificationRule,
    TimeRule,
)


class TestEventFrame:
    def test_from_api_response(self):
        data = {
            "WebId": "EF001",
            "Id": "abc-123",
            "Name": "Motor Overtemp",
            "Description": "Motor exceeded temperature threshold",
            "StartTime": "2024-06-15T08:00:00Z",
            "EndTime": "2024-06-15T09:30:00Z",
            "TemplateName": "OverTemp",
            "Severity": "Major",
            "IsAcknowledged": False,
            "CanBeAcknowledged": True,
            "AreValuesCaptured": True,
            "RefElementWebIds": ["E001", "E002"],
            "Links": {"Self": "https://server/piwebapi/eventframes/EF001"},
        }
        ef = EventFrame.model_validate(data)
        assert ef.web_id == "EF001"
        assert ef.name == "Motor Overtemp"
        assert ef.severity == "Major"
        assert ef.is_acknowledged is False
        assert ef.can_be_acknowledged is True
        assert ef.are_values_captured is True
        assert len(ef.ref_element_web_ids) == 2

    def test_defaults(self):
        data = {
            "WebId": "EF002",
            "Name": "Minimal",
            "StartTime": "2024-06-15T08:00:00Z",
            "EndTime": "2024-06-15T09:00:00Z",
        }
        ef = EventFrame.model_validate(data)
        assert ef.severity == "None"
        assert ef.template_name == ""
        assert ef.ref_element_web_ids == []

    def test_open_event_frame_null_end_time(self):
        """Open (in-progress) event frames have null EndTime."""
        data = {
            "WebId": "EF003",
            "Name": "In Progress",
            "StartTime": "2024-06-15T10:00:00Z",
            "EndTime": None,
        }
        ef = EventFrame.model_validate(data)
        assert ef.end_time is None
        assert ef.start_time is not None

    def test_open_event_frame_missing_end_time(self):
        """Open event frames may omit EndTime entirely."""
        data = {
            "WebId": "EF004",
            "Name": "In Progress No End",
            "StartTime": "2024-06-15T10:00:00Z",
        }
        ef = EventFrame.model_validate(data)
        assert ef.end_time is None


class TestAnalysis:
    def test_from_api_response(self):
        data = {
            "WebId": "AN001",
            "Id": "an-456",
            "Name": "Flow Totalizer",
            "Description": "Totalize flow rate",
            "Path": "\\\\AF\\DB\\Element|Flow Totalizer",
            "AnalysisRulePlugInName": "PerformanceEquation",
            "CategoryNames": ["Production", "Flow"],
            "Status": "Enabled",
            "Priority": "High",
            "HasTarget": True,
            "IsConfigured": True,
            "PublishResults": True,
            "Links": {},
        }
        an = Analysis.model_validate(data)
        assert an.web_id == "AN001"
        assert an.analysis_rule_plugin_name == "PerformanceEquation"
        assert an.category_names == ["Production", "Flow"]
        assert an.status == "Enabled"
        assert an.has_target is True


class TestTimeRule:
    def test_from_api_response(self):
        data = {
            "WebId": "TR001",
            "Name": "Periodic",
            "Description": "Every 5 minutes",
            "Path": "\\\\AF\\DB\\Element|Analysis|TimeRule",
            "PlugInName": "Periodic",
            "ConfigString": "Frequency=300",
            "DisplayString": "Every 5 minutes",
            "IsConfigured": True,
            "Links": {},
        }
        tr = TimeRule.model_validate(data)
        assert tr.plug_in_name == "Periodic"
        assert tr.config_string == "Frequency=300"
        assert tr.is_configured is True


class TestPIAssetServer:
    def test_from_api_response(self):
        data = {
            "WebId": "AS001",
            "Id": "guid-001",
            "Name": "MyAFServer",
            "Description": "Production AF",
            "IsConnected": True,
            "ServerVersion": "2.10.9",
            "Links": {"Self": "https://server/piwebapi/assetservers/AS001"},
        }
        svr = PIAssetServer.model_validate(data)
        assert svr.name == "MyAFServer"
        assert svr.is_connected is True
        assert svr.server_version == "2.10.9"


class TestPIDataServer:
    def test_from_api_response(self):
        data = {
            "WebId": "DS001",
            "Id": "guid-002",
            "Name": "MyPIServer",
            "Path": "\\\\MyPIServer",
            "IsConnected": True,
            "ServerVersion": "2023 SP1",
            "Links": {},
        }
        svr = PIDataServer.model_validate(data)
        assert svr.name == "MyPIServer"
        assert svr.is_connected is True


class TestEnumerationSet:
    def test_from_api_response(self):
        data = {
            "WebId": "ES001",
            "Name": "Modes",
            "Description": "Operating modes",
            "Path": "\\\\AF\\DB\\EnumSets[Modes]",
            "Links": {},
        }
        es = EnumerationSet.model_validate(data)
        assert es.name == "Modes"


class TestEnumerationValue:
    def test_from_api_response(self):
        data = {
            "WebId": "EV001",
            "Name": "Auto",
            "Description": "Automatic mode",
            "Value": 1,
            "Path": "\\\\AF\\DB\\EnumSets[Modes]|Auto",
            "Links": {},
        }
        ev = EnumerationValue.model_validate(data)
        assert ev.name == "Auto"
        assert ev.value == 1


class TestPIElementTemplate:
    def test_from_api_response(self):
        data = {
            "WebId": "ET001",
            "Name": "Pump",
            "Description": "Pump element template",
            "Path": "\\\\AF\\DB\\ElementTemplates[Pump]",
            "InstanceType": "Element",
            "CategoryNames": ["Equipment"],
            "AllowElementToExtend": True,
            "Links": {},
        }
        et = PIElementTemplate.model_validate(data)
        assert et.name == "Pump"
        assert et.instance_type == "Element"
        assert et.category_names == ["Equipment"]
        assert et.allow_element_to_extend is True


class TestPINotificationRule:
    def test_from_api_response(self):
        data = {
            "WebId": "NR001",
            "Name": "High Temp Alert",
            "Description": "Notify on high temperature",
            "Path": "\\\\AF\\DB\\Element|High Temp Alert",
            "Status": "Enabled",
            "Criteria": "Temperature > 100",
            "CategoryNames": ["Safety"],
            "Links": {},
        }
        nr = PINotificationRule.model_validate(data)
        assert nr.name == "High Temp Alert"
        assert nr.status == "Enabled"
        assert nr.criteria == "Temperature > 100"
