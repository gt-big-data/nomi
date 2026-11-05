# Contributing to Nomi

## Prerequisites

- macOS or Linux. On Windows, install [WSL](https://learn.microsoft.com/windows/wsl/install) and run everything inside it.
- Node 22 (we recommend [nvm](https://github.com/nvm-sh/nvm): run `nvm install` in the repo)
- [uv](https://docs.astral.sh/uv/) (`brew install uv` on macOS). uv installs Python 3.12 for you.
- Enable pnpm: `corepack enable`

If `corepack` fails with "Cannot find matching keyid", run `npm install -g corepack@latest`.

## Setup

```bash
git clone https://github.com/gt-big-data/nomi.git
cd nomi
pnpm install
uv sync
uv run pre-commit install
```

Pre-commit checks run automatically on every commit.

## Workflow

1. Pick an issue assigned to you.
2. Branch from `main`: `feat/NOMI-0xx-short-name`, `fix/...` or `chore/...`
3. Commit small, focused changes.
4. Push and open a PR. Put `Closes #<issue number>` in the description.
5. CI must pass and one reviewer must approve. PRs are squash-merged.

## Running checks yourself

```bash
uv run pre-commit run --all-files   # lint and format everything
uv run pytest pipeline              # Python tests
pnpm lint && pnpm typecheck && pnpm test   # JS/TS packages
```

## Rules

- Never commit data. Raw and generated data lives in `data/` and is gitignored.
- Health data never leaves the device (see ADR-0002).
- Changes to `packages/schema` need review from both Platform and Data Analysis.
- Architecture decisions go in `docs/adr/` before code depends on them.
