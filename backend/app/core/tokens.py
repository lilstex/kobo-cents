import hashlib
import secrets

# Verification and reset tokens are a different problem from passwords,
# per docs/backend-architecture/00.md, and get a different hash for a
# real reason, not the same default reused out of habit. A token is
# already a cryptographically random 256-bit value, brute-forcing it
# is infeasible regardless of hash speed, so Argon2id's deliberate
# slowness buys nothing here and only adds latency. A fast, standard
# hash is the correct tool for a high-entropy value; Argon2id stays
# reserved for the actual low-entropy case, user-chosen passwords.


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
