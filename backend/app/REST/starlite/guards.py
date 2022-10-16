import typing

import starlite


def admin_user_guard(role: str) -> typing.Callable:
    """

    :return:
    """
    def wrapper(request: starlite.Request, _: starlite.BaseRouteHandler) -> None:
        if request.auth != role:
            raise starlite.PermissionDeniedException()

    return wrapper
