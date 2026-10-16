"""Nomi data and scoring pipeline.

Stages run in order: fetch, ingest, identity, extract, evidence, score, build.
Each stage reads and writes Parquet under data/ and is invoked through the `pipeline` CLI.
"""
