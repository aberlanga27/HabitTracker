# Feature Specification: Categories & Tags

**Feature Branch**: `010-categories-tags`

**Created**: 2026-09-26

**Status**: Draft

**Input**: User description: "Users group habits into categories like Health or Work and filter their views by category."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create and Manage Categories (Priority: P1)

A user creates a category with a name and a color, renames it, changes its color, or deletes it. Deleting a category moves its habits to "Uncategorized".

**Why this priority**: Categories must exist before they can be assigned or filtered on.

**Independent Test**: Create "Health" in green, rename it to "Fitness", delete it, confirm habits are uncategorized and nothing else is lost.

**Acceptance Scenarios**:

1. **Given** a signed-in user, **When** they create a category "Health" with green, **Then** it appears in the category list.
2. **Given** an existing category, **When** renamed to "Fitness", **Then** all habits in it show the new name immediately.
3. **Given** a category containing 3 habits, **When** deleted after confirmation, **Then** those 3 habits become Uncategorized and keep all check-ins.
4. **Given** a user with 20 categories, **When** they try to create a 21st, **Then** they see "Category limit reached (20)" and nothing is saved.
5. **Given** the category form, **When** the name is blank, longer than 40 characters, or duplicates an existing category name (case-insensitive), **Then** an inline validation error appears.

---

### User Story 2 - Assign a Habit to a Category (Priority: P1)

When creating or editing a habit (spec 002), the user picks one category from a dropdown. New habits default to Uncategorized.

**Why this priority**: Assignment is the link that makes filtering meaningful.

**Independent Test**: Edit a habit, choose "Health", confirm the habit shows the Health color chip in the list.

**Acceptance Scenarios**:

1. **Given** the habit form, **When** the user selects "Health", **Then** the habit is saved with that category and shows its color chip.
2. **Given** the habit form, **When** no category is chosen, **Then** the habit is saved as Uncategorized.
3. **Given** a categorized habit, **When** the user changes it to another category, **Then** check-in history and streaks (spec 004) are unaffected.

---

### User Story 3 - Filter by Category (Priority: P2)

On the Today dashboard (spec 006) and the All Habits page, a category filter chip row lets the user show only one category or all.

**Why this priority**: Filtering is the payoff of categorizing; still secondary to core check-in flow.

**Independent Test**: Have habits in Health and Work, select the Health chip, confirm only Health habits and the correct progress ratio appear.

**Acceptance Scenarios**:

1. **Given** habits in Health and Work, **When** the Health filter is selected, **Then** only Health habits are listed and the day's progress reads over Health habits only.
2. **Given** a filter selected, **When** the user reloads the page, **Then** the filter persists for that browser.
3. **Given** a filter selected, **When** the user chooses "All", **Then** all due habits are shown again.
4. **Given** a category with no due habits today, **When** its filter is selected, **Then** an empty state says "No Health habits due today".

---

### User Story 4 - Group View (Priority: P3)

The All Habits page can toggle between a flat list and a grouped-by-category view with a header per category.

**Independent Test**: Toggle grouped view, confirm headers appear in category creation order with Uncategorized last.

**Acceptance Scenarios**:

1. **Given** grouped view, **When** rendered, **Then** each category is a section header with its color, and Uncategorized is last.
2. **Given** grouped view, **When** habits are reordered (spec 002), **Then** ordering is scoped within the category.

---

### Edge Cases

- "Uncategorized" is a virtual bucket, not a stored category; it cannot be renamed, colored, or deleted.
- Category names are trimmed and unique per user, case-insensitively.
- Colors come from the same 8-color accessible palette used by habits (spec 002).
- Exports (spec 011) include the category name on each habit so imports can recreate it.
- Category filter state is stored client-side; it is not part of the user's server-side settings.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Users MUST be able to create, rename, recolor, and delete categories, with a name of 1–40 characters unique per user.
- **FR-002**: System MUST enforce a maximum of 20 categories per user.
- **FR-003**: Each habit MUST belong to at most one category; the absence of a category is presented as "Uncategorized".
- **FR-004**: Deleting a category MUST set its habits to uncategorized and MUST NOT delete habits or check-ins.
- **FR-005**: Today and All Habits views MUST support filtering by a single category or showing all.
- **FR-006**: Filtering MUST recompute the day's progress ratio (spec 006) over the filtered habits only.
- **FR-007**: The All Habits view MUST offer a grouped-by-category layout.
- **FR-008**: System MUST only expose categories to the user who owns them.

### Key Entities

- **Category**: Belongs to one User. Attributes: name, color, sort position, created-at.
- **Habit** (spec 002, extended): gains an optional reference to one Category.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Assigning a category to a habit takes no more than 2 interactions from the habit edit form.
- **SC-002**: Applying a filter re-renders the Today list in under 50 ms with 50 habits.
- **SC-003**: Deleting a category preserves 100% of habits and check-ins in automated tests.

## Assumptions

- Free-form multi-tags per habit are out of scope for v1; one category per habit keeps filtering and grouping simple.
- Categories are not shared between users.
- No default categories are seeded; users start with only Uncategorized.
