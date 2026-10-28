"""Package identity and coverage, independent of category assignment (NOMI-026)."""

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nomi_pipeline.identity.barcode import ndc_candidates

Row = dict[str, Any]


def package_codes(package_ndc: str) -> tuple[str, str]:
    """Return normalized NDC11 and a synthetic UPC-A from a segmented NDC10.

    Segments are required: removing padding from NDC11 cannot recover the
    original NDC10 layout unambiguously.
    """
    parts = package_ndc.split("-")
    if tuple(map(len, parts)) not in {(4, 4, 2), (5, 3, 2), (5, 4, 1)}:
        raise ValueError(f"Expected segmented NDC10, got {package_ndc!r}")
    if not all(part.isascii() and part.isdigit() for part in parts):
        raise ValueError(f"Invalid NDC digits: {package_ndc!r}")
    ndc11 = "".join(part.zfill(width) for part, width in zip(parts, (5, 4, 2), strict=True))
    body = "3" + "".join(parts)
    total = sum(map(int, body[::2])) * 3 + sum(map(int, body[1::2]))
    return ndc11, body + str(-total % 10)


@dataclass(frozen=True)
class Resolution:
    status: str
    candidates: tuple[str, ...] = ()
    matches: tuple[str, ...] = ()
    product: Row | None = None


class Resolver:
    """Index bronze rows once; never choose arbitrarily between identities.

    See pipeline/docs/identity.md for the provisional ingestion contracts.
    """

    def __init__(
        self, ndc: Iterable[Row], products: Iterable[Row], ingredients: Iterable[Row]
    ) -> None:
        self.directory: dict[str, list[Row]] = defaultdict(list)
        self.labels: dict[str, list[Row]] = defaultdict(list)
        self.ingredients: dict[tuple[str, str, int], list[Row]] = defaultdict(list)
        for row in ndc:
            self.directory[row["ndc11"]].append(row)
        # Latest version is selected per label set, not globally per package.
        rows = list(products)
        latest: dict[str, int] = {}
        for row in rows:
            key = row["spl_set_id"]
            latest[key] = max(latest.get(key, 0), row["spl_version"])
        for row in rows:
            if (
                row["spl_version"] == latest[row["spl_set_id"]]
                and row not in self.labels[row["ndc11"]]
            ):
                self.labels[row["ndc11"]].append(row)
        for row in ingredients:
            key = (row["ndc11"], row["spl_set_id"], row["spl_version"])
            if row not in self.ingredients[key]:
                self.ingredients[key].append(row)

    def resolve(self, barcode: str) -> Resolution:
        parsed = ndc_candidates(barcode)
        candidates = tuple(dict.fromkeys(parsed["candidates"]))
        if parsed["status"] != "ok":
            return Resolution(parsed["status"])
        matches = tuple(sorted(code for code in candidates if code in self.directory))
        if len(matches) != 1:
            return Resolution("not_found" if not matches else "ambiguous_ndc", candidates, matches)
        ndc11 = matches[0]
        labels = self.labels.get(ndc11, [])
        if len(labels) != 1:
            return Resolution(
                "missing_label" if not labels else "ambiguous_label", candidates, matches
            )
        label = labels[0]
        key = (ndc11, label["spl_set_id"], label["spl_version"])
        active = []
        for item in self.ingredients.get(key, []):
            active.append(
                {
                    k: v
                    for k, v in item.items()
                    if k not in {"ndc11", "spl_set_id", "spl_version"} and v is not None
                }
            )
        if not active:
            return Resolution("missing_ingredients", candidates, matches)
        # Invalid strengths must never turn into a seemingly successful identity.
        for item in active:
            strength = item.get("strength")
            if (
                not item.get("unii")
                or not item.get("name")
                or not item.get("unit")
                or isinstance(strength, bool)
                or not isinstance(strength, (int, float))
                or not 0 < strength < float("inf")
                or (("per_amount" in item) != ("per_unit" in item))
            ):
                return Resolution("invalid_ingredients", candidates, matches)
        product = {k: v for k, v in label.items() if v is not None}
        product["ingredients"] = sorted(active, key=lambda item: (item["unii"], str(item)))
        return Resolution("resolved", candidates, matches, product)


