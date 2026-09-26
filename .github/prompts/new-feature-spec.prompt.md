---
description: "Create a new Spec Kit feature specification under docs/specs/ from a one-line feature description."
mode: agent
tools: ['codebase', 'editFiles', 'search', 'runCommands']
---

# Create a Feature Specification

Feature description: **${input:description:Describe the feature in one or two sentences, e.g. "Users can pause a habit for a vacation without breaking their streak"}**

You are producing a specification only. Do not write application code, plans, or tasks.

## Steps

1. Read #file:../../.specify/memory/constitution.md and follow every principle, especially
   "Spec-First, Always" and "Vertical Slices, Independently Shippable".
2. Follow the conventions in #file:../skills/speckit-specify/SKILL.md:
   - Generate a 2-4 word kebab-case short name (action-noun form).
   - Scan `docs/specs/` for the highest existing `NNN-` prefix and use the next sequential number.
   - Create `docs/specs/NNN-short-name/spec.md` from #file:../../.specify/templates/spec-template.md.
   - Write `{"feature_directory": "docs/specs/NNN-short-name"}` to `.specify/feature.json`.
3. Read #file:../../docs/specs/003-daily-check-in/spec.md as the style reference. Match its
   structure and tone exactly: `**Feature Branch**`, `**Created**` (today's date), `**Status**: Draft`,
   `**Input**` quoting the description verbatim.
4. Fill the spec:
   - **User Scenarios & Testing**: 3-5 user stories, each with a priority (P1 first), a
     "Why this priority" line, an "Independent Test" line, and Given/When/Then acceptance scenarios.
     Every story must be shippable on its own; P1 stories together form the MVP.
   - **Edge Cases**: concrete boundaries (timezones, limits, archived habits, duplicates, failures).
   - **Functional Requirements**: `FR-001`, `FR-002`, ... Each MUST be testable and technology-neutral.
     Cross-reference related specs by number, e.g. "(spec 005)".
   - **Key Entities**: only if the feature introduces or changes data; no implementation details.
   - **Success Criteria**: `SC-001`, ... measurable and verifiable without knowing the implementation.
   - **Assumptions**: the defaults you chose where the description was silent.
5. Ambiguity rules: make an informed default and record it under Assumptions. Use
   `[NEEDS CLARIFICATION: specific question]` only when the answer changes scope, security, or UX
   significantly. **Maximum 3 markers.** If you used any, list them at the end of your reply and ask
   the user to answer them before `/speckit-plan`.
6. Append one row to the table in #file:../../docs/specs/README.md with the new number, name, link,
   status `Draft`, and a one-line summary. Keep the table sorted by number.

## Output

Reply with: the spec path, the numbered list of user stories with priorities, the count of FRs and
SCs, and any open clarification questions. Do not paste the whole spec into the chat.
