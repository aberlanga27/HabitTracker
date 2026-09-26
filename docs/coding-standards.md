# Coding Standards

These standards apply to every line of code in Habitude, whether written by a human
or an AI agent. They sit below the [constitution](../.specify/memory/constitution.md)
in authority: when the two disagree, the constitution wins. Related docs:
[frontend](frontend.md), [testing](testing.md), [specs index](specs/README.md).

## 1. General Principles

- **Simplicity and YAGNI.** Write the smallest code that satisfies the spec. No
  speculative abstractions, no feature flags for hypothetical futures, no new
  dependency without one sentence of justification in the feature's `plan.md`.
- **Spec references only where non-obvious.** Code should be self-explanatory.
  Cite a spec in a comment only when the *reason* for a rule is surprising, e.g.
  `# 30-day backfill window (spec 003 FR-003)`. Do not tag every function.
- **No dead code.** No commented-out blocks, unused imports, or "just in case"
  helpers. Delete it; git remembers.
- **Small PRs.** One task from `tasks.md` per pull request. If a task needs more
  than ~400 changed lines, split the task first.
- **Boring tools.** Prefer the standard library and the tools named in the
  constitution over anything clever.

## 2. Python / Backend (`src/backend/`)

### Tooling

- Python 3.13, run from the repo's `.venv/`.
- `ruff` for both linting and formatting. Suggested `pyproject.toml` rule set:

```toml
[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM", "N", "ANN", "RUF", "DTZ", "T20"]
ignore = ["ANN401"]  # allow Any only where explicitly typed as such

[tool.mypy]
strict = true
plugins = ["pydantic.mypy"]
```

- `mypy --strict` must pass. Type hints on every function signature, including
  tests. `DTZ` rules are on so naive datetimes are rejected at lint time.
- `T20` forbids `print`; use the logger.

### Module Layout

```
src/backend/app/
  main.py            # FastAPI app factory only
  core/              # settings, db session, security, errors, logging, clock
  models/            # SQLModel ORM tables (table=True)
  schemas/           # Pydantic request/response models (never table=True)
  services/          # business logic, one module per domain (habits, checkins, streaks)
  routers/           # thin HTTP layer, one module per resource
  migrations/        # Alembic
tests/               # mirrors app/ layout
```

### Layering Rules

- **Routers are thin.** They parse input, call one service function, and return
  a schema. No queries, no branching on business rules.
- **Services hold logic.** Pure-ish functions that take a session and typed
  arguments, return domain objects or schemas, and raise domain exceptions.
- **Schemas are separate from ORM models.** Never return a `table=True` model
  from a router. Map explicitly (`HabitRead.model_validate(habit)`).
- **Dependency injection via `Depends`.** Session, current user, and clock are
  injected; never imported as globals.

```python
# Bad: logic in the router
@router.post("/habits")
def create_habit(body: HabitCreate, session: Session = Depends(get_session)):
    if session.exec(select(Habit).where(Habit.user_id == user.id)).count() >= 50:
        raise HTTPException(400, "too many")
    ...

# Good: router delegates, service enforces the rule
@router.post("/habits", response_model=HabitRead, status_code=201)
def create_habit(
    body: HabitCreate,
    user: CurrentUser,
    session: SessionDep,
) -> HabitRead:
    habit = habit_service.create(session, user_id=user.id, data=body)
    return HabitRead.model_validate(habit)
```

### Naming

- Modules and functions: `snake_case`. Classes: `PascalCase`. Constants: `UPPER_SNAKE`.
- Service functions are verbs: `create`, `archive`, `toggle_checkin`, `compute_streak`.
- Schemas are suffixed by intent: `HabitCreate`, `HabitUpdate`, `HabitRead`.
- Tables are singular nouns: `Habit`, `CheckIn`, `Schedule`.

### Error Handling

- Define domain exceptions in `core/errors.py`, e.g. `NotFoundError`,
  `ConflictError`, `ValidationError`, `AuthError`, `LimitExceededError`.
