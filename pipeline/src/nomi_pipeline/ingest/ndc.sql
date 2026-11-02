-- Run from the repo root: duckdb < pipeline/src/nomi_pipeline/ingest/ndc.sql
CREATE VIEW ndc AS SELECT * FROM read_parquet('data/bronze/ndc.parquet');
