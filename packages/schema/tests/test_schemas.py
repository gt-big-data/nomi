"""Check the schemas, their samples, and that the generated Pydantic models accept valid data."""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

import nomi_schema

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = ROOT / "schemas"
SAMPLES = ROOT / "fixtures" / "schema-samples"

SCHEMAS = {p.name.removesuffix(".schema.json"): json.loads(p.read_text()) for p in SCHEMA_DIR.glob("*.schema.json")}
DOMAIN_SCHEMAS = sorted(name for name in SCHEMAS if name != "common")
REGISTRY = Registry().with_resources(
    (f"{name}.schema.json", Resource.from_contents(schema)) for name, schema in SCHEMAS.items()
)
MODELS = {name: getattr(nomi_schema, SCHEMAS[name]["title"]) for name in DOMAIN_SCHEMAS}


def validator(name: str) -> Draft202012Validator:
    return Draft202012Validator(SCHEMAS[name], registry=REGISTRY, format_checker=FormatChecker())


def load(path: Path):
    return json.loads(path.read_text())


@pytest.mark.parametrize("name", sorted(SCHEMAS))
def test_schema_is_valid_draft_2020_12(name):
    Draft202012Validator.check_schema(SCHEMAS[name])


@pytest.mark.parametrize("name", DOMAIN_SCHEMAS)
def test_every_schema_has_valid_and_invalid_samples(name):
    assert (SAMPLES / "valid" / f"{name}.json").exists()
    assert list((SAMPLES / "invalid").glob(f"{name}.*.json")), f"no invalid sample for {name}"


@pytest.mark.parametrize("name", DOMAIN_SCHEMAS)
def test_valid_sample_passes(name):
    errors = list(validator(name).iter_errors(load(SAMPLES / "valid" / f"{name}.json")))
    assert not errors, [e.message for e in errors]


@pytest.mark.parametrize(
    "path", sorted((SAMPLES / "invalid").glob("*.json")), ids=lambda p: p.name.removesuffix(".json")
)
def test_invalid_sample_fails(path):
    name = path.name.split(".")[0]
    assert list(validator(name).iter_errors(load(path))), f"{path.name} should fail {name}"


@pytest.mark.parametrize("name", DOMAIN_SCHEMAS)
def test_generated_model_accepts_valid_sample(name):
    MODELS[name].model_validate(load(SAMPLES / "valid" / f"{name}.json"))
