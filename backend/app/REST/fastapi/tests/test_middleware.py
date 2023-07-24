import asyncio
import datetime
import typing
import unittest.mock
import uuid

import fastapi
import fastapi.testclient
import freezegun
import pytest
import pydantic
import starlette
import starlette.authentication
import starlette.datastructures
import time_machine

import backend.app.REST.fastapi.middleware


# Testing of CloneRequestMiddleware #
@pytest.fixture
def testclient():
    app = fastapi.FastAPI()
    app.add_middleware(backend.app.REST.fastapi.middleware.CloneRequestMiddleware,
                       servers=['http://test_url:9000'])

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
    with unittest.mock.patch('httpx.AsyncClient.request') as mock_requests:

        testclient.get('/test/abc',
                       params={'skip': 0, 'limit': 10})

    assert mock_requests.call_args.kwargs['url'] == 'http://test_url:9000/test/abc'
    assert mock_requests.call_args.kwargs['params'] == b'skip=0&limit=10'


def test_post_call_dict_as_json(testclient):
    with unittest.mock.patch('httpx.AsyncClient.request') as mock_requests:

        testclient.post('/test/abc',
                        params={'skip': 0, 'limit': 10},
                        json={'int_param': 7, 'str_param': 'teststr'})

    assert mock_requests.call_args.kwargs['params'] == b'skip=0&limit=10'
    assert mock_requests.call_args.kwargs['data'] == b'{"int_param": 7, "str_param": "teststr"}'


def test_post_call_bytes_as_data(testclient):
    with unittest.mock.patch('httpx.AsyncClient.request') as mock_requests:

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


# Testing of unused authenticate middleware
def test_authenticate_user_all_is_working(monkeypatch):
    headers = starlette.datastructures.Headers(
        {'Authorization': 'Basic dGVzdF91c2VyOkRnaWRYcXB0OVJJNGM3WDN0MkYz'})
    scope = {
        'method': 'GET',
        'type': 'http',
    }
    request = fastapi.requests.Request(scope)
    request._headers = headers

    monkeypatch.setattr('backend.database.usermanagement.authenticate_user', lambda **kwargs: (True, 'admin'))

    async def func(*args):
        return 1

    response = asyncio.run(backend.app.REST.fastapi.middleware.authenticate_user(request=request,
                                                                                 call_next=func))
    assert response == 1


def test_authenticate_user_error(monkeypatch):

    headers = starlette.datastructures.Headers(
        {'Authorization': 'Basic dGVzdF91c2VyOkRnaWRYcXB0OVJJNGM3WDN0MkYz'})
    scope = {
        'method': 'GET',
        'type': 'http',
    }
    request = fastapi.requests.Request(scope)
    request._headers = headers

    monkeypatch.setattr('backend.database.usermanagement.authenticate_user', lambda **kwargs: (False, None))

    async def func(*args):
        return 1

    with pytest.raises(fastapi.HTTPException):
        _ = asyncio.run(backend.app.REST.fastapi.middleware.authenticate_user(request=request,
                                                                              call_next=func))


# Testing of DBLoggingMiddleware
@pytest.fixture
def logging_testclient():
    app = fastapi.FastAPI()
    app.add_middleware(backend.app.REST.fastapi.middleware.DBLoggingMiddleware)

    @app.post('/test')
    def post_call():
        pass

    client = fastapi.testclient.TestClient(app)
    return client


@freezegun.freeze_time('2023-07-24 18:00')
def test_logging_post_call_freezegun(logging_testclient):
    with unittest.mock.patch('backend.database.queries_v2') as mock_queries, \
         unittest.mock.patch.object(uuid, 'uuid4', side_effect=[uuid.UUID('7d90a67b-282b-431f-b090-8f3f0cf78eb3')]):

        mock_queries.get_database_config.return_value = {}
        db_mock = unittest.mock.MagicMock()
        mock_queries.create_session.return_value = db_mock

        logging_testclient.post('/test', json={'txt_key': 'txt_value'})

    assert mock_queries.write_logging.call_args_list[0].kwargs == {
        'db': db_mock,
        'insert': True,
        'log_entry': {'body': '{"txt_key": "txt_value"}', 'endpoint': '/test', 'method': 'POST', 'query': '',
                      'request_id': uuid.UUID('7d90a67b-282b-431f-b090-8f3f0cf78eb3'),
                      'request_timestamp': datetime.datetime(2023, 7, 24, 18)}
    }
    assert mock_queries.write_logging.call_args_list[1].kwargs == {
        'db': db_mock,
        'insert': False,
        'log_entry': {'request_id': uuid.UUID('7d90a67b-282b-431f-b090-8f3f0cf78eb3'),
                      'status_code': 200,
                      'response_timestamp': datetime.datetime(2023, 7, 24, 18)}
    }


@time_machine.travel('2023-07-24 18:00', tick=False)
def test_logging_post_call_time_machine(logging_testclient):
    with unittest.mock.patch('backend.database.queries_v2') as mock_queries, \
         unittest.mock.patch.object(uuid, 'uuid4', side_effect=[uuid.UUID('7d90a67b-282b-431f-b090-8f3f0cf78eb3')]):
        mock_queries.get_database_config.return_value = {}
        db_mock = unittest.mock.MagicMock()
        mock_queries.create_session.return_value = db_mock

        logging_testclient.post('/test', json={'txt_key': 'txt_value'})

    assert mock_queries.write_logging.call_args_list[0].kwargs == {
        'db': db_mock,
        'insert': True,
        'log_entry': {'body': '{"txt_key": "txt_value"}', 'endpoint': '/test', 'method': 'POST', 'query': '',
                      'request_id': uuid.UUID('7d90a67b-282b-431f-b090-8f3f0cf78eb3'),
                      'request_timestamp': datetime.datetime(2023, 7, 24, 18)}

    }
    assert mock_queries.write_logging.call_args_list[1].kwargs == {
        'db': db_mock,
        'insert': False,
        'log_entry': {'request_id': uuid.UUID('7d90a67b-282b-431f-b090-8f3f0cf78eb3'),
                      'status_code': 200,
                      'response_timestamp': datetime.datetime(2023, 7, 24, 18)}
    }


# Testing of TruncateMiddleware
@pytest.fixture
def truncate_testclient():
    app = fastapi.FastAPI()
    app.add_middleware(backend.app.REST.fastapi.middleware.TruncateMiddleware,
                       long_param='long_txt',
                       limit=10)

    @app.get('/test')
    def get_call():
        pass

    class InputModel(pydantic.BaseModel):
        long_txt: typing.Optional[str]

    @app.post('/test')
    def post_call(body_input: InputModel, ):
        return fastapi.Response(body_input.long_txt)

    client = fastapi.testclient.TestClient(app)
    return client


def test_truncate_get_call(truncate_testclient):

    resp = truncate_testclient.get('/test')

    assert resp.status_code == 200


def test_truncate_post_call0(truncate_testclient):

    resp = truncate_testclient.post('/test',
                                    json={'long_txt': 'AaBbCcDdEeFf'})

    assert resp.text == 'AaBbCcDdEe'


def test_truncate_post_call1(truncate_testclient):

    resp = truncate_testclient.post('/test',
                                    json={'other_txt': 'AaBbCcDdEeFf'})

    assert resp.status_code == 200
