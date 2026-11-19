"""Writes a new random API key to .env, replacing the one that was there."""
import secrets
from pathlib import Path

Path(".env").write_text(f"PRACTICE_API_KEY=practice_key_{secrets.token_hex(12)}\n")
print("Wrote a new API key to .env")
