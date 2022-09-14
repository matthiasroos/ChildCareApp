import base64
import datetime
import typing
import uuid

import fastapi
import fastapi.requests
import fastapi.responses
import fastapi.security
import starlette.authentication
import starlette.middleware.authentication
import starlette.requests
import uvicorn

import backend.database.queries
import backend.database.schemas
import backend.database.usermanagement


app = fastapi.FastAPI(root_path='/rest/fastapi/v1')


class BasicAuthBackend(starlette.authentication.AuthenticationBackend):
    """
    Backend for Basic Authentication
    """
    def __init__(self, role: str):
        super().__init__()
        self.role = role

    async def authenticate(self, conn: fastapi.requests.HTTPConnection) \
            -> typing.Optional[typing.Tuple[starlette.authentication.AuthCredentials,
                                            starlette.authentication.BaseUser]]:
        """

        :param conn:
        :return:
        """
        if 'Authorization' not in conn.headers:
            return

        auth_header = conn.headers['Authorization']
        username, password = base64.b64decode(auth_header.split()[1]).split(b':')
        authenticated = backend.database.usermanagement.authenticate_user(user_name=username.decode('utf-8'),
                                                                          password=password.decode('utf-8'),
                                                                          role=self.role)
        if not authenticated:
            raise starlette.authentication.AuthenticationError('Invalid credentials')
        return starlette.authentication.AuthCredentials(['authenticated']), \
            starlette.authentication.SimpleUser(username)


def on_auth_error(conn: fastapi.requests.HTTPConnection, exc: Exception) -> fastapi.Response:
    """function executed on error"""
    return fastapi.responses.JSONResponse({'error': str(exc)},
                                          status_code=401,
                                          headers={"WWW-Authenticate": "Basic"})


app.add_middleware(starlette.middleware.authentication.AuthenticationMiddleware,
                   backend=BasicAuthBackend(role='admin'),
                   on_error=on_auth_error)


#@app.middleware('http')
async def authenticate_user(request: fastapi.Request, call_next: typing.Callable):
    """

    :return:
    """
    username, password = base64.b64decode(request.headers.get('authorization').split()[1]).split(b':')
    authenticated = backend.database.usermanagement.authenticate_user(username.decode('utf-8'), password.decode('utf-8'))
    if not authenticated:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    response = await call_next(request)
    return response


@app.get('/children', response_model=typing.List[backend.database.schemas.Child])
async def fetch_children(recent: bool = False, limit: int = 10):
    """

    :return:
    """
    result = backend.database.queries.fetch_children(recent=recent, limit=limit)
    return result


@app.get('/children/{child_id}', response_model=backend.database.schemas.Child)
async def fetch_child(child_id: uuid.UUID = fastapi.Path(..., title='ID of the child to get')):
    """

    :return:
    """
    result = backend.database.queries.fetch_child(child_id=child_id)
    return result


@app.post('/children', response_model=backend.database.schemas.Child)
async def fetch_one_child(body: dict):
    """

    :return:
    """
    result = backend.database.queries.fetch_child(child_id=body['child_id'])
    return result


@app.post('/children', status_code=fastapi.status.HTTP_201_CREATED)
async def create_child(child: backend.database.schemas.ChildBase):
    """

    :return:
    """
    child_id = uuid.uuid4()
    child_dict = child.dict()
    child_dict['child_id'] = child_id
    _ = backend.database.queries.create_child(child=child_dict)
    return child_id


@app.put('/children/{child_id}/update')
async def update_child(child_id: uuid.UUID, updates_for_child: backend.database.schemas.ChildUpdate):
    """

    :return:
    """
    updates_dict = {key: values for key, values in updates_for_child.dict().items() if values is not None}
    _ = backend.database.queries.update_child(child_id=child_id, updates_for_child=updates_dict)
    return


@app.delete('/children/{child_id}/delete')
async def delete_child(child_id: uuid.UUID):
    """

    :return:
    """
    backend.database.queries.delete_child(child_id=child_id)
    return


@app.post('/children/{child_id}/caretimes')
async def add_caretime(child_id: uuid.UUID,
                       ):
    """

    :return:
    """
    return None


@app.get('/parents')
async def fetch_parents(limit: int = 10):
    """

    :return:
    """
    return []


@app.get('/is_alive')
def is_alive():
    return {'message': 'Server is alive'}


if __name__ == "__main__":
    uvicorn.run(app, host='localhost', port=8083)
