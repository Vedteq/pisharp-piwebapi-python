"""Code generator: converts a PI Web API OpenAPI spec into typed Python modules.

Usage::

    python -m pisharp_piwebapi._generated.generate \\
        --spec path/to/swagger.json \\
        --output src/pisharp_piwebapi/_generated/api/

This script reads the OpenAPI/Swagger JSON, and for each controller
(tag) it generates a Python module with one function per endpoint.
The generated functions use ``GeneratedClient`` from ``runtime.py``.

If the spec is a URL, it will be fetched via HTTP.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def _snake_case(name: str) -> str:
    """Convert PascalCase or camelCase to snake_case."""
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    return s.lower()


def _sanitize_name(name: str) -> str:
    """Make a string safe for use as a Python identifier."""
    return re.sub(r"[^a-zA-Z0-9_]", "_", name)


def _python_type(schema: dict[str, Any]) -> str:
    """Map an OpenAPI schema type to a Python type hint."""
    type_map = {
        "string": "str",
        "integer": "int",
        "number": "float",
        "boolean": "bool",
        "object": "dict[str, Any]",
        "array": "list[Any]",
    }
    return type_map.get(schema.get("type", ""), "Any")


def _load_spec(spec_path: str) -> dict[str, Any]:
    """Load an OpenAPI spec from a file path or URL."""
    if spec_path.startswith(("http://", "https://")):
        import httpx

        resp = httpx.get(spec_path, verify=False)  # noqa: S501
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]
    return json.loads(Path(spec_path).read_text())  # type: ignore[no-any-return]


def _generate_module(tag: str, endpoints: list[dict[str, Any]]) -> str:
    """Generate Python source for a single controller module."""
    lines = [
        f'"""Generated API wrapper for the {tag} controller."""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Any",
        "",
        "from pisharp_piwebapi._generated.runtime import GeneratedClient",
        "",
        "",
    ]

    for ep in endpoints:
        method = ep["method"]
        path = ep["path"]
        operation_id = ep.get("operationId", f"{method}_{path}")
        func_name = _snake_case(_sanitize_name(operation_id))
        summary = ep.get("summary", "").strip()

        # Collect path and query parameters
        path_params: list[dict[str, Any]] = []
        query_params: list[dict[str, Any]] = []
        has_body = method in ("post", "put", "patch")

        for param in ep.get("parameters", []):
            p = {
                "name": param["name"],
                "py_name": _snake_case(_sanitize_name(param["name"])),
                "type": _python_type(param.get("schema", {})),
                "required": param.get("required", False),
            }
            if param.get("in") == "path":
                path_params.append(p)
            elif param.get("in") == "query":
                query_params.append(p)

        # Build function signature
        sig_parts = ["client: GeneratedClient"]
        for p in path_params:
            sig_parts.append(f"{p['py_name']}: {p['type']}")
        if has_body:
            sig_parts.append("body: dict[str, Any] | None = None")
        for p in query_params:
            if p["required"]:
                sig_parts.append(f"{p['py_name']}: {p['type']}")
            else:
                sig_parts.append(f"{p['py_name']}: {p['type']} | None = None")

        sig = ",\n    ".join(sig_parts)

        # Build function body
        func_lines = []
        if summary:
            func_lines.append(f'    """{summary}"""')

        # Build path with interpolation
        py_path = path
        for p in path_params:
            py_path = py_path.replace("{" + p["name"] + "}", "{" + p["py_name"] + "}")
        func_lines.append(f'    _path = f"{py_path}"')

        # Build query params dict
        if query_params:
            func_lines.append("    _params: dict[str, Any] = {}")
            for p in query_params:
                func_lines.append(
                    f"    if {p['py_name']} is not None:" if not p["required"] else ""
                )
                indent = "        " if not p["required"] else "    "
                func_lines.append(f'{indent}_params["{p["name"]}"] = {p["py_name"]}')
            params_arg = "_params"
        else:
            params_arg = "None"

        # Build the client call
        if has_body:
            func_lines.append(f"    return client.{method}(_path, json=body, params={params_arg})")
        else:
            func_lines.append(f"    return client.{method}(_path, params={params_arg})")

        # Filter empty lines from conditionals
        func_lines = [line for line in func_lines if line != ""]

        lines.append(f"def {func_name}(")
        lines.append(f"    {sig},")
        lines.append(") -> Any:")
        lines.extend(func_lines)
        lines.append("")
        lines.append("")

    return "\n".join(lines)


def generate(spec_path: str, output_dir: str) -> None:
    """Generate Python modules from an OpenAPI spec."""
    spec = _load_spec(spec_path)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Group endpoints by tag
    grouped: dict[str, list[dict[str, Any]]] = {}
    paths = spec.get("paths", {})

    for path, methods in paths.items():
        for method, details in methods.items():
            if method in ("get", "post", "put", "delete", "patch"):
                tags = details.get("tags", ["default"])
                tag = tags[0] if tags else "default"
                ep = {
                    "method": method,
                    "path": path,
                    "operationId": details.get("operationId", f"{method}_{path}"),
                    "summary": details.get("summary", ""),
                    "parameters": details.get("parameters", []),
                }
                grouped.setdefault(tag, []).append(ep)

    # Generate one module per tag/controller
    init_imports = []
    for tag, endpoints in sorted(grouped.items()):
        module_name = _snake_case(_sanitize_name(tag))
        source = _generate_module(tag, endpoints)
        (out / f"{module_name}.py").write_text(source)
        init_imports.append(f"from pisharp_piwebapi._generated.api.{module_name} import *  # noqa")
        print(f"  Generated {module_name}.py ({len(endpoints)} endpoints)")

    # Write __init__.py
    init_content = '"""Auto-generated API modules."""\n\n' + "\n".join(init_imports) + "\n"
    (out / "__init__.py").write_text(init_content)

    print(f"\nGenerated {len(grouped)} modules in {out}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Python API modules from a PI Web API OpenAPI spec.",
    )
    parser.add_argument(
        "--spec",
        required=True,
        help="Path or URL to the OpenAPI/Swagger JSON spec.",
    )
    parser.add_argument(
        "--output",
        default="src/pisharp_piwebapi/_generated/api",
        help="Output directory for generated modules.",
    )
    args = parser.parse_args()
    generate(args.spec, args.output)


if __name__ == "__main__":
    main()
