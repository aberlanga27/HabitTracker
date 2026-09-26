# Feature Specification: User Accounts

**Feature Branch**: `001-user-accounts`

**Created**: 2026-09-26

**Status**: Implemented

**Input**: User description: "A person can create a local account, sign in, and sign out so that their habits are private to them."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Register a New Account (Priority: P1)

A first-time visitor opens the app, enters an email and password, and gets an account. After registering they land on an empty dashboard ready to add habits.

**Why this priority**: Nothing else in the app is possible without an identity to attach habits to.

**Independent Test**: Open the app fresh, register with a valid email and password, and confirm the dashboard loads with the user's email shown in the header.

**Acceptance Scenarios**:

1. **Given** no account exists for `ana@example.com`, **When** Ana registers with that email and a 12-character password, **Then** an account is created, she is signed in, and the empty dashboard is shown.
2. **Given** an account already exists for `ana@example.com`, **When** someone tries to register with it, **Then** registration is rejected with a message that does not reveal whether the email exists beyond "could not register".
3. **Given** the registration form, **When** the password is shorter than 10 characters, **Then** the form shows an inline validation error and does not submit.

---

### User Story 2 - Sign In and Stay Signed In (Priority: P1)

A returning user signs in with email and password and remains signed in across browser reloads until they sign out or the session expires.

**Why this priority**: Returning users are the core audience of a habit tracker; friction at sign-in kills retention.

**Independent Test**: Register, reload the page, confirm still signed in; sign out, reload, confirm signed out.

**Acceptance Scenarios**:

1. **Given** a registered user, **When** they submit correct credentials, **Then** they are signed in and redirected to the dashboard.
2. **Given** a registered user, **When** they submit an incorrect password, **Then** the form shows "Invalid email or password" and does not reveal which part was wrong.
3. **Given** a signed-in user, **When** they reload the browser, **Then** they remain signed in.
4. **Given** a signed-in user, **When** 30 days pass without activity, **Then** the session expires and they are asked to sign in again.

---

### User Story 3 - Sign Out (Priority: P2)

A signed-in user clicks "Sign out" and the app returns to the sign-in screen with no user data visible.

**Why this priority**: Required for shared devices, but lower than getting in.

**Independent Test**: Sign in, sign out, attempt to open the dashboard URL directly and confirm redirect to sign-in.

**Acceptance Scenarios**:

1. **Given** a signed-in user, **When** they choose "Sign out", **Then** the session is invalidated server-side and the sign-in screen is shown.
2. **Given** a signed-out browser, **When** it requests any protected page, **Then** it is redirected to sign-in.

---

### Edge Cases

- Email addresses are compared case-insensitively; `Ana@Example.com` and `ana@example.com` are the same account.
- Five failed sign-in attempts within 15 minutes for one email trigger a 15-minute lockout for that email.
- Passwords are never logged, echoed, or stored in plaintext.
- Registration and sign-in still work with JavaScript-only clients (no server-rendered forms required).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow a visitor to register with a unique email and a password of at least 10 characters.
- **FR-002**: System MUST hash passwords with a modern adaptive algorithm before storage.
- **FR-003**: System MUST authenticate users with email and password and issue a session that survives browser reloads.
- **FR-004**: System MUST expire sessions after 30 days of inactivity.
- **FR-005**: Users MUST be able to sign out, which invalidates the session server-side.
- **FR-006**: System MUST reject requests to protected resources without a valid session with an unauthenticated error.
- **FR-007**: System MUST lock sign-in for an email after 5 failed attempts in 15 minutes.
- **FR-008**: System MUST return generic error messages for failed registration and sign-in.

### Key Entities

- **User**: A person with an account. Attributes: unique email, password hash, created timestamp, display timezone (defaults to browser timezone at registration).
- **Session**: A signed-in browser for a User. Attributes: opaque token, created at, last-used at, expires at.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new user can register and reach the dashboard in under 60 seconds.
- **SC-002**: 100% of protected API routes reject unauthenticated requests in automated tests.
- **SC-003**: Sign-in completes in under 500 ms p95 on a local machine.
- **SC-004**: Zero plaintext passwords appear in logs or the database in automated checks.

## Assumptions

- Single-tenant local deployment; no email verification or password reset flow in v1 (see spec 012 for settings, reset is out of scope).
- No social or SSO login in v1.
- Timezone is captured at registration and editable later (spec 012).
