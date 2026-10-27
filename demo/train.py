"""Train the demo's two small models on bulk openFDA OTC labels.

1. Warning predictor: TF-IDF over a product's active ingredients and uses -> one-vs-rest
   logistic regression predicting which mandated warnings its label should carry. Targets
   are weak labels from the NOMI-031 rule extractor run on the warnings text, so the model
   never sees the warnings themselves. Used to flag labels with missing/garbled warnings.
2. Alternatives index: TF-IDF over uses/purpose + nearest neighbours, to suggest products
   for the same symptoms with fewer risk flags.

  uv run --with scikit-learn --with joblib python demo/train.py ~/nomi-data/otc_labels.jsonl
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from nomi_pipeline.extract.rules import extract
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.multiclass import OneVsRestClassifier
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import FeatureUnion, make_pipeline

OUT = Path(__file__).resolve().parent / "model"
WARNING_FIELDS = [
    "warnings",
    "do_not_use",
    "ask_doctor",
    "ask_doctor_or_pharmacist",
    "stop_use",
    "pregnancy_or_breast_feeding",
    "when_using",
]
MIN_POSITIVES = 40


def text(record: dict[str, Any], *fields: str) -> str:
    return " ".join(" ".join(record.get(f) or []) for f in fields)


def features(record: dict[str, Any]) -> str:
    subs = " ".join(record.get("openfda", {}).get("substance_name") or [])
    return f"{subs} {text(record, 'active_ingredient', 'purpose', 'indications_and_usage')}"


def main(path: str) -> None:
    rows, seen = [], set()
    with open(path, encoding="utf-8") as fh:
        lines = fh.readlines()
    for line in lines:
        r = json.loads(line)
        key = (tuple(r.get("openfda", {}).get("brand_name") or []), text(r, "active_ingredient"))
        if r.get("set_id") in seen or key in seen or not text(r, "warnings").strip():
            continue
        seen.update([r.get("set_id"), key])
        rows.append(r)
    print(f"{len(rows)} unique OTC labels with a warnings section")

    targets = [
        sorted(extract({f: r[f] for f in WARNING_FIELDS if f in r}).warning_ids()) for r in rows
    ]
    counts = Counter(w for t in targets for w in t)
    labels = sorted(w for w, c in counts.items() if c >= MIN_POSITIVES)
    print("label counts:", {w: counts[w] for w in labels})
    Y = np.array([[w in t for w in labels] for t in targets], dtype=int)
    X = [features(r) for r in rows]

    X_tr, X_te, Y_tr, Y_te = train_test_split(X, Y, test_size=0.2, random_state=7)
    vec = FeatureUnion(
        [
            ("word", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
            (
                "char",
                TfidfVectorizer(
                    analyzer="char_wb", ngram_range=(3, 5), min_df=3, sublinear_tf=True
                ),
            ),
        ]
    )
    model = make_pipeline(
        vec, OneVsRestClassifier(LogisticRegression(C=4, max_iter=2000, class_weight="balanced"))
    )
    model.fit(X_tr, Y_tr)
    P = model.predict(X_te)
    metrics: dict[str, Any] = {
        "n_labels_trained": len(X_tr),
        "n_labels_test": len(X_te),
        "micro_f1": round(float(f1_score(Y_te, P, average="micro")), 3),
        "macro_f1": round(float(f1_score(Y_te, P, average="macro")), 3),
        "per_warning": {
            w: {
                "precision": round(float(precision_score(Y_te[:, i], P[:, i], zero_division=0)), 3),
                "recall": round(float(recall_score(Y_te[:, i], P[:, i], zero_division=0)), 3),
                "test_positives": int(Y_te[:, i].sum()),
            }
            for i, w in enumerate(labels)
        },
    }
    print(json.dumps(metrics, indent=2))
    model.fit(X, Y)

    uses = [text(r, "purpose", "indications_and_usage") for r in rows]
    use_vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, stop_words="english", sublinear_tf=True)
    U = use_vec.fit_transform(uses)
    nn = NearestNeighbors(n_neighbors=40, metric="cosine").fit(U)
    catalog = [
        {
            "set_id": r.get("set_id"),
            "brand": (r.get("openfda", {}).get("brand_name") or ["?"])[0],
            "generic": (r.get("openfda", {}).get("generic_name") or [""])[0],
            "manufacturer": (r.get("openfda", {}).get("manufacturer_name") or [""])[0],
            "warnings": t,
        }
        for r, t in zip(rows, targets, strict=True)
    ]

    OUT.mkdir(exist_ok=True)
    joblib.dump({"model": model, "labels": labels}, OUT / "warning_model.joblib", compress=3)
    joblib.dump(
        {"vec": use_vec, "nn": nn, "catalog": catalog}, OUT / "alternatives.joblib", compress=3
    )
    (OUT / "metrics.json").write_text(
        json.dumps(
            {
                **metrics,
                "labels": labels,
                "source": "openFDA drug/label, product_type HUMAN OTC DRUG",
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main(sys.argv[1])
