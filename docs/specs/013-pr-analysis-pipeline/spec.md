# Feature Specification: PR Analysis Pipeline

**Feature Branch**: `013-pr-analysis-pipeline`

**Created**: 2026-09-26

**Status**: Draft

**Input**: User description: "CI pipelines, starting with pull request analysis."

## Scope Note

This spec covers the first pipeline only: automated analysis of every pull request.
Build, release, deployment, and scheduled (nightly) pipelines are out of scope and
will be separate specs. The pipeline exists to enforce the constitution's quality
gates mechanically so that human and AI reviewers can focus on design and intent.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Static Analysis on Every PR (Priority: P1)

A contributor (human or AI agent) opens or updates a pull request. Within minutes the
PR shows pass/fail checks for lint, formatting, and type errors on both backend and
frontend, with failures pointing to the exact file and line.

**Why this priority**: Cheapest, fastest signal; catches the majority of low-quality
AI-generated changes before a reviewer spends time.

**Independent Test**: Open a PR that introduces an unused import in Python and an
`any` in TypeScript; confirm two named checks fail with file:line annotations. Fix
both, push, confirm both pass.

**Acceptance Scenarios**:

1. **Given** a PR with a Python lint or format violation, **When** the pipeline runs, **Then** the "Backend static analysis" check fails and annotates the offending line.
2. **Given** a PR with a TypeScript type error, **When** the pipeline runs, **Then** the "Frontend static analysis" check fails and annotates the offending line.
3. **Given** a PR that only changes files under `docs/`, **When** the pipeline runs, **Then** code analysis jobs are skipped and reported as "skipped", not "passed".
4. **Given** a clean PR, **When** the pipeline runs, **Then** all static checks pass in under 3 minutes.

---

### User Story 2 - Tests and Coverage Gate (Priority: P1)

The PR runs backend and frontend test suites. Coverage is measured, and the check
fails if changed backend modules fall below the constitution threshold.

**Why this priority**: Test-first is non-negotiable in the constitution; without a
mechanical gate the rule erodes.

**Independent Test**: Open a PR adding an untested backend function; confirm the
coverage check fails naming the module and its percentage. Add a test, confirm pass.

**Acceptance Scenarios**:

1. **Given** a PR where any test fails, **When** the pipeline runs, **Then** the "Tests" check fails and the failing test names are visible in the PR without opening logs.
2. **Given** a PR whose changed backend modules have under 85% line coverage, **When** the pipeline runs, **Then** the "Coverage" check fails and lists each module with its percentage.
3. **Given** a PR whose project-wide backend coverage is under 80%, **When** the pipeline runs, **Then** the "Coverage" check fails even if changed modules are above 85%.
4. **Given** a PR touching only frontend code, **When** the pipeline runs, **Then** backend tests are skipped and frontend unit tests still run.

---

### User Story 3 - Spec Traceability Check (Priority: P1)

Every PR must reference the spec it implements. The pipeline verifies the PR
description or title contains a valid spec reference and that the spec folder exists.

**Why this priority**: Spec-first is principle I of the constitution; AI agents drift
without a hard link between change and requirement.

**Independent Test**: Open a PR with no spec reference; confirm the "Spec reference"
check fails with instructions. Edit the description to add `docs/specs/003-daily-check-in`,
confirm pass without a new push.

**Acceptance Scenarios**:

1. **Given** a PR whose title or body contains `docs/specs/NNN-name` or `spec NNN`, **When** the pipeline runs, **Then** the check passes if that spec folder exists.
2. **Given** a PR with no spec reference, **When** the pipeline runs, **Then** the check fails with a message explaining the expected format.
3. **Given** a PR referencing a spec number that does not exist, **When** the pipeline runs, **Then** the check fails naming the missing folder.
4. **Given** a PR labeled `chore` or `docs-only`, **When** the pipeline runs, **Then** the spec reference check is skipped.

---

### User Story 4 - PR Summary Comment (Priority: P2)

After all jobs finish, a single bot comment on the PR summarizes results: each check
with pass/fail/skip, coverage numbers with deltas against the base branch, and the
list of FR ids mentioned in new or changed test names.

**Why this priority**: Reviewers should get the whole picture in one place; updating
one comment avoids notification noise.

**Independent Test**: Push twice to one PR; confirm exactly one bot comment exists
and its content reflects the latest run.

**Acceptance Scenarios**:

1. **Given** a completed pipeline run, **When** results are posted, **Then** exactly one summary comment exists on the PR and it is updated in place on later runs.
2. **Given** tests named with FR ids (e.g. `test_fr003_rejects_future_dates`), **When** the summary is built, **Then** it lists the FR ids covered by tests changed in the PR.
3. **Given** coverage dropped compared to the base branch, **When** the summary is built, **Then** the delta is shown with a warning marker.

