"""Split DailyMed OTC labels into their Drug Facts sections (NOMI-023)."""

from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

from nomi_pipeline.ingest.spl import NS, PARSER, ParseError, _label_documents

# The Drug Facts headings of 21 CFR 201.66(c), by the LOINC code SPL gives each section.
DRUG_FACTS_SECTIONS = {
    "55106-9": "Active ingredient",
    "55105-1": "Purpose",
    "34067-9": "Uses",
    "34071-1": "Warnings",
    "50570-1": "Do not use",
    "50569-3": "Ask a doctor",
    "50568-5": "Ask a doctor or pharmacist",
    "50567-7": "When using",
    "50566-9": "Stop use",
    "53414-9": "Pregnancy or breast-feeding",
    "50565-1": "Keep out of reach of children",
    "34068-7": "Directions",
}
WARNINGS = "34071-1"
# Labels code Warnings subsections such as "Liver warning" as SPL unclassified sections.
UNCLASSIFIED = "42229-5"

HL7 = "{urn:hl7-org:v3}"
# Elements that start a new line in the cleaned text.
BLOCKS = {f"{HL7}{tag}" for tag in ("paragraph", "item", "title", "tr", "caption", "section")}


@dataclass
class SectionRow:
    spl_set_id: str
    spl_version: int
    # Order of the section within its label.
    section_index: int
    loinc_code: str
    # The Drug Facts heading for the code, or "Warnings / <title>" for an unclassified subsection.
    section_name: str
    # The heading the label itself prints, which doesn't always match the code.
    title: str | None
    # Code of the nearest enclosing kept section, such as Warnings for Do not use.
    parent_loinc_code: str | None
    # All text in the section, nested sections included, as the XML has it.
    text_raw: str
    # The same text with one line per paragraph, list item or heading and whitespace collapsed.
    text_clean: str


@dataclass
class ParsedSections:
    set_id: str = ""
    version: int = 0
    sections: list[SectionRow] = field(default_factory=list)


def parse_sections(path: Path) -> ParsedSections:
    return parse_sections_bytes(path.read_bytes(), path.name)


def parse_sections_bytes(data: bytes, name: str) -> ParsedSections:
    """Parse the Drug Facts sections of one SPL document. name is only used in error messages."""
    try:
        return _parse(data, name)
    except ParseError:
        raise
    except (etree.XMLSyntaxError, ValueError, TypeError) as e:
        raise ParseError(f"{name}: {e}") from e


def _parse(data: bytes, name: str) -> ParsedSections:
    root = etree.fromstring(data, parser=PARSER)

    set_id_el = root.find("hl7:setId", namespaces=NS)
    version_el = root.find("hl7:versionNumber", namespaces=NS)
    set_id = set_id_el.get("root") if set_id_el is not None else None
    if not set_id or version_el is None:
        raise ParseError(f"{name}: missing setID or versionNumber")

    label = ParsedSections(set_id=set_id, version=int(version_el.get("value")))
    for section_el in root.findall(
        "hl7:component/hl7:structuredBody/hl7:component/hl7:section", namespaces=NS
    ):
        _walk(section_el, label, parent_code=None, direct_parent_code=None)
    return label


def _walk(
    section_el: etree._Element,
    label: ParsedSections,
    parent_code: str | None,
    direct_parent_code: str | None,
) -> None:
    code_el = section_el.find("hl7:code", namespaces=NS)
    code = code_el.get("code") if code_el is not None else None
    title_el = section_el.find("hl7:title", namespaces=NS)
    title = " ".join("".join(title_el.itertext()).split()) if title_el is not None else ""

    if code in DRUG_FACTS_SECTIONS:
        section_name = DRUG_FACTS_SECTIONS[code]
    elif code == UNCLASSIFIED and direct_parent_code == WARNINGS and title:
        section_name = f"Warnings / {title}"
    else:
        section_name = None

    child_parent = parent_code
    if code is not None and section_name is not None:
        label.sections.append(
            SectionRow(
                spl_set_id=label.set_id,
                spl_version=label.version,
                section_index=len(label.sections),
                loinc_code=code,
                section_name=section_name,
                title=title or None,
                parent_loinc_code=parent_code,
                text_raw=_raw_text(section_el, title_el),
                text_clean=_clean_text(section_el, title_el),
            )
        )
        child_parent = code

    # Sections nest at any depth, also inside sections that aren't Drug Facts.
    for child in section_el.findall("hl7:component/hl7:section", namespaces=NS):
        _walk(child, label, child_parent, code)


