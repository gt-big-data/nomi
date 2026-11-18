"""FAERS disproportionality signals per ingredient, event group, age band and sex (NOMI-053).

Reads the drug-reaction pairs (NOMI-044) and computes the BCPNN information component with the
shrinkage the design specifies (docs/system-design.md 6.4):

    IC    = log2((observed + 0.5) / (expected + 0.5))
    IC025 = log2 of the 2.5% quantile of Gamma(observed + 0.5, rate = expected + 0.5)

counted in reports, not pairs, within each stratum. IC025 above 0 counts as a signal. The rows
follow packages/schema/schemas/signal.schema.json. Signals are supporting evidence only: FAERS has
no denominator, so they never set a score (docs/scoring/v1-method.md section 4).
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any

import polars as pl
import yaml

from nomi_pipeline.config import REPO_ROOT, Settings

log = logging.getLogger(__name__)

INGREDIENTS_DIR = REPO_ROOT / "pipeline" / "knowledge" / "ingredients"
EVENT_GROUPS = REPO_ROOT / "pipeline" / "knowledge" / "faers_event_groups.yaml"
# What the app bundles: small enough to commit, so the evidence build needs no FAERS download.
SUMMARY = REPO_ROOT / "pipeline" / "derived" / "faers_signals.json"

# Words a FAERS active-ingredient name can end with that only name the salt or hydrate. They
# are stripped from the end only when what is left is one of our moieties, so "MAGNESIUM
# HYDROXIDE" stays whole.
SALT_WORDS = frozenset(
    {
        "HYDROCHLORIDE",
        "DIHYDROCHLORIDE",
        "HCL",
        "HYDROBROMIDE",
        "MALEATE",
        "SUCCINATE",
        "SODIUM",
        "MAGNESIUM",
        "POTASSIUM",
        "DIHYDRATE",
        "TRIHYDRATE",
        "MONOHYDRATE",
        "TARTRATE",
        "CITRATE",
    }
)

# International names FAERS uses for the same moiety (WHO INN or Ph. Eur. names).
SYNONYMS = {
    "PARACETAMOL": "ACETAMINOPHEN",
    "ACETYLSALICYLIC ACID": "ASPIRIN",
    "MACROGOL 3350": "POLYETHYLENE GLYCOL 3350",
    "CHLORPHENAMINE": "CHLORPHENIRAMINE",
}

Z_025 = -1.959963984540054


def build_faers_signals(
    settings: Settings, reports_dir: Path | None = None, summary_path: Path | None = None
) -> None:
    pairs_path = settings.silver_dir / "faers_pairs.parquet"
    unii_moieties = _unii_moieties()
    match = _moiety_of(set(unii_moieties.values()))
    groups = _event_group_dimensions()
    pairs = pl.scan_parquet(pairs_path)

    names = (
        pairs.select("primaryid", "drugname", "prod_ai", "age_band", "sex")
        .unique(["primaryid", "drugname"])
        .with_columns(pl.coalesce("prod_ai", "drugname").alias("ai"))
        .with_columns(pl.col("ai").str.split("\\"))
        .explode("ai")
        .collect()
    )
    # Match each distinct name once in Python, not once per row.
    mapping = {raw: match(raw) for raw in names["ai"].unique().drop_nulls().to_list()}
    mapping = {raw: moiety for raw, moiety in mapping.items() if moiety is not None}
    drugs = (
        names.with_columns(
            pl.col("ai").replace_strict(mapping, default=None, return_dtype=pl.String)
        )
        .filter(pl.col("ai").is_not_null())
        .select("primaryid", pl.col("ai").alias("moiety"), "age_band", "sex")
        .unique(["primaryid", "moiety"])
    )
    events = (
        pairs.filter(pl.col("event_group").is_not_null())
        .select("primaryid", "event_group", "age_band", "sex")
        .unique(["primaryid", "event_group"])
        .collect()
    )
    reports = pairs.select("primaryid", "age_band", "sex").unique("primaryid").collect()
    log.info("%d drug rows, %d event rows, %d reports", len(drugs), len(events), len(reports))

    rows = []
    for age_all, sex_all in ((False, False), (False, True), (True, False), (True, True)):
        rows.append(_stratum(drugs, events, reports, age_all, sex_all))
    signals = pl.concat(rows)

    unii_rows = pl.DataFrame(
        [{"moiety": m, "unii": u} for u, m in unii_moieties.items()],
        schema={"moiety": pl.String, "unii": pl.String},
    )
    signals = (
        signals.join(unii_rows, on="moiety")
        .with_columns(pl.col("event_group").replace_strict(groups).alias("dimension"))
        .with_columns(
            pl.struct("report_count", "expected_count")
            .map_elements(
                lambda r: _ic025(r["report_count"], r["expected_count"]), return_dtype=pl.Float64
            )
            .alias("ic025"),
            (((pl.col("report_count") + 0.5) / (pl.col("expected_count") + 0.5)).log(2)).alias(
                "ic"
            ),
        )
        .select(
            "unii",
            "moiety",
            "dimension",
            "event_group",
            "age_band",
            "sex",
            "ic",
            "ic025",
            "report_count",
            "expected_count",
        )
        .sort("moiety", "event_group", "age_band", "sex", "unii")
    )
    out = settings.silver_dir / "faers_signals.parquet"
    signals.write_parquet(out)
    log.info("Wrote %d signal rows to %s", len(signals), out)
    _write_report(signals, reports_dir or REPO_ROOT / "pipeline" / "reports")
    _write_summary(signals, summary_path or SUMMARY)


def _stratum(
    drugs: pl.DataFrame, events: pl.DataFrame, reports: pl.DataFrame, age_all: bool, sex_all: bool
) -> pl.DataFrame:
    """Observed and expected counts for one way of stratifying ("all" pools a column)."""

    def strata(df: pl.DataFrame) -> pl.DataFrame:
        return df.with_columns(
            pl.lit("all").alias("age_band") if age_all else pl.col("age_band"),
            pl.lit("all").alias("sex") if sex_all else pl.col("sex"),
        )

    keys = ["age_band", "sex"]
    d, e, r = strata(drugs), strata(events), strata(reports)
    n = r.group_by(keys).agg(pl.len().alias("n"))
    n_x = d.group_by(["moiety", *keys]).agg(pl.len().alias("n_x"))
    n_y = e.group_by(["event_group", *keys]).agg(pl.len().alias("n_y"))
    n_xy = (
        d.join(e.select("primaryid", "event_group"), on="primaryid")
        .group_by(["moiety", "event_group", *keys])
        .agg(pl.len().alias("report_count"))
    )
    # Every ingredient and event group pair in the stratum, including those never reported
    # together, so a zero is recorded rather than missing.
    grid = n_x.join(n_y, on=keys).join(n, on=keys)
    out = grid.join(n_xy, on=["moiety", "event_group", *keys], how="left").with_columns(
        pl.col("report_count").fill_null(0),
        _expected().alias("expected_count"),
    )
    return out.filter(pl.col("age_band") != "unknown", pl.col("sex") != "unknown").select(
        "moiety", "event_group", "age_band", "sex", "report_count", "expected_count"
    )


def _expected() -> pl.Expr:
    """n_x * n_y / n in floating point. The counts are 32-bit integers, and their product for a
    common drug and event (50,000 * 350,000) overflows and wraps around."""
    return pl.col("n_x").cast(pl.Float64) * pl.col("n_y").cast(pl.Float64) / pl.col("n")


def _ic025(observed: int, expected: float) -> float:
    """log2 of the 2.5% quantile of Gamma(observed + 0.5, rate expected + 0.5).

    Uses the Wilson-Hilferty approximation to the gamma quantile, which is deterministic and
    needs no SciPy.
    """
    shape = observed + 0.5
    rate = expected + 0.5
    if observed == 0:
        # Gamma(0.5) is chi-squared with 1 degree of freedom over 2; its 2.5% quantile is the
        # square of the normal 51.25% quantile, over 2.
        return math.log2(0.0313375**2 / 2.0 / rate)
    c = 1.0 / (9.0 * shape)
    q = shape * (1.0 - c + Z_025 * math.sqrt(c)) ** 3 / rate
    return math.log2(q) if q > 0 else float("-inf")


def _unii_moieties() -> dict[str, str]:
    """UNII to the upper-case moiety name FAERS reports would use."""
    out = {}
    for path in sorted(INGREDIENTS_DIR.glob("*.yaml")):
        data: dict[str, Any] = yaml.safe_load(path.read_text())
        name = str(data["name"]).upper().replace("_", " ")
        out[str(data["unii"])] = _strip_salt(name, None) or name
    return out


def _strip_salt(name: str, known: set[str] | None) -> str | None:
    """Drop trailing salt and hydrate words. With known moieties, stop at the first match;
    without, strip them all."""
    words = name.split()
    stripped = None
    while len(words) > 1 and words[-1] in SALT_WORDS:
        words = words[:-1]
        candidate = " ".join(words)
        candidate = SYNONYMS.get(candidate, candidate)
        if known is not None and candidate in known:
            return candidate
        stripped = candidate
    return stripped if known is None else None


def _moiety_of(known: set[str]):  # type: ignore[no-untyped-def]
    def match(raw: str | None) -> str | None:
        if raw is None:
            return None
        name = " ".join(raw.strip().upper().replace(".", "").split())
        name = SYNONYMS.get(name, name)
        if name in known:
            return name
        return _strip_salt(name, known)

    return match


def _event_group_dimensions() -> dict[str, str]:
    data: dict[str, Any] = yaml.safe_load(EVENT_GROUPS.read_text())
    return {name: g["dimension"] for name, g in data["event_groups"].items()}


def _write_report(signals: pl.DataFrame, reports_dir: Path) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    pooled = (
        signals.filter(pl.col("sex") == "all")
        .unique(["moiety", "event_group", "age_band"])
        .sort("moiety", "event_group", "age_band")
    )
    lines = [
        "# FAERS signals report",
        "",
        "Counts are reports. IC025 above 0 counts as a signal. Signals are supporting evidence and",
        "never set a score (docs/scoring/v1-method.md section 4).",
        "",
        "| Ingredient | Event group | Age band | Reports | Expected | IC | IC025 | Signal |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in pooled.iter_rows(named=True):
        if r["report_count"] == 0 and r["age_band"] != "all":
            continue
        lines.append(
            f"| {r['moiety'].lower()} | {r['event_group']} | {r['age_band']} | "
            f"{r['report_count']:,} | {r['expected_count']:,.1f} | {r['ic']:.2f} | "
            f"{r['ic025']:.2f} | {'yes' if r['ic025'] > 0 else ''} |"
        )
    (reports_dir / "faers_signals.md").write_text("\n".join(lines) + "\n")


def _write_summary(signals: pl.DataFrame, path: Path) -> None:
    """By UNII: the strongest signal (IC025 above 0) per dimension and age band, sexes pooled.
    Ties go to the event group that sorts first, so the file is the same on every run."""
    rows = (
        signals.filter(pl.col("sex") == "all", pl.col("ic025") > 0)
        .sort(["ic025", "event_group"], descending=[True, False])
        .unique(["unii", "dimension", "age_band"], keep="first", maintain_order=True)
        .sort("unii", "dimension", "age_band")
    )
    out: dict[str, list[dict[str, Any]]] = {}
    for r in rows.iter_rows(named=True):
        out.setdefault(r["unii"], []).append(
            {
                "dimension": r["dimension"],
                "age_band": r["age_band"],
                "event_group": r["event_group"],
                "ic025": round(r["ic025"], 3),
                "reports": r["report_count"],
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
