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
valid samples into the Pydantic models, and type-checks the TypeScript. CI also fails if the generated
files don't match the schemas, so always run `codegen` and commit the result after editing a schema.

## Changing a schema

1. Edit the file in `schemas/`. Give every new field a `description`.
2. Update the valid sample in `fixtures/schema-samples/valid/` and add an invalid sample if you added a rule.
3. Run `pnpm run codegen` and `pnpm run test`.
4. Commit the schema, samples and generated files together.
