"""Generate Pydantic v2 models from packages/schema/schemas into generated/python/nomi_schema."""

import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = ROOT / "schemas"
OUT_DIR = ROOT / "generated" / "python" / "nomi_schema"
HEADER = "# Generated from packages/schema/schemas by scripts/codegen_python.py. Do not edit."


def main() -> None:
    shutil.rmtree(OUT_DIR, ignore_errors=True)
    subprocess.run(
        [
            "datamodel-codegen",
            "--input", str(SCHEMA_DIR),
            "--input-file-type", "jsonschema",
            "--output", str(OUT_DIR),
            "--output-model-type", "pydantic_v2.BaseModel",
            "--target-python-version", "3.12",
            "--use-title-as-name",
            "--use-double-quotes",
            "--use-annotated",
            "--collapse-root-models",
            "--use-field-description",
            "--use-schema-description",
            "--disable-timestamp",
            "--custom-file-header", HEADER,
            "--formatters", "black", "isort",
        ],
        check=True,
    )

    # Re-export the types each schema owns, so callers can write `from nomi_schema import Product`.
    lines = [HEADER, ""]
    names = []
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        schema = json.loads(path.read_text())
        module = path.name.removesuffix(".json").replace("-", "_").replace(".", "_")
        # --collapse-root-models inlines plain strings, numbers and maps, so export only titles
        # that became classes in the generated module.
        classes = set(re.findall(r"^class (\w+)\(", (OUT_DIR / f"{module}.py").read_text(), re.M))
        titles = [d["title"] for d in schema.get("$defs", {}).values() if "title" in d]
        if "type" in schema:
            titles.insert(0, schema["title"])
        owned = [t for t in titles if t in classes]
        lines.append(f"from .{module} import {', '.join(owned)}")
        names += owned
    lines += ["", f"__all__ = {sorted(names)!r}", ""]
    (OUT_DIR / "__init__.py").write_text("\n".join(lines))
    subprocess.run(["black", "-q", str(OUT_DIR / "__init__.py")], check=True)
    print(f"Generated Pydantic models in {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
