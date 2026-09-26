# AGENTS.md — Instructions for AI Coding Agents

**Habitude** is a small full-stack habit tracker (FastAPI + SQLite backend, React + TypeScript frontend) built as a capstone demo of spec-driven, AI-assisted development with [GitHub Spec Kit](https://github.com/github/spec-kit). This file is the single source of agent instructions; `.github/copilot-instructions.md` points here.

**Current phase**: Phase 0. Specs, docs, and agent tooling exist. No application code exists yet. Every line of `src/` will be produced through the Spec Kit workflow below.

## Read these first, in order

1. `.specify/memory/constitution.md` — the highest-authority rules. Non-negotiable.
2. `docs/README.md` — index of all documentation.
3. The feature spec you are working on: `docs/specs/NNN-name/spec.md` (plus `plan.md` and `tasks.md` if they exist).
4. `docs/coding-standards.md` — naming, structure, lint, types, API conventions.
5. `docs/testing.md` — test pyramid, tools, coverage gates, what "tested" means.
6. `docs/frontend.md` and `docs/architecture.md` — when touching UI or cross-cutting design.

## Repository map

```
AGENTS.md                      # you are here
README.md                      # human-facing overview
.github/copilot-instructions.md  # "@AGENTS.md"
.github/skills/speckit-*/      # Spec Kit skills (/speckit-specify, /speckit-plan, ...)
.github/prompts/*.prompt.md    # reusable prompt files (see "Prompts and agents")
.github/agents/*.agent.md      # custom Copilot agents
.specify/memory/constitution.md
.specify/scripts/bash/         # create-new-feature.sh, check-prerequisites.sh, setup-plan.sh, ...
.specify/templates/            # spec / plan / tasks / checklist templates
docs/                          # all documentation
docs/specs/NNN-name/           # one folder per feature: spec.md, plan.md, tasks.md, research.md, data-model.md, contracts/
src/backend/                   # (planned) FastAPI app
src/frontend/                  # (planned) React app
.venv/                         # Python venv hosting specify-cli and backend tooling (never commit)
requirements-tooling.txt       # tooling deps for .venv (specify-cli)
```

## Spec Kit workflow

Specs live under **`docs/specs/`**, not `specs/`. The feature script and the `speckit-specify` skill were patched for this. Never create a top-level `specs/` folder.

| Step | Skill / command | Produces |
|------|-----------------|----------|
| 0. Principles | `/speckit-constitution` | `.specify/memory/constitution.md` (already done; amend via PR only) |
| 1. Specify | `/speckit-specify <description>` | `docs/specs/NNN-name/spec.md` |
| 2. Clarify (optional) | `/speckit-clarify` | resolves `[NEEDS CLARIFICATION]` in-place |
| 3. Plan | `/speckit-plan` | `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/` |
| 4. Tasks | `/speckit-tasks` | `tasks.md` (dependency-ordered, testable) |
| 5. Analyze (optional) | `/speckit-analyze` | consistency report across spec/plan/tasks |
| 6. Checklist (optional) | `/speckit-checklist` | `checklists/*.md` |
| 7. Implement | `/speckit-implement` | code + tests, tests first |
| 8. Converge | `/speckit-converge` | appends remaining work as tasks |

Full guide with manual script usage: `docs/spec-kit-workflow.md`.

## Hard rules

- **Spec first.** No code without a spec, plan, and tasks in `docs/specs/NNN-name/`. If asked to "just build it", create the spec first.
- **Test first.** Write the failing test from the acceptance scenario, then the code. Every `FR-xxx` maps to at least one test.
- **Ask, don't invent.** Unknown requirement → add `[NEEDS CLARIFICATION: ...]` to the spec and stop. Never guess business rules.
- **No new dependencies without justification.** One sentence in `plan.md` under "Complexity Tracking". Prefer the stack in the constitution.
- **Cite the spec.** Commit messages and PR descriptions reference the spec folder and FR ids, e.g. `feat(003): toggle check-in (FR-001, FR-004)`.
- **Never commit secrets.** No tokens, passwords, `.env` files, or real user data. `.gitignore` covers `.venv/`, `.env*`, `*.db`.
- **Never run destructive git commands.** No `push --force`, `reset --hard`, `clean -fd`, branch deletion, or history rewriting. Do not commit or push unless explicitly asked.
- **Stay in scope.** Implement the task you were given; note out-of-scope findings in your summary, don't act on them.
- **Accessibility is a requirement.** Keyboard operability and labels ship with the feature, not after.
- **Local-first.** No external services, telemetry, or network calls the spec does not name.

## Environment setup

```bash
uv venv .venv --python 3.13
uv pip install --python .venv/bin/python -r requirements-tooling.txt
.venv/bin/specify check          # verify Spec Kit tooling
```

Planned commands (not yet available; created by the first implementation specs):

```bash
# backend (planned)
.venv/bin/uvicorn src.backend.app.main:app --reload
.venv/bin/pytest src/backend
.venv/bin/ruff check src/backend && .venv/bin/ruff format src/backend
.venv/bin/mypy --strict src/backend

# frontend (planned)
cd src/frontend && npm install && npm run dev
npm test            # vitest
npm run test:e2e    # playwright
npm run lint && npm run typecheck
```

## Definition of done

- [ ] Spec, plan, and tasks exist and the task id is referenced in the change.
- [ ] Tests written first; all FRs touched have tests; tests pass locally.
- [ ] Lint, format, and strict type checks pass (backend and/or frontend).
- [ ] Coverage ≥ 85% on changed backend modules.
- [ ] No `[NEEDS CLARIFICATION]` left in the spec for the implemented stories.
- [ ] Accessibility checks pass for any UI change.
- [ ] `docs/` updated if behavior, commands, or conventions changed.
- [ ] Commit/PR cites spec folder and FR ids; no secrets; no destructive git.

## Prompts and agents

- `.github/prompts/new-feature-spec.prompt.md` — turn a one-line idea into a Spec Kit spec under `docs/specs/`. Use before `/speckit-plan`.
- `.github/prompts/implement-task.prompt.md` — implement one task from `tasks.md` test-first. Use during `/speckit-implement` or for a single task.
- `.github/prompts/review-pr.prompt.md` — review a change against its spec, the constitution, and `docs/coding-standards.md`.
- `.github/agents/spec-writer.agent.md` — custom agent that only writes and refines specs; never touches `src/`.
- `.github/agents/test-engineer.agent.md` — custom agent that derives tests from acceptance scenarios and reports coverage gaps.

Pick the narrowest tool for the job: a prompt file for a single step, a custom agent for a whole role.

## When in doubt

1. Re-read the constitution. If the request conflicts with it, say so and propose a compliant alternative.
2. Check the spec. If it is silent, add `[NEEDS CLARIFICATION]` rather than deciding.
3. Prefer the smaller change. Simplicity is a principle, not a preference.
4. Summarize what you did, what you verified, and what you left out, in that order.
