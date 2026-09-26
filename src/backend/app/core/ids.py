"""UUIDv7 identifiers (RFC 9562); Python 3.13 has no stdlib `uuid7`."""

import os
import threading
import time
import uuid

_lock = threading.Lock()
_last_ms = 0
_counter = 0


def new_id() -> str:
    """Return a new time-ordered UUIDv7 string, monotonic within this process."""
    global _last_ms, _counter
    with _lock:
        ms = time.time_ns() // 1_000_000
        if ms <= _last_ms:
            ms = _last_ms
            _counter += 1
            if _counter > 0xFFF:
                _last_ms += 1
                ms = _last_ms
                _counter = 0
        else:
            _last_ms = ms
            _counter = int.from_bytes(os.urandom(2)) & 0x3FF
        rand_a = _counter & 0xFFF
        rand_b = int.from_bytes(os.urandom(8)) & ((1 << 62) - 1)
    value = (ms << 80) | (0x7 << 76) | (rand_a << 64) | (0b10 << 62) | rand_b
    return str(uuid.UUID(int=value))
