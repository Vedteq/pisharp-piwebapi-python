# Getting Started

## Installation

```bash
pip install pisharp-piwebapi
```

### Optional dependencies

| Extra | Install command | Purpose |
|-------|----------------|---------|
| pandas | `pip install pisharp-piwebapi[pandas]` | DataFrame conversion |
| kerberos | `pip install pisharp-piwebapi[kerberos]` | Windows/Kerberos auth |
| dev | `pip install pisharp-piwebapi[dev]` | Testing & linting |

## Authentication

### Basic auth

```python
from pisharp_piwebapi import PIWebAPIClient

client = PIWebAPIClient(
    base_url="https://your-server/piwebapi",
    username="your-user",
    password="your-password",
)
```

### Kerberos auth

```python
client = PIWebAPIClient(
    base_url="https://your-server/piwebapi",
    auth_method="kerberos",
)
```

### Client certificates

```python
client = PIWebAPIClient(
    base_url="https://your-server/piwebapi",
    cert=("/path/to/cert.pem", "/path/to/key.pem"),
)
```

## Common operations

### Read current value

```python
point = client.points.get_by_path(r"\\SERVER\sinusoid")
value = client.streams.get_value(point.web_id)
print(f"{value.value} ({value.units_abbreviation})")
```

### Read historical data

```python
values = client.streams.get_recorded(
    point.web_id,
    start_time="-1h",
    end_time="*",
)
for v in values:
    print(f"{v.timestamp}: {v.value}")
```

### Convert to pandas DataFrame

```python
df = values.to_dataframe()
print(df.describe())
```

### Browse the AF hierarchy

```python
# List servers
servers = client.assetservers.list()

# List databases on a server
databases = client.assetservers.get_databases(servers[0].web_id)

# Get top-level elements
elements = client.databases.get_elements(databases[0].web_id)

# Get child elements
children = client.elements.get_children(elements[0].web_id)

# Get element attributes
attrs = client.elements.get_attributes(elements[0].web_id)
```

### Write values

```python
# Single value
client.streams.update_value(point.web_id, 42.5)

# Bulk write
client.streams.update_values(point.web_id, [
    {"Value": 1.0, "Timestamp": "2024-06-15T10:00:00Z"},
    {"Value": 2.0, "Timestamp": "2024-06-15T10:05:00Z"},
])
```

### Event Frames

```python
# Search event frames
events = client.eventframes.search("Motor*", start_time="-7d")

# Get event frames for an element
events = client.eventframes.get_by_element(element.web_id)

# Acknowledge an event frame
client.eventframes.acknowledge(events[0].web_id)
```

### Batch requests

```python
result = client.execute_batch({
    "1": {"Method": "GET", "Resource": f"/points/{point.web_id}"},
    "2": {"Method": "GET", "Resource": f"/streams/{point.web_id}/value"},
})
```
