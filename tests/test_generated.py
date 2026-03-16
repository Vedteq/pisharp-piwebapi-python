"""Tests for the _generated runtime and code generator."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import httpx
import respx

from pisharp_piwebapi._generated.generate import _snake_case, generate
from pisharp_piwebapi._generated.runtime import GeneratedClient

BASE_URL = "https://piserver.example.com/piwebapi"


class TestRuntime:
    def test_get(self):
        with respx.mock:
            respx.get(f"{BASE_URL}/test").mock(
                return_value=httpx.Response(200, json={"result": "ok"})
            )
            client = GeneratedClient(
                httpx.Client(base_url=BASE_URL, headers={"Accept": "application/json"})
            )
            result = client.get("/test")
            assert result == {"result": "ok"}
            client._client.close()

    def test_post_with_json_body(self):
        with respx.mock:
            route = respx.post(f"{BASE_URL}/test").mock(
                return_value=httpx.Response(
                    201,
                    json={"id": 1},
                    headers={"content-type": "application/json"},
                )
            )
            client = GeneratedClient(
                httpx.Client(base_url=BASE_URL, headers={"Accept": "application/json"})
            )
            result = client.post("/test", json={"data": "value"})
            assert result == {"id": 1}
            assert route.called
            client._client.close()

    def test_delete(self):
        with respx.mock:
            respx.delete(f"{BASE_URL}/test/123").mock(return_value=httpx.Response(204))
            client = GeneratedClient(
                httpx.Client(base_url=BASE_URL, headers={"Accept": "application/json"})
            )
            result = client.delete("/test/123")
            assert result is None
            client._client.close()


class TestSnakeCase:
    def test_pascal_case(self):
        assert _snake_case("GetByPath") == "get_by_path"

    def test_camel_case(self):
        assert _snake_case("getByPath") == "get_by_path"

    def test_with_acronym(self):
        assert _snake_case("PIPoint") == "pi_point"

    def test_already_snake(self):
        assert _snake_case("get_value") == "get_value"


class TestCodeGenerator:
    def test_generate_from_minimal_spec(self):
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {
                "/points": {
                    "get": {
                        "tags": ["Point"],
                        "operationId": "Point_GetByPath",
                        "summary": "Get a point by path.",
                        "parameters": [
                            {
                                "name": "path",
                                "in": "query",
                                "required": True,
                                "schema": {"type": "string"},
                            }
                        ],
                    }
                },
                "/points/{webId}": {
                    "get": {
                        "tags": ["Point"],
                        "operationId": "Point_Get",
                        "summary": "Get a point.",
                        "parameters": [
                            {
                                "name": "webId",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"},
                            }
                        ],
                    }
                },
                "/streams/{webId}/value": {
                    "get": {
                        "tags": ["Stream"],
                        "operationId": "Stream_GetValue",
                        "summary": "Get current value.",
                        "parameters": [
                            {
                                "name": "webId",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"},
                            }
                        ],
                    },
                    "post": {
                        "tags": ["Stream"],
                        "operationId": "Stream_UpdateValue",
                        "summary": "Update value.",
                        "parameters": [
                            {
                                "name": "webId",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"},
                            }
                        ],
                    },
                },
            },
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            spec_path = Path(tmpdir) / "spec.json"
            spec_path.write_text(json.dumps(spec))
            out_dir = Path(tmpdir) / "output"

            generate(str(spec_path), str(out_dir))

            # Verify structure
            assert (out_dir / "__init__.py").exists()
            assert (out_dir / "point.py").exists()
            assert (out_dir / "stream.py").exists()

            # Verify content
            point_src = (out_dir / "point.py").read_text()
            assert "def point_get_by_path(" in point_src
            assert "def point_get(" in point_src

            stream_src = (out_dir / "stream.py").read_text()
            assert "def stream_get_value(" in stream_src
            assert "def stream_update_value(" in stream_src
