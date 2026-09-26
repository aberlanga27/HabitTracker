---
description: "Review the current diff against its feature spec, the constitution, coding standards, accessibility, and security basics."
mode: agent
tools: ['codebase', 'search', 'runCommands', 'changes', 'problems']
---

# Review Changes Against the Spec

Review the current working-tree diff (or the current branch's diff against `main`).
You are a reviewer, not an author: report findings, do not edit files.

## Gather context

1. Identify the spec this change implements. Look for `docs/specs/NNN-*` references in commit
   messages, `tasks.md` checkboxes that changed, or the PR description. If none can be found,
   report that as the first finding (constitution Principle VII requires a spec reference).
2. Read that folder's `spec.md`, `plan.md`, and `tasks.md`, plus
   #file:../../.specify/memory/constitution.md, #file:../../docs/coding-standards.md,
   #file:../../docs/testing.md, and #file:../../docs/frontend.md when UI files changed.

## Checks

Work through each area and record concrete findings with `path:line` references.

- **Spec coverage**: list every FR id the diff touches. For each, name the test that exercises it.
  An FR with behavior in the diff but no test is a High finding. Behavior in the diff that no FR
  asks for is a Medium finding (scope creep).
- **Constitution**: Test-First evidence (tests exist and are not weakened), no new dependencies
  without justification in `plan.md`, API changes reflected in the OpenAPI contract, no data
  leaving the machine, timezone handling per the user's stored timezone.
- **Coding standards**: layering, naming, error handling, typing (`mypy --strict`, TS `strict`),
  formatting, no dead code or commented-out blocks, no secrets or debug logging.
- **Correctness**: off-by-one on dates and week boundaries, duplicate check-ins, ownership checks
  (a user can only reach their own habits), optimistic-update rollback, race conditions on toggles.
- **Accessibility**: keyboard operability, accessible names, focus management, contrast tokens,
  live-region announcements for progress changes.
- **Security basics**: input validation and length limits, generic auth error messages, password
  hashing, session invalidation, no raw SQL string building, no `dangerouslySetInnerHTML`.
- **Tests**: run the relevant suites if they are runnable and quote failures verbatim.

## Output

Findings ordered by severity, each in this shape:

```
[High|Medium|Low] <one-line claim> — path/to/file.ext:LINE
Why: <one or two sentences>. Spec ref: FR-00X / Principle N.
```

Then a short **Coverage table**: FR id | test name | status (covered / missing).
Finish with a verdict: `Approve`, `Approve with nits`, or `Request changes`, and one sentence why.
If nothing is wrong in an area, say "No findings" for it rather than inventing one.
