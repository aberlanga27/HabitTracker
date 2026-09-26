# Feature Specification: Settings & Preferences

**Feature Branch**: `012-settings-preferences`

**Created**: 2026-09-26

**Status**: Draft

**Input**: User description: "A settings page for timezone, week start, theme, notification opt-in, changing password, and deleting the account."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Timezone and Week Start (Priority: P1)

The user sets their timezone (defaulting to the one captured at registration, spec 001) and the day their week starts (Monday or Sunday). These drive "today", streaks, schedules, and stats.

**Why this priority**: Every date-based feature (specs 003, 004, 005, 007, 009) reads these values; a wrong timezone makes check-ins land on the wrong day.

**Independent Test**: Change timezone to one where it is already tomorrow, confirm the Today dashboard header shows the new date.

**Acceptance Scenarios**:

1. **Given** the settings page, **When** the user selects a timezone from the IANA list and saves, **Then** the Today view (spec 006) immediately reflects the new local date.
2. **Given** week start set to Sunday, **When** viewing the history calendar (spec 007), **Then** columns begin on Sunday.
3. **Given** a timezone change, **When** saved, **Then** existing check-ins keep their stored local dates and are not shifted.

---

### User Story 2 - Theme (Priority: P1)

The user chooses light, dark, or system theme. The choice applies instantly and persists.

**Why this priority**: Accessibility and comfort; cheap to build and universally expected.

**Independent Test**: Select dark, reload, confirm dark persists; select system, change OS theme, confirm the app follows.

**Acceptance Scenarios**:

1. **Given** the settings page, **When** the user selects Dark, **Then** the UI switches without reload and stays dark after reload.
2. **Given** System is selected, **When** the operating system theme changes, **Then** the app follows within one second.
3. **Given** any theme, **When** automated contrast checks run, **Then** all text meets WCAG 2.1 AA.

---

### User Story 3 - Notification Opt-In (Priority: P2)

A toggle enables browser notifications for reminders (spec 008). Turning it on triggers the browser permission prompt; turning it off falls back to in-app banners.

**Why this priority**: Spec 008 requires that permission is requested only after an explicit opt-in.

**Independent Test**: Turn the toggle on, grant permission, confirm the toggle stays on; deny permission, confirm the toggle shows a "blocked in browser" hint.

**Acceptance Scenarios**:

1. **Given** the toggle off, **When** the user turns it on, **Then** the browser permission prompt appears and, if granted, the setting is saved as enabled.
2. **Given** permission denied by the browser, **When** the toggle is on, **Then** the toggle shows a hint explaining how to unblock and reminders use in-app banners only.
3. **Given** the toggle on, **When** turned off, **Then** no browser notifications fire and no permission prompt is shown again unless re-enabled.

---

### User Story 4 - Change Password (Priority: P2)

The user enters their current password and a new password twice. All other sessions are signed out.

**Why this priority**: Basic account hygiene; required because spec 001 has no reset flow.

**Independent Test**: Change the password, sign out, sign in with the new password, confirm the old one is rejected.

**Acceptance Scenarios**:

1. **Given** the correct current password and a valid new password (spec 001 rules), **When** submitted, **Then** the password is updated and other sessions are invalidated.
2. **Given** a wrong current password, **When** submitted, **Then** the form shows "Current password is incorrect" and nothing changes.
3. **Given** new password and confirmation that differ, **When** submitted, **Then** an inline validation error appears and nothing is sent.

---

### User Story 5 - Delete Account (Priority: P3)

The user permanently deletes their account and all data after typing "DELETE" and their current password. They are offered an export (spec 011) first.

**Why this priority**: Required for data ownership (constitution principle VI), but destructive and rarely used.

**Independent Test**: Delete an account, attempt to sign in, confirm rejection; confirm no rows remain for that user.

**Acceptance Scenarios**:

1. **Given** the delete dialog, **When** the user types "DELETE" and the correct password and confirms, **Then** the user, habits, categories, reminders, check-ins, and sessions are removed and the sign-in screen is shown.
2. **Given** the delete dialog, **When** the typed confirmation or password is wrong, **Then** the delete button stays disabled or the request is rejected and nothing is removed.
3. **Given** the delete dialog, **When** the user selects "Export first", **Then** a JSON export (spec 011) downloads and the dialog remains open.

---

### Edge Cases

- Theme is stored server-side so it follows the user across browsers, with a client-side copy applied before first paint to avoid a flash.
- Timezone list is the IANA database; invalid or unknown identifiers are rejected.
- Changing week start recalculates times-per-week progress (spec 005) from the current week forward only.
- Deleting the account is irreversible; there is no soft-delete or grace period in v1.
- Settings changes are saved individually on change, not with a single save button, and each shows a brief confirmation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Users MUST be able to set their timezone from the IANA list; all date-based features MUST read it.
- **FR-002**: Users MUST be able to set the week start day to Monday or Sunday.
- **FR-003**: Users MUST be able to choose light, dark, or system theme, applied without reload and persisted.
- **FR-004**: Users MUST be able to opt in or out of browser notifications; the permission prompt MUST only appear after opt-in.
- **FR-005**: Users MUST be able to change their password by providing the current password; success MUST invalidate all other sessions.
- **FR-006**: Users MUST be able to delete their account after typing a confirmation word and their password; deletion MUST remove all their data.
- **FR-007**: The delete flow MUST offer a JSON export before deletion.
- **FR-008**: Settings MUST only be readable and writable by their owner.

### Key Entities

- **UserSettings**: Belongs to one User. Attributes: timezone, week start day, theme, notifications enabled flag, updated-at.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A settings change is reflected in the UI within 200 ms and persisted within 500 ms p95.
- **SC-002**: Theme switch causes zero flash of wrong theme on reload in automated visual tests.
- **SC-003**: Account deletion leaves zero rows for the user across all tables in automated tests.
- **SC-004**: 100% of date-based tests pass when timezone is changed mid-suite.

## Assumptions

- Email change and password reset by email are out of scope for v1.
- Language and locale selection are out of scope; the UI is English only.
- Settings live on a single page with sections; no separate profile page.
