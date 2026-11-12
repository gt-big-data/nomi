import re
import shutil
import zipfile
from pathlib import Path

import polars as pl
import pytest
from nomi_pipeline.cli import app
from nomi_pipeline.config import Settings
from nomi_pipeline.ingest.sections import (
    DRUG_FACTS_SECTIONS,
    SectionRow,
    collect_sections,
    coverage_report,
    parse_sections,
    parse_sections_bytes,
)
from nomi_pipeline.ingest.spl import ParseError
from typer.testing import CliRunner

FIXTURES = Path(__file__).parents[1] / "fixtures" / "spl"
WARNINGS = "34071-1"
runner = CliRunner()


def by_code(sections: list[SectionRow], code: str) -> SectionRow:
    return next(s for s in sections if s.loinc_code == code)


def test_twelve_drug_facts_section_types() -> None:
    assert len(DRUG_FACTS_SECTIONS) == 12


def test_ibuprofen_label_has_all_twelve_section_types() -> None:
    label = parse_sections(FIXTURES / "ibuprofen_otc.xml")

    assert label.set_id == "4aba1bf2-8146-04fa-e063-6294a90a8a21"
    assert label.version == 2
    assert {s.loinc_code for s in label.sections} >= set(DRUG_FACTS_SECTIONS)
    for section in label.sections:
        assert section.spl_set_id == label.set_id
        assert section.spl_version == 2


def test_nested_sections_record_their_parent() -> None:
    sections = parse_sections(FIXTURES / "ibuprofen_otc.xml").sections

    assert by_code(sections, "50570-1").parent_loinc_code == WARNINGS
    assert by_code(sections, "50565-1").parent_loinc_code == WARNINGS
    assert by_code(sections, WARNINGS).parent_loinc_code is None
    assert by_code(sections, "55106-9").parent_loinc_code is None
    assert by_code(sections, "50570-1").section_name == "Do not use"


def test_unclassified_warnings_subsections_are_kept_by_title() -> None:
    sections = parse_sections(FIXTURES / "ibuprofen_otc.xml").sections

    unclassified = [s for s in sections if s.loinc_code == "42229-5"]
    assert [s.section_name for s in unclassified] == [
        "Warnings / Allergy alert",
        "Warnings / Stomach bleeding warning",
        "Warnings / Heart attack and stroke warning",
    ]
    assert all(s.parent_loinc_code == WARNINGS for s in unclassified)
    assert unclassified[1].title == "Stomach bleeding warning"


def test_sections_outside_drug_facts_are_dropped() -> None:
    sections = parse_sections(FIXTURES / "ibuprofen_otc.xml").sections

    codes = {s.loinc_code for s in sections}
    # Product data, package label, storage, inactive ingredients, questions.
    assert codes.isdisjoint({"48780-1", "51945-4", "44425-7", "51727-6", "53413-1"})


def test_parent_text_includes_nested_sections() -> None:
    ibuprofen = parse_sections(FIXTURES / "ibuprofen_otc.xml").sections
    warnings = by_code(ibuprofen, WARNINGS)
    assert "Stomach bleeding warning" in warnings.text_clean
    assert "right before or after heart surgery" in warnings.text_clean

    # The overdose section is not a Drug Facts type, but its text stays in Warnings.
    liquid = parse_sections(FIXTURES / "acetaminophen_liquid_otc.xml").sections
    assert "Overdose warning" in by_code(liquid, WARNINGS).text_clean
    assert "34088-5" not in {s.loinc_code for s in liquid}


def test_clean_text_puts_blocks_on_their_own_lines() -> None:
    sections = parse_sections(FIXTURES / "ibuprofen_otc.xml").sections
    allergy = next(s for s in sections if s.title == "Allergy alert")

    lines = allergy.text_clean.splitlines()
    assert lines[0].startswith("Ibuprofen may cause a severe allergic reaction")
    assert "hives" in lines
    assert "asthma (wheezing)" in lines
    for line in lines:
        assert line == " ".join(line.split())
    # The section's own heading is in title, not in the text.
    assert "Allergy alert" not in allergy.text_clean


def test_raw_text_keeps_original_whitespace_and_same_words() -> None:
    sections = parse_sections(FIXTURES / "ibuprofen_otc.xml").sections
    for section in sections:
        assert section.text_raw.split() == section.text_clean.split()
    allergy = next(s for s in sections if s.title == "Allergy alert")
    assert "\n   " in allergy.text_raw


def test_section_code_is_trusted_over_the_label_heading() -> None:
    # Real label: "Uses" is coded as When using, and Uses is coded inside Warnings.
    sections = parse_sections(FIXTURES / "actir_acetaminophen.xml").sections

    when_using = by_code(sections, "50567-7")
    assert when_using.section_name == "When using"
    assert when_using.title == "Uses"
    assert "temporarily reduces fever" in when_using.text_clean
    assert by_code(sections, "34067-9").parent_loinc_code == WARNINGS