- One exception handler maps each to an HTTP status and a single error envelope:

```json
{ "error": { "code": "habit_limit_reached", "message": "Habit limit reached (50)", "details": {} } }
```

- Services raise domain exceptions; they never raise `HTTPException`.
- `code` values are stable `snake_case` strings the frontend can switch on.
  Messages are for humans and may change.

### Logging

- Use the standard `logging` module through `core/logging.py`; structured
  key=value extras, not f-strings with embedded data.
- Never log passwords, session tokens, cookies, or full request bodies.
- Log at `INFO` for state changes (habit created), `WARNING` for expected
  failures (lockout), `ERROR` only for unexpected exceptions.

### Dates and Times

- Store every timestamp as timezone-aware UTC (`datetime.now(tz=UTC)`). Naive
  datetimes are a lint error (`DTZ`).
- "Local date" (the `YYYY-MM-DD` a check-in belongs to) is computed in exactly
  one helper, `core/clock.py: local_date(now_utc, user_tz)`. Nothing else
  converts timezones.
- Inject the clock (`Depends(get_clock)`) so tests can freeze time.

## 3. TypeScript / Frontend (`src/frontend/`)

See [frontend.md](frontend.md) for architecture; this section is style only.

### Compiler and Lint

- `"strict": true`, `noUncheckedIndexedAccess`, `noImplicitOverride`.
- **No `any`.** Use `unknown` and narrow. `// eslint-disable` requires a comment
  explaining why.
- Exported functions declare an explicit return type.
- ESLint: `typescript-eslint` recommended-type-checked, `react-hooks`,
  `jsx-a11y`, `import/order`. Prettier owns formatting (2 spaces, single quotes,
  trailing commas, 100 cols); never argue with it.

### Naming and Files

- Files: `kebab-case.ts`. Components: `PascalCase` file and export
  (`HabitCard.tsx`). Hooks: `use-habits.ts` exporting `useHabits`.
- **Named exports only.** No `export default` (except where a framework requires it).
- Props interfaces are `XProps`, colocated with the component.
- No barrel `index.ts` files except `src/shared/ui/index.ts`.

```ts
// Bad
export default function card(props: any) { ... }

// Good
export interface HabitCardProps {
  habit: Habit;
  onToggle: (habitId: string) => void;
}
export function HabitCard({ habit, onToggle }: HabitCardProps): JSX.Element { ... }
```

### Imports

Order: node builtins, external packages, `@/` aliases, relative paths, styles.
Blank line between groups. Enforced by `import/order`.

### Data Fetching

- All server state goes through TanStack Query. No `useEffect` + `fetch`.
- One query key factory per resource in `features/<name>/queries.ts`:

```ts
export const habitKeys = {
  all: ['habits'] as const,
  list: (date: string) => [...habitKeys.all, 'list', date] as const,
  detail: (id: string) => [...habitKeys.all, 'detail', id] as const,
};
```

- Mutations invalidate by key prefix; optimistic updates must roll back on error
  (spec 003 FR-006).

### Styling

- No inline `style={{}}` except for truly dynamic values (e.g. heatmap cell color).
- CSS Modules (`*.module.css`) or plain CSS using design tokens from
  `src/styles/tokens.css`. No hard-coded colors, spacing, or font sizes.

## 4. Shared Conventions (Wire Contract)

- REST paths are plural nouns, kebab-case, no verbs:
  `GET /api/v1/habits`, `POST /api/v1/habits/{id}/check-ins`, `POST /api/v1/habits/{id}/archive`
  (state transitions are the one exception and use a verb sub-resource).
- JSON on the wire is `snake_case`. The frontend uses a generated typed client
  from the backend's OpenAPI document that maps to `camelCase`; never hand-write
  API types.
- IDs are UUIDv7 strings.
- Local dates are `YYYY-MM-DD` strings. Timestamps are ISO-8601 UTC with `Z`.
- Booleans are booleans, never `0/1` or `"true"`.
- List endpoints return `{ "items": [...], "total": n }`; never a bare array.

