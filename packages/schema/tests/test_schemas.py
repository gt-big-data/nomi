"""Check the schemas, their samples, the packaged validator and the generated Pydantic models."""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

import nomi_schema
from nomi_schema import SchemaValidationError, validate

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = ROOT / "schemas"
SAMPLES = ROOT / "fixtures" / "schema-samples"

SCHEMAS = {p.name.removesuffix(".schema.json"): json.loads(p.read_text()) for p in SCHEMA_DIR.glob("*.schema.json")}
DOMAIN_SCHEMAS = sorted(name for name in SCHEMAS if name != "common")
INVALID = sorted((SAMPLES / "invalid").glob("*.json"))


def load(path: Path):
    return json.loads(path.read_text())


@pytest.mark.parametrize("name", sorted(SCHEMAS))
def test_schema_is_valid_draft_2020_12(name):
    Draft202012Validator.check_schema(SCHEMAS[name])


@pytest.mark.parametrize("name", sorted(SCHEMAS))
def test_packaged_schema_matches_source(name):
    packaged = Path(nomi_schema.__file__).parent / "schemas" / f"{name}.schema.json"
    assert json.loads(packaged.read_text()) == SCHEMAS[name], "run pnpm run codegen"


@pytest.mark.parametrize("name", DOMAIN_SCHEMAS)
def test_every_schema_has_valid_and_invalid_samples(name):
    assert (SAMPLES / "valid" / f"{name}.json").exists()
    assert list((SAMPLES / "invalid").glob(f"{name}.*.json")), f"no invalid sample for {name}"


@pytest.mark.parametrize("name", DOMAIN_SCHEMAS)
def test_valid_sample_passes(name):
    validate(name, load(SAMPLES / "valid" / f"{name}.json"))


@pytest.mark.parametrize("path", INVALID, ids=lambda p: p.name.removesuffix(".json"))
def test_invalid_sample_fails(path):
    name = path.name.split(".")[0]
    with pytest.raises(SchemaValidationError) as raised:
        validate(name, load(path))
    assert raised.value.errors


@pytest.mark.parametrize("name", DOMAIN_SCHEMAS)
def test_generated_model_accepts_valid_sample(name):
    model = getattr(nomi_schema, SCHEMAS[name]["title"])
    model.model_validate(load(SAMPLES / "valid" / f"{name}.json"))


def test_unknown_schema_name_is_an_error():
    with pytest.raises(KeyError):
        validate("prodcut", {})
