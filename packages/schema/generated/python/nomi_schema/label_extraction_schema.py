# Generated from packages/schema/schemas by scripts/codegen_python.py. Do not edit.

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class LabelActiveIngredient(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    name: Annotated[str, Field(min_length=1)]
    strength: str | None
    """
    Strength per unit as printed, e.g. '325 mg'. Null if the label doesn't state one.
    """
    evidence: Annotated[str, Field(min_length=1, title="Evidence")]
    """
    Exact text copied from the label that supports a fact.
    """


class QuotedStatement(BaseModel):
    """
    One condition, situation or medicine the label names, in plain words, with its quote.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    text: Annotated[str, Field(min_length=1)]
    evidence: Annotated[str, Field(min_length=1, title="Evidence")]
    """
    Exact text copied from the label that supports a fact.
    """


class MandatedWarning(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    warning_id: Annotated[str, Field(pattern="^[a-z0-9_]+$")]
    """
    Warning id from pipeline/knowledge/mandated_warnings.yaml and the rule extractor.
    """
    evidence: Annotated[str, Field(min_length=1, title="Evidence")]
    """
    Exact text copied from the label that supports a fact.
    """


class Action(StrEnum):
    do_not_use = "do_not_use"
    ask_doctor = "ask_doctor"


class LabelAgeLimit(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    action: Action
    min_years: Annotated[int | None, Field(ge=0)]
    under_years: Annotated[int, Field(ge=1)]
    evidence: Annotated[str, Field(min_length=1, title="Evidence")]
    """
    Exact text copied from the label that supports a fact.
    """


class LabelMaxDailyDose(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    amount: Annotated[float, Field(gt=0.0)]
    unit: Annotated[str, Field(min_length=1)]
    evidence: Annotated[str, Field(min_length=1, title="Evidence")]
    """
    Exact text copied from the label that supports a fact.
    """


class LabelFacts(BaseModel):
    """
    The nine extracted fields. An empty list means the label has nothing for that field.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    active_ingredients: list[LabelActiveIngredient]
    uses: list[QuotedStatement]
    mandated_warnings: list[MandatedWarning]
    do_not_use: list[QuotedStatement]
    ask_doctor: list[QuotedStatement]
    """
    Conditions that mean asking a doctor before use.
    """
    drug_interactions: list[QuotedStatement]
    """
    Medicines that mean asking a doctor or pharmacist before use.
    """
    age_limits: list[LabelAgeLimit]
    max_daily_doses: list[LabelMaxDailyDose]
    allergens: list[QuotedStatement]


class LabelExtraction(BaseModel):
    """
    Structured facts an LLM pulled from one OTC Drug Facts label (NOMI-032). Every fact quotes the label text it came from, so it can be checked against the rule extractor (NOMI-031) and shown as evidence.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    set_id: Annotated[str, Field(min_length=1)]
    """
    DailyMed SPL set id of the label.
    """
    model_id: Annotated[str, Field(min_length=1)]
    """
    Exact model id that produced the facts, e.g. 'claude-haiku-4-5'.
    """
    prompt_hash: Annotated[str, Field(pattern="^[0-9a-f]{64}$")]
    """
    SHA-256 of the system prompt and output schema sent to the model, so results from different prompts are never mixed.
    """
    extracted_at: AwareDatetime
    """
    When the extraction ran (ISO 8601).
    """
    facts: LabelFacts
