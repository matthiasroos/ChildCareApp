import functools
import typing

import flask

import backend.database.usermanagement


def auth_required(role: str) -> typing.Callable:
    """
    Decorator factory to require authentication.

    :return:
    """
    def decorator(func: typing.Callable) -> typing.Callable:
        """
        Decorator.

        :param func: decorated function.
        :return:
        """
        @functools.wraps(func)
        def authenticate_user(*args, **kwargs):
            """
            Authenticate the user using password and role.

            :return:
            """
            username = flask.request.authorization['username']
            password = flask.request.authorization['password']
            authenticated = backend.database.usermanagement.authenticate_user(user_name=username,
                                                                              password=password,
                                                                              role=role)
            if not authenticated:
                raise flask.abort(flask.Response('Invalid credentials', 401))
            return func(*args, **kwargs)
        return authenticate_user
    return decorator
