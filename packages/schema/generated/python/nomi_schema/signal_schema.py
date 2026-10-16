# Generated from packages/schema/schemas by scripts/codegen_python.py. Do not edit.

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from . import common_schema


class AgeBand(StrEnum):
    """
    Patient age band in years. 'all' is the unstratified total.
    """

    field_0_11 = "0-11"
    field_12_17 = "12-17"
    field_18_64 = "18-64"
    field_65_ = "65+"
    all = "all"


class Sex(StrEnum):
    """
    Patient sex as reported. 'all' is the unstratified total.
    """

    F = "F"
    M = "M"
    all = "all"


class Signal(BaseModel):
    """
    One row of FAERS disproportionality evidence for an ingredient on a risk dimension, within an age band and sex (NOMI-053). IC025 above 0 counts as a signal.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    unii: Annotated[str, Field(pattern="^[A-Z0-9]{10}$", title="Unii")]
    """
    FDA Unique Ingredient Identifier: 10 uppercase letters or digits, e.g. 362O9ITL9D (acetaminophen).
    """
    dimension: common_schema.Dimension
    event_group: Annotated[str | None, Field(pattern="^[a-z0-9_]+$")] = None
    """
    MedDRA event group behind the dimension, e.g. 'hepatic_disorders'.
    """
    age_band: AgeBand
    """
    Patient age band in years. 'all' is the unstratified total.
    """
    sex: Sex
    """
    Patient sex as reported. 'all' is the unstratified total.
    """
    ic: float
    """
    Information component: log2((observed + 0.5) / (expected + 0.5)).
    """
    ic025: float
    """
    Lower end of the 95% credibility interval for IC.
    """
    report_count: Annotated[int, Field(ge=0)]
    """
    Reports with both the ingredient and the event group (observed).
    """
    expected_count: Annotated[float | None, Field(ge=0.0)] = None
    """
    Reports expected if ingredient and event were unrelated.
    """
