# Generated from packages/schema/schemas by scripts/codegen_python.py. Do not edit.

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any

from pydantic import AnyUrl, AwareDatetime, BaseModel, ConfigDict, Field, RootModel


class Common(RootModel[Any]):
    root: Annotated[Any, Field(title="Common")]
    """
    Shared definitions used by every Nomi schema.
    """


class Unii(RootModel[str]):
    root: Annotated[str, Field(pattern="^[A-Z0-9]{10}$", title="Unii")]
    """
    FDA Unique Ingredient Identifier: 10 uppercase letters or digits, e.g. 362O9ITL9D (acetaminophen).
    """


class Persona(StrEnum):
    """
    Type of person a score is for. The list is owned by docs/scoring/dimensions.md (NOMI-016).
    """

    adult_18_64 = "adult_18_64"
    adult_65_plus = "adult_65_plus"
    teen_12_17 = "teen_12_17"
    child_6_11 = "child_6_11"
    child_2_5 = "child_2_5"
    under_2 = "under_2"
    pregnant = "pregnant"
    breastfeeding = "breastfeeding"


class Dimension(StrEnum):
    """
    Risk dimension every ingredient is rated on. The list is owned by docs/scoring/dimensions.md (NOMI-016).
    """

    liver = "liver"
    gi_bleeding = "gi_bleeding"
    cardiovascular_bp = "cardiovascular_bp"
    kidney = "kidney"
    anticholinergic_cognitive = "anticholinergic_cognitive"
    sedation_falls = "sedation_falls"
    serotonergic_interactions = "serotonergic_interactions"
    anticoagulant_bleeding = "anticoagulant_bleeding"
    pediatric = "pediatric"
    rebound_overuse = "rebound_overuse"
    pregnancy_lactation = "pregnancy_lactation"
    duplicate_dosing = "duplicate_dosing"
    excipients = "excipients"
    local_skin = "local_skin"
    efficacy_evidence = "efficacy_evidence"


class Condition(StrEnum):
    """
    Health condition a user can add to their profile. The list is owned by docs/scoring/dimensions.md (NOMI-016).
    """

    hypertension = "hypertension"
    heart_disease = "heart_disease"
    kidney_disease = "kidney_disease"
    liver_disease = "liver_disease"
    stomach_ulcer_or_bleeding = "stomach_ulcer_or_bleeding"
    glaucoma = "glaucoma"
    enlarged_prostate = "enlarged_prostate"
    asthma = "asthma"
    diabetes = "diabetes"
    thyroid_disease = "thyroid_disease"
    phenylketonuria = "phenylketonuria"
    heavy_alcohol_use = "heavy_alcohol_use"


class MedicationType(StrEnum):
    """
    Type of medication a user already takes. The list is owned by docs/scoring/dimensions.md (NOMI-016).
    """

    anticoagulants = "anticoagulants"
    antiplatelets = "antiplatelets"
    maoi = "maoi"
    ssri_snri = "ssri_snri"
    sedatives = "sedatives"
    diuretics = "diuretics"
    blood_pressure_medications = "blood_pressure_medications"
    corticosteroids = "corticosteroids"


class Tier(StrEnum):
    """
    Color band shown with a score.
    """

    green = "green"
    yellow = "yellow"
    red = "red"


class ReviewStatus(StrEnum):
    """
    How much human review a value has had.
    """

    unreviewed = "unreviewed"
    preliminary = "preliminary"
    sampled_ok = "sampled_ok"
    pharmacist_reviewed = "pharmacist_reviewed"


class CitationSource(StrEnum):
    """
    Kind of source a value comes from.
    """

    fda_label = "fda_label"
    otc_monograph = "otc_monograph"
    stopp_start = "stopp_start"
    acb = "acb"
    faers = "faers"
    publication = "publication"
    pharmacist_review = "pharmacist_review"


class Citation(BaseModel):
    """
    Where a value comes from, specific enough that a pharmacist can check it.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    source: CitationSource
    document_id: Annotated[str, Field(min_length=1)]
    """
    Identifier of the document, e.g. an SPL set id, a monograph id, or a DOI.
    """
    section: str | None = None
    """
    Section within the document, e.g. 'Warnings' or 'Table 2'.
    """
    url: AnyUrl | None = None
    """
    Link to the source.
    """
    quote: Annotated[str | None, Field(max_length=500)] = None
    """
    Short exact quote supporting the value.
    """


class CitationId(RootModel[str]):
    root: Annotated[str, Field(pattern="^cit_[a-z0-9_]+$", title="CitationId")]
    """
    Key into a citations map, e.g. cit_acetaminophen_liver_warning.
    """


class Provenance(BaseModel):
    """
    Which data and code produced a file or record.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    dataset_version: Annotated[str, Field(min_length=1)]
    """
    Dataset release, e.g. 2026.11.0.
    """
    rubric_version: Annotated[str, Field(min_length=1)]
    """
    Rubric or model version used for scoring, e.g. rubric-v0.1.
    """
    code_commit: Annotated[str, Field(pattern="^[0-9a-f]{7,40}$")]
    """
    Git commit of the pipeline code.
    """
    generated_at: AwareDatetime
    """
    When the file or record was produced.
    """
