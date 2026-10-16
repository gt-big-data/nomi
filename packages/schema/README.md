# packages/schema

Shared data contracts between the pipeline and the app (NOMI-002). The JSON Schemas in `schemas/` are
the source of truth. TypeScript types and Pydantic models are generated from them. Changes need review
from both Platform and Data Analysis.

## Schemas

| Schema | What it describes | Written by | Read by |
|---|---|---|---|
| `common` | Shared definitions: NDC11, UNII, persona, risk dimension, condition, medication type, severity, tier, citation, provenance | n/a | All schemas |
| `product` | One OTC product package: NDC, label id, names, marketing category, OTC category, uses, scope, ingredients with strengths | Identity stage (NOMI-025, 026) | Scoring, app |
| `ingredient-dimensions` | One knowledge base file per ingredient: severity per dimension and persona, plus condition and medication modifiers. Every non-zero severity and every modifier needs a citation | Data Analysis (NOMI-034, 035) | Scoring |
| `term-tables` | The scoring model as lookup tables: points per ingredient, dimension and persona, extra points for conditions and medications, hard stops, tier bands, citations | Scoring (NOMI-051) | App scoring engine (NOMI-060) |
| `score-record` | The result of scoring one product for one profile: score, tier, contributions, hard stops, benchmark, alternatives, explanation | App and pipeline | Result screen, golden vectors (NOMI-057) |
| `signal` | One row of FAERS evidence: ingredient, dimension, age band, sex, IC and IC025 | Evidence stage (NOMI-053) | Rating, dashboard |

The persona, dimension, condition and medication type lists are owned by `docs/scoring/dimensions.md`
(NOMI-016). Change them there and here together.

## Folders

| Folder | Contents |
|---|---|
| `schemas/` | JSON Schemas (draft 2020-12). Edit these |
| `generated/ts/` | Generated TypeScript types. Import from `@nomi/schema` or `generated/ts`. Do not edit |
| `generated/python/nomi_schema/` | Generated Pydantic v2 models: `from nomi_schema import Product`. Do not edit |
| `fixtures/schema-samples/` | Format samples: `valid/` must pass, `invalid/` must fail |
| `examples/` | Hand-verified reference products (NOMI-015) |
| `golden/` | Golden scoring vectors checked in Python and TypeScript (NOMI-057) |
| `scripts/` | Code generators |
| `tests/` | Schema, sample and type tests |

## Commands

Run from `packages/schema/`:

```bash
pnpm install && uv sync
```

```bash
pnpm run codegen
```

```bash
pnpm run test
```

`codegen` regenerates both TypeScript and Python. `test` validates the schemas and samples, loads the
valid samples into the Pydantic models, and type-checks the TypeScript. CI (`.github/workflows/schema.yml`)
runs on every PR that touches this folder and also fails if the generated files don't match the
schemas, so always run `codegen` and commit the result after editing a schema.

The CI check only runs when this folder changes, so don't mark it as a required check in branch
protection: PRs that don't touch schemas would wait on it forever.

## Validating data

The Pydantic models and TypeScript types check field names, types and allowed values. They do **not**
check cross-field rules such as "a non-zero severity needs a citation" or "a hard stop targets either
an ingredient or a product". Always validate against the JSON Schema before writing a contract file:

```python
from nomi_schema import validate, SchemaValidationError

validate("ingredient-dimensions", data)  # raises SchemaValidationError listing every problem
```

## Versioning and compatibility

`provenance.schema_version` records which version of these contracts a file was written with (semver).

- **Patch** (0.1.0 to 0.1.1): descriptions, docs, stricter patterns that existing data already meets.
- **Minor** (0.1.0 to 0.2.0): new optional fields, new enum values. Readers built on the old version may
  see values they don't know; the app must ship before datasets use new enum values (set the dataset's
  minimum app version, see `docs/system-design.md` section 7.2).
- **Major** (0.x to 1.0): renamed or removed fields, new required fields, changed meanings. Coordinate
  with every team and bump the dataset's minimum app version.

## Changing a schema

1. Edit the file in `schemas/`. Give every new field a `description`.
2. Update the valid sample in `fixtures/schema-samples/valid/` and add an invalid sample if you added a rule.
3. Run `pnpm run codegen` and `pnpm run test`.
4. Bump `version` in `package.json` and `pyproject.toml` if the change is minor or major.
5. Commit the schema, samples and generated files together.
