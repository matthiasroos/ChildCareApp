import base64
import hashlib
import secrets
import string

import database.queries


def create_new_user(user_name: str, password: str):

    salt = ''.join((secrets.choice(string.ascii_letters + string.digits) for _ in range(16)))
    salt_bytes = bytes(salt, 'utf8')

    password_b64_enc = base64.b64encode(bytes(password, 'utf8'))
    pw_hash = hashlib.blake2b(password_b64_enc, salt=salt_bytes).hexdigest()

    user = dict()
    user['user_name'] = user_name
    user['salt'] = salt
    user['hashed_password'] = pw_hash

    database.queries.create_user(user=user)


def authenticate_user(user_name: str, password: str) -> bool:

    user = database.queries.fetch_user(user_name=user_name)
    if not user:
        return False
    salt_b64_enc = bytes(user.salt, 'utf8')
    password_b64_enc = base64.b64encode(bytes(password, 'utf8'))
    pw_hash = hashlib.blake2b(password_b64_enc, salt=salt_b64_enc).hexdigest()

    return secrets.compare_digest(pw_hash, user.hashed_password)
