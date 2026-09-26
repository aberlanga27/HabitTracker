# Feature Specification: Reminders

**Feature Branch**: `008-reminders`

**Created**: 2026-09-26

**Status**: Draft

**Input**: User description: "Users can set a daily reminder time per habit and receive an in-app or browser notification."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Set a Reminder Time (Priority: P1)

A user sets "remind me at 08:00" on a habit. The time is stored in their local timezone.

**Why this priority**: Configuration must exist before any notification can fire.

**Independent Test**: Set 08:00 on a habit, reload, confirm the reminder time is shown.

**Acceptance Scenarios**:

1. **Given** a habit, **When** the user sets a reminder at 08:00, **Then** it is saved and displayed on the habit.
2. **Given** a reminder, **When** the user clears it, **Then** no reminder is stored.

---

### User Story 2 - In-App Reminder Banner (Priority: P2)

When the app is open and a reminder time passes for a habit not yet completed today, a dismissible banner appears listing the habit.

**Independent Test**: Set a reminder 1 minute ahead, wait, confirm banner appears; complete the habit, confirm banner clears.

**Acceptance Scenarios**:

1. **Given** an open app and a due, incomplete habit with reminder at 08:00, **When** local time reaches 08:00, **Then** a banner appears within 60 s.
2. **Given** the banner, **When** the habit is completed, **Then** the banner disappears.
3. **Given** the habit is already complete, **When** reminder time passes, **Then** no banner is shown.

---

### User Story 3 - Browser Notification (Priority: P3)

If the user grants notification permission, a native browser notification is shown instead of (or in addition to) the banner, even when the tab is in the background.

**Independent Test**: Grant permission, set a reminder, background the tab, confirm OS notification.

**Acceptance Scenarios**:

1. **Given** permission granted, **When** a reminder fires, **Then** a browser notification with the habit name appears.
2. **Given** permission denied, **When** a reminder fires, **Then** only the in-app banner is used and no error is shown.

---

### Edge Cases

- Reminders only fire on days the habit is due (spec 005).
- If the user's timezone changes, reminder wall-clock time stays the same (08:00 local).
- Multiple habits at the same time collapse into one banner/notification listing all.
- No reminders fire for archived habits.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Users MUST be able to set, change, and clear one daily reminder time per habit.
- **FR-002**: System MUST evaluate reminders client-side while the app is open; no server push in v1.
- **FR-003**: A reminder MUST fire only if the habit is due and incomplete for the current local date.
- **FR-004**: Reminders at the same minute MUST be batched into one notification.
- **FR-005**: The app MUST request browser notification permission only after the user opts in via settings.
- **FR-006**: The app MUST degrade to the in-app banner when notifications are unsupported or denied.

### Key Entities

- **Reminder**: Belongs to one Habit. Attributes: local time (HH:MM), enabled flag.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Reminder fires within 60 s of the configured minute in automated tests using a mocked clock.
- **SC-002**: Zero reminders fire for completed or non-due habits in tests.

## Assumptions

- Server-side scheduling, email, and push to closed browsers are out of scope for v1.
- One reminder per habit; multiple times per day are a future enhancement.
