"""Resolve barcodes to products and measure coverage (NOMI-025).

Reads the bronze NDC directory (NOMI-009) and DailyMed label tables (NOMI-010); see
pipeline/docs/identity.md.
"""

from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import polars as pl

from nomi_pipeline.identity.barcode import ndc_candidates

Row = dict[str, Any]

# Homeopathic products are shown as "not evaluated by FDA" and not scored (docs/system-design.md
# 5.2). Their labels are not in DailyMed's OTC download, so they resolve without ingredients and
# are counted apart from the coverage target.
HOMEOPATHIC = "UNAPPROVED HOMEOPATHIC"
TARGET = 0.9

# Directory fields carried onto the product.
DIRECTORY_FIELDS = (
    "brand_name",
    "generic_name",
    "labeler_name",
    "dosage_form",
    "route",
    "marketing_category",
)


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


@dataclass(frozen=True)
class Resolution:
    status: str
    matches: tuple[str, ...] = ()
    product: Row | None = field(default=None, compare=False)


class Resolver:
    """Looks up barcodes; never picks arbitrarily between two possible products."""

    def __init__(
        self, ndc: Iterable[Row], products: Iterable[Row], ingredients: Iterable[Row]
    ) -> None:
        self.directory: dict[str, Row] = {}
        for row in ndc:
            self.directory.setdefault(row["ndc11"], row)
        # One label product can list many packages; one package can appear on more than one
        # label. Only each label's latest version counts (bronze already keeps just that one).
        rows = list(products)
        latest: dict[str, int] = {}
        for row in rows:
            latest[row["spl_set_id"]] = max(latest.get(row["spl_set_id"], 0), row["spl_version"])
        self.labels: dict[str, list[Row]] = defaultdict(list)
        for row in rows:
            if row["spl_version"] != latest[row["spl_set_id"]]:
                continue
            entry = {
                k: row[k] for k in ("spl_set_id", "spl_version", "product_index", "product_name")
            }
            if entry not in self.labels[row["ndc11"]]:
                self.labels[row["ndc11"]].append(entry)
        self.ingredients: dict[tuple[str, int], list[Row]] = defaultdict(list)
        for row in ingredients:
            if row["role"] == "active":
                self.ingredients[(row["spl_set_id"], row["product_index"])].append(row)

    def resolve(self, barcode: str) -> Resolution:
        parsed = ndc_candidates(barcode)
        if parsed["status"] != "ok":
            return Resolution(parsed["status"])
        matches = tuple(
            sorted(c for c in dict.fromkeys(parsed["candidates"]) if c in self.directory)
        )
        if len(matches) != 1:
            return Resolution("not_found" if not matches else "ambiguous_ndc", matches)
        ndc11 = matches[0]
        listing = self.directory[ndc11]
        product: Row = {"ndc11": ndc11, "ndc_raw": listing["ndc_raw"]}
        product |= {k: listing.get(k) for k in DIRECTORY_FIELDS}

        labels = self.labels.get(ndc11, [])
        if len(labels) > 1:
            # The directory names the package's label; use it to choose, never guess.
            labels = [lab for lab in labels if lab["spl_set_id"] == listing.get("spl_set_id")]
            if len(labels) != 1:
                return Resolution("ambiguous_label", matches)
        if not labels:
            if listing.get("marketing_category") == HOMEOPATHIC:
                return Resolution("homeopathic", matches, product | {"ingredients": []})
            return Resolution("missing_label", matches)
        label = labels[0]
        product |= label

        active = self.ingredients.get((label["spl_set_id"], label["product_index"]), [])
        if not active:
            return Resolution("missing_ingredients", matches)
        if any(item.get("part_index") is not None for item in active):
            # Kits list ingredients per part; the product record has no place for parts yet.
            return Resolution("kit", matches)
        product["ingredients"] = sorted(
            (
                {
                    k: item.get(k)
                    for k in ("unii", "name", "strength", "unit", "per_amount", "per_unit")
                }
                for item in active
            ),
            key=lambda item: (item["unii"] or "", item["name"] or ""),
        )
        if not all(valid_ingredient(item) for item in product["ingredients"]):
            # Bad strengths must never pass as a resolved product.
            return Resolution("invalid_ingredients", matches)
        return Resolution("resolved", matches, product)


