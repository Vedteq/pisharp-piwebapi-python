# pisharp-piwebapi

A modern Python SDK for PI Web API — async/sync, fully typed, Pydantic v2 models.

## Features

- **Sync and async** clients powered by [httpx](https://www.python-httpx.org/)
- **Fully typed** with `py.typed` marker (PEP 561)
- **Pydantic v2 models** for all API responses
- **Multiple auth methods** — Basic, Kerberos, client certificates
- **Pandas integration** — `StreamValues.to_dataframe()`
- **Comprehensive coverage** — Points, Streams, Elements, Event Frames, Databases, Servers, Batch, Pagination

## Quick install

```bash
pip install pisharp-piwebapi
```

With optional extras:

```bash
pip install pisharp-piwebapi[pandas]     # DataFrame support
pip install pisharp-piwebapi[kerberos]   # Windows/Kerberos auth
```

## Quick example

```python
from pisharp_piwebapi import PIWebAPIClient

with PIWebAPIClient(
    base_url="https://your-server/piwebapi",
    username="user",
    password="pass",
) as client:
    point = client.points.get_by_path(r"\\SERVER\sinusoid")
    value = client.streams.get_value(point.web_id)
    print(f"{point.name} = {value.value} at {value.timestamp}")
```

## Async example

```python
import asyncio
from pisharp_piwebapi import AsyncPIWebAPIClient

async def main():
    async with AsyncPIWebAPIClient(
        base_url="https://your-server/piwebapi",
        username="user",
        password="pass",
    ) as client:
        point = await client.points.get_by_path(r"\\SERVER\sinusoid")
        values = await client.streams.get_recorded(point.web_id)
        df = values.to_dataframe()
        print(df)

asyncio.run(main())
```
