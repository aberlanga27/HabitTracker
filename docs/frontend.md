# Frontend Guide

**Audience**: humans and AI agents implementing or reviewing the Habitude web client.
**Status**: living document. `src/frontend/` is scaffolded (spec 001); features land spec by spec and must follow the shape below.

The constitution (`.specify/memory/constitution.md`) fixes the stack. This document explains how to use it.

## Stack

| Concern | Choice | Notes |
|---|---|---|
| Language | TypeScript, `strict: true` | No `any`, no `// @ts-ignore` without a linked issue |
| UI | React 19 | Function components only |
| Build | Vite | Dev server on port 5173 |
| Routing | React Router (data router API) | Routes in `app/routes.tsx` |
| Server state | TanStack Query | The only cache for API data |
| Unit / component tests | Vitest + Testing Library | Colocated `*.test.tsx` |
| End-to-end tests | Playwright | `src/frontend/e2e/` |
| Lint / format | ESLint + Prettier | See `docs/coding-standards.md` |

## Directory Layout (`src/frontend/`)

```
src/frontend/
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
├── e2e/                         # Playwright specs, one file per feature
├── public/
└── src/
    ├── main.tsx                 # createRoot + providers
    ├── app/
    │   ├── App.tsx              # RouterProvider
    │   ├── routes.tsx           # route table (see below)
    │   ├── providers.tsx        # QueryClientProvider, ThemeProvider, AuthProvider
    │   └── layout/              # AppShell, NavBar, ProtectedRoute
    ├── features/
    │   ├── auth/                # spec 001
    │   ├── habits/              # spec 002, 005
    │   ├── check-ins/           # spec 003
    │   ├── streaks/             # spec 004
    │   ├── today/               # spec 006
    │   ├── history/             # spec 007
    │   ├── reminders/           # spec 008
    │   ├── stats/               # spec 009
    │   ├── categories/          # spec 010
    │   ├── export/              # spec 011
    │   └── settings/            # spec 012
    └── shared/
        ├── ui/                  # Button, Dialog, Toast, Skeleton, ProgressBar, EmojiPicker
        ├── lib/                 # apiClient.ts, dates.ts, queryKeys.ts, a11y.ts
        ├── theme/               # tokens.css, ThemeProvider.tsx
        └── types/
            └── api.generated.ts # generated from backend OpenAPI, never hand-edited
```

Every `features/<name>/` folder has the same internal shape:

```
features/habits/
├── components/      # HabitCard.tsx, HabitForm.tsx, HabitList.tsx
├── hooks/           # useHabits.ts, useCreateHabit.ts
├── api.ts           # typed fetchers for this feature's endpoints
├── types.ts         # feature-local view types (derived from api.generated.ts)
├── index.ts         # public surface of the feature (named exports only)
└── __tests__/       # or colocated *.test.tsx next to the component
```

Rule: a feature imports from `shared/` and from another feature's `index.ts` only. Never reach into another feature's internals.

## Routing Table

| Path | Screen | Feature folder | Spec | Auth |
|---|---|---|---|---|
| `/` | Today dashboard | `today` | 006 | required |
| `/habits` | All habits (active + archived, reorder) | `habits` | 002, 005 | required |
| `/habits/:id` | Habit detail (streaks, heatmap, reminder, schedule) | `habits`, `streaks`, `history`, `reminders` | 002, 004, 005, 007, 008 | required |
| `/history` | Overall heatmap | `history` | 007 | required |
| `/stats` | Stats and insights | `stats` | 009 | required |
| `/settings` | Profile, timezone, theme, week start, notifications, export | `settings`, `export` | 011, 012 | required |
| `/sign-in` | Sign in | `auth` | 001 | guest only |
| `/register` | Register | `auth` | 001 | guest only |

`ProtectedRoute` redirects unauthenticated users to `/sign-in?next=<path>`. Guest-only routes redirect signed-in users to `/`. Categories (spec 010) render as a filter inside `/` and `/habits`, not as a separate route.

## State Management Rules