def _raw_text(section_el: etree._Element, own_title: etree._Element | None) -> str:
    parts: list[str] = []
    for child in section_el:
        if child is not own_title and isinstance(child.tag, str):
            parts.extend(child.itertext())
    return "".join(parts)


def _clean_text(section_el: etree._Element, own_title: etree._Element | None) -> str:
    parts: list[str] = []

    def walk(el: etree._Element) -> None:
        block = el.tag in BLOCKS
        if block:
            parts.append("\n")
        if el.text:
            parts.append(el.text)
        for child in el:
            # Comments and processing instructions add no text, but their tails are text.
            if isinstance(child.tag, str):
                walk(child)
            if child.tail:
                parts.append(child.tail)
        if block:
            parts.append("\n")

    for child in section_el:
        if child is not own_title and isinstance(child.tag, str):
            walk(child)
    # str.split() below treats a non-breaking space as whitespace too.
    lines = "".join(parts).splitlines()
    return "\n".join(" ".join(line.split()) for line in lines if line.strip())


@dataclass
class SectionsResult:
    sections: list[SectionRow] = field(default_factory=list)
    failures: list[dict[str, str]] = field(default_factory=list)
    files_processed: int = 0
    superseded: int = 0
    # Labels kept after dropping older versions.
    labels: int = 0
    labels_without_sections: int = 0


def collect_sections(raw_dir: Path) -> SectionsResult:
    """Split every label in raw_dir, keeping only the highest version of each set id."""
    result = SectionsResult()
    latest: dict[str, ParsedSections] = {}
    for name, data in _label_documents(raw_dir):
        result.files_processed += 1
        try:
            label = parse_sections_bytes(data, name)
        except ParseError as e:
            result.failures.append({"file": name, "error": str(e)})
            continue
        kept = latest.get(label.set_id)
        if kept is None or label.version > kept.version:
            latest[label.set_id] = label
        if kept is not None:
            result.superseded += 1
    for label in latest.values():
        result.sections.extend(label.sections)
        if not label.sections:
            result.labels_without_sections += 1
    result.labels = len(latest)
    return result


def coverage_report(result: SectionsResult) -> str:
    """Markdown report: how many labels carry each Drug Facts section, and the parse failures."""
    labels_with: dict[str, set[str]] = {code: set() for code in DRUG_FACTS_SECTIONS}
    for section in result.sections:
        if section.loinc_code in labels_with:
            labels_with[section.loinc_code].add(section.spl_set_id)
    subsections = sum(1 for s in result.sections if s.loinc_code == UNCLASSIFIED)

    lines = [
        "# SPL Drug Facts section coverage",
        "",
        "Generated by `uv run pipeline ingest sections` (NOMI-023).",
        "",
        f"- Label files processed: {result.files_processed:,}",
        f"- Parse failures: {len(result.failures):,}",
        f"- Older or duplicate label versions dropped: {result.superseded:,}",
        f"- Labels kept: {result.labels:,}",
        f"- Labels with no Drug Facts sections: {result.labels_without_sections:,}",
        f"- Section rows: {len(result.sections):,}, of which Warnings subsections: {subsections:,}",
        "",
        "| LOINC | Section | Labels | Coverage | Missing |",
        "|---|---|---|---|---|",
    ]
    for code, name in DRUG_FACTS_SECTIONS.items():
        count = len(labels_with[code])
        share = count / result.labels * 100 if result.labels else 0.0
        lines.append(f"| {code} | {name} | {count:,} | {share:.1f}% | {result.labels - count:,} |")

    if result.failures:
        lines += ["", "## Parse failures", ""]
        lines += [f"- `{f['file']}`: {f['error']}" for f in result.failures[:20]]
        if len(result.failures) > 20:
            lines.append(f"- ... and {len(result.failures) - 20:,} more")
    return "\n".join(lines) + "\n"
