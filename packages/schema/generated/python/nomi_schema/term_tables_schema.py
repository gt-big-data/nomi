# Generated from packages/schema/schemas by scripts/codegen_python.py. Do not edit.

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from . import common_schema


class TierBands(BaseModel):
    """
    Score thresholds for each tier. Below yellow_min is red.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    green_min: Annotated[int, Field(ge=0, le=100)]
    """
    Lowest score shown as green, e.g. 75.
    """
    yellow_min: Annotated[int, Field(ge=0, le=100)]
    """
    Lowest score shown as yellow, e.g. 50.
    """


class Method(StrEnum):
    """
    'max' takes the largest ingredient's points; 'max_plus_stacking' adds stacking_points for each extra ingredient that scores on the same dimension; 'sum' adds all.
    """

    max = "max"
    max_plus_stacking = "max_plus_stacking"
    sum = "sum"


class Combine(BaseModel):
    """
    How points from several ingredients in one product combine within a dimension.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    method: Method
    """
    'max' takes the largest ingredient's points; 'max_plus_stacking' adds stacking_points for each extra ingredient that scores on the same dimension; 'sum' adds all.
    """
    stacking_points: Annotated[int | None, Field(ge=0)] = None
    """
    Extra points per additional ingredient on the same dimension, for max_plus_stacking.
    """


class Term(BaseModel):
    """
    Points taken off for one ingredient on one dimension for one persona. A row with a condition or medication_type applies only when the profile has it, on top of the base row.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    unii: Annotated[str, Field(pattern="^[A-Z0-9]{10}$", title="Unii")]
    """
    FDA Unique Ingredient Identifier: 10 uppercase letters or digits, e.g. 362O9ITL9D (acetaminophen).
    """
    dimension: common_schema.Dimension
    persona: common_schema.Persona
    condition: common_schema.Condition | None = None
    medication_type: common_schema.MedicationType | None = None
    points: Annotated[int, Field(ge=1, le=100)]
    """
    Points taken off. Rows with 0 points are not exported.
    """
    citation_ids: Annotated[list[common_schema.CitationId], Field(min_length=1)]
    """
    Keys into the citations map.
    """


class Result(StrEnum):
    """
    Tier forced when the rule matches.
    """

    red = "red"


class HardStop(BaseModel):
    """
    A rule that forces the result tier. Matches when the product contains the ingredient and the profile matches every given field.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    id: Annotated[str, Field(pattern="^hs_[a-z0-9_]+$")]
    """
    Stable rule id, e.g. 'hs_salicylate_children'.
    """
    unii: Annotated[str, Field(pattern="^[A-Z0-9]{10}$", title="Unii")]
    """
    FDA Unique Ingredient Identifier: 10 uppercase letters or digits, e.g. 362O9ITL9D (acetaminophen).
    """
    personas: Annotated[list[common_schema.Persona] | None, Field(min_length=1)] = None
    """
    Personas the rule applies to. Omit to apply to all.
    """
    condition: common_schema.Condition | None = None
    medication_type: common_schema.MedicationType | None = None
    result: Result
    """
    Tier forced when the rule matches.
    """
    message_template_id: Annotated[str, Field(min_length=1)]
    """
    Explanation template shown when the rule fires.
    """
    citation_ids: Annotated[list[common_schema.CitationId], Field(min_length=1)]
    """
    Keys into the citations map.
    """


class TermTables(BaseModel):
    """
    The scoring model exported as lookup tables. The phone adds up matching term points for a product and profile, applies hard stops, and computes score = base_score - points (NOMI-051, NOMI-060).
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    model_version: Annotated[str, Field(min_length=1)]
    """
    Version of the exported model, e.g. 'rubric-v0.1'.
    """
    rubric_version: Annotated[str, Field(min_length=1)]
    """
    Version of docs/rubric this export implements, e.g. 'v0'.
    """
    base_score: Annotated[int, Field(ge=1, le=100)]
    """
    Score before any points are taken off. Normally 100.
    """
    tier_bands: TierBands
    combine: Combine
    terms: list[Term]
    """
    Points per ingredient, dimension and persona, plus extra points for conditions and medication types.
    """
    hard_stops: list[HardStop]
    """
    Rules that make a product red regardless of points.
    """
    citations: Annotated[
        dict[
            Annotated[str, StringConstraints(pattern=r"^cit_[a-z0-9_]+$")],
            common_schema.Citation,
        ],
        Field(title="CitationMap"),
    ]
    """
    Citations keyed by citation id, so rows can reference them without repeating them.
    """
    provenance: common_schema.Provenance | None = None
