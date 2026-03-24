# PI Web API -- Expert Technical Reference

## Architecture
RESTful web service on ASP.NET/IIS, uses AF SDK internally. Base URL: `https://<server>/piwebapi/`

## Authentication

| Method | Details |
|---|---|
| **Kerberos** | Windows Integrated Auth. Default and recommended. |
| **Basic** | Base64 `username:password`. Enable in PI Web API config. HTTPS only. |
| **Bearer Token** | JWT-based. For non-Windows clients. |

## WebId
URL-safe Base64 identifier for all resources. Types: Full, IDOnly, PathOnly, LocalIDOnly, DefaultIDOnly. Cache WebIds, don't parse them.

## Key Controllers

| Controller | Resource |
|---|---|
| `DataServer` | PI Data Archive servers |
| `AssetServer` | PI AF servers |
| `AssetDatabase` | AF databases |
| `Element` / `ElementTemplate` | AF elements/templates |
| `Attribute` / `AttributeTemplate` | AF attributes/templates |
| `Point` | PI tags |
| `Stream` | Single stream time-series |
| `StreamSet` | Multiple streams |
| `EventFrame` | AF event frames |
| `Batch` | Bundled multi-request |
| `Channel` | WebSocket streaming |
| `Search` | Indexed search (Kerberos only) |
| `Calculation` | Server-side calculations |

## Stream Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/streams/{webId}/value` | Snapshot |
| GET | `/streams/{webId}/recorded` | Compressed values |
| GET | `/streams/{webId}/interpolated` | Evenly-spaced |
| GET | `/streams/{webId}/plot` | Plot-optimized |
| GET | `/streams/{webId}/summary` | Statistics |
| GET | `/streams/{webId}/end` | Most recent value |
| GET | `/streams/{webId}/channel` | WebSocket push |
| POST | `/streams/{webId}/value` | Write single value |
| POST | `/streams/{webId}/recorded` | Write multiple values |

**Query params**: `startTime`, `endTime`, `interval`, `intervals`, `summaryType` (Total/Average/Minimum/Maximum/Range/StdDev/Count/All), `selectedFields`, `desiredUnits`

## StreamSet (Bulk)
```
GET /streamsets/{webId}/value           -- all child attribute values
GET /streamsets/{webId}/recorded        -- bulk recorded
GET /streamsets/value?webId=X&webId=Y   -- arbitrary list
GET /streamsets/{webId}/channel         -- WebSocket for all
```
Handles ~400 WebIDs per request. Reduces thousands of calls to a few.

## Batch Requests

```json
{
    "GetElement": {
        "Method": "GET",
        "Resource": "https://server/piwebapi/elements?path=\\\\AF\\DB\\Elem1"
    },
    "GetValues": {
        "Method": "GET",
        "Resource": "https://server/piwebapi/streamsets/{0}/value",
        "ParentIds": ["GetElement"],
        "Parameters": ["$.GetElement.Content.WebId"]
    }
}
```
- `ParentIds` = dependency ordering
- `Parameters` = JSONPath refs to parent responses
- No ParentIds = parallel execution

## Search Query Syntax
```
GET /search/query?q=name:*pump* AND afElementTemplate:PumpTemplate
GET /search/query?q=afcategory:Equipment
```
Case-insensitive. Requires PI Web API Crawler to index AF databases.

## Channels (WebSocket)
```javascript
const ws = new WebSocket("wss://server/piwebapi/streams/{webId}/channel");
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    updateDisplay(data.Items);
};
```

## OMF Ingress

Endpoint: `POST /omf`. Three message types sent in order:

**1. Type** (define structure):
```json
[{"id": "TempSensor", "classification": "dynamic", "type": "object",
  "properties": {
    "Timestamp": {"type": "string", "format": "date-time", "isindex": true},
    "Value": {"type": "number", "format": "float32"}
}}]
```

**2. Container** (map to PI Point):
```json
[{"id": "Sensor_001", "typeid": "TempSensor"}]
```

**3. Data** (send values):
```json
[{"containerid": "Sensor_001", "values": [
    {"Timestamp": "2025-01-15T10:00:00Z", "Value": 72.5}
]}]
```

Headers: `messagetype: type|container|data`, `action: create`, `omfversion: 1.2`

## CORS Configuration
In PI System Explorer: `Elements > OSIsoft > PI Web API > <hostname> > System Configuration`
- `CorsOrigins`, `CorsMethods`, `CorsHeaders`, `CorsSupportsCred`, `EnableCSRFDefence`

## Integration Patterns

### Power BI
- PI OLEDB Enterprise (direct connection)
- AVEVA Connect Power BI Connector
- PI Integrator for Business Analytics
- PI Web API via Power Query M

### Grafana
Plugin: `gridprotectionalliance-osisoftpi-datasource`
- Access mode: proxy, URL = PI Web API base, Basic auth
- Supports PI Point queries, AF attribute queries, template variables, event frame annotations

### Custom Web Apps
```javascript
// Get element
const elem = await fetch(`${baseUrl}/elements?path=\\\\AF\\DB\\Reactor01`,
    {credentials: 'include'}).then(r => r.json());
// Get values
const values = await fetch(`${baseUrl}/streamsets/${elem.WebId}/value`).then(r => r.json());
// WebSocket real-time
const ws = new WebSocket(`wss://server/piwebapi/streams/${webId}/channel`);
```

PI time strings: `*` (now), `*-1d` (1 day ago), `t` (today midnight), `y` (yesterday)

Sources: [PI Web API Reference](https://docs.aveva.com/bundle/pi-web-api-reference/page/help.html), [Batch Support](https://docs.aveva.com/bundle/pi-web-api/page/1023110.html), [OMF Docs](https://omf-docs.osisoft.com/), [Search Syntax](https://docs.aveva.com/bundle/pi-web-api-reference/page/help/topics/search-query-syntax.html)
