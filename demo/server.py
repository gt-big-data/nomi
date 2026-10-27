"""Nomi MVP demo: barcode/name lookup on openFDA, rule extraction, prototype scoring UI.

Run from the repo root:  uv run python demo/server.py  (then open http://localhost:8000)
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from nomi_pipeline.extract.rules import extract

HERE = Path(__file__).resolve().parent
CACHE = HERE / "cache"
OPENFDA = "https://api.fda.gov/drug/label.json"
OTC = 'openfda.product_type:"HUMAN OTC DRUG"'
SECTIONS = [
    ("active_ingredient", "Active ingredient"),
    ("purpose", "Purpose"),
    ("indications_and_usage", "Uses"),
    ("warnings", "Warnings"),
    ("do_not_use", "Do not use"),
    ("ask_doctor", "Ask a doctor before use if you have"),
    ("ask_doctor_or_pharmacist", "Ask a doctor or pharmacist before use if you are"),
    ("when_using", "When using this product"),
    ("stop_use", "Stop use and ask a doctor if"),
    ("pregnancy_or_breast_feeding", "If pregnant or breast-feeding"),
    ("keep_out_of_reach_of_children", "Keep out of reach of children"),
    ("dosage_and_administration", "Directions"),
    ("inactive_ingredient", "Inactive ingredients"),
]

PICKS = [
    ("Tylenol Extra Strength", "50580-488-10"),
    ("Children's Tylenol", "50580-139-04"),
    ("Advil", "0573-0165-20"),
    ("Junior Strength Advil", "0573-0179-20"),
    ("Aleve", "0280-6080-20"),
    ("Bayer Low Dose Aspirin", "0280-2090-36"),
    ("Excedrin Extra Strength", "0067-8203-03"),
    ("NyQuil Cold & Flu", "66715-6205-2"),
    ("ZzzQuil", "69423-795-12"),
    ("Benadryl Allergy", "50580-573-04"),
    ("Pepto-Bismol", "76420-490-24"),
]


class LookupError_(Exception):
    pass


def upc_for(ndc10: str) -> str:
    """UPC-A for a 10-digit NDC package code: '3' + NDC + check digit."""
    body = "3" + re.sub(r"\D", "", ndc10)
    odd = sum(int(d) for d in body[0::2])
    even = sum(int(d) for d in body[1::2])
    return body + str((10 - (odd * 3 + even) % 10) % 10)


def ndc_candidates(code: str) -> list[str]:
    raw = code.strip()
    digits = re.sub(r"\D", "", raw)
    if "-" in raw and len(digits) in (10, 11):
        return [raw]
    if len(digits) == 13 and digits.startswith("0"):
        digits = digits[1:]
    if len(digits) == 12:
        if digits[0] != "3":
            raise LookupError_(
                "This barcode is a regular retail UPC, not an NDC barcode, so it can't be "
                "resolved from openFDA alone (that needs the product crosswalk, NOMI-025)."
            )
        core = digits[1:11]
    elif len(digits) == 10:
        core = digits
    elif len(digits) == 11:
        core = ""
        out = []
        if digits[0] == "0":
            c = digits[1:]
            out.append(f"{c[:4]}-{c[4:8]}-{c[8:]}")
        if digits[5] == "0":
            c = digits[:5] + digits[6:]
            out.append(f"{c[:5]}-{c[5:8]}-{c[8:]}")
        if digits[9] == "0":
            c = digits[:9] + digits[10:]
            out.append(f"{c[:5]}-{c[5:9]}-{c[9:]}")
        if out:
            return out
        raise LookupError_("Not a valid 11-digit NDC.")
    else:
        raise LookupError_("Enter a 12-digit UPC barcode or a 10/11-digit NDC.")
    return [
        f"{core[:4]}-{core[4:8]}-{core[8:]}",
        f"{core[:5]}-{core[5:8]}-{core[8:]}",
        f"{core[:5]}-{core[5:9]}-{core[9:]}",
    ]


def openfda(search: str, limit: int = 1) -> list[dict[str, Any]]:
    key = hashlib.sha1(f"{search}|{limit}".encode()).hexdigest()[:16]
    path = CACHE / f"{key}.json"
    if path.exists():
        return list(json.loads(path.read_text()))
    query = urllib.parse.urlencode({"search": search, "limit": limit}, safe=':"()+')
    try:
        with urllib.request.urlopen(f"{OPENFDA}?{query}", timeout=15) as resp:
            results = json.load(resp).get("results", [])
    except urllib.error.HTTPError as err:
        if err.code == 404:
            results = []
        else:
            raise LookupError_(f"openFDA error {err.code}") from err
    except (urllib.error.URLError, TimeoutError) as err:
        raise LookupError_("openFDA is unreachable and this product isn't cached.") from err
    CACHE.mkdir(exist_ok=True)
    path.write_text(json.dumps(results))
    return list(results)


def first(record: dict[str, Any], field: str) -> str:
    value = record.get(field)
    if isinstance(value, list):
        return " ".join(str(v) for v in value)
    return str(value or "")


def brief(record: dict[str, Any]) -> dict[str, Any]:
    o = record.get("openfda", {})
    return {
        "set_id": record.get("set_id"),
        "brand": (o.get("brand_name") or ["Unknown product"])[0],
        "generic": (o.get("generic_name") or [""])[0],
        "manufacturer": (o.get("manufacturer_name") or [""])[0],
    }


def summarize(record: dict[str, Any], scanned_ndc: str | None = None) -> dict[str, Any]:
    o = record.get("openfda", {})
    ndcs = o.get("package_ndc", [])
    ndc = scanned_ndc or (ndcs[0] if ndcs else None)
    return {
        **brief(record),
        "ndc": ndc,
        "upc": upc_for(ndc) if ndc else None,
        "substances": [s.lower() for s in o.get("substance_name", [])],
        "effective_time": record.get("effective_time"),
        "sections": [
            {"field": f, "title": t, "text": first(record, f)} for f, t in SECTIONS if record.get(f)
        ],
        "facts": extract(record).model_dump(),
    }


def by_barcode(code: str) -> dict[str, Any]:
    candidates = ndc_candidates(code)
    search = "(" + "+".join(f'openfda.package_ndc:"{c}"' for c in candidates) + ")"
    results = openfda(search)
    if not results:
        raise LookupError_(f"No openFDA label found for NDC {' / '.join(candidates)}.")
    hit = next(
        (c for c in candidates if c in results[0].get("openfda", {}).get("package_ndc", [])),
        None,
    )
    return summarize(results[0], hit)


def by_name(q: str) -> list[dict[str, Any]]:
    words = re.sub(r"[^\w\s'-]", " ", q).split()
    if not words:
        return []
    phrase = "+".join(words)
    return [brief(r) for r in openfda(f'openfda.brand_name:"{phrase}"+AND+{OTC}', 8)]


def by_set_id(set_id: str) -> dict[str, Any]:
    if not re.fullmatch(r"[0-9a-fA-F-]{36}", set_id):
        raise LookupError_("Bad set id.")
    results = openfda(f'set_id:"{set_id}"')
    if not results:
        raise LookupError_("Label not found.")
    return summarize(results[0])


def picks() -> list[dict[str, Any]]:
    return [{"name": name, "barcode": upc_for(ndc)} for name, ndc in PICKS]


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: bytes, ctype: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        url = urllib.parse.urlparse(self.path)
        params = {k: v[0] for k, v in urllib.parse.parse_qs(url.query).items()}
        try:
            if url.path in ("/", "/index.html"):
                self._send(200, (HERE / "index.html").read_bytes(), "text/html; charset=utf-8")
                return
            if url.path == "/api/barcode":
                data: Any = by_barcode(params.get("code", ""))
            elif url.path == "/api/search":
                data = by_name(params.get("q", ""))
            elif url.path == "/api/label":
                data = by_set_id(params.get("set_id", ""))
            elif url.path == "/api/picks":
                data = picks()
            else:
                self._send(404, b"not found", "text/plain")
                return
            self._send(200, json.dumps(data).encode(), "application/json")
        except LookupError_ as err:
            self._send(404, json.dumps({"error": str(err)}).encode(), "application/json")

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("%s\n" % (fmt % args))


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"Nomi demo on http://localhost:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
