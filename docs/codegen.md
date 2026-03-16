# Code Generator

The SDK includes a code generator that creates typed Python endpoint wrappers
from a PI Web API OpenAPI/Swagger specification.

## Usage

```bash
python -m pisharp_piwebapi._generated.generate \
    --spec https://your-server/piwebapi/help/swagger \
    --output src/pisharp_piwebapi/_generated/api/
```

Or from a local file:

```bash
python -m pisharp_piwebapi._generated.generate \
    --spec swagger.json \
    --output src/pisharp_piwebapi/_generated/api/
```

## What it generates

For each controller (tag) in the OpenAPI spec, the generator creates a Python
module with one function per endpoint. For example, a `Point` controller with
`Point_GetByPath` and `Point_Get` operations produces:

```python
# _generated/api/point.py

def point_get_by_path(
    client: GeneratedClient,
    path: str,
) -> Any:
    """Get a point by path."""
    _path = f"/points"
    _params: dict[str, Any] = {}
    _params["path"] = path
    return client.get(_path, params=_params)

def point_get(
    client: GeneratedClient,
    web_id: str,
) -> Any:
    """Get a point."""
    _path = f"/points/{web_id}"
    return client.get(_path, params=None)
```

## Runtime client

Generated functions use `GeneratedClient` from the runtime module, which wraps
an `httpx.Client` with convenience methods for GET, POST, PUT, DELETE, and PATCH.

```python
from pisharp_piwebapi._generated.runtime import GeneratedClient

gen_client = GeneratedClient(your_httpx_client)
```

## When to use

The hand-crafted mixins (`client.points`, `client.streams`, etc.) cover the
most common operations with typed return values. Use the generated client when
you need access to less common endpoints not yet covered by the high-level API.
