from app.core.security import (
    hash_password,
    hash_token,
    new_session_token,
    normalize_email,
    verify_password,
)


def test_fr002_hash_password_uses_argon2id_and_never_contains_plaintext() -> None:
    hashed = hash_password("correct-horse-battery")
    assert hashed.startswith("$argon2id$")
    assert "correct-horse-battery" not in hashed


def test_fr002_verify_password_accepts_correct_and_rejects_wrong() -> None:
    hashed = hash_password("correct-horse-battery")
    assert verify_password(hashed, "correct-horse-battery")
    assert not verify_password(hashed, "wrong-password-1")


def test_verify_password_rejects_malformed_hash() -> None:
    assert not verify_password("not-a-hash", "whatever-123")


def test_edge_email_is_trimmed_and_lowercased() -> None:
    assert normalize_email("  Ana@Example.COM ") == "ana@example.com"


def test_session_tokens_are_random_and_hashed_deterministically() -> None:
    first, second = new_session_token(), new_session_token()
    assert first != second
    assert len(first) >= 43  # 32 random bytes, url-safe base64
    assert hash_token(first) == hash_token(first)
    assert hash_token(first) != first
