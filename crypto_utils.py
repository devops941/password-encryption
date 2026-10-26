import base64
import os

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

SALT_SIZE = 16
KEY_LENGTH = 32
ITERATIONS = 600_000
VAULT_CHECK_TEXT = b"VAULT_OK"


def generate_salt() -> bytes:
    return os.urandom(SALT_SIZE)


def derive_key(master_password: str, salt: bytes, iterations: int = ITERATIONS) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=iterations,
    )
    raw_key = kdf.derive(master_password.encode("utf-8"))
    return base64.urlsafe_b64encode(raw_key)


def make_fernet(key: bytes) -> Fernet:
    return Fernet(key)


def create_check_token(fernet: Fernet) -> bytes:
    return fernet.encrypt(VAULT_CHECK_TEXT)


def verify_check_token(fernet: Fernet, token: bytes) -> bool:
    try:
        return fernet.decrypt(token) == VAULT_CHECK_TEXT
    except InvalidToken:
        return False


def encrypt_text(fernet: Fernet, plaintext: str) -> bytes:
    return fernet.encrypt((plaintext or "").encode("utf-8"))


def decrypt_text(fernet: Fernet, token: bytes) -> str:
    if not token:
        return ""
    return fernet.decrypt(token).decode("utf-8")
