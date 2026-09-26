# Documentation Index

Everything a contributor or an AI agent needs to work on Habitude. The constitution outranks every file listed here.

| Document | What it covers |
|----------|----------------|
| [../.specify/memory/constitution.md](../.specify/memory/constitution.md) | Non-negotiable principles, tech constraints, workflow, quality gates, governance |
| [../AGENTS.md](../AGENTS.md) | Instructions for AI coding agents: rules, workflow, definition of done |
| [architecture.md](architecture.md) | System overview: backend, frontend, data model, API contract, boundaries |
| [coding-standards.md](coding-standards.md) | Naming, structure, lint/format/type rules, API and error conventions |
| [testing.md](testing.md) | Test pyramid, tools, coverage gates, how specs map to tests |
| [frontend.md](frontend.md) | Frontend structure, routing, state, styling, accessibility, component rules |
| [spec-kit-workflow.md](spec-kit-workflow.md) | How Spec Kit is installed here, the step-by-step workflow, scripts, troubleshooting |
| [specs/README.md](specs/README.md) | Index of feature specs and suggested build order |
| [specs/NNN-name/](specs/) | One folder per feature: `spec.md`, then `plan.md`, `tasks.md`, and design artifacts |

## Reading order

**New human contributor**

1. [../README.md](../README.md) — what and why
2. [../.specify/memory/constitution.md](../.specify/memory/constitution.md)
3. [architecture.md](architecture.md)
4. [spec-kit-workflow.md](spec-kit-workflow.md)
5. [coding-standards.md](coding-standards.md) and [testing.md](testing.md)
6. The spec you will work on under [specs/](specs/)

**AI agent**

1. [../AGENTS.md](../AGENTS.md)
2. [../.specify/memory/constitution.md](../.specify/memory/constitution.md)
3. The feature spec (and `plan.md` / `tasks.md` if present)
4. [coding-standards.md](coding-standards.md), [testing.md](testing.md)
5. [frontend.md](frontend.md) or [architecture.md](architecture.md) as the task requires

## Conventions for docs

- Markdown, one H1 per file, sentence-case headings.
- Link with relative paths so links work on GitHub and in editors.
- When a doc describes behavior that a spec also covers, the spec wins; update the doc to match.
- Keep docs current: a change that alters commands, structure, or conventions updates the relevant doc in the same PR.
