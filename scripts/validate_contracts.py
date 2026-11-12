#!/usr/bin/env python3
"""Validate repository JSON Schemas and the OpenAPI document."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema.validators import validator_for
from openapi_spec_validator import validate

ROOT = Path(__file__).resolve().parents[1]
HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}


def validate_route_drift(openapi: dict) -> None:
    """Fail when the checked-in contract and FastAPI expose different operations."""
    from tradepilot.api import create_app

    ignored = {"/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}
    implemented = {
        (route.path, method.lower())
        for route in create_app().routes
        if route.path not in ignored
        for method in getattr(route, "methods", set())
        if method.lower() in HTTP_METHODS
    }
    documented = {
        (path, method.lower())
        for path, operations in openapi["paths"].items()
        for method in operations
        if method.lower() in HTTP_METHODS
    }
    if implemented != documented:
        missing = sorted(implemented - documented)
        extra = sorted(documented - implemented)
        raise SystemExit(f"OpenAPI route drift: undocumented={missing}, nonexistent={extra}")


def main() -> None:
    schemas = sorted((ROOT / "schemas").glob("*.schema.json"))
    if not schemas:
        raise SystemExit("No JSON schemas found")

    for path in schemas:
        document = json.loads(path.read_text(encoding="utf-8"))
        validator_for(document).check_schema(document)
        print(f"valid JSON Schema: {path.relative_to(ROOT)}")

    openapi_path = ROOT / "docs" / "api" / "openapi.yaml"
    openapi = yaml.safe_load(openapi_path.read_text(encoding="utf-8"))
    # Relative external schema references are intentional and validated above.
    validate(openapi, base_uri=openapi_path.resolve().as_uri())
    validate_route_drift(openapi)
    print(f"valid OpenAPI: {openapi_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
