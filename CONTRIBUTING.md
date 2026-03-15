# Contributing to pisharp-piwebapi

Thank you for your interest in contributing!

## Development Setup

1. Clone the repository:

```bash
git clone https://github.com/Vedteq/pisharp-piwebapi-python.git
cd pisharp-piwebapi-python
```

2. Create a virtual environment and install dev dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

3. Run tests:

```bash
pytest
```

4. Run linting:

```bash
ruff check .
ruff format .
mypy src/
```

## Making Changes

1. Create a branch from `main`
2. Make your changes
3. Add or update tests
4. Ensure `pytest`, `ruff check`, and `mypy` all pass
5. Submit a pull request

## Code Style

- We use `ruff` for linting and formatting
- All public functions need type hints
- All public functions need docstrings
- Follow existing patterns in the codebase

## Reporting Issues

Use the [GitHub issue tracker](https://github.com/Vedteq/pisharp-piwebapi-python/issues). Please include:

- Python version
- PI Web API version
- Minimal reproduction steps
- Expected vs. actual behavior
