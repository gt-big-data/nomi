"""Pull every openFDA HUMAN OTC DRUG label (about 25k) into a JSONL file for train.py.

usage: python demo/pull_labels.py ~/nomi-data/otc_labels.jsonl
"""

import json
import sys
import time
import urllib.parse
import urllib.request
from typing import Any

FIELDS = [
    "warnings",
    "do_not_use",
    "ask_doctor",
    "ask_doctor_or_pharmacist",
    "stop_use",
    "pregnancy_or_breast_feeding",
    "when_using",
    "dosage_and_administration",
    "active_ingredient",
    "purpose",
    "indications_and_usage",
    "inactive_ingredient",
    "keep_out_of_reach_of_children",
]
OPENFDA = ["brand_name", "generic_name", "manufacturer_name", "substance_name", "package_ndc"]
SEARCH = 'openfda.product_type:"HUMAN OTC DRUG"'


def page(skip: int) -> list[dict[str, Any]]:
    q = urllib.parse.urlencode({"search": SEARCH, "limit": 1000, "skip": skip})
    for _ in range(3):
        try:
            with urllib.request.urlopen(
                f"https://api.fda.gov/drug/label.json?{q}", timeout=60
            ) as r:
                results: list[dict[str, Any]] = json.load(r)["results"]
                return results
        except Exception as e:  # openFDA rate-limits and times out under load; retry
            print("retry", skip, e, file=sys.stderr)
            time.sleep(5)
    return []


def main(path: str) -> None:
    n = 0
    with open(path, "w", encoding="utf-8") as out:
        for skip in range(0, 25000, 1000):
            results = page(skip)
            if not results:
                break
            for x in results:
                o = x.get("openfda", {})
                row = {"set_id": x.get("set_id"), "openfda": {k: o.get(k) for k in OPENFDA}}
                row.update({f: x[f] for f in FIELDS if f in x})
                out.write(json.dumps(row) + "\n")
                n += 1
            print(skip, n, flush=True)
            time.sleep(0.5)
    print("done", n)


if __name__ == "__main__":
    main(sys.argv[1])
