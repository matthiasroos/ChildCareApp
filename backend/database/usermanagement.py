import base64
import hashlib
import secrets
import string
import typing

import backend.database.queries


def hash_password(password: str) -> typing.Tuple[str, str]:
    """

    :param password:
    :return:
    """
    salt = ''.join((secrets.choice(string.ascii_letters + string.digits) for _ in range(16)))
    salt_bytes = bytes(salt, 'utf8')

    password_b64_enc = base64.b64encode(bytes(password, 'utf8'))
    pw_hash = hashlib.blake2b(password_b64_enc, salt=salt_bytes).hexdigest()
    return pw_hash, salt


def create_new_user(user_name: str, password: str, role: str) -> None:
    """
    Create a new user in the users database.

    :param user_name: name of the new user
    :param password: password of the new user
    :param role: role of the new user
    :return:
    """

    pw_hash, salt = hash_password(password=password)

    user = dict()
    user['user_name'] = user_name
    user['salt'] = salt
    user['hashed_password'] = pw_hash
    user['role'] = role

    backend.database.queries.create_user(user=user)


def reset_password(user_name: str, password: str) -> None:
    """
    Reset the password of an existing user.

    :param user_name: name of the user
    :param password: new password
    :return:
    """
    pw_hash, salt = hash_password(password=password)

    new_values = dict()
    new_values['salt'] = salt
    new_values['hashed_password'] = pw_hash

    backend.database.queries.edit_user(user_name=user_name, new_values=new_values)


def reset_role(user_name: str, role: str) -> None:
    """
    Reset the role of an existing user.

    :param user_name: name of the user
    :param role: new role
    :return:
    """
    new_values = dict()
    new_values['role'] = role

    backend.database.queries.edit_user(user_name=user_name, new_values=new_values)


def authenticate_user(user_name: str, password: str, role: str) -> bool:
    """
    Authenticate the user using the password and the role.

    :param user_name: name of the user to be authenticated
    :param password: submitted password
    :param role: role the user must have to be authenticated
    :return:  boolean flag, if the user is successfully authenticated or not.
    """

    user = backend.database.queries.fetch_user(user_name=user_name)
    if not user:
        return False
    salt_b64_enc = bytes(user.salt, 'utf8')
    password_b64_enc = base64.b64encode(bytes(password, 'utf8'))
    pw_hash = hashlib.blake2b(password_b64_enc, salt=salt_b64_enc).hexdigest()

    return secrets.compare_digest(pw_hash, user.hashed_password) and secrets.compare_digest(role, user.role)