def evaluate(resolver: Resolver) -> tuple[list[Row], list[Row]]:
    """Evaluate every distinct directory package, retaining every miss."""
    products: dict[str, Row] = {}
    results: list[Row] = []
    for expected in sorted(resolver.directory):
        originals = sorted({row["package_ndc"] for row in resolver.directory[expected]})
        for original in originals:
            result: Row = {
                "package_ndc": original,
                "expected_ndc11": expected,
                "barcode": None,
                "actual_ndc11": None,
                "status": "invalid_package_ndc",
                "matches": [],
            }
            try:
                normalized, barcode = package_codes(original)
            except ValueError:
                results.append(result)
                continue
            result["barcode"] = barcode
            if normalized != expected:
                result["status"] = "ndc_normalization_mismatch"
                results.append(result)
                continue
            resolved = resolver.resolve(barcode)
            result["status"] = resolved.status
            result["matches"] = list(resolved.matches)
            if resolved.product is not None:
                actual = resolved.product["ndc11"]
                result["actual_ndc11"] = actual
                if actual == expected:
                    products[actual] = resolved.product
                else:
                    result["status"] = "wrong_product"
            results.append(result)
    return [products[key] for key in sorted(products)], results


def coverage_report(results: list[Row]) -> str:
    counts = Counter(row["status"] for row in results)
    total = len(results)
    correct = counts["resolved"]
    coverage = correct / total if total else 0.0
    lines = [
        "# Identity coverage",
        "",
        "Synthetic package-barcode coverage; not a real-box scan benchmark.",
        "",
        f"Correct: {correct}/{total} ({coverage:.2%}).",
        "",
        f"90% target: {'PASS' if total and coverage >= 0.9 else 'NOT MET'}.",
        "",
        "| Status | Count |",
        "| --- | ---: |",
    ]
    lines.extend(f"| {status} | {count} |" for status, count in sorted(counts.items()))
    lines.extend(
        [
            "",
            "## Every miss",
            "",
            "| Package NDC | Expected NDC11 | Barcode | Status | Matches |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in results:
        if row["status"] != "resolved":
            cells = [
                row["package_ndc"],
                row["expected_ndc11"],
                row["barcode"] or "—",
                row["status"],
                ", ".join(row["matches"]),
            ]
            lines.append(
                "| "
                + " | ".join(str(cell).replace("|", "\\|").replace("\n", " ") for cell in cells)
                + " |"
            )
    return "\n".join(lines) + "\n"


def build_identity(bronze_dir: Path, silver_dir: Path, report: Path) -> Mapping[str, int]:
    """Read bronze Parquet, write products and exhaustive resolution diagnostics."""
    import polars as pl

    ndc = pl.read_parquet(bronze_dir / "ndc.parquet").to_dicts()
    labels = pl.read_parquet(bronze_dir / "spl_products.parquet").to_dicts()
    ingredients = pl.read_parquet(bronze_dir / "spl_ingredients.parquet").to_dicts()
    resolver = Resolver(ndc, labels, ingredients)
    products, results = evaluate(resolver)
    silver_dir.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    if products:
        pl.from_dicts(products, infer_schema_length=None).write_parquet(
            silver_dir / "product.parquet"
        )
    else:
        # Keep an empty output readable and avoid leaving a previous successful dataset behind.
        pl.DataFrame(
            schema={
                "ndc11": pl.String,
                "spl_set_id": pl.String,
                "spl_version": pl.Int64,
                "ingredients": pl.List(
                    pl.Struct(
                        {
                            "unii": pl.String,
                            "name": pl.String,
                            "strength": pl.Float64,
                            "unit": pl.String,
                        }
                    )
                ),
            }
        ).write_parquet(silver_dir / "product.parquet")
    diagnostics_schema: dict[str, Any] = {
        "package_ndc": pl.String,
        "expected_ndc11": pl.String,
        "barcode": pl.String,
        "actual_ndc11": pl.String,
        "status": pl.String,
        "matches": pl.List(pl.String),
    }
    pl.from_dicts(results, schema=diagnostics_schema).write_parquet(
        silver_dir / "identity_results.parquet"
    )
    report.write_text(coverage_report(results))
    return {"total": len(results), "resolved": sum(row["status"] == "resolved" for row in results)}
