#!/usr/bin/env python3
"""Create GitHub labels, milestones and issues from planning/backlog.md.

Requires the GitHub CLI (`gh`) authenticated with access to the repo.
Idempotent: existing labels and milestones are kept, and existing issues (matched by the
Backlog ID in their body) are updated in place instead of duplicated. Every issue's title,
body, milestone and labels are synced from the backlog, with NOMI-XXX references turned
into #issue links and a list of the tickets each one blocks.
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


REPO_URL = "https://github.com/gt-big-data/nomi/blob/main"
NOT_JOINABLE = ("-", "*", "#", "|", "`", ">")
LIST_START_RE = re.compile(r"^\s*(?:[-*]|\d+\.)\s")


def unwrap(text):
    """Join hard-wrapped prose lines; GitHub renders each newline in an issue as a line break."""
    out = []
    in_code = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            out.append(line)
            continue
        prev = out[-1].strip() if out else ""
        joinable = (
            not in_code
            and stripped
            and prev
            and not stripped.startswith(NOT_JOINABLE)
            and not LIST_START_RE.match(line)
            and not prev.startswith(("#", "|", "```"))
        )
        if joinable:
            out[-1] = out[-1].rstrip() + " " + stripped
        else:
            out.append(line)
    return "\n".join(out)


def issue_body(ticket, refs, blocks):
    meta = ticket["meta"]
    sprint_title = MILESTONES[meta["sprint"]][0]
    team = TEAMS[meta["team"]][0]
    depends = link(meta.get("depends on", "none"), refs)
    blocked = ", ".join(refs.get(b, b) for b in blocks) or "none"
    lines = [
        f"**{sprint_title}** | {team} | {meta['priority']}  ",
        f"Depends on: {depends} | Blocks: {blocked}",
        "",
        link(unwrap(ticket["body"]), refs),
        "",
        f"<sub>{ticket['id']}. New to Nomi? Read [Nomi 101]({REPO_URL}/docs/nomi-101.md).</sub>",
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

    backlog_id_re = re.compile(r"(?:\*\*Backlog ID:\*\* |<sub>)(NOMI-\d{3})")
    existing = {}
    for issue in gh_json("issue", "list", "--state", "all", "--limit", "500", "--json", "number,title,body"):
        found = backlog_id_re.search(issue["body"] or "")
        if found:
            existing[found.group(1)] = issue["number"]

    refs = {t["id"]: f"#{existing[t['id']]}" for t in tickets if t["id"] in existing}
    for t in tickets:
        if t["id"] in refs:
            continue
        cmd = ["issue", "create", "--title", t["title"], "--body", issue_body(t, {}, blocks[t["id"]]),
               "--milestone", MILESTONES[t["meta"]["sprint"]][0]]
        for label in labels_for(t):
            cmd += ["--label", label]
        url = gh(*cmd).strip()
        refs[t["id"]] = f"#{url.rsplit('/', 1)[-1]}"
        print(f"created    {refs[t['id']]}  {t['title']}")
        time.sleep(WRITE_DELAY_SECONDS)

    # Second pass: every ticket has a number now. Sync title, body, milestone and labels,
    # linking NOMI-XXX references to issue numbers.
    for t in tickets:
        cmd = ["issue", "edit", refs[t["id"]].lstrip("#"), "--title", t["title"],
               "--body", issue_body(t, refs, blocks[t["id"]]),
               "--milestone", MILESTONES[t["meta"]["sprint"]][0]]
        for label in labels_for(t):
            cmd += ["--add-label", label]
        gh(*cmd)
        print(f"updated    {refs[t['id']]}  {t['title']}", flush=True)
        time.sleep(WRITE_DELAY_SECONDS)

    print(f"\nDone: {len(tickets)} issues synced.")


if __name__ == "__main__":
    main()
