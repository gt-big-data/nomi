# Schema samples

Format samples used to test the schemas in `../../schemas/`. They are **not verified drug data**: NDCs use the
fake labeler code `99999` and values are illustrative. Verified reference products live in `../../examples/` (NOMI-015).

- `valid/<schema>.json` must pass its schema.
- `invalid/<schema>.<reason>.json` must fail its schema. The file name says which rule it breaks.
