"""Resolve barcodes to products and measure coverage (NOMI-025).

Reads the bronze NDC directory (NOMI-009) and DailyMed label tables (NOMI-010); see
pipeline/docs/identity.md.
"""

from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import polars as pl

from nomi_pipeline.identity.barcode import Status as ParseStatus
from nomi_pipeline.identity.barcode import ndc_candidates

Row = dict[str, Any]
Status = (
    ParseStatus
    | Literal[
        "resolved",
        "homeopathic",
        "not_found",
        "ambiguous_ndc",
        "missing_label",
        "ambiguous_label",
        "label_mismatch",
        "missing_ingredients",
        "kit",
        "invalid_ingredients",
        "ingredient_conflict",
        "missing_name",
    ]
)

# Homeopathic products are shown as "not evaluated by FDA" and not scored (docs/system-design.md
# 5.2). Their labels are not in DailyMed's OTC download, so they are identified from the directory
# alone and reported apart from the scored packages.
HOMEOPATHIC = "UNAPPROVED HOMEOPATHIC"
# docs/system-design.md 5.2 and 8: 95% or higher of generated barcodes resolve correctly.
TARGET = 0.95
INGREDIENT_FIELDS = ("unii", "name", "strength", "unit", "per_amount", "per_unit")
MARKETING_CATEGORIES = {
    "otc_monograph_drug",
    "otc_monograph_final",
    "otc_monograph_not_final",
    "nda",
    "nda_authorized_generic",
    "anda",
    "bla",
    "unapproved_homeopathic",
    "unapproved_drug_other",
}


def package_codes(ndc_raw: str) -> tuple[str, str]:
    """Return the NDC11 and the UPC-A barcode for a dashed package NDC10.

    The dashes are required: NDC11 padding cannot be undone without knowing the layout.
    """
    parts = ndc_raw.split("-")
    if tuple(map(len, parts)) not in {(4, 4, 2), (5, 3, 2), (5, 4, 1)}:
        raise ValueError(f"Expected a dashed NDC10, got {ndc_raw!r}")
    if not all(part.isascii() and part.isdigit() for part in parts):
        raise ValueError(f"Invalid NDC digits: {ndc_raw!r}")
    ndc11 = "".join(part.zfill(width) for part, width in zip(parts, (5, 4, 2), strict=True))
    body = "3" + "".join(parts)
    total = sum(map(int, body[::2])) * 3 + sum(map(int, body[1::2]))
    return ndc11, body + str(-total % 10)


def marketing_category(value: str | None) -> str:
    """The directory's category as the product schema's enum value."""
    key = (value or "").lower().replace(" ", "_")
    return key if key in MARKETING_CATEGORIES else "other"


@dataclass(frozen=True)
class Resolution:
    status: Status
    matches: tuple[str, ...] = ()
    product: Row | None = field(default=None, compare=False)


