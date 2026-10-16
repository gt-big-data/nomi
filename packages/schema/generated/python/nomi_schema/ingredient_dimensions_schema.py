# Generated from packages/schema/schemas by scripts/codegen_python.py. Do not edit.

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from . import common_schema


class Rating(BaseModel):
    """
    Severity of this ingredient on one dimension for one persona. A non-zero severity needs at least one citation.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    dimension: common_schema.Dimension
    persona: common_schema.Persona
    severity: Annotated[int, Field(ge=0, le=3, title="Severity")]
    """
    Risk severity of one ingredient on one dimension for one persona: 0 none, 1 low, 2 moderate, 3 high.
    """
    citations: list[common_schema.Citation] | None = None
    """
    Sources for this rating. Required when severity is above 0.
    """


class Modifier(BaseModel):
    """
    Severity change on one dimension when the user has a condition or takes a medication type. Exactly one of condition or medication_type. Always needs a citation.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    dimension: common_schema.Dimension
    condition: common_schema.Condition | None = None
    medication_type: common_schema.MedicationType | None = None
    personas: list[common_schema.Persona] | None = None
    """
    Personas the modifier applies to. Omit to apply to all.
    """
    severity_change: Annotated[int, Field(ge=1, le=3)]
    """
    Change in severity, e.g. 1 means one level higher. Results are capped at 3.
    """
    citations: Annotated[list[common_schema.Citation], Field(min_length=1)]
    """
    Sources for this modifier.
    """


class IngredientDimensions(BaseModel):
    """
    Knowledge base entry for one ingredient: its severity on each risk dimension per persona, and how conditions or other medications change it. One file per ingredient in pipeline/knowledge/ingredients/ (NOMI-034, NOMI-035).
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    unii: Annotated[str, Field(pattern="^[A-Z0-9]{10}$", title="Unii")]
    """
    FDA Unique Ingredient Identifier: 10 uppercase letters or digits, e.g. 362O9ITL9D (acetaminophen).
    """
    name: Annotated[str, Field(min_length=1)]
    """
    Ingredient name, e.g. 'naproxen sodium'.
    """
    ratings: Annotated[list[Rating], Field(min_length=1)]
    """
    Severity per dimension and persona. Write 0 explicitly where a dimension was considered and has no risk.
    """
    modifiers: list[Modifier]
    """
    Adjustments that apply when the user has a condition or takes a type of medication.
    """
    review_status: common_schema.ReviewStatus | None = None
    notes: str | None = None
    """
    Free-text notes for reviewers. Never shown to users.
    """