---

### User Story 5 - End-to-End and Accessibility Smoke (Priority: P3)

For PRs that change frontend code, the pipeline runs the P1 end-to-end journeys
with automated accessibility checks and fails on any critical or serious violation.

**Why this priority**: Valuable but slow; runs only when relevant and after fast
checks pass.

**Independent Test**: Introduce a button with no accessible name in a P1 flow;
confirm the "E2E and accessibility" check fails naming the rule and the element.

**Acceptance Scenarios**:

1. **Given** a PR changing `src/frontend/`, **When** static and unit checks pass, **Then** the P1 end-to-end suite runs with accessibility scanning.
2. **Given** a critical or serious accessibility violation, **When** the suite runs, **Then** the check fails with rule id, selector, and page.
3. **Given** a PR not touching `src/frontend/`, **When** the pipeline runs, **Then** this job is skipped.

---

### Edge Cases

- Pipeline runs on PRs from forks must not have access to secrets; the summary comment step degrades gracefully to a job summary when it cannot comment.
- Concurrent pushes to the same PR cancel the older in-progress run.
- A flaky end-to-end test may be retried once automatically; a second failure is a real failure and is reported as such.
- Dependency install failures (registry outage) are reported as "infrastructure error", distinct from code failures, and can be re-run without a new push.
- Draft PRs run static analysis and tests but skip the end-to-end job until marked ready.
- Renamed files are analyzed as changed files for coverage purposes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The pipeline MUST run automatically on pull request open, synchronize, reopen, and ready-for-review events targeting the default branch.
- **FR-002**: The pipeline MUST run backend lint, format check, and strict type checking as one named check with file:line annotations.
- **FR-003**: The pipeline MUST run frontend lint and type checking as one named check with file:line annotations.
- **FR-004**: The pipeline MUST run backend and frontend test suites and surface failing test names in the check output.
- **FR-005**: The pipeline MUST fail if changed backend modules have under 85% line coverage or if project-wide backend coverage is under 80%.
- **FR-006**: The pipeline MUST verify the PR references an existing spec folder under `docs/specs/`, unless the PR carries a `chore` or `docs-only` label.
- **FR-007**: The pipeline MUST skip code jobs when only files under `docs/` or `*.md` changed, reporting them as skipped.
- **FR-008**: The pipeline MUST post or update exactly one summary comment per PR with per-check status, coverage with base-branch delta, and FR ids from changed tests.
- **FR-009**: The pipeline MUST run P1 end-to-end journeys with accessibility scanning when frontend files change and fast checks pass.
- **FR-010**: The pipeline MUST cancel superseded runs for the same PR.
- **FR-011**: The pipeline MUST cache dependency installs so that a no-change re-run of static checks completes in under 2 minutes.
- **FR-012**: All checks listed here MUST be configured as required status checks for merging to the default branch.
- **FR-013**: The pipeline MUST pin third-party actions and tool versions to exact versions or commit SHAs.
- **FR-014**: The pipeline MUST NOT expose secrets to fork-originated runs.

### Key Entities

- **Check**: One named result attached to a PR commit. Attributes: name, status (pass, fail, skipped, error), duration, annotations (file, line, message).
- **Run**: One execution of the pipeline for a PR head commit. Attributes: trigger event, head and base commit, checks, started/finished timestamps.
- **Summary Comment**: One bot-authored PR comment per PR. Attributes: run reference, check table, coverage totals and deltas, FR ids covered.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Static analysis results appear on the PR within 3 minutes of push at p95.
- **SC-002**: Full pipeline (excluding end-to-end) completes within 8 minutes at p95.
- **SC-003**: 100% of PRs merged to the default branch have a valid spec reference and green required checks.
- **SC-004**: Zero merged PRs in the first month reduce project-wide backend coverage below 80%.
- **SC-005**: Reviewers report the summary comment as sufficient to decide whether to open logs in at least 90% of PRs (survey of contributors).

## Assumptions

- Hosting is GitHub with GitHub Actions; branch protection on the default branch is available.
- The backend and frontend commands referenced in `docs/testing.md` section 11 exist once specs 001 to 006 are implemented; until then, jobs whose tooling does not exist yet are skipped, not failed.
- Coverage on changed modules is computed against the PR base branch using a diff-coverage tool; exact tool choice is a plan decision.
- Nightly performance tests (`perf` marker) belong to a future scheduled pipeline spec.
- No AI-driven review step is part of this spec; the `review-pr` prompt file remains a manual, reviewer-triggered aid.
