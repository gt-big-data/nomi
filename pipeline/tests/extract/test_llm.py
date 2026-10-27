"""LLM extraction (NOMI-032), with the Anthropic API replaced by a stub."""

from typing import Any

from nomi_pipeline.extract import llm

LABEL: dict[str, Any] = {
    "set_id": "abc-123",
    "active_ingredient": ["Acetaminophen 500 mg"],
    "purpose": ["Pain reliever"],
    "warnings": [
        "Liver warning: This product contains acetaminophen. Severe liver damage may occur."
    ],
    "do_not_use": ["with any other drug containing acetaminophen"],
}

FACTS: dict[str, Any] = {
    "active_ingredients": [
        {"name": "acetaminophen", "strength": "500 mg", "evidence": "Acetaminophen 500 mg"}
    ],
    "uses": [],
    "mandated_warnings": [
        {
            "warning_id": "liver_warning",
            "evidence": "Liver warning: This product contains acetaminophen.",
        }
    ],
    "do_not_use": [
        {"text": "other acetaminophen", "evidence": "with any other drug containing acetaminophen"}
    ],
    "ask_doctor": [],
    "drug_interactions": [],
    "age_limits": [],
    "max_daily_doses": [],
    "allergens": [],
}


def stub(facts: dict[str, Any]) -> llm.Transport:
    def send(body: dict[str, Any]) -> dict[str, Any]:
        assert body["tool_choice"]["name"] == llm.TOOL_NAME
        assert "Acetaminophen 500 mg" in body["messages"][0]["content"]
        return {
            "model": body["model"],
            "content": [{"type": "tool_use", "name": llm.TOOL_NAME, "input": facts}],
            "usage": {"input_tokens": 2000, "output_tokens": 400},
        }

    return send


def test_tool_schema_has_nine_fields_and_no_refs() -> None:
    schema = llm.tool_schema()
    assert len(schema["required"]) == 9
    assert "$ref" not in str(schema)


def test_prompt_hash_is_stable_sha256() -> None:
    assert llm.prompt_hash() == llm.prompt_hash()
    assert len(llm.prompt_hash()) == 64


def test_valid_extraction_records_model_and_prompt_hash() -> None:
    result = llm.extract(LABEL, stub(FACTS))
    assert result.errors == []
    assert result.record is not None
    assert result.record["model_id"] == llm.DEFAULT_MODEL
    assert result.record["prompt_hash"] == llm.prompt_hash()
    assert result.cost_usd == (2000 * 1.0 + 400 * 5.0) / 1_000_000


def test_schema_violation_is_reported() -> None:
    bad = {**FACTS, "allergens": None}
    result = llm.extract(LABEL, stub(bad))
    assert result.errors and result.errors[0].startswith("schema:")


def test_invented_evidence_is_reported() -> None:
    made_up = {**FACTS, "allergens": [{"text": "peanuts", "evidence": "contains peanut oil"}]}
    result = llm.extract(LABEL, stub(made_up))
    assert result.errors == ["evidence not in label: 'contains peanut oil'"]


def test_reply_without_tool_call_fails() -> None:
    result = llm.extract(LABEL, lambda body: {"content": [], "usage": {}})
    assert result.record is None
    assert result.errors == ["no tool call in reply"]


def test_report_projects_cost() -> None:
    results = [llm.extract(LABEL, stub(FACTS)) for _ in range(4)]
    results.append(llm.extract(LABEL, stub({**FACTS, "uses": None})))
    rep = llm.report(results, llm.DEFAULT_MODEL, in_scope_labels=25_000)
    assert rep.labels == 5
    assert rep.failed == 1
    assert rep.cost_per_label_usd == 0.004
    assert rep.projected_cost_usd == 100.0
