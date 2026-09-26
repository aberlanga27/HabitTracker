# Feature Specification: Data Export & Import

**Feature Branch**: `011-data-export`

**Created**: 2026-09-26

**Status**: Draft

**Input**: User description: "Users can download all their habits and check-ins as JSON or CSV, and restore a JSON export into the app."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export as JSON (Priority: P1)

From Settings, the user downloads a single JSON file containing every habit, schedule, category, reminder, and check-in they own, plus a format version.

**Why this priority**: Constitution principle VI (local-first, privacy-respecting) requires that users can always take their data with them; JSON is the lossless format that import depends on.

**Independent Test**: Create 2 habits with check-ins, export, open the file, confirm both habits and all check-ins are present with a `format_version` field.

**Acceptance Scenarios**:

1. **Given** a user with habits and check-ins, **When** they choose "Export JSON", **Then** a file named `habitude-export-YYYY-MM-DD.json` downloads containing all their data.
2. **Given** an archived habit, **When** exporting, **Then** the archived habit and its check-ins are included with the archived-at date.
3. **Given** a user with no habits, **When** exporting, **Then** a valid file with empty collections is produced, not an error.

---

### User Story 2 - Export as CSV (Priority: P2)

The user downloads a CSV of check-ins (one row per check-in with habit name, category, date, note) for use in spreadsheets.

**Why this priority**: Spreadsheet analysis is a common ask, but CSV is lossy and not used for import.

**Independent Test**: Export CSV, open in a spreadsheet, confirm one row per check-in and a header row.

**Acceptance Scenarios**:

1. **Given** 25 check-ins across 3 habits, **When** exporting CSV, **Then** the file has a header row and exactly 25 data rows.
2. **Given** a note containing commas, quotes, or newlines, **When** exported, **Then** the field is correctly quoted and round-trips in a spreadsheet.

---

### User Story 3 - Import JSON with Dry-Run Preview (Priority: P2)

The user selects a previously exported JSON file. Before anything changes, the app shows a preview: how many habits, categories, and check-ins will be created, updated, or skipped. The user then confirms or cancels.

**Why this priority**: Restoring data after a reinstall or moving machines is the second half of data ownership; the preview prevents accidental damage.

**Independent Test**: Export, delete one habit, import the file, confirm the preview says "1 habit to create, N unchanged", confirm, and verify the habit and its check-ins are back.

**Acceptance Scenarios**:

1. **Given** a valid export file, **When** selected, **Then** a preview lists counts of items to create, update, and skip and no data is modified yet.
2. **Given** the preview, **When** the user confirms, **Then** items are merged by id: unknown ids are created, known ids are updated to the file's values, and check-ins that already exist for the same habit and date are skipped.
3. **Given** the preview, **When** the user cancels, **Then** nothing is changed.
4. **Given** a file whose `format_version` is newer than the app supports, **When** selected, **Then** import is refused with a clear message and nothing is changed.
5. **Given** a malformed or non-JSON file, **When** selected, **Then** validation errors are shown, referencing the offending field, and nothing is changed.

---

### User Story 4 - Import into a Different Account (Priority: P3)

A user imports an export created by another account (for example, moving between two local users). Ids from the file are re-mapped so nothing collides with the importing user's data.

**Independent Test**: Export from user A, import as user B, confirm B has copies of A's habits and A's data is untouched.

**Acceptance Scenarios**:

1. **Given** an export from another user, **When** imported, **Then** all items are created under the importing user with new ids and the original user is unaffected.

---

### Edge Cases

- Import is transactional: any failure after confirmation rolls back all changes from that import.
- Exports never include password hashes, session tokens, or other users' data.
- Category names in the file are matched to existing categories case-insensitively; missing ones are created, respecting the 20-category limit (spec 010).
- Check-ins older than the 30-day backfill window (spec 003) are still imported; the window applies only to interactive editing.
- Files larger than 10 MB are rejected before parsing with a size message.
- Streaks (spec 004) and stats (spec 009) are recomputed on next read; no separate rebuild step.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Users MUST be able to export all their habits, schedules, categories, reminders, and check-ins as a single JSON file with a `format_version` field.
- **FR-002**: Users MUST be able to export check-ins as CSV with a header row and RFC 4180 quoting.
- **FR-003**: Users MUST be able to import a JSON export and see a dry-run preview of creates, updates, and skips before confirming.
- **FR-004**: Import MUST merge by id for the same user and MUST re-map ids when the export belongs to a different user.
- **FR-005**: Import MUST be atomic: all changes succeed or none are applied.
- **FR-006**: System MUST validate the file's structure and `format_version` and refuse unsupported or malformed files without modifying data.
- **FR-007**: Exports MUST contain only data owned by the requesting user and MUST exclude credentials and sessions.
- **FR-008**: Export and import MUST run entirely on the local machine with no external service, per constitution principle VI.

### Key Entities

- **ExportBundle**: A versioned document containing the user's timezone and collections of Habits, Schedules, Categories, Reminders, and CheckIns as defined in specs 002, 005, 010, 008, and 003.
- **ImportPreview** (derived, not stored): per-collection counts of create, update, skip, and a list of validation warnings.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Export of 50 habits and 10k check-ins completes in under 2 s.
- **SC-002**: A round-trip export → wipe → import reproduces 100% of habits, schedules, categories, reminders, and check-ins in automated tests.
- **SC-003**: Import preview for a 10k check-in file renders in under 3 s.
- **SC-004**: Zero credential fields appear in any export in automated checks.

## Assumptions

- Only Habitude's own JSON format is importable; importing from other apps is out of scope for v1.
- CSV export is check-ins only; habits and categories are described by their names in each row.
- Export is triggered from Settings (spec 012); no scheduled or automatic backups in v1.
