"""Auto-generated API client from PI Web API OpenAPI specification.

This package is populated by running the code generator against
the PI Web API Swagger/OpenAPI spec (available at ``/piwebapi/help/swagger``
on any PI Web API instance).

Usage::

    python -m pisharp_piwebapi._generated.generate \\
        --spec https://your-server/piwebapi/help/swagger \\
        --output src/pisharp_piwebapi/_generated/api/

The generated modules expose low-level, 1-to-1 endpoint wrappers.
For everyday usage, prefer the high-level client in the parent package.
"""

from pisharp_piwebapi._generated.runtime import GeneratedClient

__all__ = ["GeneratedClient"]
