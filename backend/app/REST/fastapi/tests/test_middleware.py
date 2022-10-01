import asyncio
import unittest.mock

import fastapi
import fastapi.testclient
import pytest
import pydantic
import starlette
import starlette.authentication
import starlette.datastructures

import backend.app.REST.fastapi.middleware


# Testing of CloneRequestMiddleware #
@pytest.fixture
def testclient():
    app = fastapi.FastAPI()
    app.add_middleware(backend.app.REST.fastapi.middleware.CloneRequestMiddleware,
                       servers=['test_url:9000'])

    class InputModel(pydantic.BaseModel):
        int_param: int
        str_param: str

    @app.get('/test/{path_param_1}')
    def get_call(path_param_1: str, skip: int = 0, limit: int = 10):
        pass

    @app.post('/test/{path_param_1}')
    def post_call(path_param_1: str, body_input: InputModel, skip: int = 0, limit: int = 10):
        pass

    client = fastapi.testclient.TestClient(app)
    return client


def test_get_call(testclient):
    with unittest.mock.patch('requests.request') as mock_requests:

        testclient.get('/test/abc',
                       params={'skip': 0, 'limit': 10})

    assert mock_requests.call_args.kwargs['url'] == 'http://test_url:9000/test/abc'
    assert mock_requests.call_args.kwargs['params'] == b'skip=0&limit=10'


def test_post_call_dict_as_json(testclient):
    with unittest.mock.patch('requests.request') as mock_requests:

        testclient.post('/test/abc',
                        params={'skip': 0, 'limit': 10},
                        json={'int_param': 7, 'str_param': 'teststr'})

    assert mock_requests.call_args.kwargs['params'] == b'skip=0&limit=10'
    assert mock_requests.call_args.kwargs['data'] == b'{"int_param": 7, "str_param": "teststr"}'


def test_post_call_bytes_as_data(testclient):
    with unittest.mock.patch('requests.request') as mock_requests:

        testclient.post('/test/abc',
                        params={'skip': 0, 'limit': 10},
                        data=b'{"int_param": 7, "str_param": "teststr"}')

    assert mock_requests.call_args.kwargs['params'] == b'skip=0&limit=10'
    assert mock_requests.call_args.kwargs['data'] == b'{"int_param": 7, "str_param": "teststr"}'


# Testing of BasicAuthBackend
def test_authenticate_all_is_working(monkeypatch):
    headers = starlette.datastructures.Headers(
        {'Authorization': 'Basic dGVzdF91c2VyOkRnaWRYcXB0OVJJNGM3WDN0MkYz'})
    scope = {
        'method': 'GET',
        'type': 'http',
        'headers': None}
    conn = fastapi.requests.HTTPConnection(scope=scope)
    conn._headers = headers

    monkeypatch.setattr('backend.database.usermanagement.authenticate_user', lambda **kwargs: (True, 'admin'))

    basicauthbackend = backend.app.REST.fastapi.middleware.BasicAuthBackend()

    credentials, user = asyncio.run(basicauthbackend.authenticate(conn=conn))

    assert credentials.scopes == ['admin']
    assert user.username == b'test_user'


def test_authenticate_error(monkeypatch):
    headers = starlette.datastructures.Headers(
        {'Authorization': 'Basic dGVzdF91c2VyOkRnaWRYcXB0OVJJNGM3WDN0MkYz'})
    scope = {
        'method': 'GET',
        'type': 'http',
        'headers': None}
    conn = fastapi.requests.HTTPConnection(scope=scope)
    conn._headers = headers

    monkeypatch.setattr('backend.database.usermanagement.authenticate_user', lambda **kwargs: (False, None))

    basicauthbackend = backend.app.REST.fastapi.middleware.BasicAuthBackend()

    with pytest.raises(starlette.authentication.AuthenticationError):
        _, _ = asyncio.run(basicauthbackend.authenticate(conn=conn))
