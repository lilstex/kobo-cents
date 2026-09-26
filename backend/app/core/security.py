from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Argon2id, per docs/backend-architecture/00.md: memory-hard, the
# current recommended default for user passwords specifically, where
# the input is low-entropy and slow, expensive hashing is the whole
# point, it's what makes large-scale guessing infeasible.
_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False
