# Identity coverage

Status: **not yet measured on the full OTC directory**.

NOMI-009 and NOMI-010 bronze outputs are not available on the checked-out main
branch. No full-data coverage percentage or 90% acceptance claim can be made yet.

Generate this report with `uv run pipeline identity resolve` after the upstream
owners agree the interfaces in `pipeline/docs/identity.md` and provide the data.
The generated report includes correct/total counts and every missed package;
`data/silver/identity_results.parquet` includes all package outcomes.

Fixture tests verify the resolver and failure accounting, not real-data coverage.
