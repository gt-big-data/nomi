import json
import zipfile
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

from nomi_pipeline.ingest._ndc import normalize_ndc


class NdcParseError(Exception):
    """Raised when the NDC directory file cannot be parsed."""


def _read_json_text(path: Path) -> str:
    if not path.name.endswith(".zip"):
        return path.read_text()
    with zipfile.ZipFile(path) as z:
        members = [n for n in z.namelist() if n.endswith(".json")]
        if len(members) != 1:
            raise NdcParseError(f"{path.name}: expected one .json file, found {len(members)}")
        return z.read(members[0]).decode()


@dataclass
class NdcRow:
    product_ndc: str
    ndc11: str
    ndc_raw: str
    brand_name: str
    generic_name: str
    labeler_name: str
    dosage_form: str
    marketing_category: str
    route: str
    spl_id: str
    spl_set_id: str | None
    # Fallback for identity resolution when a product has no spl_set_id.
    active_ingredients: list[str]
    active_strengths: list[str]
    package_description: str
    marketing_end_date: str | None
    sample: bool


@dataclass
class NdcResult:
    products: list[NdcRow] = field(default_factory=list)
    skipped_bad_ndc: int = 0
    bad_ndcs: list[str] = field(default_factory=list)
    skipped_unfinished: int = 0
    records_without_packages: int = 0
    duplicate_ndcs: int = 0
    total_records: int = 0


def dedupe_and_sort(result: NdcResult) -> None:
    """Sort by ndc11 and keep one row per ndc11, so the table is keyed by NDC.

    openFDA occasionally lists one package under two records that differ only in dates.
    """
    result.products.sort(key=lambda row: (row.ndc11, row.product_ndc, row.spl_id))
    unique: list[NdcRow] = []
    for row in result.products:
        if unique and unique[-1].ndc11 == row.ndc11:
            result.duplicate_ndcs += 1
            continue
        unique.append(row)
    result.products = unique


def parse_ndc_file(path: Path) -> NdcResult:
    """Parse an openFDA NDC JSON file, or the .json.zip that pipeline fetch delivers."""
    try:
        data = json.loads(_read_json_text(path))
    except (json.JSONDecodeError, zipfile.BadZipFile) as e:
        raise NdcParseError(f"{path.name}: invalid JSON ({e})") from e

    records = data.get("results")
    if records is None:
        raise NdcParseError(f"{path.name}: missing 'results' key")

    result = NdcResult()

    for record in records:
        result.total_records += 1
        if record.get("product_type") != "HUMAN OTC DRUG":
            continue
        # Unfinished records are bulk ingredients, never sold to a shopper.
        if record.get("finished") is False:
            result.skipped_unfinished += 1
            continue
        if not record.get("packaging"):
            result.records_without_packages += 1
            continue

        openfda = record.get("openfda", {})
        spl_set_ids = openfda.get("spl_set_id", [])
        if spl_set_ids:  # noqa: SIM108
            spl_set_id = spl_set_ids[0]
        else:
            spl_set_id = None

        route = ", ".join(record.get("route", []))
        ingredients = record.get("active_ingredients", [])

        for package in record.get("packaging", []):
            ndc_raw = package.get("package_ndc")
            if not ndc_raw:
                continue

            try:
                ndc11 = normalize_ndc(ndc_raw)
            except ValueError:
                result.skipped_bad_ndc += 1
                result.bad_ndcs.append(ndc_raw)
                continue

            result.products.append(
                NdcRow(
                    product_ndc=record.get("product_ndc", ""),
                    ndc11=ndc11,
                    ndc_raw=ndc_raw,
                    brand_name=record.get("brand_name", ""),
                    generic_name=record.get("generic_name", ""),
                    labeler_name=record.get("labeler_name", ""),
                    dosage_form=record.get("dosage_form", ""),
                    marketing_category=record.get("marketing_category", ""),
                    route=route,
                    spl_id=record.get("spl_id", ""),
                    spl_set_id=spl_set_id,
                    active_ingredients=[i.get("name", "") for i in ingredients],
                    active_strengths=[i.get("strength", "") for i in ingredients],
                    package_description=package.get("description", ""),
                    marketing_end_date=package.get("marketing_end_date")
                    or record.get("marketing_end_date"),
                    sample=bool(package.get("sample", False)),
                )
            )

    dedupe_and_sort(result)
    return result


def compute_stats(result: NdcResult) -> dict[str, Any]:
    total = len(result.products)
    null_rates = {}
    for f in fields(NdcRow):
        null_count = 0
        for row in result.products:
            value = getattr(row, f.name)
            if value is None or value == "" or value == []:
                null_count += 1

        null_rates[f.name] = null_count / total if total > 0 else 0.0

    return {
        "total_rows": total,
        "total_records_seen": result.total_records,
        "skipped_bad_ndc": result.skipped_bad_ndc,
        "skipped_unfinished": result.skipped_unfinished,
        "records_without_packages": result.records_without_packages,
        "duplicate_ndcs": result.duplicate_ndcs,
        "null_rates": null_rates,
    }
