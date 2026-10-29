from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

from nomi_pipeline.ingest._ndc import normalize_ndc

NS = {"hl7": "urn:hl7-org:v3"}


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
    role: str
    unii: str | None
    name: str
    strength: float | None = None
    unit: str | None = None
    per_amount: float | None = None
    per_unit: str | None = None


@dataclass
class ParsedLabel:
    products: list[ProductRow] = field(default_factory=list)
    ingredients: list[IngredientRow] = field(default_factory=list)


def parse_label(path: Path) -> ParsedLabel:
    try:
        tree = etree.parse(str(path))
    except etree.XMLSyntaxError as e:
        raise ParseError(f"{path.name}: invalid XML ({e})") from e
    root = tree.getroot()

    set_id_el = root.find("hl7:setId", namespaces=NS)
    version_el = root.find("hl7:versionNumber", namespaces=NS)
    if set_id_el is None or version_el is None:
        raise ParseError(f"{path.name}: missing setID or versionNumber")

    set_id = set_id_el.get("root")
    version = int(version_el.get("value"))

    label = ParsedLabel()

    manufactured_products = root.findall(
        ".//hl7:manufacturedProduct/hl7:manufacturedProduct", namespaces=NS
    )
    for index, product_el in enumerate(manufactured_products):
        name_el = product_el.find("hl7:name", namespaces=NS)

        if name_el is not None and name_el.text:  # noqa: SIM108
            product_name = name_el.text.strip()
        else:
            product_name = ""

        code_elements = product_el.findall(
            ".//hl7:containerPackagedProduct/hl7:code", namespaces=NS
        )

        for code_el in code_elements:
            ndc_raw = code_el.get("code")
            if not ndc_raw:
                continue
            try:
                ndc11 = normalize_ndc(ndc_raw)
            except ValueError:
                continue

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

        ingredient_elements = product_el.findall("hl7:ingredient", namespaces=NS)
        for ingredient_el in ingredient_elements:
            class_code = ingredient_el.get("classCode")
            if class_code in ("ACTIB", "ACTIM"):  # noqa: SIM108
                role = "active"
            else:
                role = "inactive"

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

            strength = None
            unit = None
            per_amount = None
            per_unit = None
            if role == "active":
                quantity_el = ingredient_el.find("hl7:quantity", namespaces=NS)
                if quantity_el is not None:
                    numerator_el = quantity_el.find("hl7:numerator", namespaces=NS)
                    if numerator_el is not None:
                        strength = float(numerator_el.get("value"))
                        unit = numerator_el.get("unit")

                    denominator_el = quantity_el.find("hl7:denominator", namespaces=NS)
                    if denominator_el is not None and denominator_el.get("value") not in (
                        None,
                        "1",
                    ):
                        per_amount = float(denominator_el.get("value"))
                        per_unit = denominator_el.get("unit")

            label.ingredients.append(
                IngredientRow(
                    spl_set_id=set_id,
                    product_index=index,
                    role=role,
                    unii=unii,
                    name=ingredient_name,
                    strength=strength,
                    unit=unit,
                    per_amount=per_amount,
                    per_unit=per_unit,
                )
            )

    return label


@dataclass
class IngestResult:
    products: list[ProductRow] = field(default_factory=list)
    ingredients: list[IngredientRow] = field(default_factory=list)
    failures: list[dict[str, str]] = field(default_factory=list)
    files_processed: int = 0


def collect_labels(raw_dir: Path) -> IngestResult:
    result = IngestResult()
    for path in sorted(raw_dir.glob("*.xml")):
        result.files_processed += 1
        try:
            label = parse_label(path)
        except ParseError as e:
            result.failures.append({"file": path.name, "error": str(e)})
            continue
        result.products.extend(label.products)
        result.ingredients.extend(label.ingredients)
    return result
