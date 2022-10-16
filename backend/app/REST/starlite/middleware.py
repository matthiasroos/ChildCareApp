import base64

import starlette.status
import starlite

import backend.database.queries_v2
import backend.database.usermanagement


class BasicAuthMiddleware(starlite.AbstractAuthenticationMiddleware):
    """

    """
    async def authenticate_request(self, connection: starlite.ASGIConnection) -> starlite.AuthenticationResult:
        """

        :param connection:
        :return:
        """
        if 'Authorization' not in connection.headers:
            raise starlite.NotAuthorizedException()
        db_config = backend.database.queries_v2.get_database_config()
        db = backend.database.queries_v2.create_session(db_config=db_config)
        username, password = base64.b64decode(connection.headers.get('authorization').split()[1]).split(b':')
        authenticated, role = backend.database.usermanagement.authenticate_user(db=db,
                                                                                user_name=username.decode('utf-8'),
                                                                                password=password.decode('utf-8'))

        db.close()

        if not authenticated:
            raise starlite.NotAuthorizedException()
        return starlite.AuthenticationResult(user=username, auth=role)
