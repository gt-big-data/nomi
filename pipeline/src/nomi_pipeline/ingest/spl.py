import zipfile
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

from nomi_pipeline.ingest._ndc import normalize_ndc

NS = {"hl7": "urn:hl7-org:v3"}
# A few real labels nest tables deeper than lxml's default limit of 256, so allow huge trees,
# but never resolve entities or touch the network.
PARSER = etree.XMLParser(huge_tree=True, resolve_entities=False, no_network=True)


class ParseError(Exception):
    """Raised when an SPL XML file cannot be parsed."""


@dataclass
class ProductRow:
    spl_set_id: str
    spl_version: int
    product_index: int
    product_name: str
    ndc11: str
    ndc_raw: str


@dataclass
class IngredientRow:
    spl_set_id: str
    product_index: int
    # Kits list their contents as parts; None for an ingredient of the product itself.
    part_index: int | None
    role: str
    # The SPL classCode: ACTIB, ACTIM, ACTIR (active), IACT (inactive), and a few rarer ones.
    class_code: str | None
    unii: str | None
    name: str
    strength: float | None = None
    unit: str | None = None
    per_amount: float | None = None
    per_unit: str | None = None


@dataclass
class ParsedLabel:
    set_id: str = ""
    version: int = 0
    products: list[ProductRow] = field(default_factory=list)
    ingredients: list[IngredientRow] = field(default_factory=list)


# Active by basis of strength, by moiety, or by reference to another substance.
ACTIVE_CLASS_CODES = ("ACTIB", "ACTIM", "ACTIR")


def parse_label(path: Path) -> ParsedLabel:
    return parse_label_bytes(path.read_bytes(), path.name)


def parse_label_bytes(data: bytes, name: str) -> ParsedLabel:
    """Parse one SPL document. name is only used in error messages."""
    try:
        return _parse(data, name)
    except ParseError:
        raise
    except (etree.XMLSyntaxError, ValueError, TypeError) as e:
        # Bad XML or a non-numeric value fails this one label, not the whole run.
        raise ParseError(f"{name}: {e}") from e


def _parse(data: bytes, name: str) -> ParsedLabel:
    root = etree.fromstring(data, parser=PARSER)

    set_id_el = root.find("hl7:setId", namespaces=NS)
    version_el = root.find("hl7:versionNumber", namespaces=NS)
    set_id = set_id_el.get("root") if set_id_el is not None else None
    if not set_id or version_el is None:
        raise ParseError(f"{name}: missing setID or versionNumber")

    version = int(version_el.get("value"))

    label = ParsedLabel(set_id=set_id, version=version)

    manufactured_products = root.findall(
        ".//hl7:manufacturedProduct/hl7:manufacturedProduct", namespaces=NS
    )
    for index, product_el in enumerate(manufactured_products):
        name_el = product_el.find("hl7:name", namespaces=NS)

        if name_el is not None and name_el.text:  # noqa: SIM108
            product_name = name_el.text.strip()
        else:
            product_name = ""

        # Only the product's own packages: a kit's parts have package codes of their own.
        code_elements = product_el.findall(
            "hl7:asContent//hl7:containerPackagedProduct/hl7:code", namespaces=NS
        )

        seen: set[str] = set()
        for code_el in code_elements:
            ndc_raw = code_el.get("code")
            if not ndc_raw:
                continue
            try:
                ndc11 = normalize_ndc(ndc_raw)
            except ValueError:
                continue
            # Some labels repeat one NDC at two packaging levels (a carton and its bottle).
            if ndc11 in seen:
                continue
            seen.add(ndc11)

            label.products.append(
                ProductRow(
                    spl_set_id=set_id,
                    spl_version=version,
                    product_index=index,
                    product_name=product_name,
                    ndc11=ndc11,
                    ndc_raw=ndc_raw,
                )
            )

        for ingredient_el in product_el.findall("hl7:ingredient", namespaces=NS):
            label.ingredients.append(_ingredient(ingredient_el, set_id, index, None))
        parts = product_el.findall("hl7:part/hl7:partProduct", namespaces=NS)
        for part_index, part_el in enumerate(parts):
            for ingredient_el in part_el.findall("hl7:ingredient", namespaces=NS):
                label.ingredients.append(_ingredient(ingredient_el, set_id, index, part_index))

    return label


def _ingredient(
    ingredient_el: etree._Element, set_id: str, index: int, part_index: int | None
) -> IngredientRow:
    class_code = ingredient_el.get("classCode")
    role = "active" if class_code in ACTIVE_CLASS_CODES else "inactive"

    substance_el = ingredient_el.find("hl7:ingredientSubstance", namespaces=NS)
    unii = None
    ingredient_name = ""
    if substance_el is not None:
        code_el = substance_el.find("hl7:code", namespaces=NS)
        if code_el is not None:
            unii = code_el.get("code")
        name_el = substance_el.find("hl7:name", namespaces=NS)
        if name_el is not None and name_el.text:
            ingredient_name = name_el.text.strip()

    row = IngredientRow(
        spl_set_id=set_id,
        product_index=index,
        part_index=part_index,
        role=role,
        class_code=class_code,
        unii=unii,
        name=ingredient_name,
    )
    quantity_el = ingredient_el.find("hl7:quantity", namespaces=NS)
    if role == "active" and quantity_el is not None:
        numerator_el = quantity_el.find("hl7:numerator", namespaces=NS)
        if numerator_el is not None:
            row.strength = float(numerator_el.get("value"))
            row.unit = numerator_el.get("unit")

        # "per 1 tablet" has unit "1" and adds nothing; "per 1 mL" or "per 5 mL" must be kept,
        # or a concentration would read as a dose.
        denominator_el = quantity_el.find("hl7:denominator", namespaces=NS)
        if denominator_el is not None and denominator_el.get("value") is not None:
            per_unit = denominator_el.get("unit")
            if not (denominator_el.get("value") == "1" and per_unit in (None, "1")):
                row.per_amount = float(denominator_el.get("value"))
                row.per_unit = per_unit
    return row


@dataclass
class IngestResult:
    products: list[ProductRow] = field(default_factory=list)
    ingredients: list[IngredientRow] = field(default_factory=list)
    failures: list[dict[str, str]] = field(default_factory=list)
    files_processed: int = 0
    superseded: int = 0


def collect_labels(raw_dir: Path) -> IngestResult:
    """Parse every label in raw_dir: loose *.xml files and the *.xml.zip parts from fetch.

    The DailyMed release can hold several versions of one label (set id); only the highest
    version is kept, since ingredient rows don't record which version they came from.
    """
    result = IngestResult()
    latest: dict[str, ParsedLabel] = {}
    for name, data in _label_documents(raw_dir):
        result.files_processed += 1
        try:
            label = parse_label_bytes(data, name)
        except ParseError as e:
            result.failures.append({"file": name, "error": str(e)})
            continue
        kept = latest.get(label.set_id)
        if kept is None or label.version > kept.version:
            latest[label.set_id] = label
        if kept is not None:
            result.superseded += 1
    for label in latest.values():
        result.products.extend(label.products)
        result.ingredients.extend(label.ingredients)
    return result


def _label_documents(raw_dir: Path) -> Iterator[tuple[str, bytes]]:
    for path in sorted(raw_dir.glob("*.xml")):
        yield path.name, path.read_bytes()
    for path in sorted(raw_dir.glob("*.xml.zip")):
        with zipfile.ZipFile(path) as z:
            for member in sorted(z.namelist()):
                if member.endswith(".xml"):
                    yield f"{path.name}/{member}", z.read(member)
