# password-encryption

A secure, zero-knowledge desktop password manager engineered in Python using PBKDF2-HMAC-SHA256 (600,000 iterations), Fernet authenticated symmetric encryption (AES-128-CBC + HMAC-SHA256), and local embedded SQLite storage.

## Features
- **Zero-Knowledge Architecture:** Master password is never stored or hashed on disk; verified via an encrypted check token.
- **High-Work-Factor Key Stretching:** 600,000 iterations of PBKDF2-HMAC-SHA256 with a 16-byte CSPRNG salt.
- **Authenticated Symmetrical Encryption:** Fernet cipher with AES-128-CBC and tamper-evident HMAC-SHA256 tags.
- **CSPRNG Password Generation:** Configurable random password generator utilizing modern Fisher-Yates shuffling.
- **Real-Time Shannon Entropy:** Visual strength rating ($H = L \log_2 N$) with offline common password blacklist screening.
- **Memory & Clipboard Hygiene:** Automatic 5-minute inactivity auto-lock and 20-second operating system clipboard sanitization.
- **Atomic Backup:** Secure database export without decrypting secrets.

## Tech Stack
- **Language:** Python 3.10+
- **Cryptography:** `cryptography>=41.0.0`
- **Database:** SQLite 3
- **GUI:** Tkinter / ttk

## Quick Start
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the application
python main.py
```
