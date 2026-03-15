# CLAUDE.md — pisharp-piwebapi Python SDK

## What This Is

`pisharp-piwebapi` is a modern Python SDK for AVEVA PI Web API. It provides:

- **Sync and async clients** — `PIWebAPIClient` and `AsyncPIWebAPIClient`
- **Fully typed** — type hints everywhere, Pydantic v2 response models
- **Authentication** — Basic, Kerberos, NTLM, certificate-based
- **Common tasks** — point lookup, read/write values, batch requests, pagination
- **Pandas integration** — optional helpers to convert responses to DataFrames
- **Python 3.10+** — uses `httpx` under the hood

## Package Structure

```
src/
  pisharp_piwebapi/
    __init__.py       # Public exports (PIWebAPIClient, AsyncPIWebAPIClient)
    client.py         # Client classes (sync + async)
    auth.py           # Authentication handlers (Basic, Kerberos, NTLM, cert)
    models.py         # Pydantic v2 response models
    points.py         # Points resource (get_by_path, search, etc.)
    values.py         # Streams/values resource (get_value, get_recorded, update_value, etc.)
    batch.py          # Batch request support
    pagination.py     # Pagination helpers
    exceptions.py     # SDK exceptions
    _generated/       # Auto-generated API wrappers (do not edit manually)
```

## Commands

```bash
# Install for development (from repo root)
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=src

# Lint (check only)
ruff check src/

# Lint (auto-fix)
ruff check --fix src/

# Format
ruff format src/

# Type check
mypy src/

# Build distribution packages
python -m build
```

## Conventions

### Code Style
- Line length: 100 characters (enforced by ruff)
- Target: Python 3.10+ syntax
- Ruff rules: E, F, I, UP, B, SIM, TCH (see `pyproject.toml`)
- Mypy: strict mode

### Type Hints
- All public functions and methods **must** have complete type hints
- Use `from __future__ import annotations` when needed for forward references
- Prefer `X | Y` union syntax over `Union[X, Y]` (Python 3.10+)
- Use `Sequence`, `Mapping` from `collections.abc` for parameters; `list`, `dict` for return types

### Docstrings
- All public modules, classes, and methods **must** have docstrings
- Use Google-style docstrings:

```python
def get_by_path(self, path: str, *, web_id_type: str = "Full") -> PIPoint:
    """Look up a PI point by its full path.

    Args:
        path: The full PI point path, e.g. ``\\\\SERVER\\sinusoid``.
        web_id_type: The WebID type to request. Defaults to ``"Full"``.

    Returns:
        A :class:`PIPoint` model populated from the API response.

    Raises:
        PIWebAPIError: If the server returns a non-2xx response.
        PIWebAPINotFoundError: If the point does not exist.
    """
```

### Error Handling
- Raise SDK-specific exceptions from `exceptions.py`, not raw `httpx` errors
- Never swallow exceptions silently
- Surface the HTTP status code and response body in error messages

### Testing
- Tests live in `tests/`
- Use `respx` for mocking `httpx` requests (no live PI server required)
- `pytest-asyncio` is configured with `asyncio_mode = "auto"` — async tests just work
- Every public method needs at least one test covering the happy path
- Add edge-case tests for error responses (404, 401, 500, etc.)

### Adding New Resources
Follow the pattern in `points.py` and `values.py`:
1. Create a new file `src/pisharp_piwebapi/<resource>.py`
2. Define a sync class and derive the async version (or implement both)
3. Add Pydantic models to `models.py`
4. Export from `__init__.py`
5. Write tests in `tests/test_<resource>.py`

## Never
- Commit `.env*` files
- Edit files in `_generated/` by hand (they are auto-generated)
- Use `print()` for debugging in library code (use `logging` if needed)
- Add dependencies without updating `pyproject.toml`
