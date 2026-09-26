# Spec Kit workflow in this repo

This guide explains how [GitHub Spec Kit](https://github.com/github/spec-kit) is installed and used in Habitude. For the principles behind the workflow, read the [constitution](../.specify/memory/constitution.md).

## What is installed and where

| Item | Location | Notes |
|------|----------|-------|
| `specify-cli` | `.venv/bin/specify` | Installed from `git+https://github.com/github/spec-kit.git` via `requirements-tooling.txt` |
| Spec Kit config | `.specify/init-options.json`, `.specify/integration.json` | Integration: `copilot`, scripts: `sh`, numbering: `sequential` |
| Constitution | `.specify/memory/constitution.md` | Project principles; edit only via PR |
| Templates | `.specify/templates/` | `spec-template.md`, `plan-template.md`, `tasks-template.md`, `checklist-template.md`, `constitution-template.md` |
| Scripts | `.specify/scripts/bash/` | `create-new-feature.sh`, `check-prerequisites.sh`, `setup-plan.sh`, `setup-tasks.sh`, `resolve-template.sh`, `common.sh` |
| Copilot skills | `.github/skills/speckit-*/SKILL.md` | Exposed in Copilot Chat as `/speckit-*` commands |
| Feature specs | `docs/specs/NNN-name/` | See below |

The project was initialized with:

```bash
.venv/bin/specify init --here --force --non-interactive --integration copilot --script sh --ignore-agent-tools
```

## Why specs live under `docs/specs/`

Spec Kit defaults to a top-level `specs/` folder. This repo keeps all documentation, including specs, under `docs/`, so two files were patched after `specify init`:

1. `.specify/scripts/bash/create-new-feature.sh` — the line `SPECS_DIR="$REPO_ROOT/specs"` now reads `SPECS_DIR="$REPO_ROOT/docs/specs"`.
2. `.github/skills/speckit-specify/SKILL.md` — every mention of `specs/` was changed to `docs/specs/` so the skill scans and writes the right folder.

The other scripts resolve the feature folder from `.specify/feature.json` (written by `create-new-feature.sh`) or from the `SPECIFY_FEATURE_DIRECTORY` environment variable, so they needed no change.

If you ever re-run `specify init` or upgrade the skills, re-apply both patches. Never create a top-level `specs/` folder.

## Step-by-step workflow

All commands run in VS Code Copilot Chat. Each feature moves through the steps in order; optional steps are marked.

### 1. Specify

```
/speckit-specify Users can snooze a reminder for 10 minutes from the notification banner
```

Produces `docs/specs/014-snooze-reminder/spec.md` from `spec-template.md` (next free number is chosen automatically). The spec has prioritized user stories, acceptance scenarios, functional requirements with `FR-xxx` ids, key entities, success criteria, and assumptions. Anything unknown is marked `[NEEDS CLARIFICATION: ...]`.

The `.github/prompts/new-feature-spec.prompt.md` prompt and the `.github/agents/spec-writer.agent.md` agent wrap this step with project-specific guidance.

### 2. Clarify (optional, recommended)

```
/speckit-clarify
```

Asks up to a handful of structured questions about ambiguous areas and edits the spec in place. Run it until no `[NEEDS CLARIFICATION]` markers remain; planning is blocked while they exist.

### 3. Plan

```
/speckit-plan
```

Produces, inside the feature folder:

- `plan.md` — technical approach, constitution check, project structure, complexity tracking
- `research.md` — decisions and alternatives considered
- `data-model.md` — entities, fields, relationships, validation rules
- `quickstart.md` — how to run and verify the feature
- `contracts/` — API contract files (OpenAPI fragments or endpoint descriptions)

### 4. Tasks

```
/speckit-tasks
```

Produces `tasks.md`: dependency-ordered tasks grouped by user story, each small enough to complete and test independently, with test tasks before implementation tasks.

### 5. Analyze (optional)

```
/speckit-analyze
```

Reports inconsistencies between spec, plan, and tasks (missing coverage of an FR, tasks with no story, constitution violations). Fix findings before implementing.

### 6. Checklist (optional)

```
/speckit-checklist
```

Generates `checklists/*.md` for requirement completeness and clarity.

### 7. Implement

```
/speckit-implement
```

Executes `tasks.md` in order: writes failing tests from acceptance scenarios, then the code, then refactors. Use `.github/prompts/implement-task.prompt.md` to run a single task instead of the whole list, and `.github/agents/test-engineer.agent.md` to derive or audit tests.

### 8. Converge

```
/speckit-converge
```

Compares the codebase to the spec and appends any remaining work as new tasks.

## Running the scripts manually

Useful for debugging or when working outside Copilot.

```bash
# create the next feature folder + spec.md from a description
.specify/scripts/bash/create-new-feature.sh "Users can snooze a reminder for 10 minutes"

# same, with an explicit short name and number, JSON output
.specify/scripts/bash/create-new-feature.sh --json --short-name snooze-reminder --number 13 "Snooze reminders"

# preview without writing anything
.specify/scripts/bash/create-new-feature.sh --dry-run "Snooze reminders"

# print resolved paths for the current feature (used by plan/tasks steps)
.specify/scripts/bash/check-prerequisites.sh --json --paths-only

# validate that plan.md (and optionally tasks.md) exist before a step
.specify/scripts/bash/check-prerequisites.sh --json
.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
```

### Targeting a specific feature

The scripts locate the active feature from `.specify/feature.json` (git-ignored, written by `create-new-feature.sh`). To work on a different feature, or when that file is missing, set the override:

```bash
export SPECIFY_FEATURE_DIRECTORY=docs/specs/003-daily-check-in
.specify/scripts/bash/check-prerequisites.sh --json --paths-only
```

The path is relative to the repo root; an absolute path also works.

## Upgrading `specify-cli`

```bash
uv pip install --python .venv/bin/python --upgrade --force-reinstall "specify-cli @ git+https://github.com/github/spec-kit.git"
.venv/bin/specify version
```

Upgrading the CLI does not rewrite `.specify/` or `.github/skills/`. If you want the newer templates and skills, run `specify init --here --force --non-interactive --integration copilot --script sh` again, then re-apply the `docs/specs` patches described above and diff the constitution to make sure it was not touched.

## Troubleshooting

- **`specify check` fails or reports missing tools** — run it to see what is missing: `.venv/bin/specify check`. Only `git` is required for branch creation; agent CLIs are optional (`--ignore-agent-tools` was used at init).
- **"Not a git repository" / no branch created** — `create-new-feature.sh` creates a `NNN-name` branch only when the repo is a git repository. Without git it still creates the folder and `spec.md` and writes `.specify/feature.json`. Run `git init` if you want branches.
- **Spec landed in top-level `specs/`** — the `docs/specs` patch was lost (probably after a re-init). Re-apply it, move the folder, and delete `specs/`.
- **"Feature directory not found"** — `.specify/feature.json` is missing or points to a folder that no longer exists. Set `SPECIFY_FEATURE_DIRECTORY` as shown above.
- **`/speckit-*` commands not showing in Copilot Chat** — confirm `.github/skills/` exists, reload the VS Code window, and check that Copilot Chat has agent skills enabled.
- **Next spec number is wrong** — numbering scans `docs/specs/` for the highest `NNN-` prefix. Pass `--number N` to force one; the script bumps it if that prefix already exists.
