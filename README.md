# pisharp-piwebapi

A modern Python SDK for PI Web API. Async and sync, fully typed, Pydantic v2 models.

[![PyPI](https://img.shields.io/pypi/v/pisharp-piwebapi)](https://pypi.org/project/pisharp-piwebapi/)
[![Python](https://img.shields.io/pypi/pyversions/pisharp-piwebapi)](https://pypi.org/project/pisharp-piwebapi/)
[![License](https://img.shields.io/github/license/Vedteq/pisharp-piwebapi-python)](LICENSE)

## Install

```bash
pip install pisharp-piwebapi
```

With Kerberos support:

```bash
pip install pisharp-piwebapi[kerberos]
```

With pandas integration:

```bash
pip install pisharp-piwebapi[pandas]
```

## Quick Start

```python
from pisharp_piwebapi import PIWebAPIClient

# Connect with Basic auth
client = PIWebAPIClient(
    base_url="https://your-server/piwebapi",
    username="your-username",
    password="your-password",
    verify_ssl=False,  # Set True in production with proper certs
)

# Look up a PI point
point = client.points.get_by_path(r"\\SERVER\sinusoid")

# Read the current value
value = client.streams.get_value(point.web_id)
print(f"{point.name}: {value.value} at {value.timestamp}")

# Read recorded values over a time range
values = client.streams.get_recorded(
    point.web_id,
    start_time="-1h",
    end_time="*",
)
for v in values:
    print(f"  {v.timestamp}: {v.value}")

# Write a value
client.streams.update_value(point.web_id, value=42.0)
```

### Async Usage

```python
import asyncio
from pisharp_piwebapi import AsyncPIWebAPIClient

async def main():
    async with AsyncPIWebAPIClient(
        base_url="https://your-server/piwebapi",
        username="your-username",
        password="your-password",
    ) as client:
        point = await client.points.get_by_path(r"\\SERVER\sinusoid")
        value = await client.streams.get_value(point.web_id)
        print(f"{point.name}: {value.value}")

asyncio.run(main())
```

## Features

- **Sync and async** clients — use whichever fits your workflow
- **Fully typed** — type hints everywhere, Pydantic v2 response models
- **Authentication** — Basic, Kerberos, NTLM, certificate-based
- **Common tasks** — point lookup, read/write values, batch requests, pagination
- **Pandas-friendly** — optional helpers to convert responses to DataFrames
- **Modern Python** — requires Python 3.10+, uses `httpx` under the hood

## Documentation

- [PiSharp Developer Hub](https://pisharp.com/developer-hub) — guided tutorials and learning paths
- [PI Web API Guide](https://pisharp.com/developer-hub/pi-web-api) — core concepts and how-to guides
- [Cookbook](https://pisharp.com/developer-hub/pi-web-api/cookbook) — packaged examples and recipes
- [SDK Comparison](https://pisharp.com/developer-hub/pi-web-api/sdk-comparison) — raw requests vs. this SDK

## Examples

See the [`examples/`](examples/) directory for complete working examples:

- [`basic_auth.py`](examples/basic_auth.py) — connect with Basic authentication
- [`read_current_values.py`](examples/read_current_values.py) — read current and recorded values
- [`write_values.py`](examples/write_values.py) — write single and multiple values
- [`batch_requests.py`](examples/batch_requests.py) — batch multiple API calls
- [`async_usage.py`](examples/async_usage.py) — async client patterns

## Need Help?

- [Open an issue](https://github.com/Vedteq/pisharp-piwebapi-python/issues) for bugs or feature requests
- [PiSharp Developer Hub](https://pisharp.com/developer-hub) for guided learning
- [PiSharp Services](https://pisharp.com/developer-hub/services/quickstart-package) for implementation help

## Acknowledgments

This project was informed by prior work in the PI ecosystem. See [NOTICE](NOTICE) for details.

## License

Apache-2.0 — see [LICENSE](LICENSE).