class Resolver:
    """Looks up barcodes; never picks arbitrarily between two possible products.

    `ingredients` holds the active-ingredient rows of spl_ingredients. Bronze keeps one version of
    each label, so (spl_set_id, product_index) names one label product.
    """

    def __init__(
        self, ndc: Iterable[Row], products: Iterable[Row], ingredients: Iterable[Row]
    ) -> None:
        self.directory: dict[str, Row] = {}
        # The 10 digits printed in a barcode -> the NDC11s of real packages with those digits.
        # Two different NDC10s can pad to one NDC11 (12345-0678-9 and 12345-678-09), so a
        # package only matches a scan when its own digits are the scanned ones.
        self.packages: dict[str, set[str]] = defaultdict(set)
        for row in ndc:
            if self.directory.setdefault(row["ndc11"], row) is row:
                self.packages[digits(row.get("ndc_raw"))].add(row["ndc11"])
        # One label product can list many packages; one package can appear on more than one label.
        self.labels: dict[tuple[str, str], list[Row]] = defaultdict(list)
        for row in products:
            entry = {k: row[k] for k in ("spl_set_id", "spl_version", "product_index")}
            key = (digits(row.get("ndc_raw")), row["ndc11"])
            if entry not in self.labels[key]:
                self.labels[key].append(entry)
                self.packages[key[0]].add(row["ndc11"])
        self.ingredients: dict[tuple[str, int], list[Row]] = defaultdict(list)
        for row in ingredients:
            self.ingredients[(row["spl_set_id"], row["product_index"])].append(row)

    def resolve(self, barcode: str) -> Resolution:
        parsed = ndc_candidates(barcode)
        if parsed["status"] != "ok":
            return Resolution(parsed["status"])
        # The 4-4-2 candidate is "0" + the scanned 10 digits.
        scanned = parsed["candidates"][0][1:]
        # A real package, in the directory or on any label, whose own digits were scanned. A box
        # that is only on a label must not resolve to a directory package with other digits.
        matches = tuple(sorted(self.packages.get(scanned, set())))
        if len(matches) > 1:
            return Resolution("ambiguous_ndc", matches)
        if not matches:
            return Resolution("not_found")
        ndc11 = matches[0]
        listing = self.directory.get(ndc11)
        if listing is None or digits(listing.get("ndc_raw")) != scanned:
            return Resolution("not_found", matches)
        set_id = listing.get("spl_set_id")

        labels = self.labels.get((scanned, ndc11), [])
        if set_id is not None and labels:
            # The directory names the package's label; never accept or pick a different one.
            chosen = [label for label in labels if label["spl_set_id"] == set_id]
            if not chosen:
                return Resolution("label_mismatch", matches)
            labels = chosen
        if len(labels) > 1:
            return Resolution("ambiguous_label", matches)
        if not labels:
            if listing.get("marketing_category") == HOMEOPATHIC:
                return Resolution("homeopathic", matches)
            return Resolution("missing_label", matches)
        label = labels[0]

        active = self.ingredients.get((label["spl_set_id"], label["product_index"]), [])
        if not active:
            return Resolution("missing_ingredients", matches)
        if any(item.get("part_index") is not None for item in active):
            # Kits list ingredients per part; the product record has no place for parts yet.
            return Resolution("kit", matches)
        ingredients = sorted(
            ({k: item.get(k) for k in INGREDIENT_FIELDS} for item in active),
            key=lambda item: (item["unii"] or "", item["name"] or ""),
        )
        if not all(valid_ingredient(item) for item in ingredients):
            # Bad strengths must never pass as a resolved product.
            return Resolution("invalid_ingredients", matches)
        listed = listing.get("active_ingredients")
        if listed is not None and len(listed) != len(ingredients):
            # The label and the directory disagree on what is in the box. On today's data every case
            # is an ingredient name containing ";", which openFDA's directory splits in two.
            return Resolution("ingredient_conflict", matches)

        if not (listing.get("brand_name") and listing.get("generic_name")):
            # The product schema requires both names.
            return Resolution("missing_name", matches)
        product: Row = {
            "ndc11": ndc11,
            "spl_set_id": label["spl_set_id"],
            "spl_version": label["spl_version"],
            "brand_name": listing.get("brand_name"),
            "generic_name": listing.get("generic_name"),
            "labeler": listing.get("labeler_name"),
            "dosage_form": listing.get("dosage_form"),
            "marketing_category": marketing_category(listing.get("marketing_category")),
            "ingredients": ingredients,
        }
        return Resolution("resolved", matches, product)


def digits(ndc_raw: str | None) -> str:
    return (ndc_raw or "").replace("-", "")


def positive(value: Any) -> bool:
    return (
        isinstance(value, int | float) and not isinstance(value, bool) and 0 < value < float("inf")
    )


def valid_ingredient(item: Row) -> bool:
    """The product schema's rules for an active ingredient."""
    if not (item["unii"] and item["name"] and item["unit"] and positive(item["strength"])):
        return False
    if item["per_amount"] is None and item["per_unit"] is None:
        return True
    return positive(item["per_amount"]) and bool(item["per_unit"])


def evaluate(resolver: Resolver) -> tuple[list[Row], list[Row]]:
    """Build a barcode for every directory package and resolve it, keeping every miss.

    Sample packages are skipped: they are not sold.
    """
    products: list[Row] = []
    results: list[Row] = []
    for expected in sorted(resolver.directory):
        listing = resolver.directory[expected]
        if listing.get("sample"):
            continue
        result: Row = {
            "ndc_raw": listing["ndc_raw"],
            "expected_ndc11": expected,
            "barcode": None,
            "status": "invalid_package_ndc",
            "matches": [],
            "marketing_category": listing.get("marketing_category"),
        }
        try:
            normalized, barcode = package_codes(listing["ndc_raw"])
        except ValueError:
            results.append(result)
            continue
        result["barcode"] = barcode
        if normalized != expected:
            result["status"] = "ndc_mismatch"
            results.append(result)
            continue
        # The package's own NDC is always a candidate, so a single match is that package.
        resolved = resolver.resolve(barcode)
        result["status"] = resolved.status
        result["matches"] = list(resolved.matches)
        if resolved.product is not None:
            products.append(resolved.product)
        results.append(result)
    return products, results


def is_homeopathic(row: Row) -> bool:
    return bool(row["marketing_category"] == HOMEOPATHIC)


def coverage(results: list[Row]) -> tuple[int, int]:
    """Resolved and total among the packages Nomi scores (not homeopathic)."""
    scored = [r for r in results if not is_homeopathic(r)]
    return sum(r["status"] == "resolved" for r in scored), len(scored)