## 5. Git and Pull Requests

- Branches are created by Spec Kit: `NNN-feature-name` (e.g. `003-daily-check-in`).
- Commits follow Conventional Commits with the spec number as scope and the FR
  in the subject when applicable:

```
feat(003): add check-in toggle endpoint (FR-001, FR-004)
test(004): cover streak across DST boundary
docs(specs): clarify reminder batching in 008
```

- PR description template checklist (every box must be checked or explained):
  - [ ] Spec linked (`docs/specs/NNN-.../spec.md`) and task ID from `tasks.md`
  - [ ] Tests added or updated; all FRs touched have a test
  - [ ] Docs updated (`docs/`, OpenAPI, or spec) if behavior changed
  - [ ] Accessibility checked for any UI change (keyboard, labels, contrast)
  - [ ] `ruff`, `mypy`, `eslint`, `tsc`, and all tests pass locally
- Squash-merge. The squashed message is the PR title.

## 6. Code Review Checklist

Reviewers (human or agent) confirm:

1. The change does what the referenced spec and task say, and nothing more.
2. Tests exist for each acceptance scenario touched and fail without the change.
3. Routers are thin; logic lives in services; schemas are not ORM models.
4. No naive datetimes; local-date logic goes through `core/clock.py`.
5. Errors use the single envelope with a stable `code`.
6. No `any`, no default exports, no hand-written API types on the frontend.
7. UI changes are keyboard operable and have accessible names.
8. No secrets, tokens, or personal data in code, fixtures, or logs.
9. New dependencies are justified in `plan.md`.

## 7. Security Basics

- Passwords hashed with **argon2id** (fallback: bcrypt with cost ≥ 12). Never
  store or log plaintext.
- Sessions are opaque random tokens in an `httpOnly`, `Secure` (in prod),
  `SameSite=Lax` cookie. No JWT in `localStorage`.
- CSRF: `SameSite=Lax` plus a required custom header (`X-Requested-With`) on
  state-changing requests. The API rejects form-encoded bodies.
- Validate all input at the boundary with Pydantic schemas; services may assume
  validated data.
- Every query that touches user data filters by the current user's ID. There is
  no "admin sees all" path in v1.
- No secrets in the repo. `.env` is git-ignored; `.env.example` documents every
  variable with a safe placeholder.
- Generic auth errors only (`Invalid email or password`), per spec 001.

## 8. Documentation Standards

- Public functions, services, and non-trivial hooks get a docstring / JSDoc
  stating purpose, inputs, and raised errors. Skip docstrings on obvious
  one-liners and on tests.
- A `README.md` inside a feature folder (`src/frontend/src/features/<name>/`)
  is optional and only for non-obvious structure.
- When behavior changes, update the relevant doc in the same PR: `docs/`, the
  spec's `Status` or `Assumptions`, and the OpenAPI examples.
- Keep this file current. If a rule here is wrong, change the rule, not the
  code that follows it.

## 9. AI Agent Rules

1. **Read first.** Before writing code, read `AGENTS.md`, the constitution, the
   feature's `spec.md`, `plan.md`, and `tasks.md`.
2. **Never invent requirements.** If the spec is silent, do not guess. Mark it
   `[NEEDS CLARIFICATION: ...]` in the spec and stop that task.
3. **Mark uncertainty in code** with `TODO(spec-NNN): reason` so it is
   greppable and traceable. No bare `TODO`.
4. **Tests before code.** Write the failing test from the acceptance scenario,
   then implement.
5. **Prove it.** Run `ruff check`, `ruff format --check`, `mypy`, `pytest`,
   `npm run lint`, `npm run typecheck`, and `npm test` before declaring a task
   done, and paste the results in the PR.
6. **Stay in scope.** One task per PR. Note out-of-scope discoveries in the PR
   description or as a new task; do not fix them silently.
7. **Cite the spec** in commit messages and PR descriptions
   (`feat(NNN): ... (FR-xxx)`).
