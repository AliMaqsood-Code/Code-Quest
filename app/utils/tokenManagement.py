import secrets
import hashlib


def generate_token():
    raw_token = secrets.token_urlsafe(32)

    token_hash = hash_token(raw_token)

    return raw_token, token_hash


def hash_token(raw_token):
    return hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()