def miss_table(rows: list[Row]) -> list[str]:
    lines = [
        "| Package NDC | Expected NDC11 | Barcode | Status | Matches |",
        "| --- | --- | --- | --- | --- |",
    ]
    lines += [
        f"| {r['ndc_raw']} | {r['expected_ndc11']} | {r['barcode'] or '-'} | {r['status']} "
        f"| {', '.join(r['matches'])} |"
        for r in rows
    ]
    return lines


def coverage_report(results: list[Row]) -> str:
    correct, total = coverage(results)
    rate = correct / total if total else 0.0
    found = sum(r["status"] in {"resolved", "homeopathic"} for r in results)
    full = sum(r["status"] == "resolved" for r in results)
    scored = Counter(r["status"] for r in results if not is_homeopathic(r))
    homeopathic = Counter(r["status"] for r in results if is_homeopathic(r))
    lines = [
        "# Identity coverage",
        "",
        "Generated by `uv run pipeline identity resolve`. Each package in the NDC directory gets the",
        "barcode it would carry (`3` + NDC10 + check digit), which is then resolved like a scan.",
        "Sample packages are left out. This measures the lookup, not real-world box scans.",
        "",
        "A scored package resolves when it is the only package, in the directory or on the labels,",
        "whose own NDC has the barcode's 10 digits, its label is the one the directory names (or,",
        "when the directory names none, the only label listing it), it is not a kit, the label's",
        "active ingredients are complete and agree in number with the directory's (when the directory",
        "lists any), and the directory gives a brand and generic name.",
        "",
        f"**Scored packages resolved: {correct} of {total} ({rate:.2%}).** "
        f"Target {TARGET:.0%}: {'met' if total and rate >= TARGET else 'not met'}.",
        "",
        "Homeopathic products are not scored, so they are counted apart. Counting them as found when",
        "the directory identifies them, all packages: "
        f"{found} of {len(results)} ({found / len(results) if results else 0:.2%}). "
        "With a full product record (label and ingredients), all packages: "
        f"{full} of {len(results)} ({full / len(results) if results else 0:.2%}).",
        "",
        "| Status | Scored packages | Homeopathic packages |",
        "| --- | ---: | ---: |",
    ]
    lines += [
        f"| {status} | {scored[status]} | {homeopathic[status]} |"
        for status in sorted(scored.keys() | homeopathic.keys())
    ]
    lines += ["", "## Every scored miss", ""]
    lines += miss_table([r for r in results if not is_homeopathic(r) and r["status"] != "resolved"])
    lines += ["", "## Every homeopathic miss", ""]
    lines += miss_table(
        [r for r in results if is_homeopathic(r) and r["status"] not in {"resolved", "homeopathic"}]
    )
    return "\n".join(lines) + "\n"


PRODUCT_SCHEMA: dict[str, Any] = {
    "ndc11": pl.String,
    "spl_set_id": pl.String,
    "spl_version": pl.Int64,
    "brand_name": pl.String,
    "generic_name": pl.String,
    "labeler": pl.String,
    "dosage_form": pl.String,
    "marketing_category": pl.String,
    "ingredients": pl.List(
        pl.Struct(
            {
                "unii": pl.String,
                "name": pl.String,
                "strength": pl.Float64,
                "unit": pl.String,
                "per_amount": pl.Float64,
                "per_unit": pl.String,
            }
        )
    ),
}
RESULT_SCHEMA: dict[str, Any] = {
    "ndc_raw": pl.String,
    "expected_ndc11": pl.String,
    "barcode": pl.String,
    "status": pl.String,
    "matches": pl.List(pl.String),
    "marketing_category": pl.String,
}


def build_identity(bronze_dir: Path, silver_dir: Path, report: Path) -> tuple[int, int]:
    """Write product.parquet, identity_results.parquet and the coverage report.

    Returns resolved and total scored packages, for the coverage target.
    """
    ndc = pl.read_parquet(bronze_dir / "ndc.parquet").to_dicts()
    labels = pl.read_parquet(bronze_dir / "spl_products.parquet").to_dicts()
    ingredients = (
        pl.read_parquet(bronze_dir / "spl_ingredients.parquet")
        .filter(pl.col("role") == "active")
        .to_dicts()
    )
    products, results = evaluate(Resolver(ndc, labels, ingredients))
    silver_dir.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(products, schema=PRODUCT_SCHEMA).write_parquet(silver_dir / "product.parquet")
    pl.DataFrame(results, schema=RESULT_SCHEMA).write_parquet(
        silver_dir / "identity_results.parquet"
    )
    report.write_text(coverage_report(results), encoding="utf-8")
    return coverage(results)
