# Generated from packages/schema/schemas by scripts/codegen_python.py. Do not edit.

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from . import common_schema


class Profile(BaseModel):
    """
    Who the score is for. Lives only on the user's device.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    persona: common_schema.Persona
    conditions: list[common_schema.Condition]
    medication_types: list[common_schema.MedicationType]


class Contribution(BaseModel):
    """
    Points one dimension took off the score, and why.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    dimension: common_schema.Dimension
    points: Annotated[int, Field(ge=1)]
    """
    Points taken off on this dimension.
    """
    ingredient_uniis: list[common_schema.Unii] | None = None
    """
    Ingredients that contributed.
    """
    citations: Annotated[list[common_schema.Citation], Field(min_length=1)]


class TriggeredHardStop(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    id: Annotated[str, Field(pattern="^hs_[a-z0-9_]+$")]
    """
    Hard-stop rule id from the term tables.
    """
    message: Annotated[str, Field(min_length=1)]
    """
    Rendered message shown to the user.
    """


class Benchmark(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    use: Annotated[str, Field(pattern="^[a-z0-9_]+$")]
    """
    Use the product is compared within, e.g. 'pain'.
    """
    percentile: Annotated[int, Field(ge=0, le=100)]
    """
    Share of comparable products this one scores better than, 0 to 100.
    """


class Alternative(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    ndc11: Annotated[str, Field(pattern="^[0-9]{11}$", title="Ndc11")]
    """
    National Drug Code normalized to 11 digits with no hyphens, e.g. 50580044902.
    """
    score: Annotated[int, Field(ge=0, le=100)]
    """
    The alternative's score for the same profile.
    """
    shared_use: Annotated[str, Field(pattern="^[a-z0-9_]+$")]
    """
    Use both products share, e.g. 'pain'.
    """
    reason: Annotated[str, Field(min_length=1)]
    """
    One-line reason it's safer for this profile.
    """


class ExplanationLine(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    template_id: Annotated[str, Field(min_length=1)]
    """
    Template the sentence was built from.
    """
    text: Annotated[str, Field(min_length=1)]
    """
    Rendered sentence.
    """
    citations: list[common_schema.Citation]


class ScoreRecord(BaseModel):
    """
    The result of scoring one product for one profile: what the result screen shows and what golden vectors check (NOMI-051, NOMI-057, NOMI-060).
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    ndc11: Annotated[str, Field(pattern="^[0-9]{11}$", title="Ndc11")]
    """
    National Drug Code normalized to 11 digits with no hyphens, e.g. 50580044902.
    """
    profile: Profile
    score: Annotated[int, Field(ge=0, le=100)]
    """
    Safety score from 0 (highest risk) to 100.
    """
    tier: common_schema.Tier
    contributions: list[Contribution]
    """
    Points taken off per dimension, largest first.
    """
    hard_stops_triggered: list[TriggeredHardStop]
    """
    Hard-stop rules that fired. Any entry makes the tier red.
    """
    benchmark: Benchmark | None
    """
    Rank among products with the same use for this profile. Null when there are too few comparable products.
    """
    alternatives: list[Alternative]
    """
    Safer options with a shared use, best first. Empty means 'ask your pharmacist'.
    """
    explanation: list[ExplanationLine]
    """
    Plain-language sentences, each with its sources.
    """
    review_status: common_schema.ReviewStatus
    provenance: common_schema.Provenance