1. **Server state lives in TanStack Query.** Anything that came from the API is read through `useQuery` / `useMutation`. No copying API data into `useState` or context.
2. **Local UI state stays local.** Open dialogs, form drafts, selected date: `useState` in the component or a small hook. Lift only as far as needed.
3. **No global store.** No Redux, Zustand, or similar. The three providers in `app/providers.tsx` (query client, theme, auth session) are the only app-wide state.
4. **URL is state.** Selected day on the dashboard (`/?date=2026-09-25`), selected category filter, and stats range live in search params so they survive reload and are shareable.

### Query key conventions

Keys are built by factories in `shared/lib/queryKeys.ts` so invalidation is predictable:

```ts
export const queryKeys = {
  me: () => ['me'] as const,
  habits: {
    all: () => ['habits'] as const,
    list: (filter: { archived?: boolean }) => ['habits', 'list', filter] as const,
    detail: (id: string) => ['habits', 'detail', id] as const,
  },
  day: (date: string) => ['day', date] as const,           // spec 006 DaySummary
  heatmap: (habitId: string | 'all', from: string, to: string) =>
    ['heatmap', habitId, from, to] as const,               // spec 007
  stats: (range: string) => ['stats', range] as const,     // spec 009
};
```

Invalidate by prefix: a check-in mutation invalidates `['day']`, `['habits']`, `['heatmap']`, `['stats']`.

## API Client Conventions

- `shared/lib/apiClient.ts` wraps `fetch` with the base URL, `credentials: 'include'` (session cookie), JSON handling, and error normalization. Nothing else calls `fetch` directly.
- Types come from `shared/types/api.generated.ts`, generated from the backend's OpenAPI document (`npm run gen:api`). Do not hand-write request or response types.
- Each feature has one `api.ts` exposing plain async functions (`listHabits`, `toggleCheckIn`). Hooks in `hooks/` wrap them with TanStack Query.
- Every non-2xx response is thrown as an `ApiError`:

```ts
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,            // e.g. 'HABIT_LIMIT_REACHED', 'UNAUTHENTICATED'
    message: string,
    public details?: Record<string, unknown>,
  ) { super(message); }
}
```

  A `401` anywhere clears the `me` query and routes to `/sign-in`.

## Optimistic Check-In Pattern (spec 003)

Toggling a habit must reflect in under 100 ms and roll back on failure (FR-006). The canonical shape:

```ts
const toggle = useMutation({
  mutationFn: (vars: { habitId: string; date: string; completed: boolean }) =>
    checkInsApi.toggle(vars),
  onMutate: async (vars) => {
    const key = queryKeys.day(vars.date);
    await queryClient.cancelQueries({ queryKey: key });
    const previous = queryClient.getQueryData<DaySummary>(key);
    queryClient.setQueryData<DaySummary>(key, (old) => applyToggle(old, vars));
    return { previous, key };
  },
  onError: (_err, _vars, ctx) => {
    if (ctx) queryClient.setQueryData(ctx.key, ctx.previous);
    toast.error('Could not save. Please try again.');
  },
  onSettled: (_data, _err, vars) => {
    queryClient.invalidateQueries({ queryKey: queryKeys.day(vars.date) });
    queryClient.invalidateQueries({ queryKey: queryKeys.habits.all() });
    queryClient.invalidateQueries({ queryKey: ['heatmap'] });
    queryClient.invalidateQueries({ queryKey: ['stats'] });
  },
});
```

Rapid double taps are de-duplicated by disabling the control while `toggle.isPending` for that habit.

## Design Tokens

All tokens are CSS custom properties in `shared/theme/tokens.css`. Components never hard-code colors or spacing.

**Theme switching**: `:root` holds light values; `:root[data-theme="dark"]` overrides them; `@media (prefers-color-scheme: dark)` applies when `data-theme="system"` (spec 012). `ThemeProvider` sets the attribute on `<html>`.

**Habit palette** (spec 002, FR-001): eight presets, each with a light and dark value that passes 4.5:1 against the card surface.

