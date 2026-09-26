# Feature Specification: Habit Management

**Feature Branch**: `002-habit-management`

**Created**: 2026-09-26

**Status**: Draft

**Input**: User description: "Users can create, edit, reorder, archive and delete habits they want to track."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create a Habit (Priority: P1)

A signed-in user adds a habit with a name (e.g. "Drink 2L of water"), an optional description, an optional emoji/icon, and a color. The new habit appears immediately in their list.

**Why this priority**: A habit tracker with no habits is empty; this is the first thing every user does.

**Independent Test**: Sign in, create a habit named "Read 10 pages", confirm it appears in the habit list and persists after reload.

**Acceptance Scenarios**:

1. **Given** a signed-in user on the dashboard, **When** they submit the new-habit form with name "Read 10 pages", **Then** the habit is saved and shown in the list.
2. **Given** the new-habit form, **When** the name is blank or longer than 80 characters, **Then** an inline validation error appears and nothing is saved.
3. **Given** a user with 50 habits, **When** they try to create a 51st, **Then** they see "Habit limit reached (50)" and nothing is saved.

---

### User Story 2 - Edit a Habit (Priority: P1)

A user changes a habit's name, description, icon, or color. Historical check-ins remain attached to the habit.

**Why this priority**: Users refine wording constantly; losing history on rename would be unacceptable.

**Independent Test**: Create a habit, check it in once, rename it, confirm the check-in still appears.

**Acceptance Scenarios**:

1. **Given** an existing habit with check-ins, **When** the user renames it, **Then** the name updates and all check-ins remain.
2. **Given** an edit form, **When** the user cancels, **Then** no changes are persisted.

---

### User Story 3 - Archive and Restore (Priority: P2)

A user archives a habit they no longer track. It disappears from the daily view but its history stays available. They can restore it later.

**Why this priority**: Preserves data while decluttering; safer than deletion.

**Independent Test**: Archive a habit, confirm it leaves the Today view and appears under "Archived", restore it, confirm it returns.

**Acceptance Scenarios**:

1. **Given** an active habit, **When** archived, **Then** it no longer appears in Today and is listed under Archived.
2. **Given** an archived habit, **When** restored, **Then** it returns to the active list with its history intact.

---

### User Story 4 - Delete a Habit (Priority: P3)

A user permanently deletes a habit and all its check-ins after confirming.

**Why this priority**: Needed for privacy and cleanup but destructive, so lowest priority and behind a confirmation.

**Independent Test**: Delete a habit, confirm it and its check-ins are gone and totals update.

**Acceptance Scenarios**:

1. **Given** a habit, **When** the user chooses Delete and confirms by typing the habit name, **Then** the habit and its check-ins are removed permanently.
2. **Given** the delete dialog, **When** the user cancels, **Then** nothing is removed.

---

### User Story 5 - Reorder Habits (Priority: P3)

A user drags habits to reorder them; the order persists across devices/sessions.

**Independent Test**: Reorder two habits, reload, confirm order persists.

**Acceptance Scenarios**:

1. **Given** three habits, **When** the user moves the third to the top, **Then** the new order is saved and shown after reload.
2. **Given** keyboard-only navigation, **When** the user uses "move up/down" controls, **Then** reordering works without a mouse.

---

### Edge Cases

- Habit names are trimmed; two habits may share a name (no uniqueness constraint).
- Deleting a habit that is referenced by a reminder (spec 008) also removes the reminder.
- Archiving does not break an in-progress streak calculation; streaks freeze at archive time.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Users MUST be able to create a habit with a name (1–80 chars), optional description (≤500 chars), optional icon, and a color from a fixed palette.
- **FR-002**: Users MUST be able to edit any of those fields without affecting check-in history.
- **FR-003**: Users MUST be able to archive and restore habits.
- **FR-004**: Users MUST be able to permanently delete a habit after a typed confirmation.
- **FR-005**: Users MUST be able to reorder habits with both pointer and keyboard.
- **FR-006**: System MUST enforce a maximum of 50 active habits per user.
- **FR-007**: System MUST only expose a habit to the user who owns it.

### Key Entities

- **Habit**: Belongs to one User. Attributes: name, description, icon, color, sort position, archived-at (nullable), created-at.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Creating a habit takes fewer than 3 interactions after opening the form.
- **SC-002**: Renaming a habit preserves 100% of check-ins in automated tests.
- **SC-003**: List of 50 habits renders in under 100 ms after data arrives.

## Assumptions

- Icon is a single emoji character chosen from a picker; custom images are out of scope.
- Color palette has 8 accessible presets defined in the frontend design tokens.
