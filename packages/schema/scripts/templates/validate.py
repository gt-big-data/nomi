"""Validate data against the Nomi JSON Schemas.

The Pydantic models check types and allowed values, but not cross-field rules such as
"a non-zero severity needs a citation". Call validate() before writing any contract file.

    from nomi_schema import validate
    validate("ingredient-dimensions", data)   # raises SchemaValidationError
"""

import json
from functools import cache
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

_SCHEMA_DIR = files(__package__) / "schemas"


class SchemaValidationError(ValueError):
    """Raised when data does not match a schema. `errors` lists every problem found."""

    def __init__(self, schema: str, errors: list[str]):
        self.schema = schema
        self.errors = errors
        super().__init__(f"{len(errors)} error(s) against {schema}:\n" + "\n".join(errors))


@cache
def _schemas() -> dict[str, dict[str, Any]]:
    return {
        p.name.removesuffix(".schema.json"): json.loads(p.read_text())
        for p in _SCHEMA_DIR.iterdir()
        if p.name.endswith(".schema.json")
    }


@cache
def _validator(schema: str) -> Draft202012Validator:
    schemas = _schemas()
    if schema not in schemas:
        raise KeyError(f"Unknown schema {schema!r}. Known: {sorted(schemas)}")
    registry = Registry().with_resources(
        (f"{name}.schema.json", Resource.from_contents(contents)) for name, contents in schemas.items()
    )
    return Draft202012Validator(schemas[schema], registry=registry, format_checker=FormatChecker())


def errors(schema: str, data: Any) -> list[str]:
    """Return every validation error as 'path: message', or an empty list if valid."""
    found = sorted(_validator(schema).iter_errors(data), key=lambda e: list(e.absolute_path))
    return [f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}" for e in found]


def validate(schema: str, data: Any) -> None:
    """Raise SchemaValidationError if data doesn't match the named schema, e.g. 'product'."""
    problems = errors(schema, data)
    if problems:
        raise SchemaValidationError(schema, problems)
