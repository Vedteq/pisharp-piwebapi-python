# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - Unreleased

### Added

- `PIWebAPIClient` (sync) and `AsyncPIWebAPIClient` (async) clients
- Basic and Kerberos authentication support
- Point lookup by path, WebID, and search
- Stream value reads (current, recorded, interpolated)
- Stream value writes (single and bulk)
- Element operations (get by path/WebID, children, attributes, create, delete)
- Event Frame operations (get, search, create, acknowledge, delete)
- Asset Server operations (list, get by name/WebID, list databases)
- Data Server operations (list, get by name/WebID)
- Database operations (get by path/WebID, list top-level elements)
- Batch request support
- Pagination helpers (`get_all_pages`)
- `StreamValues.to_dataframe()` — pandas DataFrame conversion (optional dependency)
- Pydantic v2 models: `PIPoint`, `PIAttribute`, `PIElement`, `PIDatabase`,
  `PIAssetServer`, `PIDataServer`, `EventFrame`, `Analysis`, `TimeRule`,
  `EnumerationSet`, `EnumerationValue`, `PIElementTemplate`, `PINotificationRule`,
  `StreamValue`, `StreamValues`, `BatchResponse`, `BatchResponseItem`
- OpenAPI code generator scaffold (`python -m pisharp_piwebapi._generated.generate`)
- CI/CD pipeline with lint, type check, test matrix (Python 3.10–3.13), and PyPI publish
- Full type hints and `py.typed` marker (PEP 561)
- Integration test suite with respx-mocked HTTP

### Fixed

- Event hook now calls `response.read()` before accessing error response body