def test_sections_are_in_document_order() -> None:
    sections = parse_sections(FIXTURES / "kit_parts_triclosan_soap.xml").sections

    assert [s.loinc_code for s in sections] == [
        "55106-9",
        "55105-1",
        WARNINGS,
        "50567-7",
        "50565-1",
        "34068-7",
    ]
    assert [s.section_index for s in sections] == list(range(6))
    assert by_code(sections, "55106-9").title == "Active Ingredients"
    assert by_code(sections, "50567-7").title is None


def test_label_without_drug_facts_has_no_sections() -> None:
    label = parse_sections(FIXTURES / "kit_two_products.xml")

    assert label.set_id
    assert label.sections == []


def test_raises_parse_error_for_bad_labels() -> None:
    with pytest.raises(ParseError):
        parse_sections(FIXTURES / "missing_set_id.xml")
    with pytest.raises(ParseError):
        parse_sections(FIXTURES / "not_xml.xml")
    xml = (FIXTURES / "ibuprofen_otc.xml").read_bytes()
    broken = re.sub(rb'(<versionNumber value=")[^"]*', rb"\1x", xml, count=1)
    with pytest.raises(ParseError):
        parse_sections_bytes(broken, "broken.xml")


def test_collect_sections_tracks_failures_and_reads_zips(tmp_path: Path) -> None:
    shutil.copy(FIXTURES / "kit_parts_triclosan_soap.xml", tmp_path / "kit.xml")
    with zipfile.ZipFile(tmp_path / "dm_spl_release_human_otc_part1.xml.zip", "w") as z:
        z.write(FIXTURES / "ibuprofen_otc.xml", "20261104_set-a.xml")
        z.write(FIXTURES / "not_xml.xml", "20261104_set-b.xml")

    result = collect_sections(tmp_path)

    assert result.files_processed == 3
    assert result.labels == 2
    assert [f["file"] for f in result.failures] == [
        "dm_spl_release_human_otc_part1.xml.zip/20261104_set-b.xml"
    ]
    assert {s.spl_set_id for s in result.sections} == {
        "4aba1bf2-8146-04fa-e063-6294a90a8a21",
        parse_sections(FIXTURES / "kit_parts_triclosan_soap.xml").set_id,
    }


def test_collect_sections_keeps_only_the_latest_version(tmp_path: Path) -> None:
    xml = (FIXTURES / "ibuprofen_otc.xml").read_bytes()
    older = re.sub(rb'(<versionNumber value=")\d+', rb"\g<1>1", xml, count=1)
    (tmp_path / "a_new.xml").write_bytes(xml)
    (tmp_path / "b_old.xml").write_bytes(older)

    result = collect_sections(tmp_path)

    assert result.superseded == 1
    assert result.labels == 1
    assert {s.spl_version for s in result.sections} == {2}


def test_coverage_report_counts_each_section_type_and_failures(tmp_path: Path) -> None:
    shutil.copy(FIXTURES / "ibuprofen_otc.xml", tmp_path / "ibuprofen.xml")
    shutil.copy(FIXTURES / "kit_parts_triclosan_soap.xml", tmp_path / "kit.xml")
    shutil.copy(FIXTURES / "kit_two_products.xml", tmp_path / "empty.xml")
    shutil.copy(FIXTURES / "not_xml.xml", tmp_path / "not_xml.xml")

    report = coverage_report(collect_sections(tmp_path))

    assert "Parse failures: 1" in report
    assert "not_xml.xml" in report
    assert "Labels with no Drug Facts sections: 1" in report
    for code, name in DRUG_FACTS_SECTIONS.items():
        assert f"| {code} | {name} |" in report
    # Warnings is on two of three labels; Stop use only on ibuprofen.
    assert f"| {WARNINGS} | Warnings | 2 | 66.7% | 1 |" in report
    assert "| 50566-9 | Stop use | 1 | 33.3% | 2 |" in report


def test_ingest_sections_writes_parquet_and_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    raw = tmp_path / "raw" / "dailymed-otc"
    raw.mkdir(parents=True)
    shutil.copy(FIXTURES / "ibuprofen_otc.xml", raw / "ibuprofen_otc.xml")
    shutil.copy(FIXTURES / "not_xml.xml", raw / "not_xml.xml")
    report = tmp_path / "coverage.md"

    result = runner.invoke(app, ["ingest", "sections", "--report", str(report)])

    assert result.exit_code == 0, result.output
    sections = pl.read_parquet(tmp_path / "bronze" / "spl_sections.parquet")
    assert sections.columns == [
        "spl_set_id",
        "spl_version",
        "section_index",
        "loinc_code",
        "section_name",
        "title",
        "parent_loinc_code",
        "text_raw",
        "text_clean",
    ]
    assert set(sections["loinc_code"]) >= set(DRUG_FACTS_SECTIONS)
    assert "Parse failures: 1" in report.read_text()


def test_ingest_sections_writes_empty_table_without_labels(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    (tmp_path / "raw" / "dailymed-otc").mkdir(parents=True)

    result = runner.invoke(app, ["ingest", "sections", "--report", str(tmp_path / "r.md")])

    assert result.exit_code == 0, result.output
    sections = pl.read_parquet(tmp_path / "bronze" / "spl_sections.parquet")
    assert len(sections) == 0
    assert "loinc_code" in sections.columns
