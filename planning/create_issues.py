#!/usr/bin/env python3
"""Create GitHub labels, milestones and issues from planning/backlog.md.

Requires the GitHub CLI (`gh`) authenticated with access to the repo.
Idempotent: existing labels, milestones and issues (matched by title) are skipped.
After creating issues, every issue body is rewritten so NOMI-XXX references become
#issue links and each issue lists the tickets it blocks.
"""

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

BACKLOG = Path(__file__).with_name("backlog.md")

# GitHub limits content-creating requests (roughly 80 per minute), so pace writes.
WRITE_DELAY_SECONDS = 1.0

MILESTONES = {
    "S1": ("Sprint 1 (Oct 16-22)", "2026-10-22", "Foundations: repo, contracts, ADRs, raw data mirror, scanner, risk dimension definitions."),
    "S2": ("Sprint 2 (Oct 23-29)", "2026-10-29", "Identity resolver, label sections, FAERS ingest, knowledge base for the demo aisles, core app screens."),
    "S3": ("Sprint 3 (Oct 30-Nov 5)", "2026-11-05", "Label extraction, uses, rubric spec, dataset builder v1, on-device lookup and profiles."),
    "S4": ("Sprint 4 (Nov 6-12)", "2026-11-12", "Scoring, benchmarks, alternatives, signals, on-device engine. Feature freeze Nov 12."),
    "S5": ("Sprint 5 (Nov 13-19)", "2026-11-19", "Hardening, performance, blind test, rehearsals. Code freeze Nov 17, demo Nov 20."),
}

TEAMS = {
    "platform": ("Platform", "7f7f7f", "Backend: data engineering, contracts, dataset build and release"),
    "visualization": ("Visualization", "e377c2", "Frontend: app UI, scanner, on-device scoring, dashboards"),
    "data-analysis": ("Data Analysis", "1f77b4", "Extraction, knowledge base, signals, scoring models"),
    "cofounders": ("Cofounders", "8c564b", "Process, legal, clinical partnership, demo"),
    "all": ("Everyone", "0e8a16", "Every team member contributes"),
}

LABELS = {f"team:{key}": (color, description) for key, (_, color, description) in TEAMS.items()}
LABELS.update({
    "P0": ("b60205", "Blocks the demo"),
    "P1": ("fbca04", "Should land in its sprint"),
})

HEADER_RE = re.compile(r"^## (NOMI-\d{3}): (.+)$")
META_RE = re.compile(r"\*\*([\w ]+):\*\* ([^|]+)")
ID_RE = re.compile(r"NOMI-\d{3}")


def parse_backlog(text):
    tickets = []
    current = None
    for line in text.splitlines():
        header = HEADER_RE.match(line)
        if header:
            current = {"id": header.group(1), "title": header.group(2).strip(), "meta": None, "body": []}
            tickets.append(current)
        elif current is None:
            continue
        elif line.startswith("# ") or line.strip() == "---":
            current = None
        elif current["meta"] is None and line.startswith("**Team:**"):
            current["meta"] = {k.strip().lower(): v.strip() for k, v in META_RE.findall(line)}
        else:
            current["body"].append(line)
    for t in tickets:
        if t["meta"] is None:
            sys.exit(f"{t['id']} is missing its metadata line")
        t["body"] = "\n".join(t["body"]).strip()
        t["deps"] = ID_RE.findall(t["meta"].get("depends on", ""))
    return tickets


def gh(*args):
    return subprocess.run(["gh", *args], check=True, text=True, capture_output=True).stdout


def gh_json(*args):
    return json.loads(gh(*args) or "null")


def link(text, refs):
    return ID_RE.sub(lambda m: refs.get(m.group(0), m.group(0)), text)


def unwrap(text):
    """Join hard-wrapped prose lines; GitHub renders each newline in an issue as a line break."""
    out = []
    for line in text.splitlines():
        is_prose = bool(line.strip()) and not line.lstrip().startswith(("-", "*", "#", "|", "`"))
        prev_is_prose = bool(out) and bool(out[-1].strip()) and not out[-1].lstrip().startswith(("-", "*", "#", "|", "`"))
        if is_prose and prev_is_prose:
            out[-1] += " " + line.strip()
        else:
            out.append(line)
    return "\n".join(out)


