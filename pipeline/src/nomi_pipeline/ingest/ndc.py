import json
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

from nomi_pipeline.ingest._ndc import normalize_ndc


class NdcParseError(Exception):
    """Raised when the NDC directory file cannot be parsed."""


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


@dataclass
class NdcResult:
    products: list[NdcRow] = field(default_factory=list)
    skipped_bad_ndc: int = 0
    total_records: int = 0


def parse_ndc_file(path: Path) -> NdcResult:
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise NdcParseError(f"{path.name}: invalid JSON ({e})") from e

    records = data.get("results")
    if records is None:
        raise NdcParseError(f"{path.name}: missing 'results' key")

    result = NdcResult()

    for record in records:
        result.total_records += 1
        if record.get("product_type") != "HUMAN OTC DRUG":
            continue

        openfda = record.get("openfda", {})
        spl_set_ids = openfda.get("spl_set_id", [])
        if spl_set_ids:  # noqa: SIM108
            spl_set_id = spl_set_ids[0]
        else:
            spl_set_id = None

        route_list = record.get("route", [])
        route = route_list[0] if route_list else ""

        for package in record.get("packaging", []):
            ndc_raw = package.get("package_ndc")
            if not ndc_raw:
                continue

            try:
                ndc11 = normalize_ndc(ndc_raw)
            except ValueError:
                result.skipped_bad_ndc += 1
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
                )
            )

    result.products.sort(key=lambda row: row.ndc11)
    return result


def compute_stats(result: NdcResult) -> dict[str, Any]:
    total = len(result.products)
    null_rates = {}
    for f in fields(NdcRow):
        null_count = 0
        for row in result.products:
            value = getattr(row, f.name)
            if value is None or value == "":
                null_count += 1

        null_rates[f.name] = null_count / total if total > 0 else 0.0

    return {
        "total_rows": total,
        "total_records_seen": result.total_records,
        "skipped_bad_ndc": result.skipped_bad_ndc,
        "null_rates": null_rates,
    }
