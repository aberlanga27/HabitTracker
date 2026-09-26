---
description: "Implement one task from a feature's tasks.md, tests first, and verify with lint, type-check, and tests."
mode: agent
tools: ['codebase', 'editFiles', 'search', 'runCommands', 'problems', 'testFailure']
---

# Implement a Task

Spec number: **${input:spec:e.g. 003}**
Task: **${input:task:Task id from tasks.md (e.g. T012) or a short description}**

## Before writing anything

1. Read #file:../../.specify/memory/constitution.md. Principle III (Test-First) is non-negotiable.
2. Locate the feature folder matching `docs/specs/${input:spec}-*/` and read, in order:
   `spec.md`, `plan.md`, `tasks.md`, and `data-model.md` / `contracts/` if present.
   If `plan.md` or `tasks.md` is missing, stop and tell the user to run `/speckit-plan` or
   `/speckit-tasks` first.
3. Find the task in `tasks.md`. Note which FR ids and user story it fulfils and which tasks it
   depends on. If a dependency is unchecked, stop and say so.
4. Read #file:../../docs/coding-standards.md and #file:../../docs/testing.md. For UI work also
   read #file:../../docs/frontend.md.

## Red

5. Write the failing tests first, derived from the spec's acceptance scenarios and edge cases for
   the FRs this task covers. Name tests with the spec and FR ids as `docs/testing.md` prescribes.
   Run only those tests and confirm they fail for the right reason (missing behavior, not a typo).

## Green

6. Implement the smallest change that makes the tests pass. Follow the layering and naming rules
   in `docs/coding-standards.md`. Do not add dependencies, configuration, or abstractions the task
   does not require (Principle IV). Do not modify existing tests to make them pass.

## Refactor and verify

7. Tidy names and duplication without changing behavior, then run the full checks:
   - Backend: `ruff check`, `ruff format --check`, `mypy --strict`, `pytest` (use the commands in `docs/testing.md`).
   - Frontend: `npm run lint`, `npm run typecheck`, `npm test` from `src/frontend`.
   Fix everything that fails. Paste any remaining failure output verbatim; do not describe it as passing.
8. Mark the task `[x]` in `tasks.md`.

## Report

Reply with:
- Task id, spec number, and the FR ids covered.
- Files created or changed, one line each.
- Test names added and the final pass/fail counts.
- A Conventional Commit message in a code block, e.g.
  `feat(check-in): toggle completion for today (spec 003, FR-001, FR-004)`.
Do not commit; the human reviewer does that.
