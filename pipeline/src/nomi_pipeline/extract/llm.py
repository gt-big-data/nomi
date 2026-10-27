"""LLM label extraction v1 (NOMI-032).

Sends one openFDA label to Claude with a forced tool call whose input schema is the nine-field
`LabelFacts` definition from packages/schema, then validates the result against the
`label-extraction` schema and checks that every evidence quote really appears in the label.
"""

from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from importlib import resources
from typing import Any

from nomi_schema import errors as schema_errors
from pydantic import BaseModel

from .rules import DOSAGE_FIELDS, INACTIVE_FIELDS, SCANNED_FIELDS, WARNING_RULES

DEFAULT_MODEL = "claude-haiku-4-5"
# USD per million tokens (input, output), from Anthropic's public price list. Check before quoting.
PRICES: dict[str, tuple[float, float]] = {
    "claude-haiku-4-5": (1.0, 5.0),
    "claude-sonnet-4-5": (3.0, 15.0),
}
LABEL_FIELDS = tuple(
    dict.fromkeys(
        (
            "active_ingredient",
            "purpose",
            "indications_and_usage",
            *SCANNED_FIELDS,
            *DOSAGE_FIELDS,
            *INACTIVE_FIELDS,
        )
    )
)
API_URL = "https://api.anthropic.com/v1/messages"
TOOL_NAME = "record_label_facts"

SYSTEM_PROMPT = f"""You read US over-the-counter Drug Facts labels and record their facts.
Rules:
- Only record what the label says. Never add medical knowledge the label doesn't state.
- Every `evidence` value must be copied exactly from the label text, without rewording.
- mandated_warnings: use only these ids, and only when the label carries that warning:
  {", ".join(sorted(r.warning_id for r in WARNING_RULES))}.
- age_limits: `under_years` is the age the rule applies below; `min_years` is the lower bound
  for ranges such as "children 6 to under 12 years: ask a doctor", otherwise null.
- max_daily_doses: the most the label allows in 24 hours, for adults if it lists several ages.
- Use an empty list when the label has nothing for a field.
Call {TOOL_NAME} exactly once."""

Transport = Callable[[dict[str, Any]], dict[str, Any]]


def _schema() -> dict[str, Any]:
    path = resources.files("nomi_schema") / "schemas" / "label-extraction.schema.json"
    loaded: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return loaded


def _inline(node: Any, defs: dict[str, Any]) -> Any:
    """Resolve local $refs so the tool schema is self-contained."""
    if isinstance(node, dict):
        if "$ref" in node:
            return _inline(defs[node["$ref"].rsplit("/", 1)[-1]], defs)
        return {k: _inline(v, defs) for k, v in node.items() if k not in ("title", "$id")}
    if isinstance(node, list):
        return [_inline(v, defs) for v in node]
    return node


def tool_schema() -> dict[str, Any]:
    defs = _schema()["$defs"]
    inlined: dict[str, Any] = _inline(defs["label_facts"], defs)
    return inlined


def prompt_hash() -> str:
    payload = SYSTEM_PROMPT + json.dumps(tool_schema(), sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def label_text(record: dict[str, Any]) -> str:
    parts = []
    for field in LABEL_FIELDS:
        value = record.get(field)
        items = [value] if isinstance(value, str) else value or []
        parts += [f"[{field}] {item}" for item in items]
    return "\n".join(parts)


def request_body(record: dict[str, Any], model: str) -> dict[str, Any]:
    return {
        "model": model,
        "max_tokens": 2048,
        "temperature": 0,
        "system": SYSTEM_PROMPT,
        "tools": [
            {
                "name": TOOL_NAME,
                "description": "Record the facts from one Drug Facts label.",
                "input_schema": tool_schema(),
            }
        ],
        "tool_choice": {"type": "tool", "name": TOOL_NAME},
        "messages": [{"role": "user", "content": label_text(record)}],
    }


def http_transport(api_key: str) -> Transport:
    def send(body: dict[str, Any]) -> dict[str, Any]:
        req = urllib.request.Request(
            API_URL,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            reply: dict[str, Any] = json.load(resp)
            return reply

    return send


def cost_usd(model: str, usage: dict[str, Any]) -> float:
    price_in, price_out = PRICES[model]
    tokens_in = usage.get("input_tokens", 0)
    tokens_out = usage.get("output_tokens", 0)
    return float(tokens_in * price_in + tokens_out * price_out) / 1_000_000


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def unquoted_evidence(facts: dict[str, Any], text: str) -> list[str]:
    """Evidence strings that don't appear in the label, ignoring case and whitespace."""
    haystack = _norm(text)
    return [
        item["evidence"]
        for items in facts.values()
        for item in items
        if isinstance(item, dict) and _norm(str(item.get("evidence", ""))) not in haystack
    ]


class Result(BaseModel):
    set_id: str
    record: dict[str, Any] | None
    cost_usd: float
    errors: list[str]


def extract(record: dict[str, Any], send: Transport, model: str = DEFAULT_MODEL) -> Result:
    set_id = str(record.get("set_id") or "unknown")
    reply = send(request_body(record, model))
    cost = cost_usd(model, reply.get("usage", {}))
    calls = [c for c in reply.get("content", []) if c.get("type") == "tool_use"]
    if not calls:
        return Result(set_id=set_id, record=None, cost_usd=cost, errors=["no tool call in reply"])
    out = {
        "set_id": set_id,
        "model_id": reply.get("model", model),
        "prompt_hash": prompt_hash(),
        "extracted_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "facts": calls[0]["input"],
    }
    problems = [f"schema: {e}" for e in schema_errors("label-extraction", out)]
    if not problems:
        problems = [
            f"evidence not in label: {q!r}"
            for q in unquoted_evidence(out["facts"], label_text(record))
        ]
    return Result(set_id=set_id, record=out, cost_usd=cost, errors=problems)


class Report(BaseModel):
    model_id: str
    prompt_hash: str
    labels: int
    failed: int
    total_cost_usd: float
    cost_per_label_usd: float
    projected_cost_usd: float
    in_scope_labels: int
    failures: dict[str, list[str]]


def report(results: Iterable[Result], model: str, in_scope_labels: int) -> Report:
    rs = list(results)
    total = sum(r.cost_usd for r in rs)
    per = total / len(rs) if rs else 0.0
    return Report(
        model_id=model,
        prompt_hash=prompt_hash(),
        labels=len(rs),
        failed=sum(1 for r in rs if r.errors),
        total_cost_usd=round(total, 4),
        cost_per_label_usd=round(per, 6),
        projected_cost_usd=round(per * in_scope_labels, 2),
        in_scope_labels=in_scope_labels,
        failures={r.set_id: r.errors for r in rs if r.errors},
    )
