"""Symmetric encryption for BYOK provider credentials at rest.

v1 limitation, documented rather than hidden: this uses a single app-wide
Fernet key (``SECRET_ENCRYPTION_KEY``), not per-workspace envelope
encryption or a KMS. That means anyone with database *and* application
config access can decrypt every workspace's stored keys — acceptable for
a self-hosted v1 where the operator controls both, but not a substitute
for a real secrets manager in a hosted multi-customer deployment. Rotating
the key requires re-encrypting existing rows (not implemented here).
"""

from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings


@lru_cache
def _fernet() -> Fernet:
    key = get_settings().secret_encryption_key
    if not key:
        raise RuntimeError(
            "SECRET_ENCRYPTION_KEY is not set — required before storing any provider "
            "credential. Generate one with: "
            'python -c "from cryptography.fernet import Fernet; '
            'print(Fernet.generate_key().decode())"'
        )
    return Fernet(key.encode())


def encrypt_secret(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_secret(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise RuntimeError(
            "Could not decrypt stored provider credential — SECRET_ENCRYPTION_KEY may "
            "have changed since it was stored."
        ) from exc
