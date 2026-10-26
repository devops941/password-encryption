import math
import secrets
import string
from pathlib import Path

LOWER = string.ascii_lowercase
UPPER = string.ascii_uppercase
DIGITS = string.digits
SYMBOLS = "!@#$%^&*()-_=+[]{};:,.<>/?"

COMMON_PASSWORDS_PATH = Path(__file__).resolve().parent / "data" / "common_passwords.txt"

_common_cache = None


def load_common_passwords() -> set:
    global _common_cache
    if _common_cache is None:
        try:
            with open(COMMON_PASSWORDS_PATH, "r", encoding="utf-8") as f:
                _common_cache = {line.strip().lower() for line in f if line.strip()}
        except FileNotFoundError:
            _common_cache = set()
    return _common_cache


def generate_password(length=16, use_upper=True, use_lower=True, use_digits=True, use_symbols=True) -> str:
    pool = ""
    required = []
    if use_lower:
        pool += LOWER
        required.append(secrets.choice(LOWER))
    if use_upper:
        pool += UPPER
        required.append(secrets.choice(UPPER))
    if use_digits:
        pool += DIGITS
        required.append(secrets.choice(DIGITS))
    if use_symbols:
        pool += SYMBOLS
        required.append(secrets.choice(SYMBOLS))

    if not pool:
        raise ValueError("Select at least one character type.")
    if length < len(required):
        raise ValueError(f"Length must be at least {len(required)} for the selected options.")

    remaining = [secrets.choice(pool) for _ in range(length - len(required))]
    password_chars = required + remaining

    for i in range(len(password_chars) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        password_chars[i], password_chars[j] = password_chars[j], password_chars[i]

    return "".join(password_chars)


def calculate_entropy(password: str) -> float:
    pool_size = 0
    if any(c.islower() for c in password):
        pool_size += len(LOWER)
    if any(c.isupper() for c in password):
        pool_size += len(UPPER)
    if any(c.isdigit() for c in password):
        pool_size += len(DIGITS)
    if any(c in SYMBOLS for c in password):
        pool_size += len(SYMBOLS)
    if pool_size == 0:
        return 0.0
    return len(password) * math.log2(pool_size)


def rate_strength(password: str) -> str:
    if not password:
        return "Weak"
    if password.lower() in load_common_passwords():
        return "Weak"

    entropy = calculate_entropy(password)
    if entropy < 40:
        return "Weak"
    if entropy < 60:
        return "Medium"
    if entropy < 80:
        return "Strong"
    return "Very Strong"