def issue_body(ticket, refs, blocks):
    meta = ticket["meta"]
    sprint_title = MILESTONES[meta["sprint"]][0]
    team = TEAMS[meta["team"]][0]
    lines = [
        f"**Sprint:** {sprint_title}  ",
        f"**Team:** {team}  ",
        f"**Priority:** {meta['priority']}  ",
        f"**Depends on:** {link(meta.get('depends on', 'none'), refs)}  ",
        f"**Blocks:** {', '.join(refs.get(b, b) for b in blocks) or 'none'}  ",
        f"**Backlog ID:** {ticket['id']}",
        "",
        link(unwrap(ticket["body"]), refs),
        "",
        "Full plan: `planning/backlog.md`. Dependencies marked (same sprint) can start against the "
        "reference products in `packages/schema/examples/` or a fixture.",
    ]
    return "\n".join(lines) + "\n"


def labels_for(ticket):
    meta = ticket["meta"]
    labels = [f"team:{meta['team']}", meta["priority"]]
    if "extra" in meta:
        labels.append(meta["extra"])
    return labels


def validate(tickets):
    ids = {t["id"] for t in tickets}
    by_id = {t["id"]: t for t in tickets}
    for t in tickets:
        meta = t["meta"]
        if meta.get("sprint") not in MILESTONES:
            sys.exit(f"{t['id']} has unknown sprint {meta.get('sprint')}")
        if meta.get("team") not in TEAMS:
            sys.exit(f"{t['id']} has unknown team {meta.get('team')}")
        for dep in t["deps"]:
            if dep not in ids:
                sys.exit(f"{t['id']} depends on unknown ticket {dep}")
            if by_id[dep]["meta"]["sprint"] > meta["sprint"]:
                sys.exit(f"{t['id']} depends on {dep}, which is in a later sprint")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="print what would be created")
    args = parser.parse_args()

    tickets = parse_backlog(BACKLOG.read_text())
    validate(tickets)
    blocks = {t["id"]: [] for t in tickets}
    for t in tickets:
        for dep in t["deps"]:
            blocks[dep].append(t["id"])

    if args.dry_run:
        for t in tickets:
            print(f"{t['id']}  {t['meta']['sprint']}  [{', '.join(labels_for(t))}]  {t['title']}")
        print(f"\n{len(tickets)} issues, {len(LABELS)} labels, {len(MILESTONES)} milestones")
        return

    existing_labels = {l["name"] for l in gh_json("label", "list", "--limit", "200", "--json", "name")}
    for name, (color, description) in LABELS.items():
        if name not in existing_labels:
            gh("label", "create", name, "--color", color, "--description", description)
            print(f"label      {name}")

    existing_milestones = {m["title"] for m in gh_json("api", "repos/{owner}/{repo}/milestones?state=all&per_page=100")}
    for title, due, description in MILESTONES.values():
        if title not in existing_milestones:
            gh("api", "repos/{owner}/{repo}/milestones", "-f", f"title={title}",
               "-f", f"due_on={due}T23:59:59Z", "-f", f"description={description}")
            print(f"milestone  {title}")

    existing_issues = {
        i["title"]: i["number"]
        for i in gh_json("issue", "list", "--state", "all", "--limit", "500", "--json", "title,number")
    }
    refs = {}
    for t in tickets:
        if t["title"] in existing_issues:
            refs[t["id"]] = f"#{existing_issues[t['title']]}"
            continue
        cmd = ["issue", "create", "--title", t["title"], "--body", issue_body(t, {}, blocks[t["id"]]),
               "--milestone", MILESTONES[t["meta"]["sprint"]][0]]
        for label in labels_for(t):
            cmd += ["--label", label]
        url = gh(*cmd).strip()
        refs[t["id"]] = f"#{url.rsplit('/', 1)[-1]}"
        print(f"issue      {refs[t['id']]}  {t['title']}")
        time.sleep(WRITE_DELAY_SECONDS)

    # Second pass: every ticket now has a number, so link dependencies and blockers.
    for t in tickets:
        gh("issue", "edit", refs[t["id"]].lstrip("#"), "--body", issue_body(t, refs, blocks[t["id"]]))
        time.sleep(WRITE_DELAY_SECONDS)

    print(f"\nDone: {len(tickets)} issues linked.")


if __name__ == "__main__":
    main()