def valid_ingredient(item: Row) -> bool:
    strength = item["strength"]
    return (
        bool(item["unii"] and item["name"] and item["unit"])
        and isinstance(strength, int | float)
        and not isinstance(strength, bool)
        and 0 < strength < float("inf")
        and (item["per_amount"] is None) == (item["per_unit"] is None)
    )


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
        resolved = resolver.resolve(barcode)
        result["status"] = resolved.status
        result["matches"] = list(resolved.matches)
        if resolved.product is not None:
            if resolved.product["ndc11"] != expected:
                result["status"] = "wrong_product"
            else:
                # Homeopathic products are kept too, so the app can say they are not evaluated.
                products.append(resolved.product)
        results.append(result)
    return products, results


def coverage(results: list[Row]) -> tuple[int, int]:
    """Correct and total among packages Nomi scores (homeopathic ones are not)."""
    scored = [r for r in results if r["marketing_category"] != HOMEOPATHIC]
    return sum(r["status"] == "resolved" for r in scored), len(scored)


def coverage_report(results: list[Row]) -> str:
    correct, total = coverage(results)
    rate = correct / total if total else 0.0
    scored = Counter(r["status"] for r in results if r["marketing_category"] != HOMEOPATHIC)
    homeopathic = Counter(r["status"] for r in results if r["marketing_category"] == HOMEOPATHIC)
    lines = [
        "# Identity coverage",
        "",
        "Generated by `uv run pipeline identity resolve`. Each package in the NDC directory gets the",
        "barcode it would carry (`3` + NDC10 + check digit), which is then resolved like a scan.",
        "Sample packages are left out. This measures the lookup, not real-world box scans.",
        "",
        f"**Correct: {correct} of {total} ({rate:.2%}).** "
        f"Target {TARGET:.0%}: {'met' if total and rate >= TARGET else 'not met'}.",
        "",
        "Homeopathic products are not scored, so they are counted apart and not in the target.",
        "",
        "| Status | Scored packages | Homeopathic packages |",
        "| --- | ---: | ---: |",
    ]
    lines += [
        f"| {status} | {scored[status]} | {homeopathic[status]} |"
        for status in sorted(scored.keys() | homeopathic.keys())
    ]
    misses = [
        r for r in results if r["marketing_category"] != HOMEOPATHIC and r["status"] != "resolved"
    ]
    lines += [
        "",
        "## Every miss",
        "",
        "| Package NDC | Expected NDC11 | Barcode | Status | Matches |",
        "| --- | --- | --- | --- | --- |",
    ]
    lines += [
        f"| {r['ndc_raw']} | {r['expected_ndc11']} | {r['barcode'] or '-'} | {r['status']} "
        f"| {', '.join(r['matches'])} |"
        for r in misses
    ]
    return "\n".join(lines) + "\n"


INGREDIENT = pl.Struct(
    {
        "unii": pl.String,
        "name": pl.String,
        "strength": pl.Float64,
        "unit": pl.String,
        "per_amount": pl.Float64,
        "per_unit": pl.String,
    }
)
PRODUCT_SCHEMA: dict[str, Any] = {
    "ndc11": pl.String,
    "ndc_raw": pl.String,
    **{name: pl.String for name in DIRECTORY_FIELDS},
    "spl_set_id": pl.String,
    "spl_version": pl.Int64,
    "product_index": pl.Int64,
    "product_name": pl.String,
    "ingredients": pl.List(INGREDIENT),
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

    Returns correct and total for the coverage target.
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
