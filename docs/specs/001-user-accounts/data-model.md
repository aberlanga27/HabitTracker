# Data Model: User Accounts

All timestamps are timezone-aware UTC. IDs are UUIDv7 strings.

## User (`user`)

| Field | Type | Constraints |
|---|---|---|
| id | str (UUIDv7) | PK |
| email | str | required, trimmed + lowercased, ≤ 254 chars, UNIQUE |
| password_hash | str | argon2id hash, never exposed |
| timezone | str | IANA name validated by `zoneinfo`, default `UTC` |
| created_at | datetime (UTC) | required |

## AuthSession (`auth_session`)

| Field | Type | Constraints |
|---|---|---|
| id | str (UUIDv7) | PK |
| user_id | str | FK → user.id, ON DELETE CASCADE, indexed |
| token_hash | str | SHA-256 hex of the cookie token, UNIQUE |
| created_at | datetime (UTC) | required |
| last_used_at | datetime (UTC) | refreshed on each authenticated request |
| expires_at | datetime (UTC) | `last_used_at + 30 days` |

State: created on register/sign-in → refreshed on use → deleted on sign-out or when presented
after `expires_at`.

## FailedLogin (`failed_login`)

| Field | Type | Constraints |
|---|---|---|
| id | str (UUIDv7) | PK |
| email | str | normalized email as submitted (may not match a user), indexed |
| attempted_at | datetime (UTC) | required |

Rows for an email are deleted on successful sign-in.

## Validation rules

- Password: 10–128 characters (FR-001, research R4).
- Email: `local@domain.tld` shape, ≤ 254 chars, compared case-insensitively.
- Timezone: must resolve with `zoneinfo.ZoneInfo`.
