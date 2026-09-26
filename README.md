# Habitude

A small full-stack habit tracker, built as a capstone demo of **spec-driven, AI-assisted development**.

Habitude lets a person create habits, check them off each day, keep streaks, and see their consistency over time. It runs entirely on a laptop: a FastAPI backend with SQLite and a React frontend, no external services.

## Why this repo exists

The point of the project is not the habit tracker. It is to show how a team prepares a codebase so that AI coding agents can do the work reliably:

- Every feature starts as a written spec with prioritized user stories and testable acceptance scenarios.
- A project constitution defines non-negotiable principles (spec-first, test-first, simplicity, accessibility, local-first).
- Coding standards, testing strategy, and frontend guidelines are written down before the first line of code.
- Agent instructions, reusable prompts, and custom agents live in the repo alongside the docs.

The workflow is [GitHub Spec Kit](https://github.com/github/spec-kit), installed in a Python virtual environment and wired into GitHub Copilot.

## Status

**Phase 1: MVP implementation in progress.**

Specs, docs, constitution, prompts, and agents are in place. Application code in `src/backend/` and `src/frontend/` is produced by running the Spec Kit workflow feature by feature; the Status column in [docs/specs/README.md](docs/specs/README.md) shows which specs are implemented.

## Features (specs)

| # | Feature | Spec |
|---|---------|------|
| 001 | User Accounts | [docs/specs/001-user-accounts/spec.md](docs/specs/001-user-accounts/spec.md) |
| 002 | Habit Management | [docs/specs/002-habit-management/spec.md](docs/specs/002-habit-management/spec.md) |
| 003 | Daily Check-In | [docs/specs/003-daily-check-in/spec.md](docs/specs/003-daily-check-in/spec.md) |
| 004 | Streak Tracking | [docs/specs/004-streak-tracking/spec.md](docs/specs/004-streak-tracking/spec.md) |
| 005 | Habit Schedules | [docs/specs/005-habit-schedules/spec.md](docs/specs/005-habit-schedules/spec.md) |
| 006 | Today Dashboard | [docs/specs/006-today-dashboard/spec.md](docs/specs/006-today-dashboard/spec.md) |
| 007 | History Calendar | [docs/specs/007-history-calendar/spec.md](docs/specs/007-history-calendar/spec.md) |
| 008 | Reminders | [docs/specs/008-reminders/spec.md](docs/specs/008-reminders/spec.md) |
| 009 | Stats & Insights | [docs/specs/009-stats-insights/spec.md](docs/specs/009-stats-insights/spec.md) |
| 010 | Categories & Tags | [docs/specs/010-categories-tags/spec.md](docs/specs/010-categories-tags/spec.md) |
| 011 | Data Export & Import | [docs/specs/011-data-export/spec.md](docs/specs/011-data-export/spec.md) |
| 012 | Settings & Preferences | [docs/specs/012-settings-preferences/spec.md](docs/specs/012-settings-preferences/spec.md) |
| 013 | PR Analysis Pipeline | [docs/specs/013-pr-analysis-pipeline/spec.md](docs/specs/013-pr-analysis-pipeline/spec.md) |

See [docs/specs/README.md](docs/specs/README.md) for the spec index and the suggested build order.

## Tech stack

| Layer | Choice |
|-------|--------|
| Backend | Python 3.13, FastAPI, SQLModel, SQLite, Alembic |
| Backend quality | pytest, ruff, mypy `--strict` |
| Frontend | TypeScript (strict), React 19, Vite, TanStack Query, React Router |
| Frontend quality | Vitest + Testing Library, Playwright, ESLint, Prettier |
| Workflow | GitHub Spec Kit (`specify-cli`), GitHub Copilot skills, prompts, and custom agents |

The full constraints are in [.specify/memory/constitution.md](.specify/memory/constitution.md).

## Repository layout

```
AGENTS.md                 # instructions every AI agent reads first
README.md
.github/
  copilot-instructions.md # points to AGENTS.md
  skills/speckit-*/       # Spec Kit skills for Copilot Chat
  prompts/                # reusable prompt files
  agents/                 # custom Copilot agents
.specify/                 # Spec Kit config, scripts, templates, constitution
docs/                     # architecture, coding standards, testing, frontend, workflow
docs/specs/NNN-name/      # one folder per feature
src/backend/              # FastAPI app
src/frontend/             # React app
requirements-tooling.txt  # deps for the .venv (specify-cli)
```

## Getting started

Requirements: Python 3.13, [uv](https://docs.astral.sh/uv/), Node 22 LTS, VS Code with GitHub Copilot.

```bash
git clone <this-repo> habitude && cd habitude

# tooling venv with specify-cli
uv venv .venv --python 3.13
uv pip install --python .venv/bin/python -r requirements-tooling.txt

# verify
.venv/bin/specify check

# backend deps, database, and dev server (http://localhost:8000)
uv pip install --python .venv/bin/python -r src/backend/pyproject.toml --extra dev
cd src/backend && ../../.venv/bin/alembic upgrade head && ../../.venv/bin/uvicorn app.main:app --reload

# frontend dev server in another terminal (http://localhost:5173)
cd src/frontend && npm install && npm run dev
```

See [AGENTS.md](AGENTS.md) for test, lint, and type-check commands.

## Using the Spec Kit workflow

Open the repo in VS Code and use Copilot Chat. The skills installed under `.github/skills/` expose these commands:

```
/speckit-specify  Users can snooze a reminder for 10 minutes   # new spec under docs/specs/014-...
/speckit-clarify                                                # resolve open questions in the spec
/speckit-plan                                                   # plan.md, research.md, data-model.md, contracts/
/speckit-tasks                                                  # tasks.md
/speckit-analyze                                                # consistency check
/speckit-implement                                              # tests first, then code
```

Specs are written to `docs/specs/` (the default `specs/` location was changed for this repo). Details, manual script usage, and troubleshooting are in [docs/spec-kit-workflow.md](docs/spec-kit-workflow.md).

## Documentation

- [docs/README.md](docs/README.md) — documentation index and reading order
- [docs/architecture.md](docs/architecture.md) — system overview
- [docs/coding-standards.md](docs/coding-standards.md) — conventions for backend and frontend
- [docs/testing.md](docs/testing.md) — test strategy and gates
- [docs/frontend.md](docs/frontend.md) — frontend structure, state, styling, accessibility
- [docs/spec-kit-workflow.md](docs/spec-kit-workflow.md) — how Spec Kit is set up and used here
- [AGENTS.md](AGENTS.md) — rules for AI agents

## License

MIT (placeholder; add a `LICENSE` file before publishing).