| Token | Name |
|---|---|
| `--habit-1` | coral |
| `--habit-2` | amber |
| `--habit-3` | lime |
| `--habit-4` | teal |
| `--habit-5` | sky |
| `--habit-6` | indigo |
| `--habit-7` | violet |
| `--habit-8` | rose |

**Semantic colors**: `--bg`, `--surface`, `--surface-raised`, `--text`, `--text-muted`, `--border`, `--accent`, `--success`, `--danger`, `--focus-ring`.

**Heatmap scale** (spec 007): `--heat-0` … `--heat-4` plus `--heat-not-due`. Levels differ in luminance, not just hue, and cells carry a text label for screen readers.

**Spacing scale**: `--space-1: 4px`, `--space-2: 8px`, `--space-3: 12px`, `--space-4: 16px`, `--space-6: 24px`, `--space-8: 32px`, `--space-12: 48px`.

**Radii / motion**: `--radius-sm: 6px`, `--radius-md: 10px`, `--radius-full: 999px`; `--motion-fast: 120ms`, `--motion-base: 240ms`. Honor `prefers-reduced-motion`.

## Accessibility Requirements

WCAG 2.1 AA is a requirement, not a polish item (constitution, Technology Constraints).

- Every interactive element is reachable and operable by keyboard with a visible focus ring (`--focus-ring`).
- Habit reordering (spec 002 FR-005) offers "Move up" / "Move down" buttons in addition to drag and drop.
- Dashboard progress (spec 006 FR-006) is announced through an `aria-live="polite"` region: "3 of 5 habits done".
- Heatmap cells (spec 007 FR-003) are focusable buttons with an accessible name such as "25 September 2026, done".
- Check-in controls are `<button aria-pressed>` , not bare `div`s.
- Dialogs trap focus, restore it on close, and close on Escape.
- Color is never the only signal: completed habits also get a checkmark, missed days get a pattern or label.
- Automated checks: `vitest-axe` in component tests and `@axe-core/playwright` in end-to-end tests; violations fail CI.

## Component Conventions

- Function components with an explicit `Props` interface; no `React.FC`.
- Named exports only. `index.ts` re-exports the feature's public surface.
- One component per file, file named after the component (`HabitCard.tsx`).
- Tests colocated: `HabitCard.test.tsx` beside `HabitCard.tsx`. Test behavior through the DOM (`getByRole`), never implementation details.
- Data fetching happens in hooks, not in components. Components receive data via props or a feature hook.
- Loading states use skeletons (`shared/ui/Skeleton`) to avoid layout shift; empty and error states are explicit components, not conditionals inline.
- No inline styles except for dynamic values (e.g. habit color as `style={{ '--habit-color': ... }}`).

## Performance Budgets

From the constitution. CI measures these on a cold local build.

| Metric | Budget |
|---|---|
| First contentful paint (Today, cold load) | < 1.5 s |
| Check-in visual feedback | < 100 ms |
| Render 50 habits after data arrives | < 100 ms |
| Render 366 heatmap cells after data arrives | < 50 ms |
| Lighthouse accessibility | ≥ 95 |
| Initial JS bundle (gzipped) | < 150 kB |

Code-split routes with `React.lazy`; keep the heatmap and stats charts out of the initial chunk.

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Backend origin. Vite dev server also proxies `/api` to it so cookies stay same-site in development. |

Copy `.env.example` to `.env.local`; never commit `.env.local`.

## Commands

Run from `src/frontend/`.

| Command | What it does |
|---|---|
| `npm run dev` | Vite dev server on http://localhost:5173 |
| `npm run build` | Type-check then production build to `dist/` |
| `npm run preview` | Serve the production build locally |
| `npm run test` | Vitest unit and component tests |
| `npm run test:e2e` | Playwright end-to-end tests (expects backend on 8000) |
| `npm run lint` | ESLint + Prettier check |
| `npm run typecheck` | `tsc --noEmit` |
| `npm run gen:api` | Regenerate `api.generated.ts` from the backend OpenAPI document |

See `docs/testing.md` for the test pyramid and `docs/coding-standards.md` for lint rules.
