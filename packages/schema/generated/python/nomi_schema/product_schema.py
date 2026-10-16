# Generated from packages/schema/schemas by scripts/codegen_python.py. Do not edit.

from __future__ import annotations

from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, RootModel

from . import common_schema


class MarketingCategory(StrEnum):
    """
    How the product is legally sold, from the NDC directory.
    """

    otc_monograph_drug = "otc_monograph_drug"
    otc_monograph_final = "otc_monograph_final"
    otc_monograph_not_final = "otc_monograph_not_final"
    nda = "nda"
    nda_authorized_generic = "nda_authorized_generic"
    anda = "anda"
    bla = "bla"
    unapproved_homeopathic = "unapproved_homeopathic"
    unapproved_drug_other = "unapproved_drug_other"
    other = "other"


class Use(RootModel[str]):
    root: Annotated[str, Field(pattern="^[a-z0-9_]+$")]


class Scope(StrEnum):
    """
    Whether Nomi scores this product. Homeopathic products are shown but not scored.
    """

    in_scope = "in_scope"
    homeopathic = "homeopathic"
    out_of_scope = "out_of_scope"


class ActiveIngredient(BaseModel):
    """
    One active ingredient and its strength, e.g. 500 mg, or 650 mg per 30 mL for liquids.
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
    Ingredient name as on the label, e.g. 'acetaminophen'.
    """
    strength: Annotated[float, Field(gt=0.0)]
    """
    Amount of the ingredient, e.g. 500.
    """
    unit: Annotated[str, Field(min_length=1)]
    """
    Unit of strength, e.g. 'mg'.
    """
    per_amount: Annotated[float | None, Field(gt=0.0)] = None
    """
    For liquids and similar forms: the amount the strength is per, e.g. 30.
    """
    per_unit: Annotated[str | None, Field(min_length=1)] = None
    """
    Unit of per_amount, e.g. 'mL'.
    """


class InactiveIngredient(BaseModel):
    """
    One inactive ingredient. UNII may be missing on some labels.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    unii: Annotated[str | None, Field(pattern="^[A-Z0-9]{10}$", title="Unii")] = None
    """
    FDA Unique Ingredient Identifier: 10 uppercase letters or digits, e.g. 362O9ITL9D (acetaminophen).
    """
    name: Annotated[str, Field(min_length=1)]
    """
    Ingredient name as on the label, e.g. 'FD&C red no. 40'.
    """


class Product(BaseModel):
    """
    One OTC product package, identified by its NDC. Produced by the identity stage (NOMI-025, NOMI-026); read by scoring and the app.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    ndc11: Annotated[str, Field(pattern="^[0-9]{11}$", title="Ndc11")]
    """
    National Drug Code normalized to 11 digits with no hyphens, e.g. 50580044902.
    """
    spl_set_id: UUID
    """
    DailyMed label set id, stable across label versions.
    """
    spl_version: Annotated[int, Field(ge=1)]
    """
    DailyMed label version number.
    """
    brand_name: Annotated[str, Field(min_length=1)]
    """
    Name on the box, e.g. 'Tylenol Extra Strength'.
    """
    generic_name: Annotated[str, Field(min_length=1)]
    """
    Generic name of the active ingredients, e.g. 'acetaminophen'.
    """
    labeler: str | None = None
    """
    Company that markets the product.
    """
    dosage_form: str | None = None
    """
    Dosage form from the NDC directory, e.g. 'TABLET, COATED'.
    """
    marketing_category: MarketingCategory
    """
    How the product is legally sold, from the NDC directory.
    """
    otc_category: Annotated[str | None, Field(pattern="^[a-z0-9_]+$")]
    """
    Our OTC grouping, e.g. 'internal_analgesics' or 'antacids' (values assigned in NOMI-026). Null for out-of-scope products.
    """
    uses: list[Use]
    """
    Consumer uses from the label, e.g. ['pain', 'fever'] (taxonomy in NOMI-047).
    """
    scope: Scope
    """
    Whether Nomi scores this product. Homeopathic products are shown but not scored.
    """
    ingredients: Annotated[list[ActiveIngredient], Field(min_length=1)]
    """
    Active ingredients with strengths.
    """
    inactive_ingredients: list[InactiveIngredient] | None = None
    """
    Inactive ingredients, used for allergen and excipient checks.
    """
    review_status: common_schema.ReviewStatus | None = None
