"""Load raw sources into typed bronze tables: NDC directory, DailyMed SPL, FAERS, RxNorm (NOMI-009, 010, 023, 024)."""

from nomi_pipeline._stage import placeholder_app

app = placeholder_app("ingest")
