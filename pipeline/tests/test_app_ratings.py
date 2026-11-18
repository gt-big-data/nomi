from __future__ import annotations

from nomi_pipeline.build.app_ratings import OUTPUT, render


def test_the_app_ratings_match_the_knowledge_base() -> None:
    assert OUTPUT.read_text(encoding="utf-8") == render(), (
        "Stale: run uv run python -m nomi_pipeline.build.app_ratings"
    )
